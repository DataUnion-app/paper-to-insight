from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_e3_receipt", ROOT / "scripts" / "validate_e3_receipt.py"
)
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def receipt():
    digest = "a" * 64
    return {
        "schema": "brainstem.e3-validation-receipt/v1",
        "candidateManifestSha256": digest,
        "algorithmImageDigest": "sha256:" + "b" * 64,
        "study": {
            "id": "generated-study",
            "protocolSha256": digest,
            "datasetSchema": "generated/v1",
            "datasetSchemaSha256": digest,
            "populationDigest": digest,
            "deviceContractDigest": digest,
            "preregistrationDigest": digest,
        },
        "labels": {
            "referenceStandard": "clinician_confirmed",
            "selfReportUse": "supplemental",
            "labelProtocolDigest": digest,
            "blindedToModelOutput": True,
        },
        "split": {
            "unit": "participant",
            "participantSeparated": True,
            "overlapCount": 0,
            "trainingParticipants": 40,
            "validationParticipants": 20,
            "testParticipants": 20,
            "frozenBeforeEvaluation": True,
            "powerAnalysisDigest": digest,
        },
        "performance": {
            "primaryMetric": "AUROC",
            "estimate": 0.8,
            "lower95": 0.7,
            "upper95": 0.9,
            "brierScore": 0.15,
            "calibrationSlope": 1.0,
            "subgroupFloor": 20,
            "missingnessRate": 0.05,
            "artifactRate": 0.05,
            "acceptanceCriteriaDigest": digest,
            "criteriaMet": True,
            "repeatedRunDeterministic": True,
        },
        "abstention": {
            "implemented": True,
            "oodTested": True,
            "qualityTested": True,
            "policyDigest": digest,
        },
        "use": {
            "evidenceTier": "E3_brainstem_validated_research",
            "useClass": "protocol_bound_research",
            "clinicalUse": "prohibited",
            "personalOutput": "relative_indicator_with_uncertainty",
            "nextStepLanguage": "consider_professional_evaluation",
            "diagnosis": False,
            "treatment": False,
        },
        "reviews": [
            {
                "role": role,
                "reviewerPseudonymSha256": {
                    "scientific": "1",
                    "privacy": "2",
                    "security": "3",
                }[role]
                * 64,
                "decision": "approved",
                "reviewedAt": "2026-07-29T00:00:00Z",
                "artifactSha256": digest,
            }
            for role in ("scientific", "privacy", "security")
        ],
    }


class E3ReceiptTest(unittest.TestCase):
    def test_complete_protected_receipt_passes(self):
        value = receipt()
        self.assertIs(validator.validate(value), value)

    def test_self_report_overlap_small_cells_and_clinical_claims_fail(self):
        changes = (
            ("labels", "referenceStandard", "self_report"),
            ("split", "overlapCount", 1),
            ("split", "testParticipants", 19),
            ("performance", "subgroupFloor", 19),
            ("use", "clinicalUse", "allowed"),
            ("abstention", "oodTested", False),
        )
        for owner, key, value in changes:
            invalid = receipt()
            invalid[owner][key] = value
            with self.assertRaises(validator.E3ReceiptError):
                validator.validate(invalid)

    def test_three_independent_review_roles_are_required(self):
        invalid = receipt()
        invalid["reviews"][2]["role"] = "scientific"
        with self.assertRaises(validator.E3ReceiptError):
            validator.validate(invalid)
        invalid = receipt()
        invalid["reviews"][1]["reviewerPseudonymSha256"] = invalid["reviews"][
            0
        ]["reviewerPseudonymSha256"]
        with self.assertRaises(validator.E3ReceiptError):
            validator.validate(invalid)

    def test_receipt_text_cannot_carry_rows_or_labels(self):
        for field, value in (
            ("datasetSchema", "participant_id,label\n123,positive"),
            ("id", "participant-123"),
            ("id", "participant123"),
            ("id", "study-0x" + "1" * 40),
            ("id", "device42"),
        ):
            invalid = receipt()
            invalid["study"][field] = value
            with self.assertRaises(validator.E3ReceiptError):
                validator.validate(invalid)

    def test_device_is_allowed_as_a_study_subject_not_an_identifier(self):
        value = receipt()
        value["study"]["id"] = "brainstem-device-vs-psg-study/v1"
        value["study"]["datasetSchema"] = "brainstem-device-vs-psg/v1"
        self.assertIs(validator.validate(value), value)

    def test_invalid_calendar_date_and_duplicate_keys_fail(self):
        invalid = receipt()
        invalid["reviews"][0]["reviewedAt"] = "2026-02-30T00:00:00Z"
        with self.assertRaises(validator.E3ReceiptError):
            validator.validate(invalid)
        with self.assertRaises(validator.E3ReceiptError):
            validator.duplicate_safe([("use", "allowed"), ("use", "prohibited")])


if __name__ == "__main__":
    unittest.main()
