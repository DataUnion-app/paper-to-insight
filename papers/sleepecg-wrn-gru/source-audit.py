#!/usr/bin/env python3
"""Checksum-pinned audit of SleepECG and the public SLPDB manifest."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MAX_BYTES = 1_000_000
REQUIRED = {"sleepecg-sdist", "slpdb-checksums", "slpdb-records"}
MODEL_SHA256 = "5622a858c855b0090e1fbcbdc35334ea459707c830eae1a26a4375e33091e869"


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


def _member(archive: tarfile.TarFile, suffix: str) -> bytes:
    matches = [item for item in archive.getmembers() if item.name.endswith(suffix)]
    if not matches:
        raise AuditError(f"expected {suffix}")
    depth = min(item.name.count("/") for item in matches)
    matches = [item for item in matches if item.name.count("/") == depth]
    if len(matches) != 1:
        raise AuditError(f"expected one top-level {suffix}, found {len(matches)}")
    stream = archive.extractfile(matches[0])
    if stream is None:
        raise AuditError(f"could not read {suffix}")
    return stream.read()


def audit(assets: dict[str, bytes]) -> dict:
    if set(assets) != REQUIRED:
        raise AuditError("audit asset set differs")

    with tarfile.open(fileobj=io.BytesIO(assets["sleepecg-sdist"]), mode="r:gz") as tar:
        package = _member(tar, "/PKG-INFO").decode()
        license_text = _member(tar, "/LICENSE").decode()
        docs = _member(tar, "/docs/classification.md").decode()
        training = _member(tar, "/examples/classifiers/wrn_gru_mesa.py").decode()
        model = _member(tar, "/src/sleepecg/classifiers/wrn-gru-mesa.zip")

    if hashlib.sha256(model).hexdigest() != MODEL_SHA256:
        raise AuditError("embedded model checksum differs")
    with zipfile.ZipFile(io.BytesIO(model)) as archive:
        info = archive.read("info.yml").decode()

    required_package = (
        "Name: sleepecg",
        "Version: 0.5.9",
        "License: BSD 3-Clause",
        "10.21105/joss.05411",
    )
    required_docs = (
        "`wrn-gru-mesa`",
        "MESA (1971)",
        "SHHS (1000)",
        "|0.75|0.54|",
        "limited performance in WAKE–REM–NREM classification",
    )
    required_training = (
        "read_mesa",
        "read_shhs",
        '"recording_start_time"',
        '"age"',
        '"gender"',
        'stages_mode = "wake-rem-nrem"',
    )
    required_info = (
        "hrv-time",
        "hrv-frequency",
        "recording_start_time",
        "age",
        "gender",
        "stages_mode: wake-rem-nrem",
    )
    checks = {
        "package metadata": all(marker in package for marker in required_package),
        "BSD license": "BSD 3-Clause License" in license_text,
        "published metrics": all(marker in docs for marker in required_docs),
        "training script": all(marker in training for marker in required_training),
        "model contract": all(marker in info for marker in required_info),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    records = assets["slpdb-records"].decode().split()
    if len(records) != 18 or len(set(records)) != 18:
        raise AuditError("SLPDB record set differs")
    checksums = {
        line.split()[1]: line.split()[0]
        for line in assets["slpdb-checksums"].decode().splitlines()
        if len(line.split()) == 2
    }
    annotation_count = sum(
        f"{record}.{extension}" in checksums
        for record in records
        for extension in ("hea", "ecg", "st")
    )
    if annotation_count != 54:
        raise AuditError("SLPDB annotation checksum set differs")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.sleepecg-wrn-gru",
        "sourceVersion": "0.5.9",
        "sourceLicense": "BSD-3-Clause",
        "softwarePaperDoi": "10.21105/joss.05411",
        "modelSha256": MODEL_SHA256,
        "modelStagesMode": "wake-rem-nrem",
        "modelUsesAgeAndGender": True,
        "authorTrainingDataset": "MESA",
        "authorExternalTestDataset": "SHHS",
        "authorTrainingNights": 1971,
        "authorExternalTestNights": 1000,
        "authorExternalAccuracy": 0.75,
        "authorExternalKappa": 0.54,
        "slpdbRecordCount": 18,
        "slpdbParticipantCount": 16,
        "slpdbAnnotationFilesPinned": annotation_count,
        "brainstemClassificationEnabled": False,
        "eligibleForRuntimeReview": False,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv[1:])
    if not args.verify:
        parser.error("--verify is required")
    try:
        result = audit(download(load_sources()))
        expected = json.loads((ROOT / "expected-audit.json").read_text())
        if result != expected:
            raise AuditError("audit result differs from expected-audit.json")
    except (AuditError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
