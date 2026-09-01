#!/usr/bin/env python3
"""Checksum-pinned audit of the author heart-rate-fragmentation materials."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MAX_BYTES = 5_000_000
REQUIRED = {
    "original-paper-xml",
    "reference-code",
    "reference-license",
    "reference-readme",
    "reference-series-a",
    "reference-series-b",
    "reference-series-c",
}
EXPECTED_OUTPUTS = {
    "reference-series-a": "PIP = 33/53 = 62.264;   PNNSS = 24/43*100 = 55.814;   PNNLS = 19/51*100 = 37.255",
    "reference-series-b": "PIP = 31/50 = 62.000;   PNNSS = 21/40*100 = 52.500;   PNNLS = 19/47*100 = 40.426",
    "reference-series-c": "PIP = 30/46 = 65.217;   PNNSS = 21/36*100 = 58.333;   PNNLS = 15/43*100 = 34.884",
}
BLOCK_REASONS = [
    "normal_to_normal_annotations_unavailable",
    "source_interval_upper_bound_inconsistent",
    "minimum_reliable_window_unresolved",
    "brainstem_device_transfer_unvalidated",
    "detector_artifact_sensitivity_unvalidated",
]


class AuditError(ValueError):
    pass


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "paper-to-insight-source-audit/1"})
    with urlopen(request, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise AuditError(f"asset exceeds {MAX_BYTES} bytes")
    return data


def load_sources(path: Path = ROOT / "public-sources.json") -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "paper-to-insight.public-sources/v1":
        raise AuditError("unsupported public-sources schema")
    assets = value.get("assets")
    if not isinstance(assets, dict) or set(assets) != REQUIRED:
        raise AuditError("public source set differs")
    return assets


def download(assets: dict) -> dict[str, bytes]:
    result = {}
    for name, item in sorted(assets.items()):
        data = fetch(item["url"])
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise AuditError(f"{name} checksum differs")
        result[name] = data
    return result


def execute_reference(code: bytes, series: bytes) -> str:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "HRF.awk"
        path.write_bytes(code)
        process = subprocess.run(
            ["awk", "-f", str(path)],
            input=series,
            capture_output=True,
            check=True,
            timeout=10,
        )
    return process.stdout.decode().strip()


def audit(assets: dict[str, bytes], runner=execute_reference) -> dict:
    if set(assets) != REQUIRED:
        raise AuditError("audit asset set differs")
    paper = assets["original-paper-xml"].decode()
    code = assets["reference-code"].decode()
    readme = assets["reference-readme"].decode()
    license_text = assets["reference-license"].decode()

    checks = {
        "paper identity": "10.3389/fphys.2017.00255" in paper,
        "paper licence": "Creative Commons Attribution License (CC BY)" in paper,
        "original metric definitions": all(
            marker in paper for marker in ("percentage of zero-crossing", "inverse of the average length", "alternation segment")
        ),
        "normal-beat input": "ann == 1" in code and "normal sinus" in code,
        "reference metrics": all(marker in code for marker in ("PIP", "PNNSS", "PNNLS")),
        "reference GPL": "GNU GENERAL PUBLIC LICENSE" in license_text and "Version 3" in license_text,
        "code upper bound": bool(re.search(r"NN_max\s*=\s*1\.800", code)),
        "readme upper bound": "NN intervals < 0.3 s or > 1.5 s were excluded" in readme,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AuditError(f"source evidence differs: {', '.join(failed)}")

    actual = {
        name: runner(assets["reference-code"], assets[name])
        for name in sorted(EXPECTED_OUTPUTS)
    }
    if actual != EXPECTED_OUTPUTS:
        raise AuditError("author reference output differs")

    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.heart-rate-fragmentation",
        "paperLicense": "CC-BY-4.0",
        "referenceCodeLicense": "GPL-3.0-only",
        "authorReferenceReproduced": True,
        "referenceSeriesCount": 3,
        "sourceThresholdConflict": {"codeUpperBoundSeconds": 1.8, "readmeUpperBoundSeconds": 1.5},
        "promotionStatus": "study_only",
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
    except (AuditError, OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
