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
        "10.1038/s41746-023-00960-2 "
        "Creative Commons Attribution 4.0 International License "
        "https://github.com/HyeonhoonLee/hrvarrest "
        "LGBM model using 33 HRV measures "
        "5\u2009min epochs "
        "development (80%) and validation (20%) sets at the patient level "
        "dataset used in this study is not publicly available"
    )
    source = """
hrvs = pd.read_csv(f'dataset.csv', index_col=0)
stayids = hrvs['stayid']
tests = hrvs['test']
params = {'num_leaves': int(round(num_leaves))}
optimizer = BayesianOptimization(f=eval_function, pbounds={})
"""
    return {
        "paper-xml": paper.encode(),
        "source-readme": b"Real-time prediction of in-hospital cardiac arrest",
        "source-main": source.encode(),
        "source-tree": json.dumps(
            {"tree": [{"path": "README.md"}, {"path": "main.py"}]}
        ).encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_blocks_incomplete_unlicensed_source(self):
        result = source_audit.audit(evidence())
        self.assertFalse(result["trainingScriptRunnable"])
        self.assertFalse(result["eligibleForRuntimeReview"])
        self.assertIn("public_reproduction_failed", result["blockReasons"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["source-main"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_detects_future_optimizer_fix(self):
        assets = evidence()
        assets["source-main"] += b"\ndef eval_function(): pass\n"
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
