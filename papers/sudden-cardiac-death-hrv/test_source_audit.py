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
        "10.3390/medicina59081394 "
        "Creative Commons Attribution (CC BY) license "
        "115 subjects This study included five subject groups "
        "six features mentioned above, this study includes two other features "
        "six segments per subject segmented into 5 min intervals "
        "30 min preceding the onset of VF "
        "grid search identifies the hyperparameters that yield the best "
        "performance on the testing set "
        "training distribution of 80% and a testing distribution of 20%"
    )
    return {
        "paper-xml": paper.encode(),
        "source-readme": (
            b"Research-paper(SVM algorithm Implementation) "
            b"Prediction of Sudden Cardiac Death using SVM"
        ),
        "source-tree": json.dumps(
            {
                "tree": [
                    {"path": "README.md"},
                    {"path": "SVM_Based_Classification_for_SCD_prediction.pdf"},
                ]
            }
        ).encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_blocks_unrelated_document_only_source(self):
        result = source_audit.audit(evidence())
        self.assertEqual(
            result["sourceRelationship"], "unrelated_supplied_repository"
        )
        self.assertTrue(result["paperUsesTestingSetForModelSelection"])
        self.assertFalse(result["eligibleForRuntimeReview"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["paper-xml"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_detects_future_executable_source(self):
        assets = evidence()
        tree = json.loads(assets["source-tree"])
        tree["tree"].append({"path": "model.py"})
        assets["source-tree"] = json.dumps(tree).encode()
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
