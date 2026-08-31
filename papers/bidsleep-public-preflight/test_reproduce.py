#!/usr/bin/env python3

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("bidsleep_reproduce", ROOT / "reproduce.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReproduceTest(unittest.TestCase):
    def test_rwl_is_finite_and_ignores_masked_labels(self):
        false_negative, false_positive = MODULE.rwl_matrices(np.asarray([10, 20, 30, 40]))
        self.assertTrue(torch.equal(torch.diag(false_positive), torch.zeros(4)))
        logits = torch.tensor([[[2.0, 1.0, 0.0, -1.0], [1.0, 2.0, 0.0, -1.0]]])
        labels = torch.tensor([[0, 1]])
        mask = torch.tensor([[True, False]])
        first = MODULE.masked_rwl_loss(logits, labels, mask, false_negative, false_positive)
        labels[0, 1] = 3
        logits[0, 1] = 100
        second = MODULE.masked_rwl_loss(logits, labels, mask, false_negative, false_positive)
        self.assertTrue(torch.equal(first, second))
        self.assertTrue(torch.isfinite(first))

    def test_metrics_are_exact_for_perfect_predictions(self):
        labels = torch.tensor([0, 1, 2, 3])
        logits = torch.full((4, 4), -10.0)
        logits[torch.arange(4), labels] = 10.0
        metrics = MODULE.metrics_from_logits(logits, labels)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["weightedF1"], 1.0)
        self.assertEqual(metrics["weightedMcc"], 1.0)
        self.assertEqual(metrics["confusionTruthByPrediction"], np.eye(4, dtype=int).tolist())

    def test_metrics_follow_paper_macro_and_inverse_frequency_formulas(self):
        labels = torch.tensor([0, 0, 0, 1, 2, 3])
        predictions = torch.tensor([0, 0, 1, 1, 2, 3])
        logits = torch.full((len(labels), 4), -10.0)
        logits[torch.arange(len(labels)), predictions] = 10.0
        metrics = MODULE.metrics_from_logits(logits, labels)
        per_class = list(metrics["perClass"].values())
        self.assertAlmostEqual(
            metrics["sensitivity"], np.mean([item["sensitivity"] for item in per_class])
        )
        self.assertNotAlmostEqual(metrics["sensitivity"], metrics["accuracy"])
        inverse = np.reciprocal(np.asarray([item["support"] for item in per_class], dtype=float))
        inverse /= inverse.sum()
        self.assertAlmostEqual(
            metrics["weightedF1"], inverse @ [item["f1"] for item in per_class]
        )

    def test_class_counts_use_only_released_labels(self):
        records = [
            {
                "labels": np.asarray([0, 1, 2, 3, 3]),
                "releaseMask": np.asarray([True, True, True, True, False]),
            }
        ]
        self.assertEqual(MODULE.train_class_counts(records).tolist(), [1, 1, 1, 1])

    def test_partition_rejects_path_escape_before_reading(self):
        plan = {
            "schema": "paper-to-insight.bidsleep-public-plan/v2",
            "assignment": {"status": "reconstructed_from_published_counts"},
            "partitions": {"train": {"nights": ["../outside"]}},
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "unsafe night identity"):
                MODULE.load_partition(Path(directory), plan, "train")

    def test_checkpoint_signature_mismatch_fails_closed(self):
        payload = {
            "schema": "paper-to-insight.bidsleep-training-checkpoint/v1",
            "signature": {"seed": 1},
        }
        MODULE.validate_checkpoint(payload, {"seed": 1})
        with self.assertRaisesRegex(ValueError, "different experiment"):
            MODULE.validate_checkpoint(payload, {"seed": 2})

    def test_checkpoint_round_trip_restores_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.pt"
            signature = {"seed": 7}
            model = torch.nn.Linear(2, 1)
            optimizer = torch.optim.Adam(model.parameters())
            model(torch.ones(1, 2)).sum().backward()
            optimizer.step()
            expected = {name: value.detach().clone() for name, value in model.state_dict().items()}
            MODULE.save_checkpoint(
                path,
                signature,
                3,
                model,
                optimizer,
                {"weightedF1": 0.5},
                [{"epoch": 3}],
                12.5,
                torch.device("cpu"),
            )
            restored = torch.nn.Linear(2, 1)
            restored_optimizer = torch.optim.Adam(restored.parameters())
            start, best, history, elapsed = MODULE.restore_checkpoint(
                path, signature, restored, restored_optimizer, torch.device("cpu")
            )
            self.assertEqual(start, 4)
            self.assertEqual(best["weightedF1"], 0.5)
            self.assertEqual(history, [{"epoch": 3}])
            self.assertEqual(elapsed, 12.5)
            for name, value in restored.state_dict().items():
                self.assertTrue(torch.equal(value, expected[name]))


if __name__ == "__main__":
    unittest.main()
