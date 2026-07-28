#!/usr/bin/env python3
"""Checksum-pinned public reproduction for resting R–R sample entropy."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("sample_entropy_algorithm", HERE / "algorithm.py")
algorithm = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(algorithm)
MAX_BYTES = 500_000


def download(item: dict, cache: Path) -> Path:
    name = item.get("name") or f'{item["record"]}.txt'
    target = cache / name
    if not target.exists():
        request = urllib.request.Request(
            item["url"], headers={"User-Agent": "paper-to-insight/0.1"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError(f"{name} exceeds the download limit")
        target.write_bytes(data)
    if hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]:
        raise ValueError(f"{name} checksum mismatch")
    return target


def five_minutes(path: Path) -> list[float]:
    intervals = []
    duration = 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        seconds = float(line)
        if duration + seconds > 300:
            break
        intervals.append(seconds * 1000)
        duration += seconds
    if duration < 299:
        raise ValueError(f"{path.name} has no complete five-minute window")
    return intervals


def reproduce(cache: Path) -> dict:
    manifest = json.loads((HERE / "public-data.json").read_text())
    cache.mkdir(parents=True, exist_ok=True)
    reference_files = {
        item["name"]: download(item, cache)
        for item in manifest["reference"]["files"]
    }
    source = reference_files["sampen.c"].read_text()
    if not all(
        marker in source
        for marker in (
            "Last revised:",
            "1 November 2004",
            "normalize(double *data, int n)",
            "p[m] = A[m] / B[m - 1]",
        )
    ):
        raise ValueError("reference source contract differs")
    expected_match = re.search(
        r"SampEn\(2,0\.2,1024\) = ([0-9.]+)",
        reference_files["expected.out"].read_text(),
    )
    if expected_match is None:
        raise ValueError("reference output is missing m=2")
    reference_values = [
        float(value) for value in reference_files["sampentest.txt"].read_text().split()
    ]
    reference_result = algorithm.sample_entropy(reference_values)
    if reference_result is None:
        raise ValueError("reference vector abstained")
    expected_reference = round(float(expected_match.group(1)), 6)
    if round(reference_result["sampleEntropy"], 6) != expected_reference:
        raise ValueError("independent implementation differs from reference output")

    records = []
    for item in manifest["dataset"]["files"]:
        result = algorithm.resting_rr_sample_entropy(
            five_minutes(download(item, cache))
        )
        if result is None:
            raise ValueError(f'{item["record"]} abstained')
        records.append({
            "record": item["record"],
            "metrics": {
                "intervalCount": result["intervalCount"],
                "sampleEntropy": round(result["sampleEntropy"], 6),
                "templateMatches": result["templateMatches"],
                "extendedMatches": result["extendedMatches"],
            },
        })

    return {
        "schema": "paper-to-insight.public-reproduction/v1",
        "paper": manifest["paper"]["doi"],
        "dataset": {
            key: manifest["dataset"][key] for key in ("name", "version", "doi")
        },
        "window": "first complete five-minute interval sequence",
        "records": records,
        "attribution": manifest["dataset"]["attribution"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=HERE / ".cache")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = reproduce(args.cache)
    if args.verify and result != json.loads((HERE / "expected-public.json").read_text()):
        raise SystemExit("public reproduction differs from expected-public.json")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
