#!/usr/bin/env python3

import copy
import hashlib
import json
import math
import unittest
from pathlib import Path

from algorithm import InputError, SCHEMA, analyze
from generate_fixture import PROTOCOL, recording


ROOT = Path(__file__).resolve().parent


def participant(index: int, recordings: list[dict]) -> dict:
    return {
        "subjectId": hashlib.sha256(f"test-breathing-subject-{index}".encode()).hexdigest(),
        "recordings": recordings,
    }


class GuidedBreathingResponseTest(unittest.TestCase):
    def test_generated_cohort(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        expected = json.loads((ROOT / "expected-public.json").read_text())
        self.assertEqual(analyze(source), expected)

    def test_personal_change_uses_matched_protocol_only(self):
        value = {
            "schema": SCHEMA,
            "mode": "personal",
            "protocol": PROTOCOL,
            "participants": [participant(0, [recording(900, 20, 1), recording(880, 35, 2)])],
        }
        result = analyze(value)
        self.assertEqual(result["recordingCount"], 2)
        self.assertIsNotNone(result["metrics"]["rmssdMs"]["changeLatestMinusEarliest"])

        mixed = copy.deepcopy(value)
        mixed["participants"][0]["recordings"][1]["protocol"] = {
            "rateCPM": 7.5, "ih": 4.0, "ip": 0.0, "eh": 4.0, "ep": 0.0
        }
        with self.assertRaises(InputError):
            analyze(mixed)

    def test_cohort_floor_and_participant_equal_weight(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        below = copy.deepcopy(source)
        below["participants"] = below["participants"][:19]
        self.assertEqual(analyze(below)["reason"], "privacy_floor")

        single = copy.deepcopy(source)
        for item in single["participants"]:
            item["recordings"] = item["recordings"][:1]
        repeated = copy.deepcopy(single)
        first = repeated["participants"][0]["recordings"][0]
        repeated["participants"][0]["recordings"] = [
            {**copy.deepcopy(first), "recordingIndex": index} for index in range(1, 8)
        ]
        single_result = analyze(single)
        repeated_result = analyze(repeated)
        for metric in ("meanHeartRateBpm", "rmssdMs", "sd1Ms"):
            self.assertEqual(
                repeated_result["metrics"][metric]["median"],
                single_result["metrics"][metric]["median"],
            )
            self.assertIsNone(repeated_result["metrics"][metric]["changeLatestMinusEarliest"])

    def test_rejects_generic_incomplete_nonfinite_short_and_uploaded_metrics(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        generic = copy.deepcopy(source)
        generic["participants"][0]["recordings"][0]["recordType"] = "rest"
        incomplete = copy.deepcopy(source)
        del incomplete["participants"][0]["recordings"][0]["protocol"]["ep"]
        nonfinite = copy.deepcopy(source)
        nonfinite["participants"][0]["recordings"][0]["protocol"]["ih"] = math.nan
        short = copy.deepcopy(source)
        short["participants"][0]["recordings"][0]["rrIntervalsMs"] = [1000] * 30
        tampered = copy.deepcopy(source)
        tampered["participants"][0]["recordings"][0]["rsa"] = 999
        for value in (generic, incomplete, nonfinite, short, tampered):
            with self.subTest(value=value):
                with self.assertRaises(InputError):
                    analyze(value)


if __name__ == "__main__":
    unittest.main()
