#!/usr/bin/env python3

import copy
import hashlib
import json
import unittest
from pathlib import Path

from algorithm import InputError, PROTOCOL, RATES, SCHEMA, analyze
from generate_fixture import session, trial


ROOT = Path(__file__).resolve().parent


def participant(index: int, sessions: list[dict]) -> dict:
    return {
        "subjectId": hashlib.sha256(f"test-six-rate-subject-{index}".encode()).hexdigest(),
        "sessions": sessions,
    }


def personal(sessions: list[dict]) -> dict:
    return {
        "schema": SCHEMA,
        "mode": "personal",
        "protocol": PROTOCOL,
        "participants": [participant(0, sessions)],
    }


class SixRateBreathingResponseTest(unittest.TestCase):
    def test_generated_cohort(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        expected = json.loads((ROOT / "expected-public.json").read_text())
        self.assertEqual(analyze(source), expected)

    def test_personal_curve_preserves_all_exact_ties(self):
        value = personal([session(0, 1)])
        same = copy.deepcopy(value["participants"][0]["sessions"][0]["trials"][0]["rrIntervalsMs"])
        for item in value["participants"][0]["sessions"][0]["trials"]:
            item["rrIntervalsMs"] = copy.deepcopy(same)
        result = analyze(value)
        self.assertEqual(result["largestObservedMedianRmssdRatesCpm"], list(RATES))
        self.assertEqual(result["sessions"][0]["largestObservedRmssdRatesCpm"], list(RATES))
        self.assertNotIn("optimal", result)

    def test_cohort_floor_and_participant_equal_weight(self):
        source = json.loads((ROOT / "public-data.json").read_text())
        below = copy.deepcopy(source)
        below["participants"] = below["participants"][:19]
        self.assertEqual(analyze(below)["reason"], "privacy_floor")

        one_each = copy.deepcopy(source)
        for item in one_each["participants"]:
            item["sessions"] = item["sessions"][:1]
        repeated = copy.deepcopy(one_each)
        first = repeated["participants"][0]["sessions"][0]
        repeated["participants"][0]["sessions"] = [
            {**copy.deepcopy(first), "sessionIndex": index} for index in range(1, 8)
        ]
        self.assertEqual(analyze(one_each)["curve"], analyze(repeated)["curve"])

    def test_rejects_incomplete_reordered_short_and_uploaded_metrics(self):
        base = personal([session(0, 1)])
        incomplete = copy.deepcopy(base)
        incomplete["participants"][0]["sessions"][0]["trials"].pop()
        reordered = copy.deepcopy(base)
        reordered["participants"][0]["sessions"][0]["trials"].reverse()
        short = copy.deepcopy(base)
        short["participants"][0]["sessions"][0]["trials"][0]["rrIntervalsMs"] = [1000] * 30
        tampered = copy.deepcopy(base)
        tampered["participants"][0]["sessions"][0]["trials"][0]["rsa"] = 999
        adherence = copy.deepcopy(base)
        adherence["protocol"]["adherenceMeasured"] = True
        malformed = copy.deepcopy(base)
        malformed["participants"][0]["sessions"][0]["trials"][0]["rateCpm"] = "7.0"
        for value in (incomplete, reordered, short, tampered, adherence, malformed):
            with self.subTest(value=value):
                with self.assertRaises(InputError):
                    analyze(value)


if __name__ == "__main__":
    unittest.main()
