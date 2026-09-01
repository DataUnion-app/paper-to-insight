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
    def test_promotes_only_exact_protocol_descriptors(self):
        evidence = (
            b"10.1007/s10484-023-09582-6 Creative Commons Attribution 4.0 International License "
            b"there is still a lack of a <italic>gold standard</italic> inhalation and exhalation rate "
            b"monitoring whether participants/patients breathe at the correct ratio is crucial "
            b"plan for artifact prevention and data analysis"
        )
        result = source_audit.audit(evidence)
        self.assertEqual(result["promotionStatus"], "promote")
        self.assertEqual(result["promotionScope"], "exact_protocol_descriptive_heart_rate_only")
        self.assertIn("measured_breathing_adherence", result["unavailableSignals"])

    def test_rejects_missing_protocol_boundary(self):
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(b"10.1007/s10484-023-09582-6")


if __name__ == "__main__":
    unittest.main()
