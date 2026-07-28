#!/usr/bin/env python3
"""Validate the security-critical candidate contract with the Python stdlib."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


TOP = {
    "schema", "approvalState", "packageId", "version", "paper", "sources",
    "datasets", "compatibility", "evidence", "modes", "abstention",
    "prohibitedClaims", "files",
}
PAPER = {
    "title", "canonicalUrl", "doi", "claim", "claimClass", "population",
    "referenceStandard", "implementationRelation", "relationEvidence",
    "classification",
}
CLASSIFICATION = {"paperDecision", "labels", "unit"}
SOURCE = {
    "name", "url", "revisionType", "revision", "sha256", "license", "licenseUrl"
}
DATASET = {
    "name", "kind", "url", "version", "doi", "sha256", "license", "licenseUrl"
}
COMPATIBILITY = {
    "brainstemContract", "requiredSignals", "window", "preprocessing",
    "brainstemVerdict", "mismatches"
}
EVIDENCE = {"tier", "useClass", "clinicalUse", "brainstemDecision"}
MODES = {"cohort", "personal"}
COHORT = {"proposed", "minimumParticipants", "minimumCell", "output"}
PERSONAL = {"proposed", "inputOwner", "referencePolicy", "output"}
FILE = {"path", "sha256"}

TIERS = {
    "E0_candidate", "E1_public_reproduced",
    "E2_brainstem_compatible_exploratory",
}
USES = {"methods_only", "exploratory_research", "protocol_bound_research"}
ABSTENTIONS = {
    "unsupported_signal", "insufficient_quality", "insufficient_coverage",
    "privacy_floor", "uncalibrated_device", "outside_validated_population",
    "out_of_distribution", "model_uncertainty", "reference_unavailable",
}
SENSITIVE = {
    "address", "apikey", "deviceid", "email", "mnemonic", "participantid",
    "privatekey", "recordid", "secret", "token", "wallet",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{7,64}$")
PACKAGE_ID = re.compile(r"^[a-z0-9][a-z0-9.-]{2,79}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
WALLET = re.compile(r"\b0x[0-9a-fA-F]{40}\b")
SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|mnemonic|participant[_-]?id|private[_-]?key|"
    r"record[_-]?id|secret|token|wallet)\s*[:=]"
)


class CandidateError(ValueError):
    pass


def exact(value: object, keys: set[str], where: str) -> dict:
    if not isinstance(value, dict):
        raise CandidateError(f"{where} must be an object")
    actual = set(value)
    if actual != keys:
        raise CandidateError(
            f"{where} keys differ: missing={sorted(keys - actual)} "
            f"extra={sorted(actual - keys)}"
        )
    return value


def text(value: object, where: str, limit: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise CandidateError(f"{where} must be non-empty and at most {limit} chars")
    return value


def digest(value: object, where: str) -> None:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise CandidateError(f"{where} must be a lowercase sha256")


def public_url(value: object, where: str) -> None:
    parsed = urlparse(text(value, where, 2000))
    if parsed.scheme != "https" or not parsed.hostname or parsed.username:
        raise CandidateError(f"{where} must be a public https URL")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".local"):
        raise CandidateError(f"{where} must not be local")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise CandidateError(f"{where} must not use a private or reserved IP")


def strings(
    value: object, where: str, minimum: int = 0, maximum: int = 30
) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise CandidateError(f"{where} must contain {minimum}..{maximum} items")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise CandidateError(f"{where} must contain non-empty strings")
    if len(set(value)) != len(value):
        raise CandidateError(f"{where} must not contain duplicates")
    return value


def scan_sensitive(value: object, where: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", key.lower())
            if normalized in SENSITIVE:
                raise CandidateError(f"{where}.{key} is a forbidden sensitive field")
            scan_sensitive(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_sensitive(child, f"{where}[{index}]")
    elif isinstance(value, str) and (
        EMAIL.search(value) or WALLET.search(value) or SECRET_ASSIGNMENT.search(value)
    ):
        raise CandidateError(f"{where} contains sensitive-looking content")


def validate(value: object) -> dict:
    root = exact(value, TOP, "$")
    if root["schema"] != "paper-to-insight.candidate/v1":
        raise CandidateError("$.schema is unsupported")
    if root["approvalState"] != "candidate":
        raise CandidateError("$.approvalState must be candidate")
    if not isinstance(root["packageId"], str) or not PACKAGE_ID.fullmatch(root["packageId"]):
        raise CandidateError("$.packageId is invalid")
    if not isinstance(root["version"], str) or not VERSION.fullmatch(root["version"]):
        raise CandidateError("$.version must be semver")

    paper = exact(root["paper"], PAPER, "$.paper")
    for key in (
        "title", "doi", "claim", "population", "referenceStandard",
        "relationEvidence",
    ):
        text(paper[key], f"$.paper.{key}")
    public_url(paper["canonicalUrl"], "$.paper.canonicalUrl")
    if paper["claimClass"] not in {"descriptive", "association", "prediction", "intervention"}:
        raise CandidateError("$.paper.claimClass is invalid")
    if paper["implementationRelation"] not in {
        "author_reference_implementation",
        "independent_reimplementation",
        "method_only",
    }:
        raise CandidateError("$.paper.implementationRelation is invalid")
    classification = exact(
        paper["classification"], CLASSIFICATION, "$.paper.classification"
    )
    if classification["paperDecision"] not in {
        "classified", "abstained", "not_applicable"
    }:
        raise CandidateError("$.paper.classification.paperDecision is invalid")
    labels = strings(classification["labels"], "$.paper.classification.labels", maximum=20)
    text(classification["unit"], "$.paper.classification.unit", 200)
    if (classification["paperDecision"] == "not_applicable") != (not labels):
        raise CandidateError("paper classification decision and labels disagree")

    for name, keyset in (("sources", SOURCE), ("datasets", DATASET)):
        items = root[name]
        if not isinstance(items, list) or not 1 <= len(items) <= 20:
            raise CandidateError(f"$.{name} must contain 1..20 entries")
        for index, item in enumerate(items):
            entry = exact(item, keyset, f"$.{name}[{index}]")
            text(entry["name"], f"$.{name}[{index}].name", 200)
            public_url(entry["url"], f"$.{name}[{index}].url")
            public_url(entry["licenseUrl"], f"$.{name}[{index}].licenseUrl")
            digest(entry["sha256"], f"$.{name}[{index}].sha256")
            license_name = text(entry["license"], f"$.{name}[{index}].license", 100)
            if license_name.lower() in {"unknown", "none", "unlicensed"}:
                raise CandidateError(f"$.{name}[{index}].license must be explicit")
            if name == "sources":
                if entry["revisionType"] not in {"git_commit", "content_sha256"}:
                    raise CandidateError(f"$.sources[{index}].revisionType is invalid")
                if not isinstance(entry["revision"], str) or not REVISION.fullmatch(entry["revision"]):
                    raise CandidateError(f"$.sources[{index}].revision must be immutable hex")
                if (
                    entry["revisionType"] == "content_sha256"
                    and entry["revision"] != entry["sha256"]
                ):
                    raise CandidateError(
                        f"$.sources[{index}] content revision must equal its sha256"
                    )
                if entry["revisionType"] == "git_commit" and len(entry["revision"]) not in {40, 64}:
                    raise CandidateError(
                        f"$.sources[{index}] git revision must be a full commit"
                    )
            else:
                if entry["kind"] not in {"public", "synthetic"}:
                    raise CandidateError(f"$.datasets[{index}].kind is invalid")
                text(entry["version"], f"$.datasets[{index}].version", 100)
                text(entry["doi"], f"$.datasets[{index}].doi", 200)

    compatibility = exact(root["compatibility"], COMPATIBILITY, "$.compatibility")
    text(compatibility["brainstemContract"], "$.compatibility.brainstemContract", 300)
    strings(compatibility["requiredSignals"], "$.compatibility.requiredSignals", 1)
    text(compatibility["window"], "$.compatibility.window", 300)
    text(compatibility["preprocessing"], "$.compatibility.preprocessing")
    if compatibility["brainstemVerdict"] not in {
        "compatible", "partially_compatible", "incompatible", "unknown"
    }:
        raise CandidateError("$.compatibility.brainstemVerdict is invalid")
    strings(compatibility["mismatches"], "$.compatibility.mismatches")

    evidence = exact(root["evidence"], EVIDENCE, "$.evidence")
    if evidence["tier"] not in TIERS or evidence["useClass"] not in USES:
        raise CandidateError("$.evidence tier or use class is invalid")
    if evidence["clinicalUse"] != "prohibited":
        raise CandidateError("$.evidence.clinicalUse must be prohibited")
    if evidence["brainstemDecision"] not in {"abstained", "not_applicable"}:
        raise CandidateError("$.evidence.brainstemDecision is invalid")
    if paper["claimClass"] != "descriptive" and evidence["brainstemDecision"] != "abstained":
        raise CandidateError("non-descriptive candidates must abstain on Brainstem")

    modes = exact(root["modes"], MODES, "$.modes")
    cohort = exact(modes["cohort"], COHORT, "$.modes.cohort")
    if not isinstance(cohort["proposed"], bool):
        raise CandidateError("$.modes.cohort.proposed must be boolean")
    for key in ("minimumParticipants", "minimumCell"):
        number = cohort[key]
        if not isinstance(number, int) or isinstance(number, bool) or number < 20:
            raise CandidateError(f"$.modes.cohort.{key} must be at least 20")
    text(cohort["output"], "$.modes.cohort.output", 500)
    personal = exact(modes["personal"], PERSONAL, "$.modes.personal")
    if not isinstance(personal["proposed"], bool):
        raise CandidateError("$.modes.personal.proposed must be boolean")
    if personal["inputOwner"] != "authenticated_participant_only":
        raise CandidateError("$.modes.personal.inputOwner is unsafe")
    if personal["referencePolicy"] != "immutable_reviewed_aggregate_only":
        raise CandidateError("$.modes.personal.referencePolicy is unsafe")
    text(personal["output"], "$.modes.personal.output", 500)

    unknown = set(strings(root["abstention"], "$.abstention", 1)) - ABSTENTIONS
    if unknown:
        raise CandidateError(f"$.abstention has unknown codes: {sorted(unknown)}")
    strings(root["prohibitedClaims"], "$.prohibitedClaims", 1)

    files = root["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= 200:
        raise CandidateError("$.files must contain 1..200 entries")
    seen = set()
    for index, item in enumerate(files):
        entry = exact(item, FILE, f"$.files[{index}]")
        path = text(entry["path"], f"$.files[{index}].path", 300)
        parsed = Path(path)
        if parsed.is_absolute() or ".." in parsed.parts or path in seen:
            raise CandidateError(f"$.files[{index}].path is unsafe or duplicated")
        seen.add(path)
        digest(entry["sha256"], f"$.files[{index}].sha256")

    scan_sensitive(root)
    return root


def duplicate_safe(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise CandidateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_bytes(candidate: dict) -> bytes:
    return (json.dumps(candidate, sort_keys=True, separators=(",", ":")) + "\n").encode()


def verify_files(candidate: dict, base: Path) -> None:
    base = base.resolve()
    for item in candidate["files"]:
        path = (base / item["path"]).resolve()
        if path.parent != base and base not in path.parents:
            raise CandidateError(f'{item["path"]} escapes the candidate directory')
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise CandidateError(f'{item["path"]} cannot be read') from exc
        if actual != item["sha256"]:
            raise CandidateError(f'{item["path"]} digest does not match')


def load(path: Path) -> tuple[dict, str]:
    try:
        with path.open(encoding="utf-8") as handle:
            candidate = json.load(handle, object_pairs_hook=duplicate_safe)
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateError(str(exc)) from exc
    checked = validate(candidate)
    verify_files(checked, path.parent)
    return checked, hashlib.sha256(canonical_bytes(checked)).hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} CANDIDATE.json", file=sys.stderr)
        return 2
    try:
        candidate, candidate_sha = load(Path(argv[1]))
    except CandidateError as exc:
        print(f"invalid candidate: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "approvalState": "candidate",
        "candidateSha256": candidate_sha,
        "packageId": candidate["packageId"],
        "valid": True,
        "version": candidate["version"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
