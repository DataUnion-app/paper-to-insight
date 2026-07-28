import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_candidate", ROOT / "scripts" / "validate_candidate.py"
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(validator)


class CandidateValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = json.loads(
            (ROOT / "examples" / "minimal-methods" / "candidate.json").read_text()
        )

    def rejects(self, mutate):
        candidate = copy.deepcopy(self.valid)
        mutate(candidate)
        with self.assertRaises(validator.CandidateError):
            validator.validate(candidate)

    def test_valid_candidate_is_deterministic(self):
        candidate = validator.validate(copy.deepcopy(self.valid))
        self.assertEqual(
            validator.canonical_bytes(candidate),
            validator.canonical_bytes(copy.deepcopy(candidate)),
        )

    def test_rejects_forged_approval(self):
        self.rejects(lambda value: value.update(approvalState="approved"))

    def test_rejects_private_endpoint(self):
        self.rejects(
            lambda value: value["datasets"][0].update(url="https://127.0.0.1/data")
        )

    def test_rejects_mutable_source_revision(self):
        self.rejects(lambda value: value["sources"][0].update(revision="main"))

    def test_rejects_mismatched_content_revision(self):
        self.rejects(lambda value: value["sources"][0].update(revision="f" * 64))

    def test_rejects_unknown_license(self):
        self.rejects(lambda value: value["sources"][0].update(license="unknown"))

    def test_rejects_duplicate_source_revision(self):
        def mutate(value):
            duplicate = copy.deepcopy(value["sources"][0])
            duplicate["sha256"] = "f" * 64
            value["sources"].append(duplicate)

        self.rejects(mutate)

    def test_rejects_identity_bearing_field(self):
        self.rejects(lambda value: value.update(wallet="0xdeadbeef"))

    def test_rejects_identity_bearing_value(self):
        self.rejects(
            lambda value: value["paper"].update(
                claim="contact alice@example.org; apiKey=do-not-store"
            )
        )

    def test_rejects_disease_candidate_that_does_not_abstain(self):
        def mutate(value):
            value["paper"]["claimClass"] = "prediction"
            value["evidence"]["brainstemDecision"] = "not_applicable"

        self.rejects(mutate)

    def test_rejects_personal_raw_cohort_policy(self):
        self.rejects(
            lambda value: value["modes"]["personal"].update(
                referencePolicy="live_raw_cohort"
            )
        )

    def test_rejects_small_cohort(self):
        self.rejects(
            lambda value: value["modes"]["cohort"].update(minimumParticipants=19)
        )

    def test_rejects_stale_file_digest(self):
        candidate = copy.deepcopy(self.valid)
        candidate["files"][0]["sha256"] = "f" * 64
        with self.assertRaises(validator.CandidateError):
            validator.verify_files(
                candidate, ROOT / "examples" / "minimal-methods"
            )


if __name__ == "__main__":
    unittest.main()
