#!/usr/bin/env python3
"""Checksum-pinned audit of the paper-linked AF CRNN source."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "81a7983574153d2ef2d3c412a650900f8b1127d4"
MAX_BYTES = 1_000_000
REQUIRED = {
    "paper-pdf",
    "source-dataset-helper",
    "source-readme",
    "source-split-properties",
    "source-tree",
}
BLOCK_REASONS = [
    "license_unverified",
    "participant_split_unproven",
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

    paper = assets["paper-pdf"]
    readme = assets["source-readme"].decode()
    helper = assets["source-dataset-helper"].decode()
    properties = json.loads(assets["source-split-properties"])
    tree = json.loads(assets["source-tree"])
    paths = {item.get("path") for item in tree.get("tree", [])}

    checks = {
        "paper is a PDF": paper.startswith(b"%PDF-"),
        "source identifies the exact paper": (
            "Convolutional Recurrent Neural Networks for Electrocardiogram Classification"
            in readme
            and "https://arxiv.org/abs/1710.06122" in readme
        ),
        "source identifies the challenge data": (
            "2017 PhysioNet/CinC Challenge" in readme
        ),
        "source has no license": not any(
            str(path).lower().startswith(("license", "copying"))
            for path in paths
            if path
        ),
        "source has paper model configurations": all(
            path in paths
            for path in ("models/CNN_paper.json", "models/CRNN_paper.json")
        ),
        "source has no fitted model": not any(
            str(path).lower().endswith((".ckpt", ".h5", ".pb", ".onnx", ".pt"))
            for path in paths
            if path
        ),
        "split operates on recording IDs": all(
            marker in helper
            for marker in (
                "id_list=ids",
                "labels=load_label(ids)",
                "stratified_split(",
                "shuffle=True",
            )
        ),
        "split declares no holdout": (
            properties["inputs"]["holdout"] is False
            and properties["relative size"]["holdout"] == 0
        ),
        "split manifest has no participant key": (
            "patient" not in json.dumps(properties).lower()
            and "participant" not in json.dumps(properties).lower()
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.atrial-fibrillation-crnn",
        "sourceRevision": REVISION,
        "sourceRelationship": "author_reference_implementation",
        "paperVersion": "arXiv:1710.06122v2",
        "paperLicense": "arXiv-nonexclusive-distribution-1.0",
        "sourceCodeLicenseVerified": False,
        "paperClassCount": 4,
        "rawEcgRequired": True,
        "paperHiddenTestAvailable": False,
        "sourceFittedModelAvailable": False,
        "participantIdentityAvailableForSplit": False,
        "participantSeparatedValidation": False,
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
