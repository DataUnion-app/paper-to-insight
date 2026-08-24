#!/usr/bin/env python3
import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import re


SHA256 = re.compile(r"^[0-9a-f]{64}$")
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
REVIEW_ROLES = {"scientific", "privacy", "security"}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
PRIVATE_LABEL = re.compile(
    r"(?:^|[._:/-])(?:participant|patient|subject|user|wallet|"
    r"recording|email)(?:$|[._:/-])",
    re.I,
)
PRIVATE_SUFFIX = re.compile(
    r"(?:participant|patient|subject|user|wallet|device|recording|email)"
    r"(?:id)?[._:/-]?(?:0x)?[0-9a-f]{2,}",
    re.I,
)
WALLET_ADDRESS = re.compile(r"0x[0-9a-f]{40}", re.I)


class E3ReceiptError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise E3ReceiptError(message)


def duplicate_safe(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "duplicate JSON key: {}".format(key))
        value[key] = item
    return value


def exact(value, keys, path):
    require(isinstance(value, dict), "{} must be an object".format(path))
    require(set(value) == set(keys), "{} has missing or unknown fields".format(path))
    return value


def digest(value, path):
    require(isinstance(value, str) and SHA256.fullmatch(value), "{} is invalid".format(path))


def identifier(value, path):
    require(
        isinstance(value, str) and IDENTIFIER.fullmatch(value),
        "{} is invalid".format(path),
    )


def public_identifier(value, path):
    identifier(value, path)
    require(
        "@" not in value
        and WALLET_ADDRESS.search(value) is None
        and PRIVATE_LABEL.search(value) is None
        and PRIVATE_SUFFIX.search(value) is None,
        "{} may contain a protected identifier".format(path),
    )


def finite(value, path, minimum=None, maximum=None):
    require(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value),
        "{} is invalid".format(path),
    )
    if minimum is not None:
        require(value >= minimum, "{} is below its bound".format(path))
    if maximum is not None:
        require(value <= maximum, "{} is above its bound".format(path))


def timestamp(value, path):
    require(isinstance(value, str) and RFC3339.fullmatch(value), "{} is invalid".format(path))
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise E3ReceiptError("{} is invalid".format(path)) from error


def validate(value):
    root = exact(
        value,
        {
            "schema",
            "candidateManifestSha256",
            "algorithmImageDigest",
            "study",
            "labels",
            "split",
            "performance",
            "abstention",
            "use",
            "reviews",
        },
        "$",
    )
    require(root["schema"] == "brainstem.e3-validation-receipt/v1", "$.schema is invalid")
    digest(root["candidateManifestSha256"], "$.candidateManifestSha256")
    require(
        isinstance(root["algorithmImageDigest"], str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", root["algorithmImageDigest"]),
        "$.algorithmImageDigest is invalid",
    )

    study = exact(
        root["study"],
        {
            "id",
            "protocolSha256",
            "datasetSchema",
            "datasetSchemaSha256",
            "populationDigest",
            "deviceContractDigest",
            "preregistrationDigest",
        },
        "$.study",
    )
    public_identifier(study["id"], "$.study.id")
    public_identifier(study["datasetSchema"], "$.study.datasetSchema")
    for key in (
        "protocolSha256",
        "datasetSchemaSha256",
        "populationDigest",
        "deviceContractDigest",
        "preregistrationDigest",
    ):
        digest(study[key], "$.study.{}".format(key))

    labels = exact(
        root["labels"],
        {
            "referenceStandard",
            "selfReportUse",
            "labelProtocolDigest",
            "blindedToModelOutput",
        },
        "$.labels",
    )
    require(
        labels["referenceStandard"]
        in {"clinician_confirmed", "adjudicated_outcome", "validated_measurement"},
        "$.labels.referenceStandard cannot be self-report only",
    )
    require(
        labels["selfReportUse"] in {"not_used", "supplemental", "stratification_only"},
        "$.labels.selfReportUse is invalid",
    )
    digest(labels["labelProtocolDigest"], "$.labels.labelProtocolDigest")
    require(labels["blindedToModelOutput"] is True, "$.labels must be blinded")

    split = exact(
        root["split"],
        {
            "unit",
            "participantSeparated",
            "overlapCount",
            "trainingParticipants",
            "validationParticipants",
            "testParticipants",
            "frozenBeforeEvaluation",
            "powerAnalysisDigest",
        },
        "$.split",
    )
    require(split["unit"] == "participant", "$.split.unit must be participant")
    require(split["participantSeparated"] is True and split["overlapCount"] == 0, "$.split leakage detected")
    for key in ("trainingParticipants", "validationParticipants", "testParticipants"):
        require(
            isinstance(split[key], int) and not isinstance(split[key], bool) and split[key] >= 20,
            "$.split.{} is too small".format(key),
        )
    require(split["frozenBeforeEvaluation"] is True, "$.split was not frozen")
    digest(split["powerAnalysisDigest"], "$.split.powerAnalysisDigest")

    performance = exact(
        root["performance"],
        {
            "primaryMetric",
            "estimate",
            "lower95",
            "upper95",
            "brierScore",
            "calibrationSlope",
            "subgroupFloor",
            "missingnessRate",
            "artifactRate",
            "acceptanceCriteriaDigest",
            "criteriaMet",
            "repeatedRunDeterministic",
        },
        "$.performance",
    )
    identifier(performance["primaryMetric"], "$.performance.primaryMetric")
    for key in ("estimate", "lower95", "upper95", "brierScore", "missingnessRate", "artifactRate"):
        finite(performance[key], "$.performance.{}".format(key), 0, 1)
    require(
        performance["lower95"] <= performance["estimate"] <= performance["upper95"],
        "$.performance interval is invalid",
    )
    finite(performance["calibrationSlope"], "$.performance.calibrationSlope", 0, 3)
    require(
        isinstance(performance["subgroupFloor"], int)
        and not isinstance(performance["subgroupFloor"], bool)
        and performance["subgroupFloor"] >= 20,
        "$.performance.subgroupFloor is too small",
    )
    digest(performance["acceptanceCriteriaDigest"], "$.performance.acceptanceCriteriaDigest")
    require(performance["criteriaMet"] is True, "$.performance acceptance criteria failed")
    require(performance["repeatedRunDeterministic"] is True, "$.performance is not deterministic")

    abstention = exact(
        root["abstention"],
        {"implemented", "oodTested", "qualityTested", "policyDigest"},
        "$.abstention",
    )
    require(
        abstention["implemented"] is True
        and abstention["oodTested"] is True
        and abstention["qualityTested"] is True,
        "$.abstention is incomplete",
    )
    digest(abstention["policyDigest"], "$.abstention.policyDigest")

    use = exact(
        root["use"],
        {
            "evidenceTier",
            "useClass",
            "clinicalUse",
            "personalOutput",
            "nextStepLanguage",
            "diagnosis",
            "treatment",
        },
        "$.use",
    )
    require(
        use
        == {
            "evidenceTier": "E3_brainstem_validated_research",
            "useClass": "protocol_bound_research",
            "clinicalUse": "prohibited",
            "personalOutput": "relative_indicator_with_uncertainty",
            "nextStepLanguage": "consider_professional_evaluation",
            "diagnosis": False,
            "treatment": False,
        },
        "$.use exceeds the E3 non-clinical boundary",
    )

    reviews = root["reviews"]
    require(isinstance(reviews, list) and len(reviews) == 3, "$.reviews must contain three approvals")
    roles = set()
    reviewers = set()
    for index, candidate in enumerate(reviews):
        review = exact(
            candidate,
            {
                "role",
                "reviewerPseudonymSha256",
                "decision",
                "reviewedAt",
                "artifactSha256",
            },
            "$.reviews[{}]".format(index),
        )
        require(review["role"] in REVIEW_ROLES and review["role"] not in roles, "$.reviews role is invalid")
        roles.add(review["role"])
        digest(
            review["reviewerPseudonymSha256"],
            "$.reviews reviewer pseudonym",
        )
        require(
            review["reviewerPseudonymSha256"] not in reviewers,
            "$.reviews reviewers are not independent",
        )
        reviewers.add(review["reviewerPseudonymSha256"])
        require(review["decision"] == "approved", "$.reviews decision is not approved")
        timestamp(review["reviewedAt"], "$.reviews timestamp")
        digest(review["artifactSha256"], "$.reviews artifact digest")
    require(roles == REVIEW_ROLES, "$.reviews roles are incomplete")
    return root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(
            args.receipt.read_text(encoding="utf-8"),
            object_pairs_hook=duplicate_safe,
        )
        validate(value)
    except (OSError, UnicodeError, json.JSONDecodeError, E3ReceiptError) as error:
        parser.error(str(error))
    print("valid E3 validation receipt")


if __name__ == "__main__":
    main()
