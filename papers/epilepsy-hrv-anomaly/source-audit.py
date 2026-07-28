#!/usr/bin/env python3
"""Checksum-pinned audit of the proposed epileptic-seizure HRV source."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "de3b26039f76ce2ceac9a74a6bc179b8f7bddb1e"
MAX_BYTES = 1_000_000
REQUIRED = {
    "paper-xml",
    "source-license",
    "source-prediction-readme",
    "source-readme",
    "source-tree",
}
BLOCK_REASONS = [
    "paper_implementation_identity_unproven",
    "population_or_device_unvalidated",
    "public_reproduction_failed",
    "reference_labels_missing",
    "temporal_coverage_missing",
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
    prediction = assets["source-prediction-readme"].decode()
    license_text = assets["source-license"].decode()
    tree = json.loads(assets["source-tree"])
    paths = {item.get("path") for item in tree.get("tree", [])}

    checks = {
        "paper DOI is correct": "10.3390/s20143987" in paper,
        "paper method is CC BY": (
            "Creative Commons Attribution (CC BY) license" in paper
        ),
        "paper uses eight HRV indices": (
            "four time-domain indices" in paper
            and "four frequency-domain indices" in paper
        ),
        "paper uses a three-minute window": "three-minute moving window" in paper,
        "paper uses six components": "six principal components" in paper,
        "paper uses fourteen training patients": "Data from fourteen patients" in paper,
        "paper evaluates seven patients": "remaining seven patients" in paper,
        "paper uses specialist video EEG labels": (
            "Two or more experts from the Japan Epilepsy Society labeled seizures"
            in paper
        ),
        "paper reuses prior fitted parameters": (
            "modeling parameters of" in paper
            and "used from Fujiwara et al." in paper
        ),
        "paper does not identify this repository": "github.com" not in paper.lower(),
        "repository license is BSD three clause": all(
            marker in license_text
            for marker in (
                "Redistribution and use in source and binary forms",
                "Neither the name of epilepsy-system",
            )
        ),
        "repository describes a different fused model": (
            "Deep Learning on Fused Brain and Heart Signals" in readme
            and "features extracted from EEG and ECG signal" in readme
        ),
        "repository requires restricted source data": (
            "Download patient data from [Epilepsiae dataset]" in prediction
        ),
        "repository model is patient specific": (
            "patient-specific model" in prediction
        ),
        "repository prediction includes EEG features": (
            "EEG - Features of Spectral Power Analysis" in prediction
            or "Bands of EEG:" in prediction
        ),
        "repository evidence files exist": all(
            path in paths
            for path in (
                "LICENSE",
                "README.md",
                "seizure prediction code/README.md",
            )
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.epilepsy-hrv-anomaly",
        "sourceRevision": REVISION,
        "sourceRelationship": "unrelated_supplied_repository",
        "paperMethodLicense": "CC-BY-4.0",
        "sourceCodeLicense": "BSD-3-Clause",
        "paperHrvIndexCount": 8,
        "paperWindowMinutes": 3,
        "paperPrincipalComponents": 6,
        "paperTrainingPatients": 14,
        "paperProspectivePatients": 7,
        "paperImplementationAvailable": False,
        "paperFittedModelAvailable": False,
        "paperTrainingDataAvailable": False,
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
