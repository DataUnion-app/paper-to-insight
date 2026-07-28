#!/usr/bin/env python3
"""Checksum-pinned audit of the cardiac-arrhythmia CNN-LSTM source."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
REVISION = "dedf64a06e92db213354f918179102bc8fea0290"
MAX_BYTES = 1_000_000
REQUIRED = {"paper-bibtex", "source-main", "source-readme", "source-tree"}
BLOCK_REASONS = [
    "evaluation_leakage",
    "implementation_mismatch",
    "license_unverified",
    "participant_split_unproven",
    "population_or_device_unvalidated",
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

    paper = assets["paper-bibtex"].decode()
    readme = assets["source-readme"].decode()
    source = assets["source-main"].decode()
    tree = json.loads(assets["source-tree"])
    paths = {item.get("path") for item in tree.get("tree", [])}

    checks = {
        "paper DOI is correct": "10.1007/978-981-16-8774-7_32" in paper,
        "paper title is correct": (
            "Automated Detection of Cardiac Arrhythmia Based on a Hybrid CNN-LSTM Network"
            in paper
        ),
        "repository points to the paper": (
            "https://link.springer.com/chapter/10.1007/978-981-16-8774-7_32"
            in readme
        ),
        "repository declares five classes": all(
            label in readme
            for label in (
                "non-ectopic (N)",
                "ventricular tachycardia (V)",
                "supraventricular tachycardia (S)",
                "fusion (F)",
                "unclassifiable beats (U)",
            )
        ),
        "repository has no license": not any(
            str(path).lower().startswith(("license", "copying"))
            for path in paths
            if path
        ),
        "repository has source but no model": (
            "src/ECG_Hybrid.py" in paths
            and not any(
                str(path).lower().endswith((".h5", ".keras", ".onnx", ".pt", ".pb"))
                for path in paths
                if path
            )
        ),
        "source combines original train and test": (
            "self.df_combine = pd.concat([self.df_train, self.df_test])" in source
        ),
        "source upsamples with replacement": all(
            marker in source
            for marker in (
                "resample(df_1, replace=True",
                "resample(df_2, replace=True",
                "resample(df_3, replace=True",
                "resample(df_4, replace=True",
            )
        ),
        "source splits only after resampling": (
            0
            <= source.find("self.df_train_balanced = pd.concat")
            < source.find("train_test_split(X, Y, test_size=0.1)")
        ),
        "source leaves PCA disabled": (
            "# pca = PCA(n_components=combined_predictors)" in source
            and "# pca.fit(X)" in source
            and "# x_pca = pca.transform(X)" in source
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.cardiac-arrhythmia-cnn-lstm",
        "sourceRevision": REVISION,
        "sourceRelationship": "author_reference_implementation",
        "paperRights": "Springer-standard-copyright",
        "sourceCodeLicenseVerified": False,
        "paperClassCount": 5,
        "rawEcgRequired": True,
        "sourceCombinesTrainAndTestBeforeSplit": True,
        "sourceUpsamplesBeforeSplit": True,
        "duplicateLeakagePossible": True,
        "claimedPcaEnabled": False,
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
