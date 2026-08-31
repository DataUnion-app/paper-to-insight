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


if __name__ == "__main__":
    unittest.main()
