#!/usr/bin/env python3

import copy
import json
import math
import unittest
from pathlib import Path

from algorithm import InputError, SCHEMA, analyze


ROOT = Path(__file__).resolve().parent


class RestingHrvRepeatabilityTest(unittest.TestCase):
    def test_generated_cohort(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        expected = json.loads((ROOT / "expected-public.json").read_text())
        self.assertEqual(analyze(source), expected)

    def test_personal_summary(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        source["mode"] = "personal"
        source["participants"] = source["participants"][:1]
        result = analyze(source)
        self.assertEqual(result["mode"], "personal")
        self.assertEqual(result["recordingCount"], 7)
        self.assertGreater(result["metrics"]["rmssdMs"]["cvPercent"], 0)

    def test_cohort_floor(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        source["participants"] = source["participants"][:19]
        self.assertEqual(analyze(source)["reason"], "privacy_floor")

    def test_rejects_duplicate_nonfinite_and_unknown_fields(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        duplicate = copy.deepcopy(source)
        duplicate["participants"][1]["subjectId"] = duplicate["participants"][0]["subjectId"]
        nonfinite = copy.deepcopy(source)
        nonfinite["participants"][0]["recordings"][0]["rmssdMs"] = math.nan
        unknown = copy.deepcopy(source)
        unknown["extra"] = True
        for value in (duplicate, nonfinite, unknown):
            with self.subTest(value=value):
                with self.assertRaises(InputError):
                    analyze(value)


if __name__ == "__main__":
    unittest.main()
