#!/usr/bin/env python3
"""Checksum-pinned public-data check for the resting-HRV methods candidate."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("hrv_algorithm", HERE / "algorithm.py")
algorithm = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(algorithm)


def download(file: dict, cache: Path) -> Path:
    target = cache / f'{file["record"]}.txt'
    if not target.exists():
        request = urllib.request.Request(
            file["url"], headers={"User-Agent": "paper-to-insight/0.1"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            target.write_bytes(response.read())
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    if actual != file["sha256"]:
        target.unlink(missing_ok=True)
        raise ValueError(f'{file["record"]} checksum mismatch')
    return target


def five_minutes(path: Path) -> list[float]:
    intervals = []
    duration = 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        seconds = float(line.strip())
        if duration + seconds > 300:
            break
        intervals.append(seconds * 1000)
        duration += seconds
    if duration < 299 or len(intervals) < 180:
        raise ValueError(f"{path.name} does not contain a complete five-minute window")
    return intervals


def reproduce(cache: Path) -> dict:
    manifest = json.loads((HERE / "public-data.json").read_text())
    cache.mkdir(parents=True, exist_ok=True)
    records = []
    for file in manifest["files"]:
        metrics = algorithm.hrv(five_minutes(download(file, cache)))
        if metrics is None:
            raise ValueError(f'{file["record"]} failed the fixed quality screen')
        records.append({
            "record": file["record"],
            "metrics": {key: round(value, 6) for key, value in metrics.items()},
        })
    return {
        "schema": "paper-to-insight.public-reproduction/v1",
        "paper": "10.1161/01.CIR.93.5.1043",
        "dataset": {
            "name": manifest["database"],
            "version": manifest["version"],
            "doi": manifest["doi"],
        },
        "window": "first complete five-minute interval sequence",
        "records": records,
        "attribution": manifest["attribution"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=HERE / ".cache")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = reproduce(args.cache)
    if args.verify:
        expected = json.loads((HERE / "expected-public.json").read_text())
        if result != expected:
            raise SystemExit("public reproduction differs from expected-public.json")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

