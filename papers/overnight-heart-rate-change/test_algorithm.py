#!/usr/bin/env python3

import json
import math
import unittest
from pathlib import Path

from algorithm import InputError, SCHEMA, analyze


ROOT = Path(__file__).resolve().parent


class OvernightHeartRateChangeTest(unittest.TestCase):
    def test_public_fixture(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        expected = json.loads((ROOT / "expected-public.json").read_text())
        self.assertEqual(analyze(source), expected)

    def test_translation_excludes_comparison_nights_from_baseline(self):
        result = analyze({"schema": SCHEMA, "nightlyMeanBpm": [60] * 7 + [64, 65]})
        translation = result["brainstemTranslation"]
        self.assertEqual(translation["baselineMedianBpm"], 60)
        self.assertTrue(translation["consecutiveIncreaseAtLeast4Bpm"])

    def test_rejects_unknown_nonfinite_and_short_inputs(self):
        invalid = [
            {"schema": SCHEMA, "nightlyMeanBpm": [60] * 8},
            {"schema": SCHEMA, "nightlyMeanBpm": [60] * 8 + [math.nan]},
            {"schema": SCHEMA, "nightlyMeanBpm": [60] * 9, "extra": True},
        ]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(InputError):
                    analyze(value)


if __name__ == "__main__":
    unittest.main()
