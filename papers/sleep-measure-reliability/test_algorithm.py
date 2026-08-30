import copy
import json
import unittest
from pathlib import Path

from algorithm import InputError, analyze


HERE = Path(__file__).resolve().parent


def fixture():
    return json.loads((HERE / "public-data.json").read_text())


class SleepMeasureReliabilityTest(unittest.TestCase):
    def test_generated_result_is_deterministic_and_bounded(self):
        value = fixture()
        result = analyze(value)
        self.assertEqual(result["status"], "complete")
        reordered = copy.deepcopy(value)
        reordered["participantNights"].reverse()
        self.assertEqual(result, analyze(reordered))
        rendered = json.dumps(result).lower()
        self.assertNotIn("participantnights", rendered)
        self.assertNotIn("participantid", rendered)

    def test_privacy_floor_releases_no_metrics(self):
        value = fixture()
        value["participantNights"] = value["participantNights"][:19]
        result = analyze(value)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["metrics"], [])

    def test_one_frequent_recorder_cannot_inflate_the_cohort(self):
        value = fixture()
        value["participantNights"] = [value["participantNights"][0] * 20]
        with self.assertRaises(InputError):
            analyze(value)

    def test_non_finite_and_degenerate_values_fail_or_abstain(self):
        invalid = fixture()
        invalid["participantNights"][0][0] = float("nan")
        with self.assertRaises(InputError):
            analyze(invalid)
        degenerate = fixture()
        degenerate["participantNights"] = [[7.0] * 7 for _ in range(20)]
        self.assertEqual(analyze(degenerate)["status"], "insufficient_data")


if __name__ == "__main__":
    unittest.main()

