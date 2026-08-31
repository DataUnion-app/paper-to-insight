#!/usr/bin/env python3

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("bidsleep_paper_lstm", ROOT / "paper_lstm.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PaperLSTMTest(unittest.TestCase):
    def test_shapes_and_one_seeded_step(self):
        MODULE.seed_everything(7)
        model = MODULE.PaperLSTM()
        signal = torch.randn(1, 8, 30, 2)
        covariates = torch.randn(1, 8, 2)
        sequence_mask = torch.tensor([[True, True, True, True, True, True, False, False]])
        labels = torch.tensor([[0, 1, 1, 2, 3, 0, 0, 0]])
        logits = model(signal, covariates, sequence_mask, labels, sequence_mask)
        self.assertEqual(tuple(logits.shape), (1, 8, 4))
        loss = torch.nn.functional.cross_entropy(logits[sequence_mask], labels[sequence_mask])
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        model.eval()
        self.assertEqual(tuple(model(signal, covariates, sequence_mask).shape), (1, 8, 4))

    def test_unreleased_label_cannot_enter_teacher_forcing(self):
        MODULE.seed_everything(9)
        model = MODULE.PaperLSTM().eval()
        signal = torch.randn(1, 4, 30, 2)
        covariates = torch.randn(1, 4, 2)
        sequence_mask = torch.ones(1, 4, dtype=torch.bool)
        teacher_mask = torch.tensor([[True, False, True, True]])
        labels_a = torch.tensor([[0, 0, 1, 2]])
        labels_b = torch.tensor([[0, 3, 1, 2]])
        with torch.no_grad():
            output_a = model(signal, covariates, sequence_mask, labels_a, teacher_mask)
            output_b = model(signal, covariates, sequence_mask, labels_b, teacher_mask)
        self.assertTrue(torch.equal(output_a, output_b))

    def test_rejects_empty_attention_mask(self):
        model = MODULE.PaperLSTM()
        with self.assertRaisesRegex(ValueError, "at least one valid epoch"):
            model(
                torch.zeros(1, 2, 30, 2),
                torch.zeros(1, 2, 2),
                torch.zeros(1, 2, dtype=torch.bool),
            )

    def test_rejects_non_contiguous_sequence_mask(self):
        model = MODULE.PaperLSTM()
        with self.assertRaisesRegex(ValueError, "left-aligned contiguous"):
            model(
                torch.zeros(1, 3, 30, 2),
                torch.zeros(1, 3, 2),
                torch.tensor([[True, False, True]]),
            )

    def test_public_archive_binding_and_separate_masks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "aligned.npz"
            np.savez(
                archive,
                signal_1hz=np.arange(120, dtype=np.float32).reshape(60, 2) + 1,
                epoch_freq_hr_stats=np.asarray([[0.2, 60, 1], [0.1, 62, 2]], dtype=np.float32),
                epoch_time_candidates=np.asarray([[0.5, 0], [0.6, 0.5]], dtype=np.float32),
                stage_four=np.asarray([0, 1], dtype=np.uint8),
                stage_mask=np.asarray([True, False]),
            )
            receipt = root / "aligned.receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "schema": "paper-to-insight.bidsleep-aligned-night/v1",
                        "brainstemExecutionEnabled": False,
                        "outputSha256": MODULE.sha256(archive),
                    }
                )
            )
            _, _, _, sequence_mask, release_mask, _ = MODULE.load_public_night(
                archive, receipt, epochs=4
            )
            self.assertEqual(sequence_mask.tolist(), [True, True, False, False])
            self.assertEqual(release_mask.tolist(), [True, False, False, False])
            receipt.write_text(receipt.read_text().replace(MODULE.sha256(archive), "0" * 64))
            with self.assertRaisesRegex(ValueError, "hash"):
                MODULE.load_public_night(archive, receipt, epochs=4)


if __name__ == "__main__":
    unittest.main()
