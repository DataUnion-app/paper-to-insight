#!/usr/bin/env python3
"""Run the checksum-pinned official apdet package on public Apnea-ECG labels."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
BASE = "https://physionet.org/files/apnea-ecg/1.0.0"
SOURCE_URL = "https://physionet.org/files/apdet/1.0.0/apdet.src.tar.gz"
SOURCE_SHA256 = "b4961dae0e5bded52a2caecf6bcc186837d4deccf1ac2f173c9f6d5f0a376eac"
MANIFEST_SHA256 = "970d643ec848af6bbc2bda148d1f8e165d439514948b23e5df76e962ba7a5b61"
TOOLS = ("av", "detruns", "filt", "ht", "htavsd", "htmedfilt", "ldetrend", "linsamp", "mm", "smooth")
RECORDS = tuple(
    [f"a{i:02d}" for i in range(1, 21)]
    + [f"b{i:02d}" for i in range(1, 6)]
    + [f"c{i:02d}" for i in range(1, 11)]
)
RR_LIST = r'''#!{python}
import sys
import wfdb

if len(sys.argv) != 6 or sys.argv[1] != "qrs" or sys.argv[3:] != ["-a", "N", "-s"]:
    raise SystemExit("unsupported rrlist invocation")
record = sys.argv[2]
header = wfdb.rdheader(record)
ann = wfdb.rdann(record, "qrs")
normal = [sample for sample, symbol in zip(ann.sample, ann.symbol) if symbol == "N"]
for previous, current in zip(normal, normal[1:]):
    print(f"{{current / header.fs:.3f}} {{(current - previous) / header.fs:.3f}} N")
'''


class ReproductionError(ValueError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _download(url: str, maximum: int) -> bytes:
    request = Request(url, headers={"User-Agent": "paper-to-insight-reproduction/2"})
    with urlopen(request, timeout=60) as response:
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ReproductionError(f"download exceeds {maximum} bytes")
    return data


def _get(path: Path, url: str, maximum: int, digest: str) -> bytes:
    data = path.read_bytes() if path.exists() else _download(url, maximum)
    if _sha(data) != digest:
        raise ReproductionError(f"{path.name} checksum differs")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return data


def _environment(wfdb_version: str) -> dict:
    compiler = subprocess.run(
        [os.environ.get("CC", "cc"), "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0]
    return {
        "python": ".".join(map(str, sys.version_info[:3])),
        "wfdb": wfdb_version,
        "system": platform.system(),
        "machine": platform.machine(),
        "release": platform.release(),
        "compiler": compiler,
    }


def _build(source: bytes, directory: Path) -> Path:
    try:
        with tarfile.open(fileobj=__import__("io").BytesIO(source), mode="r:gz") as archive:
            members = {member.name: member for member in archive.getmembers()}
            for tool in TOOLS:
                member = members[f"apdet-1.0/{tool}.c"]
                (directory / f"{tool}.c").write_bytes(archive.extractfile(member).read())
            script = archive.extractfile(members["apdet-1.0/get_apdet"]).read().decode("ascii")
    except (KeyError, AttributeError, tarfile.TarError, OSError) as exc:
        raise ReproductionError("official source archive is invalid") from exc

    compiler = os.environ.get("CC", "cc")
    for tool in TOOLS:
        command = [compiler, "-std=gnu89", "-O2", "-Wno-implicit-function-declaration", "-o", str(directory / tool), str(directory / f"{tool}.c")]
        if tool in {"av", "ht", "htavsd"}:
            command.append("-lm")
        subprocess.run(command, check=True, capture_output=True)

    rrlist = directory / "rrlist"
    rrlist.write_text(RR_LIST.format(python=sys.executable), encoding="utf-8")
    rrlist.chmod(0o755)
    get_apdet = directory / "get_apdet"
    get_apdet.write_text(
        re.sub(r"^BINDIR=.*$", f"BINDIR={directory}", script, count=1, flags=re.MULTILINE),
        encoding="ascii",
    )
    get_apdet.chmod(0o755)
    return get_apdet


def _seconds(value: str) -> int:
    hours, minutes, seconds = map(int, value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def _execute_apdet(runner: Path, record: Path, local: Path) -> tuple[list[tuple[int, int]], float]:
    local.mkdir()
    completed = subprocess.run(
        [str(runner), str(record), "qrs"],
        cwd=local,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": f"{runner.parent}:{os.environ.get('PATH', '')}"},
    )
    intervals = []
    for line in completed.stdout.splitlines():
        match = re.fullmatch(r"(\d\d:\d\d:\d\d) - (\d\d:\d\d:\d\d)", line.strip())
        if match:
            intervals.append((_seconds(match.group(1)), _seconds(match.group(2))))
    total = re.search(r"tot = (\d\d:\d\d:\d\d) / (\d\d:\d\d:\d\d) = ([0-9.]+)", completed.stdout)
    if not total:
        raise ReproductionError(f"{record.name} output is invalid")
    detected_seconds = _seconds(total.group(1))
    total_seconds = _seconds(total.group(2))
    return intervals, detected_seconds / total_seconds


def _run_record(record: str, data: Path, runner: Path, work: Path, wfdb) -> dict:
    intervals, fraction = _execute_apdet(runner, data / record, work / record)

    header = wfdb.rdheader(str(data / record))
    truth = wfdb.rdann(str(data / record), "apn")
    predicted = [
        "A" if any(start <= sample / header.fs < end for start, end in intervals) else "N"
        for sample in truth.sample
    ]
    matrix = [[0, 0], [0, 0]]
    index = {"N": 0, "A": 1}
    for actual, estimate in zip(truth.symbol, predicted):
        if actual not in index:
            raise ReproductionError(f"{record} has unsupported reference label")
        matrix[index[actual]][index[estimate]] += 1
    expected = record[0].upper()
    record_prediction = "A" if fraction >= 0.05 else "C"
    return {
        "record": record,
        "minutes": len(predicted),
        "confusionMatrix": matrix,
        "detectedFraction": round(fraction, 6),
        "referenceClass": expected,
        "predictedClass": record_prediction,
    }


def reproduce(cache: Path) -> dict:
    try:
        import wfdb
    except ImportError as exc:
        raise ReproductionError('install "wfdb==4.3.1"') from exc

    environment = _environment(wfdb.__version__)
    expected_environment = json.loads((ROOT / "reproduction-environment.json").read_text())
    if environment != expected_environment:
        raise ReproductionError(f"environment differs: {environment}")

    cache = cache.expanduser().resolve()
    source = _get(cache / "apdet.src.tar.gz", SOURCE_URL, 100_000, SOURCE_SHA256)
    data = cache / "apnea-ecg-1.0.0"
    manifest_data = _get(data / "SHA256SUMS.txt", f"{BASE}/SHA256SUMS.txt", 100_000, MANIFEST_SHA256)
    manifest = {
        fields[1]: fields[0]
        for line in manifest_data.decode().splitlines()
        if len(fields := line.split()) == 2
    }
    for record in RECORDS:
        for extension, maximum in (("hea", 10_000), ("qrs", 250_000), ("apn", 25_000)):
            name = f"{record}.{extension}"
            if name not in manifest:
                raise ReproductionError(f"{name} is absent from the official manifest")
            _get(data / name, f"{BASE}/{name}", maximum, manifest[name])

    with tempfile.TemporaryDirectory(prefix="apdet-reproduction-") as temporary:
        work = Path(temporary)
        runner = _build(source, work)
        with ThreadPoolExecutor(max_workers=8) as pool:
            records = list(pool.map(lambda name: _run_record(name, data, runner, work, wfdb), RECORDS))

    matrix = [[0, 0], [0, 0]]
    for item in records:
        for row in range(2):
            for column in range(2):
                matrix[row][column] += item["confusionMatrix"][row][column]
    minutes = sum(map(sum, matrix))
    correct = matrix[0][0] + matrix[1][1]
    sensitivity = matrix[1][1] / sum(matrix[1])
    specificity = matrix[0][0] / sum(matrix[0])
    classified = [item for item in records if item["referenceClass"] != "B"]
    record_correct = sum(item["referenceClass"] == item["predictedClass"] for item in classified)
    record_digest = _sha(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    )
    return {
        "schema": "paper-to-insight.public-reproduction/v2",
        "candidate": "brainstem.apnea-ecg-heart-rate",
        "method": "official PhysioNet apdet 1.0.0 source",
        "sourceSha256": SOURCE_SHA256,
        "dataset": "PhysioNet Apnea-ECG Database",
        "datasetVersion": "1.0.0",
        "datasetManifestSha256": MANIFEST_SHA256,
        "learningRecords": len(records),
        "participantSeparated": False,
        "knownOverlappingRecords": ["c05", "c06"],
        "minutes": minutes,
        "confusionMatrixRowsTruthNThenA": matrix,
        "correctMinutes": correct,
        "minuteAccuracy": round(correct / minutes, 6),
        "sensitivity": round(sensitivity, 6),
        "specificity": round(specificity, 6),
        "balancedAccuracy": round((sensitivity + specificity) / 2, 6),
        "nonBorderlineRecordCorrect": record_correct,
        "nonBorderlineRecordTotal": len(classified),
        "nonBorderlineMisclassified": [
            item["record"]
            for item in classified
            if item["referenceClass"] != item["predictedClass"]
        ],
        "borderlineRecordPredictions": {
            item["record"]: item["predictedClass"]
            for item in records
            if item["referenceClass"] == "B"
        },
        "recordResultsSha256": record_digest,
        "historicalPaperTarget": {
            "correctMinutes": 13985,
            "minutes": 17045,
            "nonBorderlineRecordCorrect": 26,
            "nonBorderlineRecordTotal": 30,
        },
        "historicalHeadlineReproducedExactly": correct == 13985 and record_correct == 26,
        "publicReproductionAccepted": False,
        "status": "current_official_package_executed_historical_result_mismatch",
        "brainstemClassificationEnabled": False,
        "eligibleForRuntimeReview": False,
        "environment": environment,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args(argv[1:])
    if not args.verify:
        parser.error("--verify is required")
    try:
        result = reproduce(args.cache)
        expected = json.loads((ROOT / "expected-public.json").read_text())
        if result != expected:
            raise ReproductionError("result differs from expected-public.json")
    except (OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError, ReproductionError) as exc:
        print(f"reproduction failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
