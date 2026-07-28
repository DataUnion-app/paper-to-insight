#!/usr/bin/env python3
"""Checksum-pinned audit of the proposed global HRV stress source."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "4d1568c274fddc25de1b2c6f2416a82197a5d603"
MAX_BYTES = 1_000_000
REQUIRED = {
    "dataset-card",
    "paper-xml",
    "source-notebook",
    "source-readme",
    "source-tree",
}
FEATURES = (
    "KURT, VLF, MEAN_REL_RR, HR_HF, pNN25, KURT_REL_RR, TP, "
    "and MEDIAN_REL_RR_LOG"
)
BLOCK_REASONS = [
    "license_unverified",
    "participant_split_leakage",
    "population_or_device_unvalidated",
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
    notebook = json.loads(assets["source-notebook"])
    tree = json.loads(assets["source-tree"])
    dataset = json.loads(assets["dataset-card"])
    code = "".join(
        line
        for cell in notebook.get("cells", [])
        for line in cell.get("source", [])
    )
    paths = {item.get("path") for item in tree.get("tree", [])}

    checks = {
        "paper DOI is correct": "10.3390/s23115220" in paper,
        "paper method is CC BY": "Creative Commons Attribution (CC BY)" in paper,
        "combined eight features are declared": FEATURES in paper,
        "paper declares per-subject 70/30": (
            "70% of data instances of each subject dataset" in paper
            and "testing dataset has 30% of data instances" in paper
        ),
        "repository points to the audited datasets": (
            "qiriro/stress" in readme
            and "10.17026/dans-x55-69zp" in readme.lower()
        ),
        "repository has no license file": not any(
            str(path).lower().startswith(("license", "copying"))
            for path in paths
            if path
        ),
        "repository contains the audited notebook": (
            "combined_20_100.ipynb" in paths
        ),
        "notebook splits inside each subject": all(
            marker in code
            for marker in (
                "for group_id, group_data in df.groupby(group_col):",
                "train_test_split(",
                "test_size=test_size",
                "test_size = 0.3",
            )
        ),
        "notebook uses the paper RF": all(
            marker in code
            for marker in (
                "RandomForestClassifier(max_depth=20",
                "min_samples_split=2",
                "n_estimators=100",
            )
        ),
        "aggregate dataset card claims CC0": (
            dataset.get("licenseName") == "CC0: Public Domain"
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.global-hrv-stress",
        "sourceRevision": REVISION,
        "paperMethodLicense": "CC-BY-4.0",
        "sourceCodeLicenseVerified": False,
        "aggregateDatasetCardLicense": dataset["licenseName"],
        "underlyingDatasetLicenseChainVerified": False,
        "paperFeatureCount": 8,
        "paperValidationIncludesEverySubjectInTraining": True,
        "participantHeldOutValidation": False,
        "eligibleForIndependentReimplementation": True,
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
