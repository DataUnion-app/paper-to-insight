import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("source_audit", ROOT / "source-audit.py")
source_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(source_audit)


def evidence():
    return {
        "source-readme": b"This is a personal project for the Insight Data Science program. The dataset has 70 participants.",
        "source-license": b"MIT License",
        "source-model-evaluation": (
            b"StratifiedKFold\n"
            b'skf.split(file_df, file_df["group"])\n'
            b'file_df.loc[idx_train, "file"]\n'
            b'file_df.loc[idx_val, "file"]\n'
        ),
        "source-training-index": b"file,group,neg,pos\nc05,C,1,2\nc06,C,2,1\n",
        "dataset-page": (
            b"The data consist of 70 records. c05 and c06 come from the same original recording; "
            b"c05 begins 80 seconds later than c06."
        ),
        "dataset-manifest": (
            b"25c86153fc254cff961541ee414d8174c9b5f29e3ec989cebc1103edd02b8ec9 "
            b"additional-information.txt\n"
        ),
    }


class SourceAuditTest(unittest.TestCase):
    def test_blocks_record_level_source(self):
        result = source_audit.audit(evidence())
        self.assertFalse(result["eligibleForRuntimeReview"])
        self.assertFalse(result["brainstemClassificationEnabled"])
        self.assertIn("participant_split_leakage", result["blockReasons"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["dataset-page"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_requires_participant_mapping(self):
        assets = evidence()
        assets["source-training-index"] = (
            b"file,group,neg,pos,participant_id\nc05,C,1,2,p1\nc06,C,2,1,p1\n"
        )
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
