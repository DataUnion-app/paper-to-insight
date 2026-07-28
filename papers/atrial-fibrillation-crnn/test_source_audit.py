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
    readme = (
        "Convolutional Recurrent Neural Networks for Electrocardiogram "
        "Classification https://arxiv.org/abs/1710.06122 "
        "2017 PhysioNet/CinC Challenge"
    )
    helper = (
        "stratified_split(id_list=ids, labels=load_label(ids), "
        "shuffle=True)"
    )
    paths = [
        "README.md",
        "codes/train.py",
        "models/CNN_paper.json",
        "models/CRNN_paper.json",
    ]
    return {
        "paper-pdf": b"%PDF-1.4",
        "source-readme": readme.encode(),
        "source-dataset-helper": helper.encode(),
        "source-split-properties": json.dumps(
            {
                "inputs": {"holdout": False},
                "relative size": {"holdout": 0},
            }
        ).encode(),
        "source-tree": json.dumps(
            {"tree": [{"path": path} for path in paths]}
        ).encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_blocks_unlicensed_record_split_source(self):
        result = source_audit.audit(evidence())
        self.assertFalse(result["sourceCodeLicenseVerified"])
        self.assertFalse(result["participantSeparatedValidation"])
        self.assertFalse(result["eligibleForRuntimeReview"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["paper-pdf"]
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
