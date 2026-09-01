#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("source_audit", ROOT / "source-audit.py")
source_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(source_audit)


class SourceAuditTest(unittest.TestCase):
    def test_promotes_only_the_descriptive_subset(self):
        evidence = (
            b"10.1007/s10286-019-00606-y continuous beat-to-beat non-invasive blood pressure monitoring "
            b"first 3&#xa0;min of active standing focusing on beat-to-beat BP technologies "
            b"complexity of its interpretation"
        )
        result = source_audit.audit(evidence)
        self.assertEqual(result["promotionStatus"], "promote")
        self.assertEqual(result["promotionScope"], "descriptive_heart_rate_only")
        self.assertFalse(result["fullTextAudited"])

    def test_rejects_missing_blood_pressure_boundary(self):
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(b"10.1007/s10286-019-00606-y")


if __name__ == "__main__":
    unittest.main()
