#!/usr/bin/env python3

import copy
import hashlib
import json
import math
import unittest
from pathlib import Path

from algorithm import InputError, SCHEMA, analyze
from generate_fixture import recording


ROOT = Path(__file__).resolve().parent


def participant(index: int, recordings: list[dict]) -> dict:
    return {
        "subjectId": hashlib.sha256(f"test-subject-{index}".encode()).hexdigest(),
        "recordings": recordings,
    }


class StandingHeartRateResponseTest(unittest.TestCase):
    def test_generated_cohort(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        expected = json.loads((ROOT / "expected-public.json").read_text())
        self.assertEqual(analyze(source), expected)

    def test_canonical_windows_and_personal_summary(self):
        value = {
            "schema": SCHEMA,
            "mode": "personal",
            "participants": [participant(0, [recording(60, 20, 1)])],
        }
        result = analyze(value)
        self.assertEqual(result["recordingCount"], 1)
        self.assertAlmostEqual(result["metrics"]["restingHeartRateBpm"]["median"], 60, places=1)
        self.assertAlmostEqual(result["metrics"]["standingP95HeartRateBpm"]["median"], 80, places=1)
        self.assertAlmostEqual(result["metrics"]["responseBpm"]["median"], 20, places=1)

    def test_cohort_floor(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        source["participants"] = source["participants"][:19]
        self.assertEqual(analyze(source)["reason"], "privacy_floor")

    def test_repeated_records_do_not_change_participant_weight(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        single = copy.deepcopy(source)
        for item in single["participants"]:
            item["recordings"] = item["recordings"][:1]
        repeated = copy.deepcopy(single)
        first = repeated["participants"][0]["recordings"][0]
        repeated["participants"][0]["recordings"] = [
            {**copy.deepcopy(first), "recordingIndex": index}
            for index in range(1, 8)
        ]
        self.assertEqual(analyze(single)["metrics"], analyze(repeated)["metrics"])

    def test_rejects_tampering_artifacts_missing_coverage_and_duplicates(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        extra = copy.deepcopy(source)
        extra["participants"][0]["recordings"][0]["postureScore"] = 999
        artifact = copy.deepcopy(source)
        artifact["participants"][0]["recordings"][0]["rrIntervalsMs"][0] = math.nan
        short = copy.deepcopy(source)
        short["participants"][0]["recordings"][0]["rrIntervalsMs"] = [1000] * 200
        duplicate = copy.deepcopy(source)
        duplicate["participants"][1]["subjectId"] = duplicate["participants"][0]["subjectId"]
        for value in (extra, artifact, short, duplicate):
            with self.subTest(value=value):
                with self.assertRaises(InputError):
                    analyze(value)


if __name__ == "__main__":
    unittest.main()

