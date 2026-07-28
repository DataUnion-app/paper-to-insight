#!/usr/bin/env python3
"""Deterministic, methods-only HRV candidate for cohort and personal use."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


ANALYSIS_ID = "brainstem.resting-hrv-methods/v1"
RESULT_SCHEMA = "brainstem.insight-result/v1"
COHORT_SCHEMA = "paper-to-insight.resting-hrv/cohort-v1"
PERSONAL_SCHEMA = "paper-to-insight.resting-hrv/personal-v1"
REFERENCE_SCHEMA = "paper-to-insight.resting-hrv/reference-v1"
ALGORITHM_VERSION = "0.1.0"
MINIMUM_COHORT = 20
MAX_PARTICIPANTS = 1000
MAX_RECORDINGS = 16
MAX_INTERVALS = 3600
MAX_ARTIFACT_FRACTION = 0.05
METRICS = ("sdnnMs", "rmssdMs", "sd1Ms", "sd2Ms")
LABELS = {
    "sdnnMs": "SDNN",
    "rmssdMs": "RMSSD",
    "sd1Ms": "Poincaré SD1",
    "sd2Ms": "Poincaré SD2",
}


class InputError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InputError(message)


def exact(value: object, keys: set[str], where: str) -> dict:
    require(isinstance(value, dict), f"{where} must be an object")
    require(set(value) == keys, f"{where} has missing or unknown fields")
    return value


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def validate_recording(value: object, where: str) -> dict:
    recording = exact(
        value,
        {"recordingType", "durationSeconds", "rrIntervalsMs"},
        where,
    )
    require(recording["recordingType"] == "rest", f"{where} must be resting")
    duration = recording["durationSeconds"]
    require(
        isinstance(duration, int)
        and not isinstance(duration, bool)
        and 240 <= duration <= 360,
        f"{where} duration is invalid",
    )
    intervals = recording["rrIntervalsMs"]
    require(
        isinstance(intervals, list) and 180 <= len(intervals) <= MAX_INTERVALS,
        f"{where} interval count is invalid",
    )
    require(
        all(
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and math.isfinite(item)
            and 100 <= item <= 5000
            for item in intervals
        ),
        f"{where} contains an invalid interval",
    )
    represented_seconds = sum(intervals) / 1000
    require(
        abs(represented_seconds - duration) <= max(5, duration * 0.1),
        f"{where} interval duration does not match durationSeconds",
    )
    return recording


def validate_reference(value: object) -> dict:
    reference = exact(
        value,
        {"schema", "version", "minimumParticipants", "bands", "sha256"},
        "reference",
    )
    require(reference["schema"] == REFERENCE_SCHEMA, "reference schema is invalid")
    require(
        isinstance(reference["version"], str) and reference["version"],
        "reference version is invalid",
    )
    require(
        isinstance(reference["minimumParticipants"], int)
        and not isinstance(reference["minimumParticipants"], bool)
        and reference["minimumParticipants"] >= MINIMUM_COHORT,
        "reference cohort is too small",
    )
    bands = exact(reference["bands"], set(METRICS), "reference bands")
    for key, values in bands.items():
        require(
            isinstance(values, list)
            and len(values) == 2
            and all(
                isinstance(item, (int, float))
                and not isinstance(item, bool)
                and math.isfinite(item)
                and item >= 0
                for item in values
            )
            and values[0] <= values[1],
            f"reference band {key} is invalid",
        )
    expected = sha256({key: reference[key] for key in reference if key != "sha256"})
    require(reference["sha256"] == expected, "reference digest is invalid")
    return reference


def validate_input(value: object) -> dict:
    require(isinstance(value, dict), "input must be an object")
    schema = value.get("schema")
    if schema == COHORT_SCHEMA:
        dataset = exact(value, {"schema", "participants"}, "input")
        participants = dataset["participants"]
        require(
            isinstance(participants, list) and len(participants) <= MAX_PARTICIPANTS,
            "participants are invalid",
        )
        seen = set()
        for participant_index, item in enumerate(participants):
            participant = exact(
                item, {"subjectId", "recordings"}, f"participant {participant_index}"
            )
            subject_id = participant["subjectId"]
            require(
                isinstance(subject_id, str)
                and len(subject_id) == 64
                and all(char in "0123456789abcdef" for char in subject_id)
                and subject_id not in seen,
                "subjectId is invalid or duplicated",
            )
            seen.add(subject_id)
            recordings = participant["recordings"]
            require(
                isinstance(recordings, list) and 1 <= len(recordings) <= MAX_RECORDINGS,
                "recordings count is invalid",
            )
            for index, recording in enumerate(recordings):
                validate_recording(recording, f"participant {participant_index} recording {index}")
        return dataset
    if schema == PERSONAL_SCHEMA:
        dataset = exact(value, {"schema", "recordings", "reference"}, "input")
        recordings = dataset["recordings"]
        require(
            isinstance(recordings, list) and 1 <= len(recordings) <= MAX_RECORDINGS,
            "recordings count is invalid",
        )
        for index, recording in enumerate(recordings):
            validate_recording(recording, f"recording {index}")
        validate_reference(dataset["reference"])
        return dataset
    raise InputError("unsupported input schema")


def hrv(intervals: list[float]) -> dict[str, float] | None:
    valid = [300 <= item <= 2000 for item in intervals]
    accepted = [float(item) for item, keep in zip(intervals, valid) if keep]
    artifact_fraction = 1 - len(accepted) / len(intervals)
    differences = [
        float(intervals[index] - intervals[index - 1])
        for index in range(1, len(intervals))
        if valid[index] and valid[index - 1]
    ]
    if (
        artifact_fraction > MAX_ARTIFACT_FRACTION
        or len(accepted) < 180
        or len(differences) < 2
    ):
        return None
    sdnn = statistics.stdev(accepted)
    sdsd = statistics.stdev(differences)
    rmssd = math.sqrt(statistics.fmean(item * item for item in differences))
    return {
        "sdnnMs": sdnn,
        "rmssdMs": rmssd,
        "sd1Ms": sdsd / math.sqrt(2),
        "sd2Ms": math.sqrt(max(0, 2 * sdnn * sdnn - 0.5 * sdsd * sdsd)),
        "artifactPercent": artifact_fraction * 100,
    }


def participant_metrics(recordings: list[dict]) -> dict[str, float] | None:
    results = [hrv(recording["rrIntervalsMs"]) for recording in recordings]
    eligible = [result for result in results if result is not None]
    if not eligible:
        return None
    return {
        key: statistics.median(result[key] for result in eligible)
        for key in (*METRICS, "artifactPercent")
    }


def evidence() -> dict:
    return {
        "tier": "E2_brainstem_compatible_exploratory",
        "useClass": "methods_only",
        "clinicalUse": "prohibited",
    }


def paper_classification() -> dict:
    return {"decision": "not_applicable", "label": None, "score": None}


def insufficient(scope: str, reason: str, manifest_sha256: str) -> dict:
    return {
        "schema": RESULT_SCHEMA,
        "analysisId": ANALYSIS_ID,
        "scope": scope,
        "status": "insufficient_data",
        "abstentionReason": reason,
        "evidence": evidence(),
        "paperClassification": paper_classification(),
        "title": "Resting heart variability methods",
        "summary": "The method did not have enough compatible data to return a result.",
        "metrics": [],
        "charts": [],
        "table": None,
        "warnings": ["Descriptive research method only; not medical advice."],
        "provenance": {
            "algorithmVersion": ALGORITHM_VERSION,
            "candidateManifestSha256": manifest_sha256,
            "referenceSha256": None,
        },
    }


def metric_rows(metrics: dict[str, float], reference: dict | None = None) -> list[dict]:
    rows = []
    for key in METRICS:
        row = {
            "key": key,
            "label": LABELS[key],
            "value": round(metrics[key], 2),
            "unit": "ms",
            "comparison": None,
        }
        if reference:
            low, high = reference["bands"][key]
            row["comparison"] = (
                "below reference middle band"
                if metrics[key] < low
                else "above reference middle band"
                if metrics[key] > high
                else "within reference middle band"
            )
        rows.append(row)
    rows.append({
        "key": "artifactPercent",
        "label": "Intervals removed by the fixed quality screen",
        "value": round(metrics["artifactPercent"], 2),
        "unit": "%",
        "comparison": None,
    })
    return rows


def build_reference(dataset: dict, version: str) -> dict:
    validate_input(dataset)
    require(dataset["schema"] == COHORT_SCHEMA, "reference requires cohort input")
    values = [
        participant_metrics(participant["recordings"])
        for participant in dataset["participants"]
    ]
    eligible = [value for value in values if value is not None]
    require(len(eligible) >= MINIMUM_COHORT, "reference cohort is too small")
    bands = {}
    for key in METRICS:
        quartiles = statistics.quantiles(
            [value[key] for value in eligible], n=4, method="inclusive"
        )
        bands[key] = [round(quartiles[0], 2), round(quartiles[2], 2)]
    reference = {
        "schema": REFERENCE_SCHEMA,
        "version": version,
        "minimumParticipants": len(eligible),
        "bands": bands,
    }
    return {**reference, "sha256": sha256(reference)}


def build_result(dataset: dict, manifest_sha256: str) -> dict:
    validate_input(dataset)
    require(
        isinstance(manifest_sha256, str)
        and len(manifest_sha256) == 64
        and all(char in "0123456789abcdef" for char in manifest_sha256),
        "candidate manifest digest is invalid",
    )
    if dataset["schema"] == COHORT_SCHEMA:
        participant_values = [
            participant_metrics(participant["recordings"])
            for participant in dataset["participants"]
        ]
        eligible = [value for value in participant_values if value is not None]
        if len(eligible) < MINIMUM_COHORT:
            return insufficient("cohort", "privacy_floor", manifest_sha256)
        metrics = {
            key: statistics.median(value[key] for value in eligible)
            for key in (*METRICS, "artifactPercent")
        }
        scope = "cohort"
        summary = "Disclosure-protected median HRV methods across the eligible group."
        reference_sha = None
    else:
        metrics = participant_metrics(dataset["recordings"])
        if metrics is None:
            return insufficient("personal", "insufficient_quality", manifest_sha256)
        scope = "personal"
        summary = (
            "Your compatible resting recordings compared with a frozen aggregate "
            "reference. The bands are descriptive, not normal ranges."
        )
        reference_sha = dataset["reference"]["sha256"]

    rows = metric_rows(
        metrics, dataset.get("reference") if scope == "personal" else None
    )
    return {
        "schema": RESULT_SCHEMA,
        "analysisId": ANALYSIS_ID,
        "scope": scope,
        "status": "complete",
        "abstentionReason": None,
        "evidence": evidence(),
        "paperClassification": paper_classification(),
        "title": "Resting heart variability methods",
        "summary": summary,
        "metrics": [
            {"label": row["label"], "value": row["value"], "unit": row["unit"]}
            for row in rows
        ],
        "charts": [{
            "type": "bar",
            "title": "Time-domain and Poincaré measures",
            "x": {"label": "Method", "values": [LABELS[key] for key in METRICS]},
            "y": {"label": "Value", "unit": "ms"},
            "series": [{
                "label": "Result",
                "values": [round(metrics[key], 2) for key in METRICS],
            }],
        }],
        "table": {
            "columns": ["Measure", "Value", "Comparison"],
            "rows": [
                [row["label"], f'{row["value"]} {row["unit"]}', row["comparison"] or "—"]
                for row in rows
            ],
        },
        "warnings": [
            "Descriptive research method only; not medical advice.",
            "Reference bands are not clinical normal ranges.",
        ],
        "provenance": {
            "algorithmVersion": ALGORITHM_VERSION,
            "candidateManifestSha256": manifest_sha256,
            "referenceSha256": reference_sha,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--reference-output", type=Path)
    parser.add_argument("--reference-version", default="generated-v1")
    args = parser.parse_args()
    dataset = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_result(dataset, args.candidate_sha256)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.reference_output:
        reference = build_reference(dataset, args.reference_version)
        args.reference_output.write_text(
            json.dumps(reference, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
