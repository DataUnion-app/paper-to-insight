#!/usr/bin/env python3

import copy
import json
import math
import unittest
from pathlib import Path

from algorithm import InputError, analyze


ROOT = Path(__file__).resolve().parent


class HeartRateFragmentationTest(unittest.TestCase):
    def source(self):
        return json.loads((ROOT / "generated-fixture.json").read_text())

    def test_generated_result_is_deterministic(self):
        source = self.source()
        expected = json.loads((ROOT / "expected-generated.json").read_text())
        self.assertEqual(analyze(source), expected)
        self.assertEqual(analyze(source), analyze(copy.deepcopy(source)))

    def test_order_and_artifacts_change_the_metric(self):
        source = self.source()
        baseline = analyze(source)["metrics"]["pipPercent"]
        reordered = copy.deepcopy(source)
        reordered["normalToNormalIntervalsMs"] = sorted(
            reordered["normalToNormalIntervalsMs"]
        )
        self.assertNotEqual(analyze(reordered)["metrics"]["pipPercent"], baseline)

        artifact = copy.deepcopy(source)
        artifact["normalToNormalIntervalsMs"][20:30] = [760, 840] * 5
        self.assertGreater(analyze(artifact)["metrics"]["pipPercent"], baseline)

    def test_rejects_seconds_missing_nonfinite_short_and_extra_fields(self):
        source = self.source()
        seconds = copy.deepcopy(source)
        seconds["normalToNormalIntervalsMs"] = [item / 1000 for item in seconds["normalToNormalIntervalsMs"]]
        missing = copy.deepcopy(source)
        del missing["normalToNormalIntervalsMs"]
        nonfinite = copy.deepcopy(source)
        nonfinite["normalToNormalIntervalsMs"][0] = math.nan
        short = copy.deepcopy(source)
        short["normalToNormalIntervalsMs"] = short["normalToNormalIntervalsMs"][:49]
        brief = copy.deepcopy(source)
        brief["normalToNormalIntervalsMs"] = [400] * 50
        extra = copy.deepcopy(source)
        extra["reportedRisk"] = 99
        for value in (seconds, missing, nonfinite, short, brief, extra):
            with self.subTest(value=value):
                with self.assertRaises(InputError):
                    analyze(value)


if __name__ == "__main__":
    unittest.main()
