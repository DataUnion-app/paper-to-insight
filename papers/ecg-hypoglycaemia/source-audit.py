#!/usr/bin/env python3
"""Checksum-pinned audit of the proposed ECG hypoglycaemia source."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "38a95fc6600cb4f82574a543f91941c19eddde51"
MAX_BYTES = 1_000_000
REQUIRED = {"paper-xml", "source-license", "source-readme", "source-tree"}
BLOCK_REASONS = [
    "paper_is_protocol",
    "population_or_device_unvalidated",
    "public_reproduction_failed",
    "raw_signal_missing",
    "reference_labels_missing",
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
    license_text = assets["source-license"].decode()
    tree = json.loads(assets["source-tree"])
    paths = {item.get("path") for item in tree.get("tree", [])}
    executable_suffixes = {".py", ".ipynb", ".r", ".m", ".js", ".ts"}
    executables = [
        path
        for path in paths
        if path and Path(path).suffix.lower() in executable_suffixes
    ]

    checks = {
        "paper DOI is correct": "10.1007/s12553-022-00719-x" in paper,
        "paper method is CC BY": (
            "Creative Commons Attribution 4.0 International License" in paper
        ),
        "paper identifies itself as a protocol": "study protocol" in paper,
        "paper result is prospective": (
            "Data collection is expected to be completed approximately by June 2023"
            in paper
        ),
        "paper plans sixty-four children": "64 paediatric patients" in paper,
        "paper requires CGM": (
            "use continuous glucose monitoring (CGM) systems" in paper
        ),
        "paper uses raw ECG excerpts": "five to fifteen minutes excerpts" in paper,
        "paper proposes three glycaemic labels": (
            "normal, severe hypoglycaemic or severe hyperglycaemic events" in paper
        ),
        "paper does not identify this repository": "github.com" not in paper.lower(),
        "repository is Apache licensed": (
            "Apache License" in license_text and "Version 2.0" in license_text
        ),
        "repository contains only documents": paths == {
            "ECG_DIABETES.docx",
            "ECG_DIABETES.pdf",
            "LICENSE",
            "README.md",
        },
        "repository has no executable implementation": not executables,
        "repository describes a separate public dataset": (
            "open D1NAMO dataset" in readme
            and "20 healthy subjects and 9 subjects diagnosed with Type-1 diabetes"
            in readme
        ),
        "repository requires raw ECG": (
            "first 200 beats" in readme
            and "transformed into an image using spectrograms" in readme
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.ecg-hypoglycaemia",
        "sourceRevision": REVISION,
        "sourceRelationship": "unproven_supporting_artifacts",
        "paperMethodLicense": "CC-BY-4.0",
        "sourceLicense": "Apache-2.0",
        "paperIsProspectiveProtocol": True,
        "paperPlannedParticipants": 64,
        "paperRawEcgRequired": True,
        "paperCgmLabelsRequired": True,
        "sourceExecutableFiles": 0,
        "sourceFittedModelAvailable": False,
        "sourceValidationReceiptAvailable": False,
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
