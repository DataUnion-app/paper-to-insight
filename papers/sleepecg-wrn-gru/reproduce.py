#!/usr/bin/env python3
"""Reproduce the exact SleepECG model on public SLPDB annotations."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import statistics
import sys
import warnings
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
BASE_URL = "https://physionet.org/files/slpdb/1.0.0"
RECORDS_SHA256 = "aed670a466eb29b50de1f9098928a6818a51f043415137a1c88d24bb84e05d48"
MANIFEST_SHA256 = "c07dc13222cbf509d0efc8b598b31b69b71357141f97562ddc97ade72341a7ac"
MODEL_SHA256 = "5622a858c855b0090e1fbcbdc35334ea459707c830eae1a26a4375e33091e869"
MAX_BYTES = {"RECORDS": 1_000, "SHA256SUMS.txt": 20_000, "hea": 4_096, "ecg": 250_000, "st": 100_000}


class ReproductionError(ValueError):
    pass


def _download(url: str, maximum: int) -> bytes:
    request = Request(url, headers={"User-Agent": "paper-to-insight-reproduction/1"})
    with urlopen(request, timeout=60) as response:
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ReproductionError(f"download exceeds {maximum} bytes")
    return data


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get(path: Path, url: str, maximum: int, digest: str) -> bytes:
    data = path.read_bytes() if path.exists() else _download(url, maximum)
    if _sha(data) != digest:
        raise ReproductionError(f"{path.name} checksum differs")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return data


def _subject(record: str) -> str:
    if record.startswith("slp01"):
        return "subject-01"
    if record.startswith("slp02"):
        return "subject-02"
    return f"subject-{record[3:]}"


def _metrics(matrix: list[list[int]]) -> dict:
    total = sum(map(sum, matrix))
    if not total:
        raise ReproductionError("empty confusion matrix")
    correct = sum(matrix[index][index] for index in range(3))
    rows = [sum(row) for row in matrix]
    columns = [sum(matrix[row][column] for row in range(3)) for column in range(3)]
    accuracy = correct / total
    expected = sum(rows[index] * columns[index] for index in range(3)) / total**2
    kappa = (accuracy - expected) / (1 - expected) if expected < 1 else 0.0
    classes = {}
    for index, name in enumerate(("NREM", "REM", "WAKE")):
        true_positive = matrix[index][index]
        precision = true_positive / columns[index] if columns[index] else 0.0
        recall = true_positive / rows[index] if rows[index] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        classes[name] = {
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "support": rows[index],
        }
    return {
        "epochs": total,
        "accuracy": round(accuracy, 6),
        "cohenKappa": round(kappa, 6),
        "classMetrics": classes,
    }


def reproduce(data_dir: Path) -> dict:
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    try:
        import numpy
        import scipy
        import tensorflow
        import wfdb
        import sleepecg
        from sleepecg import (
            Gender,
            SleepRecord,
            SleepStage,
            SubjectData,
            load_classifier,
            stage,
        )
    except ImportError as exc:
        raise ReproductionError('install "sleepecg[full]==0.5.9"') from exc

    environment = {
        "python": ".".join(map(str, sys.version_info[:3])),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "tensorflow": tensorflow.__version__,
        "wfdb": wfdb.__version__,
        "sleepecg": sleepecg.__version__,
    }
    expected_environment = json.loads(
        (ROOT / "reproduction-environment.json").read_text()
    )
    if environment != expected_environment:
        raise ReproductionError(f"environment differs: {environment}")

    database = data_dir.expanduser().resolve() / "slpdb"
    records_data = _get(
        database / "RECORDS", f"{BASE_URL}/RECORDS", MAX_BYTES["RECORDS"], RECORDS_SHA256
    )
    manifest_data = _get(
        database / "SHA256SUMS.txt",
        f"{BASE_URL}/SHA256SUMS.txt",
        MAX_BYTES["SHA256SUMS.txt"],
        MANIFEST_SHA256,
    )
    records = records_data.decode().split()
    if len(records) != 18 or len(set(records)) != 18:
        raise ReproductionError("SLPDB record set differs")
    manifest = {
        fields[1]: fields[0]
        for line in manifest_data.decode().splitlines()
        if len(fields := line.split()) == 2
    }
    for record in records:
        for extension in ("hea", "ecg", "st"):
            name = f"{record}.{extension}"
            if name not in manifest:
                raise ReproductionError(f"{name} missing from manifest")
            _get(
                database / name,
                f"{BASE_URL}/{name}",
                MAX_BYTES[extension],
                manifest[name],
            )

    model_path = Path(sleepecg.__file__).parent / "classifiers/wrn-gru-mesa.zip"
    if _sha(model_path.read_bytes()) != MODEL_SHA256:
        raise ReproductionError("installed model checksum differs")
    classifier = load_classifier("wrn-gru-mesa", "SleepECG")

    stage_map = {
        "W": SleepStage.WAKE,
        "R": SleepStage.REM,
        "1": SleepStage.N1,
        "2": SleepStage.N2,
        "3": SleepStage.N3,
        "4": SleepStage.N3,
    }
    merged = {
        int(SleepStage.WAKE): 3,
        int(SleepStage.REM): 2,
        int(SleepStage.N1): 1,
        int(SleepStage.N2): 1,
        int(SleepStage.N3): 1,
    }
    matrix = numpy.zeros((3, 3), dtype=numpy.int64)
    subject_matrices = {}
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    for record_id in records:
        base = str(database / record_id)
        header = wfdb.rdheader(base)
        beats = wfdb.rdann(base, "ecg")
        annotations = wfdb.rdann(base, "st")
        last = next(
            int(sample)
            for sample, note in zip(
                annotations.sample[::-1], annotations.aux_note[::-1]
            )
            if note[:1] in stage_map
        )
        truth_raw = numpy.full(
            last // int(30 * header.fs) + 1, SleepStage.UNDEFINED
        )
        for sample, note in zip(annotations.sample, annotations.aux_note):
            if note[:1] in stage_map:
                truth_raw[int(sample) // int(30 * header.fs)] = stage_map[note[:1]]
        age, _, weight, _ = header.comments[0].split()
        record = SleepRecord(
            sleep_stages=truth_raw,
            sleep_stage_duration=30,
            id=record_id,
            recording_start_time=header.base_time,
            heartbeat_times=numpy.asarray(beats.sample) / header.fs,
            subject_data=SubjectData(
                gender=Gender.MALE,
                age=None if age == "x" else int(age),
                weight=None if weight == "x" else int(weight),
            ),
        )
        with contextlib.redirect_stdout(io.StringIO()):
            predicted = stage(classifier, record, return_mode="int")
        truth = numpy.asarray([merged.get(int(value), 0) for value in truth_raw])
        if len(truth) != len(predicted):
            raise ReproductionError("prediction length differs")
        valid = (truth > 0) & (predicted > 0) & (predicted <= 3)
        local = numpy.zeros((3, 3), dtype=numpy.int64)
        numpy.add.at(local, (truth[valid] - 1, predicted[valid] - 1), 1)
        matrix += local
        key = _subject(record_id)
        subject_matrices[key] = subject_matrices.get(
            key, numpy.zeros((3, 3), dtype=numpy.int64)
        ) + local

    result_metrics = _metrics(matrix.tolist())
    accuracies = sorted(
        float(numpy.trace(value) / value.sum()) for value in subject_matrices.values()
    )
    return {
        "schema": "paper-to-insight.public-reproduction/v1",
        "candidate": "brainstem.sleepecg-wrn-gru",
        "sourceVersion": "0.5.9",
        "sourceSdistSha256": "f15ee55ec5567e13cb57a99009d2fe8533702a32cbb4d24c0551fefd45e920ac",
        "modelSha256": MODEL_SHA256,
        "dataset": "MIT-BIH Polysomnographic Database",
        "datasetVersion": "1.0.0",
        "datasetManifestSha256": MANIFEST_SHA256,
        "records": len(records),
        "participants": len(subject_matrices),
        "epochs": result_metrics["epochs"],
        "ontology": ["NREM", "REM", "WAKE"],
        "confusionMatrix": matrix.tolist(),
        "accuracy": result_metrics["accuracy"],
        "cohenKappa": result_metrics["cohenKappa"],
        "classMetrics": result_metrics["classMetrics"],
        "participantAccuracy": {
            "min": round(accuracies[0], 6),
            "median": round(statistics.median(accuracies), 6),
            "max": round(accuracies[-1], 6),
        },
        "publicReproductionAccepted": True,
        "transferOutcome": "poor_external_transfer",
        "brainstemClassificationEnabled": False,
        "eligibleForRuntimeReview": False,
        "blockReasons": [
            "external_transfer_performance_insufficient",
            "public_population_not_representative",
            "brainstem_device_not_calibrated",
            "brainstem_psg_reference_labels_missing",
            "model_requires_age_and_binary_gender",
        ],
        "environment": environment,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args(argv[1:])
    if not args.verify:
        parser.error("--verify is required")
    try:
        result = reproduce(args.data_dir)
        expected = json.loads((ROOT / "expected-public.json").read_text())
        if result != expected:
            raise ReproductionError("result differs from expected-public.json")
    except (OSError, UnicodeError, json.JSONDecodeError, ReproductionError) as exc:
        print(f"reproduction failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

