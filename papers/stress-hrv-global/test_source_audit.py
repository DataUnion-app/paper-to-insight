import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "source_audit", ROOT / "source-audit.py"
)
source_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(source_audit)


def evidence():
    notebook = {
        "cells": [
            {
                "source": [
                    "for group_id, group_data in df.groupby(group_col):\n",
                    " train_test_split(\n",
                    " test_size=test_size\n",
                    "test_size = 0.3\n",
                    "RandomForestClassifier(max_depth=20, "
                    "min_samples_split=2, n_estimators=100)\n",
                ]
            }
        ]
    }
    return {
        "paper-xml": (
            b"10.3390/s23115220 Creative Commons Attribution (CC BY) "
            b"KURT, VLF, MEAN_REL_RR, HR_HF, pNN25, KURT_REL_RR, TP, "
            b"and MEDIAN_REL_RR_LOG 70% of data instances of each subject "
            b"dataset testing dataset has 30% of data instances"
        ),
        "source-readme": (
            b"https://www.kaggle.com/datasets/qiriro/stress "
            b"https://doi.org/10.17026/dans-x55-69zp"
        ),
        "source-notebook": json.dumps(notebook).encode(),
        "source-tree": json.dumps(
            {"tree": [{"path": "README.md"}, {"path": "combined_20_100.ipynb"}]}
        ).encode(),
        "dataset-card": json.dumps(
            {"licenseName": "CC0: Public Domain"}
        ).encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_dataset_checksum_ignores_usage_counters(self):
        card = {
            "id": 191041,
            "ref": "qiriro/stress",
            "title": "Biometrics for stress monitoring",
            "ownerRef": "qiriro",
            "licenseName": "CC0: Public Domain",
            "currentVersionNumber": 1,
            "lastUpdated": "2019-05-12T16:31:04.393Z",
            "totalBytes": 9253090345,
            "viewCount": 1,
        }
        first = source_audit.checksum("dataset-card", json.dumps(card).encode())
        card["viewCount"] = 2
        self.assertEqual(
            first,
            source_audit.checksum("dataset-card", json.dumps(card).encode()),
        )

    def test_blocks_subject_mixed_unlicensed_source(self):
        result = source_audit.audit(evidence())
        self.assertFalse(result["eligibleForRuntimeReview"])
        self.assertFalse(result["brainstemClassificationEnabled"])
        self.assertTrue(result["eligibleForIndependentReimplementation"])
        self.assertIn("participant_split_leakage", result["blockReasons"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["paper-xml"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_detects_future_license_file(self):
        assets = evidence()
        assets["source-tree"] = json.dumps(
            {
                "tree": [
                    {"path": "README.md"},
                    {"path": "combined_20_100.ipynb"},
                    {"path": "LICENSE"},
                ]
            }
        ).encode()
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
