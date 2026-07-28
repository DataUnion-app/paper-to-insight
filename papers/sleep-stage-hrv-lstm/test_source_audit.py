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
        "10.1038/s41598-019-49703-y "
        "Creative Commons Attribution 4.0 International License "
        "total number of participants was 292 584 nights 132 HRV features "
        "randomly split into folds at the level of participants "
        "For wake, precision For REM, precision "
        "For combined N1/N2 Finally, for N3"
    )
    readme = (
        "this databse is not free {AWAKE REM S1 S2 S3 S4} "
        "just a simple framework"
    )
    return {
        "paper-xml": paper.encode(),
        "source-readme": readme.encode(),
        "source-tree": json.dumps(
            {
                "tree": [
                    {"path": "README.md"},
                    {"path": "FeatureSample.mat"},
                    {"path": "lstm_classification.m"},
                    {"path": "lstm_regression.m"},
                ]
            }
        ).encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_blocks_unrelated_unlicensed_framework(self):
        result = source_audit.audit(evidence())
        self.assertTrue(result["paperParticipantLevelValidation"])
        self.assertEqual(result["sourceClassCount"], 6)
        self.assertFalse(result["eligibleForRuntimeReview"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["paper-xml"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_detects_future_license_file(self):
        assets = evidence()
        tree = json.loads(assets["source-tree"])
        tree["tree"].append({"path": "LICENSE"})
        assets["source-tree"] = json.dumps(tree).encode()
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
