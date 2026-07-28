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
    paper = (
        "10.3390/s20143987 "
        "Creative Commons Attribution (CC BY) license "
        "four time-domain indices four frequency-domain indices "
        "three-minute moving window six principal components "
        "Data from fourteen patients remaining seven patients "
        "Two or more experts from the Japan Epilepsy Society labeled seizures "
        "modeling parameters of x used from Fujiwara et al."
    )
    prediction = (
        "Download patient data from [Epilepsiae dataset] "
        "patient-specific model Bands of EEG:"
    )
    return {
        "paper-xml": paper.encode(),
        "source-readme": (
            b"Deep Learning on Fused Brain and Heart Signals "
            b"features extracted from EEG and ECG signal"
        ),
        "source-prediction-readme": prediction.encode(),
        "source-license": (
            b"Redistribution and use in source and binary forms "
            b"Neither the name of epilepsy-system"
        ),
        "source-tree": json.dumps(
            {
                "tree": [
                    {"path": "LICENSE"},
                    {"path": "README.md"},
                    {"path": "seizure prediction code/README.md"},
                ]
            }
        ).encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_blocks_unrelated_incomplete_source(self):
        result = source_audit.audit(evidence())
        self.assertEqual(
            result["sourceRelationship"], "unrelated_supplied_repository"
        )
        self.assertFalse(result["eligibleForRuntimeReview"])
        self.assertIn("public_reproduction_failed", result["blockReasons"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["paper-xml"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_rejects_a_future_repository_link(self):
        assets = evidence()
        assets["paper-xml"] += b" https://github.com/example/repository"
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
