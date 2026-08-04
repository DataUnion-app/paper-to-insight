#!/usr/bin/env python3
"""Run the pre-committed UCDDB external evaluation without tuning."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import reproduce


ROOT = Path(__file__).resolve().parent
BASE = "https://physionet.org/files/ucddb/1.0.0"
MANIFEST_SHA256 = "c844fb0eb8bc35936d7a5b07cecab895e29d9a2c93dac3a23465e799e00385a1"
PLAN_SHA256 = "44ed0e698e21dcb683e332e90b50756a19c28954b7c30c2c80a1a2ac1fdb3d68"
RR_LIST = r'''#!{python}
import sys
from pathlib import Path
if len(sys.argv) != 6 or sys.argv[1] != "qrs" or sys.argv[3:] != ["-a", "N", "-s"]:
    raise SystemExit("unsupported rrlist invocation")
sys.stdout.write(Path(sys.argv[2] + ".rr").read_text())
'''


def _matrix_metrics(matrix: list[list[int]]) -> dict:
    negative = sum(matrix[0])
    positive = sum(matrix[1])
    total = negative + positive
    sensitivity = matrix[1][1] / positive if positive else math.nan
    specificity = matrix[0][0] / negative if negative else math.nan
    accuracy = (matrix[0][0] + matrix[1][1]) / total if total else math.nan
    balanced = (sensitivity + specificity) / 2
    return {
        "sensitivity": sensitivity,
        "specificity": specificity,
        "balancedAccuracy": balanced,
        "accuracy": accuracy,
    }


def _round_metrics(metrics: dict) -> dict:
    return {
        key: None if math.isnan(value) else round(value, 6)
        for key, value in metrics.items()
    }


def _events(text: str, start: datetime, duration: float) -> list[tuple[float, float]]:
    result = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 3 or not re.fullmatch(r"\d\d:\d\d:\d\d", fields[0]):
            continue
        if not (fields[1].startswith("APNEA-") or fields[1].startswith("HYP-")):
            continue
        seconds = next((int(value) for value in fields[2:] if value.isdigit()), None)
        if seconds is None or seconds <= 0:
            raise reproduce.ReproductionError("respiratory event duration is invalid")
        event = datetime.combine(start.date(), datetime.strptime(fields[0], "%H:%M:%S").time())
        while event < start:
            event += timedelta(days=1)
        offset = (event - start).total_seconds()
        if offset < 0 or offset >= duration or offset + seconds > duration:
            raise reproduce.ReproductionError("respiratory event falls outside EDF duration")
        result.append((offset, offset + seconds))
    return result


def _evaluate(record: str, data: Path, manifest: dict, source: bytes, plan: dict) -> dict:
    import numpy
    import pyedflib
    import wfdb
    from wfdb import processing

    names = {
        "edf": f"{record}.rec",
        "events": f"{record}_respevt.txt",
        "stages": f"{record}_stage.txt",
    }
    for kind, name in names.items():
        maximum = 50_000_000 if kind == "edf" else 100_000
        reproduce._get(data / name, f"{BASE}/{name}", maximum, manifest[name])

    reader = pyedflib.EdfReader(str(data / names["edf"]))
    try:
        labels = [label.strip() for label in reader.getSignalLabels()]
        matches = [index for index, label in enumerate(labels) if label == "ECG"]
        if len(matches) != 1:
            return {"participant": record, "abstention": "ecg_channel_not_unique"}
        index = matches[0]
        sample_rate = float(reader.getSampleFrequency(index))
        duration = float(reader.file_duration)
        start = reader.getStartdatetime()
        ecg = reader.readSignal(index, digital=False)
    finally:
        reader.close()

    if sample_rate != plan["input"]["expectedSampleRateHz"]:
        return {"participant": record, "abstention": "sample_rate_differs"}
    if not 5 * 3600 <= duration <= 12 * 3600:
        return {"participant": record, "abstention": "duration_outside_contract"}
    if not numpy.isfinite(ecg).all():
        return {"participant": record, "abstention": "non_finite_ecg"}

    peaks = numpy.asarray(
        processing.xqrs_detect(sig=ecg, fs=sample_rate, verbose=False),
        dtype=numpy.int64,
    )
    if len(peaks) < 2 or numpy.any(numpy.diff(peaks) <= 0):
        return {"participant": record, "abstention": "invalid_detector_peaks"}
    complete_minutes = int(duration // 60)
    beat_counts, _ = numpy.histogram(peaks / sample_rate, bins=numpy.arange(complete_minutes + 1) * 60)
    coverage = float(numpy.mean(beat_counts >= 20))
    rr = numpy.diff(peaks) / sample_rate
    median_rr = float(numpy.median(rr))
    if coverage < 0.8:
        return {"participant": record, "abstention": "insufficient_minute_beat_coverage"}
    if not 0.4 <= median_rr <= 2.0:
        return {"participant": record, "abstention": "median_rr_outside_contract"}

    try:
        events = _events(
            (data / names["events"]).read_text(errors="strict"), start, duration
        )
    except reproduce.ReproductionError:
        return {"participant": record, "abstention": "respiratory_event_outside_contract"}
    truth = [
        any(event_start < (minute + 1) * 60 and event_end > minute * 60 for event_start, event_end in events)
        for minute in range(complete_minutes)
    ]
    stages = [int(value) for value in (data / names["stages"]).read_text().split()]
    if any(value not in range(8) for value in stages):
        return {"participant": record, "abstention": "sleep_stage_code_invalid"}
    expected_stages = int(duration // 30)
    if abs(len(stages) - expected_stages) > 1:
        return {"participant": record, "abstention": "sleep_stage_duration_mismatch"}
    sleep_hours = (
        sum(value in range(1, 6) for value in stages[:expected_stages]) * 30 / 3600
    )
    if sleep_hours <= 0:
        return {"participant": record, "abstention": "sleep_time_unavailable"}

    with tempfile.TemporaryDirectory(prefix=f"ucddb-{record}-") as temporary:
        work = Path(temporary)
        runner = reproduce._build(source, work)
        rrlist = work / "rrlist"
        rrlist.write_text(RR_LIST.format(python=sys.executable), encoding="utf-8")
        rrlist.chmod(0o755)
        base = work / record
        base.with_suffix(".rr").write_text(
            "".join(
                f"{current / sample_rate:.3f} {(current - previous) / sample_rate:.3f} N\n"
                for previous, current in zip(peaks, peaks[1:])
            ),
            encoding="ascii",
        )
        intervals, detected_fraction = reproduce._execute_apdet(runner, base, work / "run")

    predicted = [
        any(interval_start < (minute + 1) * 60 and interval_end > minute * 60 for interval_start, interval_end in intervals)
        for minute in range(complete_minutes)
    ]
    matrix = [[0, 0], [0, 0]]
    for actual, estimate in zip(truth, predicted):
        matrix[int(actual)][int(estimate)] += 1
    metrics = _matrix_metrics(matrix)
    reference_fraction = sum(truth) / len(truth)
    predicted_fraction = sum(predicted) / len(predicted)
    ahi = len(events) / sleep_hours
    return {
        "participant": record,
        "minutes": complete_minutes,
        "durationHours": round(duration / 3600, 6),
        "beatCoverage": round(coverage, 6),
        "medianRrSeconds": round(median_rr, 6),
        "respiratoryEvents": len(events),
        "derivedAhi": round(ahi, 6),
        "referencePositiveFraction": round(reference_fraction, 6),
        "predictedPositiveFraction": round(predicted_fraction, 6),
        "detectedTimeFraction": round(detected_fraction, 6),
        "confusionMatrixRowsTruthNThenA": matrix,
        **_round_metrics(metrics),
    }


def _bootstrap(participants: list[dict], numpy) -> dict:
    names = ("sensitivity", "specificity", "balancedAccuracy", "accuracy")
    values = numpy.asarray(
        [
            [numpy.nan if item[name] is None else item[name] for name in names]
            for item in participants
        ],
        dtype=float,
    )
    generator = numpy.random.default_rng(20260804)
    sample = values[generator.integers(0, len(values), size=(10_000, len(values)))]
    result = {}
    for index, name in enumerate(names):
        metric_sample = sample[:, :, index]
        counts = numpy.sum(numpy.isfinite(metric_sample), axis=1)
        means = numpy.divide(
            numpy.nansum(metric_sample, axis=1),
            counts,
            out=numpy.full(len(metric_sample), numpy.nan),
            where=counts > 0,
        )
        finite = means[numpy.isfinite(means)]
        result[name] = (
            {
                "low": round(float(numpy.quantile(finite, 0.025)), 6),
                "high": round(float(numpy.quantile(finite, 0.975)), 6),
            }
            if len(finite)
            else {"low": None, "high": None}
        )
    return result


def validate(cache: Path) -> dict:
    import numpy
    import pyedflib
    import scipy
    import wfdb
    from scipy.stats import spearmanr

    plan_data = (ROOT / "ucddb-evaluation-plan.json").read_bytes()
    if reproduce._sha(plan_data) != PLAN_SHA256:
        raise reproduce.ReproductionError("locked UCDDB plan digest differs")
    plan = json.loads(plan_data)
    environment = {
        "python": ".".join(map(str, sys.version_info[:3])),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "wfdb": wfdb.__version__,
        "pyedflib": pyedflib.__version__,
    }
    if environment != plan["environment"]:
        raise reproduce.ReproductionError(f"environment differs: {environment}")

    cache = cache.expanduser().resolve()
    source = reproduce._get(cache / "apdet.src.tar.gz", reproduce.SOURCE_URL, 100_000, reproduce.SOURCE_SHA256)
    data = cache / "ucddb-1.0.0"
    manifest_data = reproduce._get(data / "SHA256SUMS.txt", f"{BASE}/SHA256SUMS.txt", 100_000, MANIFEST_SHA256)
    manifest = {
        fields[1]: fields[0]
        for line in manifest_data.decode().splitlines()
        if len(fields := line.split()) == 2
    }
    required = [
        f"{record}{suffix}"
        for record in plan["dataset"]["participants"]
        for suffix in (".rec", "_respevt.txt", "_stage.txt")
    ]
    if any(name not in manifest for name in required):
        raise reproduce.ReproductionError("locked UCDDB input is absent from manifest")

    def fetch(name: str) -> None:
        maximum = 50_000_000 if name.endswith(".rec") else 100_000
        reproduce._get(data / name, f"{BASE}/{name}", maximum, manifest[name])

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fetch, required))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(
                lambda record: _evaluate(record, data, manifest, source, plan),
                plan["dataset"]["participants"],
            )
        )

    abstentions = [item for item in results if "abstention" in item]
    participants = [item for item in results if "abstention" not in item]
    if not participants:
        raise reproduce.ReproductionError("every UCDDB participant abstained")
    aggregate = [[0, 0], [0, 0]]
    for item in participants:
        matrix = item["confusionMatrixRowsTruthNThenA"]
        for row in range(2):
            for column in range(2):
                aggregate[row][column] += matrix[row][column]
    def participant_summary(name: str, function) -> float | None:
        values = numpy.asarray(
            [
                numpy.nan if item[name] is None else item[name]
                for item in participants
            ],
            dtype=float,
        )
        value = float(function(values))
        return None if math.isnan(value) else round(value, 6)

    metric_names = ("sensitivity", "specificity", "balancedAccuracy", "accuracy")
    macro = {name: participant_summary(name, numpy.nanmean) for name in metric_names}
    medians = {name: participant_summary(name, numpy.nanmedian) for name in metric_names}
    reference = numpy.asarray([item["referencePositiveFraction"] for item in participants])
    predicted = numpy.asarray([item["predictedPositiveFraction"] for item in participants])
    ahi = numpy.asarray([item["derivedAhi"] for item in participants])
    detected = numpy.asarray([item["detectedTimeFraction"] for item in participants])
    prevalence_correlation = float(spearmanr(reference, predicted).statistic)
    ahi_correlation = float(spearmanr(ahi, detected).statistic)
    record_matrix = [[0, 0], [0, 0]]
    for item in participants:
        record_matrix[int(item["derivedAhi"] >= 15)][int(item["detectedTimeFraction"] >= 0.05)] += 1

    participant_digest = hashlib.sha256(
        json.dumps(results, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "schema": "paper-to-insight.external-validation/v1",
        "candidate": "brainstem.apnea-ecg-heart-rate",
        "dataset": "UCDDB",
        "datasetVersion": "1.0.0",
        "datasetManifestSha256": MANIFEST_SHA256,
        "planSha256": PLAN_SHA256,
        "participantsPlanned": len(results),
        "participantsEvaluated": len(participants),
        "abstentions": abstentions,
        "participantResultsSha256": participant_digest,
        "aggregateMinuteConfusionMatrixRowsTruthNThenA": aggregate,
        "aggregateMinuteMetrics": _round_metrics(_matrix_metrics(aggregate)),
        "participantMacroMean": macro,
        "participantMedian": medians,
        "participantBootstrap95": _bootstrap(participants, numpy),
        "calibration": {
            "meanAbsolutePrevalenceError": round(float(numpy.mean(numpy.abs(predicted - reference))), 6),
            "medianSignedPrevalenceError": round(float(numpy.median(predicted - reference)), 6),
            "prevalenceSpearman": None if math.isnan(prevalence_correlation) else round(prevalence_correlation, 6),
        },
        "secondary": {
            "recordConfusionMatrixRowsAhiBelow15ThenAtLeast15": record_matrix,
            "detectedFractionAhiSpearman": None if math.isnan(ahi_correlation) else round(ahi_correlation, 6),
        },
        "participants": participants,
        "status": "reported_without_success_threshold",
        "brainstemDeviceValidated": False,
        "personalApneaOutputEnabled": False,
        "runnableApneaOfferEnabled": False,
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
        result = validate(args.cache)
        expected = json.loads((ROOT / "expected-external.json").read_text())
        if result != expected:
            raise reproduce.ReproductionError("external result differs from expected-external.json")
    except (OSError, UnicodeError, json.JSONDecodeError, reproduce.ReproductionError) as exc:
        print(f"external validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
