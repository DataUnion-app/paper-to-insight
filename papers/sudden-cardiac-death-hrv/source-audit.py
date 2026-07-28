#!/usr/bin/env python3
"""Checksum-pinned audit of the proposed sudden-cardiac-death HRV source."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "25f405beeeede69f9870ff1e5760467242f34ffc"
MAX_BYTES = 1_000_000
REQUIRED = {"paper-xml", "source-readme", "source-tree"}
BLOCK_REASONS = [
    "paper_implementation_identity_unproven",
    "population_or_device_unvalidated",
    "public_reproduction_failed",
    "reference_labels_missing",
    "test_set_model_selection",
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
    executable_suffixes = {".py", ".ipynb", ".r", ".m", ".js", ".ts"}
    executables = [
        path
        for path in paths
        if path and Path(path).suffix.lower() in executable_suffixes
    ]

    checks = {
        "paper DOI is correct": "10.3390/medicina59081394" in paper,
        "paper method is CC BY": (
            "Creative Commons Attribution (CC BY) license" in paper
        ),
        "paper uses one hundred fifteen subjects": "115 subjects" in paper,
        "paper uses five groups": "This study included five subject groups" in paper,
        "paper uses eight HRV features": (
            "six features mentioned above, this study includes two other features"
            in paper
        ),
        "paper uses six five-minute segments": (
            "six segments per subject" in paper
            and "segmented into 5 min intervals" in paper
        ),
        "paper uses pre-event SCD data": (
            "30 min preceding the onset of VF" in paper
        ),
        "paper uses test set for selection": (
            "grid search identifies the hyperparameters that yield the best "
            "performance on the testing set" in paper
        ),
        "paper declares eighty twenty distribution": (
            "training distribution of 80% and a testing distribution of 20%"
            in paper
        ),
        "paper does not identify this repository": "github.com" not in paper.lower(),
        "supplied repository describes SVM": (
            "SVM algorithm Implementation" in readme
            and "Prediction of Sudden Cardiac Death using SVM" in readme
        ),
        "supplied repository has no license": not any(
            str(path).lower().startswith(("license", "copying"))
            for path in paths
            if path
        ),
        "supplied repository has only documents": (
            paths == {
                "README.md",
                "SVM_Based_Classification_for_SCD_prediction.pdf",
            }
            and not executables
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.sudden-cardiac-death-hrv",
        "sourceRevision": REVISION,
        "sourceRelationship": "unrelated_supplied_repository",
        "paperMethodLicense": "CC-BY-4.0",
        "sourceCodeLicenseVerified": False,
        "paperSubjectCount": 115,
        "paperGroupCount": 5,
        "paperHrvFeatureCount": 8,
        "paperSegmentsPerSubject": 6,
        "paperWindowMinutes": 5,
        "paperUsesTestingSetForModelSelection": True,
        "sourceExecutableFiles": 0,
        "sourceFittedModelAvailable": False,
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
