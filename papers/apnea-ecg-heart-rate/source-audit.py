#!/usr/bin/env python3
"""Checksum-pinned audit of the proposed Apnea-ECG source."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "aaaf046741696e1c6267f707853e6e79b31c9ae5"
MAX_BYTES = 2_000_000
REQUIRED = {
    "dataset-manifest",
    "dataset-page",
    "source-license",
    "source-model-evaluation",
    "source-readme",
    "source-training-index",
}
BLOCK_REASONS = [
    "paper_implementation_identity_unproven",
    "participant_split_leakage",
    "population_or_device_unvalidated",
    "reference_labels_missing",
]


class AuditError(ValueError):
    pass


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "paper-to-insight-source-audit/1"})
    with urlopen(request, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise AuditError(f"asset exceeds {MAX_BYTES} bytes")
    return data


def load_sources(path: Path = ROOT / "public-sources.json") -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "paper-to-insight.public-sources/v1":
        raise AuditError("unsupported public-sources schema")
    assets = value.get("assets")
    if not isinstance(assets, dict) or set(assets) != REQUIRED:
        raise AuditError("public source set differs")
    return assets


def download(assets: dict) -> dict[str, bytes]:
    result = {}
    for name, item in sorted(assets.items()):
        data = fetch(item["url"])
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise AuditError(f"{name} checksum differs")
        result[name] = data
    return result


def audit(assets: dict[str, bytes]) -> dict:
    if set(assets) != REQUIRED:
        raise AuditError("audit asset set differs")

    readme = assets["source-readme"].decode()
    license_text = assets["source-license"].decode()
    evaluator = assets["source-model-evaluation"].decode()
    dataset_page = assets["dataset-page"].decode()
    manifest = assets["dataset-manifest"].decode()
    rows = list(csv.DictReader(io.StringIO(assets["source-training-index"].decode())))

    personal_project = "personal project for the Insight Data Science program" in readme
    record_split = all(
        marker in evaluator
        for marker in (
            "StratifiedKFold",
            'skf.split(file_df, file_df["group"])',
            'file_df.loc[idx_train, "file"]',
            'file_df.loc[idx_val, "file"]',
        )
    )
    participant_ids = bool(rows) and any(
        key.lower() in {"participant", "participant_id", "patient", "subject", "subject_id"}
        for key in rows[0]
    )
    training_records = {row.get("file") for row in rows}
    overlapping_pair = {"c05", "c06"}.issubset(training_records) and all(
        marker in dataset_page
        for marker in (
            "same original recording",
            "c05 begins 80 seconds later than c06",
        )
    )
    count_unit_mismatch = (
        "70 participants" in readme and "The data consist of 70 records" in dataset_page
    )
    manifest_pins_metadata = (
        "25c86153fc254cff961541ee414d8174c9b5f29e3ec989cebc1103edd02b8ec9 "
        "additional-information.txt" in manifest
    )
    source_license = "MIT License" in license_text

    checks = {
        "independent personal project": personal_project,
        "record-level cross-validation": record_split,
        "participant identifiers absent": not participant_ids,
        "documented overlapping records in training": overlapping_pair,
        "record/participant count mismatch": count_unit_mismatch,
        "official metadata is manifest-pinned": manifest_pins_metadata,
        "source license is explicit": source_license,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.apnea-ecg-heart-rate",
        "sourceRevision": REVISION,
        "sourceRelationship": "independent_personal_project",
        "sourceLicenseVerified": True,
        "publicDatasetLicense": "ODC-By-1.0",
        "recordLevelCrossValidation": True,
        "participantIdentifiersAvailable": False,
        "knownOverlappingRecordsInTraining": ["c05", "c06"],
        "sourcePopulationCountUnitMismatch": True,
        "publicReproductionAccepted": False,
        "brainstemClassificationEnabled": False,
        "eligibleForRuntimeReview": False,
        "blockReasons": BLOCK_REASONS,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv[1:])
    if not args.verify:
        parser.error("--verify is required")
    try:
        result = audit(download(load_sources()))
        expected = json.loads((ROOT / "expected-audit.json").read_text(encoding="utf-8"))
        if result != expected:
            raise AuditError("audit result differs from expected-audit.json")
    except (AuditError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
