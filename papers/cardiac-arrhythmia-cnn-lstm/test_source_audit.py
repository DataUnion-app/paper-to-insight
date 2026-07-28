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
    source = """
self.df_combine = pd.concat([self.df_train, self.df_test])
df_1_up = resample(df_1, replace=True)
df_2_up = resample(df_2, replace=True)
df_3_up = resample(df_3, replace=True)
df_4_up = resample(df_4, replace=True)
self.df_train_balanced = pd.concat([df_0, df_1_up])
# pca = PCA(n_components=combined_predictors)
# pca.fit(X)
# x_pca = pca.transform(X)
train_test_split(X, Y, test_size=0.1)
"""
    labels = (
        "non-ectopic (N) ventricular tachycardia (V) "
        "supraventricular tachycardia (S) fusion (F) "
        "unclassifiable beats (U)"
    )
    return {
        "paper-bibtex": (
            b"10.1007/978-981-16-8774-7_32 "
            b"Automated Detection of Cardiac Arrhythmia Based on a Hybrid "
            b"CNN-LSTM Network"
        ),
        "source-readme": (
            "https://link.springer.com/chapter/"
            "10.1007/978-981-16-8774-7_32 " + labels
        ).encode(),
        "source-main": source.encode(),
        "source-tree": json.dumps(
            {"tree": [{"path": "README.md"}, {"path": "src/ECG_Hybrid.py"}]}
        ).encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_blocks_leaking_unlicensed_source(self):
        result = source_audit.audit(evidence())
        self.assertTrue(result["duplicateLeakagePossible"])
        self.assertFalse(result["claimedPcaEnabled"])
        self.assertFalse(result["eligibleForRuntimeReview"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["source-main"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_detects_future_split_repair(self):
        assets = evidence()
        assets["source-main"] = assets["source-main"].replace(
            b"self.df_train_balanced = pd.concat([df_0, df_1_up])",
            b"# repaired before resampling",
        )
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
