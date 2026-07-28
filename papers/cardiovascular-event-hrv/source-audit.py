#!/usr/bin/env python3
"""Checksum-pinned audit of the cardiovascular-event HRV source."""

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
REVISION = "acda0446d9996314005a7d20492369d5212f4ac5"
MAX_BYTES = 1_000_000
REQUIRED = {
    "source-license",
    "source-make-dataset",
    "source-predict-model",
    "source-readme",
    "source-synthetic-ce",
    "source-test-model",
    "source-train-model",
    "source-transfer-model",
}
BLOCK_REASONS = [
    "brainstem_contract_missing",
    "population_or_device_unvalidated",
    "public_reproduction_failed",
    "reference_labels_missing",
    "required_signal_missing",
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

    readme = assets["source-readme"].decode()
    license_text = assets["source-license"].decode()
    train = assets["source-train-model"].decode()
    transfer = assets["source-transfer-model"].decode()
    test = assets["source-test-model"].decode()
    predict = assets["source-predict-model"]
    header = next(csv.reader(io.StringIO(assets["source-synthetic-ce"].decode())))

    checks = {
        "paper DOI is source-declared": "10.3390/app15031178" in readme,
        "source license is explicit": "The MIT License" in license_text,
        "64 features are present": len(header) == 65 and header[-1] == "label",
        "scaler is fitted": "sc = StandardScaler()" in train
        and "sc = StandardScaler()" in transfer,
        "scaler is not serialized": "scaler" not in readme.lower()
        and "joblib.dump" not in train
        and "joblib.dump" not in transfer,
        "prediction module is empty": not predict,
        "test labels remain external": "dataframe['label']" in test
        and "csv2df(input_filepath)" in test,
        "AUC uses thresholded labels": "roc_auc_score(y, y_predictions)" in test,
        "confusion matrix is mis-mapped": (
            "calculate_sensitivity_specificity(cm_list[0], cm_list[3], "
            "cm_list[1], cm_list[2])" in test
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.cardiovascular-event-hrv",
        "sourceRevision": REVISION,
        "sourceRelationship": "author_reference_implementation",
        "sourceLicenseVerified": True,
        "featureCount": 64,
        "serializedScalerAvailable": False,
        "productionInferenceAvailable": False,
        "pairedPublicTestLabelsAvailable": False,
        "probabilityBasedAuc": False,
        "sensitivitySpecificityMappingCorrect": False,
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
