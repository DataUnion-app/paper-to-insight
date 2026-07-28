#!/usr/bin/env python3
"""Checksum-pinned audit of the in-hospital cardiac-arrest HRV source."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "7d87a343a8f2d476577f66e668f814e133b802e3"
MAX_BYTES = 1_000_000
REQUIRED = {"paper-xml", "source-main", "source-readme", "source-tree"}
BLOCK_REASONS = [
    "brainstem_contract_missing",
    "license_unverified",
    "population_or_device_unvalidated",
    "public_reproduction_failed",
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
    source = assets["source-main"].decode()
    tree = json.loads(assets["source-tree"])
    paths = {item.get("path") for item in tree.get("tree", [])}

    checks = {
        "paper DOI is correct": "10.1038/s41746-023-00960-2" in paper,
        "paper method is CC BY": (
            "Creative Commons Attribution 4.0 International License" in paper
        ),
        "paper points to this source": (
            "https://github.com/HyeonhoonLee/hrvarrest" in paper
            and "Real-time prediction of in-hospital cardiac arrest" in readme
        ),
        "paper uses 33 HRV measures": "LGBM model using 33 HRV measures" in paper,
        "paper uses five-minute epochs": "5\u2009min epochs" in paper,
        "paper validates at patient level": (
            "development (80%) and validation (20%) sets at the patient level"
            in paper
        ),
        "paper says training data are private": (
            "dataset used in this study is not publicly available" in paper
        ),
        "repository has no license": not any(
            str(path).lower().startswith(("license", "copying"))
            for path in paths
            if path
        ),
        "repository has no runtime artifacts": paths == {"README.md", "main.py"},
        "source requires missing dataset": "pd.read_csv(f'dataset.csv'" in source,
        "source requires missing split metadata": all(
            marker in source for marker in ("hrvs['stayid']", "hrvs['test']")
        ),
        "source references undefined optimizer function": (
            "BayesianOptimization(f=eval_function" in source
            and "def eval_function" not in source
        ),
        "source references undefined hyperparameters": (
            "'num_leaves': int(round(num_leaves))" in source
            and "def eval_function" not in source
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.in-hospital-cardiac-arrest-hrv",
        "sourceRevision": REVISION,
        "sourceRelationship": "author_reference_implementation",
        "paperMethodLicense": "CC-BY-4.0",
        "sourceCodeLicenseVerified": False,
        "paperFeatureCount": 33,
        "paperEpochMinutes": 5,
        "paperPatientLevelValidation": True,
        "publicTrainingDataAvailable": False,
        "selectedFeatureManifestAvailable": False,
        "fittedModelAvailable": False,
        "trainingScriptRunnable": False,
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
