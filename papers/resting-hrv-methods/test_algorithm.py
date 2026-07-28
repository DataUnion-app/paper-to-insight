import importlib.util
import json
import math
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("hrv_algorithm", HERE / "algorithm.py")
algorithm = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(algorithm)
MANIFEST_SHA = "a" * 64


def intervals(seed: int = 0, artifact_count: int = 0) -> list[float]:
    values = [
        900 + 35 * math.sin((index + seed) / 11) + (index % 5 - 2) * 2
        for index in range(330)
    ]
    return [2500.0] * artifact_count + values[artifact_count:]


def recording(seed: int = 0, artifact_count: int = 0) -> dict:
    return {
        "recordingType": "rest",
        "durationSeconds": 300,
        "rrIntervalsMs": intervals(seed, artifact_count),
    }


def cohort(count: int = 20) -> dict:
    return {
        "schema": algorithm.COHORT_SCHEMA,
        "participants": [
            {"subjectId": f"{index:064x}", "recordings": [recording(index)]}
            for index in range(1, count + 1)
        ],
    }


class RestingHrvMethodsTest(unittest.TestCase):
    def test_cohort_and_personal_use_same_methods(self):
        group = cohort()
        group_result = algorithm.build_result(group, MANIFEST_SHA)
        self.assertEqual(group_result["status"], "complete")
        reference = algorithm.build_reference(group, "generated-test-v1")
        personal_input = {
            "schema": algorithm.PERSONAL_SCHEMA,
            "recordings": [recording(1)],
            "reference": reference,
        }
        personal = algorithm.build_result(personal_input, MANIFEST_SHA)
        self.assertEqual(personal["status"], "complete")
        self.assertEqual(personal["paperClassification"]["decision"], "not_applicable")
        self.assertEqual(
            personal["provenance"]["referenceSha256"], reference["sha256"]
        )
        self.assertIn("Comparison", personal["table"]["columns"])

    def test_privacy_floor_has_no_measurements(self):
        result = algorithm.build_result(cohort(19), MANIFEST_SHA)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["abstentionReason"], "privacy_floor")
        self.assertEqual(result["metrics"], [])
        self.assertEqual(result["charts"], [])
        self.assertIsNone(result["table"])

    def test_excess_artifacts_abstain(self):
        reference = algorithm.build_reference(cohort(), "generated-test-v1")
        result = algorithm.build_result({
            "schema": algorithm.PERSONAL_SCHEMA,
            "recordings": [recording(1, artifact_count=20)],
            "reference": reference,
        }, MANIFEST_SHA)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["abstentionReason"], "insufficient_quality")

    def test_rejected_interval_does_not_join_non_adjacent_beats(self):
        values = intervals()
        values[100] = 2500.0
        result = algorithm.hrv(values)
        valid = [300 <= value <= 2000 for value in values]
        differences = [
            values[index] - values[index - 1]
            for index in range(1, len(values))
            if valid[index] and valid[index - 1]
        ]
        self.assertAlmostEqual(
            result["rmssdMs"],
            math.sqrt(sum(value * value for value in differences) / len(differences)),
        )

    def test_reference_digest_is_enforced(self):
        reference = algorithm.build_reference(cohort(), "generated-test-v1")
        reference["bands"]["sdnnMs"][0] += 1
        with self.assertRaises(algorithm.InputError):
            algorithm.build_result({
                "schema": algorithm.PERSONAL_SCHEMA,
                "recordings": [recording()],
                "reference": reference,
            }, MANIFEST_SHA)

    def test_declared_duration_must_match_intervals(self):
        bad = cohort()
        bad["participants"][0]["recordings"][0]["rrIntervalsMs"] = [300.0] * 180
        with self.assertRaises(algorithm.InputError):
            algorithm.build_result(bad, MANIFEST_SHA)

    def test_results_do_not_contain_subject_ids_or_intervals(self):
        result = algorithm.build_result(cohort(), MANIFEST_SHA)
        rendered = json.dumps(result, sort_keys=True)
        self.assertNotIn("subjectId", rendered)
        self.assertNotIn("rrIntervalsMs", rendered)
        self.assertLess(len(rendered.encode()), 256 * 1024)


if __name__ == "__main__":
    unittest.main()
