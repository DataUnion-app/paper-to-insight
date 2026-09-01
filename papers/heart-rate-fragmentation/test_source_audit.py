#!/usr/bin/env python3

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
        "original-paper-xml": (
            b"10.3389/fphys.2017.00255 Creative Commons Attribution License (CC BY) "
            b"percentage of zero-crossing inverse of the average length alternation segment"
        ),
        "reference-code": (
            b"ann == 1 normal sinus PIP PNNSS PNNLS NN_max = 1.800"
        ),
        "reference-license": b"GNU GENERAL PUBLIC LICENSE Version 3",
        "reference-readme": b"NN intervals < 0.3 s or > 1.5 s were excluded",
        "reference-series-a": b"a",
        "reference-series-b": b"b",
        "reference-series-c": b"c",
    }


def expected_runner(_code, series):
    key = {
        b"a": "reference-series-a",
        b"b": "reference-series-b",
        b"c": "reference-series-c",
    }[series]
    return source_audit.EXPECTED_OUTPUTS[key]


class SourceAuditTest(unittest.TestCase):
    def test_reproduction_stays_study_only(self):
        result = source_audit.audit(evidence(), runner=expected_runner)
        self.assertTrue(result["authorReferenceReproduced"])
        self.assertEqual(result["promotionStatus"], "study_only")
        self.assertFalse(result["eligibleForRuntimeReview"])
        self.assertIn("normal_to_normal_annotations_unavailable", result["blockReasons"])

    def test_requires_complete_evidence_and_exact_outputs(self):
        incomplete = evidence()
        del incomplete["reference-readme"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(incomplete, runner=expected_runner)
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(evidence(), runner=lambda _code, _series: "different")


if __name__ == "__main__":
    unittest.main()
