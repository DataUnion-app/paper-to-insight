#!/usr/bin/env python3
"""Checksum-pinned audit of the proposed sleep-stage HRV source."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "5c37352230cc9be04b716a665d2f05251ee5848d"
MAX_BYTES = 1_000_000
REQUIRED = {"paper-xml", "source-readme", "source-tree"}
BLOCK_REASONS = [
    "paper_implementation_identity_unproven",
    "population_or_device_unvalidated",
    "public_reproduction_failed",
    "reference_labels_missing",
    "source_data_license_unverified",
]


class AuditError(ValueError):
    pass


def load_sources(path: Path = ROOT / "public-sources.json") -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assets = value.get("assets")
    if value.get("schema") != "paper-to-insight.public-sources/v1":
        raise AuditError("unsupported public-sources schema")
    if not isinstance(assets, dict) or set(assets) != REQUIRED:
        raise AuditError("public source set differs")
    return assets


def download(assets: dict) -> dict[str, bytes]:
    result = {}
    for name, item in sorted(assets.items()):
        request = Request(
            item["url"], headers={"User-Agent": "paper-to-insight-source-audit/1"}
        )
        with urlopen(request, timeout=30) as response:
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise AuditError(f"{name} exceeds {MAX_BYTES} bytes")
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise AuditError(f"{name} checksum differs")
        result[name] = data
    return result


def audit(assets: dict[str, bytes]) -> dict:
    if set(assets) != REQUIRED:
        raise AuditError("audit asset set differs")

    paper = assets["paper-xml"].decode()
    readme = assets["source-readme"].decode()
    tree = json.loads(assets["source-tree"])
    paths = {item.get("path") for item in tree.get("tree", [])}

    checks = {
        "paper DOI is correct": "10.1038/s41598-019-49703-y" in paper,
        "paper method is CC BY": (
            "Creative Commons Attribution 4.0 International License" in paper
        ),
        "paper uses two hundred ninety-two participants": (
            "total number of participants was 292" in paper
        ),
        "paper uses five hundred eighty-four nights": "584 nights" in paper,
        "paper uses one hundred thirty-two features": "132 HRV features" in paper,
        "paper validates at participant level": (
            "randomly split into folds at the level of participants" in paper
        ),
        "paper defines four reported classes": all(
            marker in paper
            for marker in (
                "For wake, precision",
                "For REM, precision",
                "For combined N1/N2",
                "Finally, for N3",
            )
        ),
        "paper does not identify this repository": "github.com" not in paper.lower(),
        "source says SIESTA is not free": (
            "this databse is not free" in readme
        ),
        "source declares six different stages": (
            "{AWAKE REM S1 S2 S3 S4}" in readme
        ),
        "source calls itself a simple framework": (
            "just a simple framework" in readme
        ),
        "source has no license": not any(
            str(path).lower().startswith(("license", "copying"))
            for path in paths
            if path
        ),
        "source includes MATLAB and sample matrices": (
            "lstm_classification.m" in paths
            and "lstm_regression.m" in paths
            and any(str(path).endswith(".mat") for path in paths if path)
        ),
        "source has no fitted runtime model": not any(
            str(path).lower().endswith((".onnx", ".h5", ".keras", ".pt", ".pb"))
            for path in paths
            if path
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.sleep-stage-hrv-lstm",
        "sourceRevision": REVISION,
        "sourceRelationship": "unrelated_supplied_repository",
        "paperMethodLicense": "CC-BY-4.0",
        "sourceCodeLicenseVerified": False,
        "paperParticipantCount": 292,
        "paperNightCount": 584,
        "paperHrvFeatureCount": 132,
        "paperClassCount": 4,
        "paperParticipantLevelValidation": True,
        "paperFittedModelAvailable": False,
        "paperTrainingDataFreelyAvailable": False,
        "sourceClassCount": 6,
        "sourceCallsItselfSimpleFramework": True,
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
        expected = json.loads(
            (ROOT / "expected-audit.json").read_text(encoding="utf-8")
        )
        if result != expected:
            raise AuditError("audit result differs from expected-audit.json")
    except (AuditError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
