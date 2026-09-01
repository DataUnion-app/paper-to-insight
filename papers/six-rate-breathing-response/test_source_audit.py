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
    def test_holds_runtime_and_resolves_only_curve_rule(self):
        evidence = {
            "practical-guide-full-text": (
                b"10.3389/fnins.2020.570400 Creative Commons Attribution License (CC BY) "
                b"6.5 to 4.5 breaths per min 2-min intervals from 6.5 to 4.5 bpm"
            ),
            "brief-exercise-full-text": (
                b"10.1007/s10484-025-09687-0 Creative Commons Attribution 4.0 International License "
                b"Initially, participants were asked to breath at a rate of 7.0 "
                b"decreased by increments of 0.5 respiration belt and three-lead ECG sensors "
                b"visually inspected for artifacts"
            ),
        }
        result = source_audit.audit(evidence)
        self.assertEqual(result["promotionStatus"], "hold")
        self.assertFalse(result["eligibleForProtectedRuntimeReview"])
        self.assertEqual(result["resolvedDelta"], "generated_response_curve_and_all_ties_rule")

    def test_rejects_missing_adherence_boundary(self):
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(
                {
                    "practical-guide-full-text": b"10.3389/fnins.2020.570400",
                    "brief-exercise-full-text": b"10.1007/s10484-025-09687-0",
                }
            )


if __name__ == "__main__":
    unittest.main()
