import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("source_audit", ROOT / "source-audit.py")
source_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(source_audit)


def evidence():
    features = [f"f{index}" for index in range(64)] + ["label"]
    return {
        "source-readme": b"doi 10.3390/app15031178",
        "source-license": b"The MIT License",
        "source-make-dataset": b"train_test_split",
        "source-predict-model": b"",
        "source-synthetic-ce": (",".join(features) + "\n").encode(),
        "source-train-model": b"sc = StandardScaler()",
        "source-transfer-model": b"sc = StandardScaler()",
        "source-test-model": (
            b"csv2df(input_filepath)\n"
            b"dataframe['label']\n"
            b"roc_auc_score(y, y_predictions)\n"
            b"calculate_sensitivity_specificity(cm_list[0], cm_list[3], cm_list[1], cm_list[2])"
        ),
    }


class SourceAuditTest(unittest.TestCase):
    def test_blocks_incomplete_inference_contract(self):
        result = source_audit.audit(evidence())
        self.assertFalse(result["eligibleForRuntimeReview"])
        self.assertFalse(result["brainstemClassificationEnabled"])
        self.assertIn("public_reproduction_failed", result["blockReasons"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["source-test-model"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_detects_future_prediction_implementation(self):
        assets = evidence()
        assets["source-predict-model"] = b"def predict(): pass"
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
