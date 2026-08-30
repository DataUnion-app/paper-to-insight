#!/usr/bin/env python3
"""Generated methods example for repeated five-minute resting HRV."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics


SCHEMA = "paper-to-insight.resting-hrv-repeatability/generated-v1"
RESULT_SCHEMA = "paper-to-insight.resting-hrv-repeatability/result-v1"
METRICS = ("heartRateBpm", "sdnnMs", "rmssdMs", "sd1Ms", "sd2Ms")
BOUNDS = {
    "heartRateBpm": (30, 220),
    "sdnnMs": (0, 1000),
    "rmssdMs": (0, 1000),
    "sd1Ms": (0, 1000),
    "sd2Ms": (0, 1500),
}
MAX_PARTICIPANTS = 1000
MAX_RECORDINGS = 7
MINIMUM_COHORT = 20
BOOTSTRAPS = 1000


class InputError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InputError(message)


def exact(value: object, keys: set[str], where: str) -> dict:
    require(isinstance(value, dict), f"{where} must be an object")
    require(set(value) == keys, f"{where} fields differ")
    return value


def validate(value: object) -> tuple[str, list[dict]]:
    root = exact(value, {"schema", "mode", "participants"}, "input")
    require(root["schema"] == SCHEMA, "unsupported schema")
    mode = root["mode"]
    require(mode in {"personal", "cohort"}, "unsupported mode")
    participants = root["participants"]
    require(
        isinstance(participants, list)
        and 1 <= len(participants) <= MAX_PARTICIPANTS,
        "participant count is invalid",
    )
    require(mode != "personal" or len(participants) == 1, "personal mode needs one participant")
    seen_subjects = set()
    for participant_index, item in enumerate(participants):
        participant = exact(item, {"subjectId", "recordings"}, f"participant {participant_index}")
        subject_id = participant["subjectId"]
        require(
            isinstance(subject_id, str)
            and len(subject_id) == 64
            and all(char in "0123456789abcdef" for char in subject_id)
            and subject_id not in seen_subjects,
            "subjectId is invalid or duplicated",
        )
        seen_subjects.add(subject_id)
        recordings = participant["recordings"]
        minimum = 7 if mode == "cohort" else 2
        require(
            isinstance(recordings, list)
            and minimum <= len(recordings) <= MAX_RECORDINGS,
            "recording count is invalid",
        )
        seen_indices = set()
        for recording_index, item in enumerate(recordings):
            recording = exact(
                item,
                {"recordingIndex", *METRICS},
                f"participant {participant_index} recording {recording_index}",
            )
            index = recording["recordingIndex"]
            require(
                isinstance(index, int)
                and not isinstance(index, bool)
                and 1 <= index <= MAX_RECORDINGS
                and index not in seen_indices,
                "recordingIndex is invalid or duplicated",
            )
            seen_indices.add(index)
            for metric in METRICS:
                metric_value = recording[metric]
                low, high = BOUNDS[metric]
                require(
                    isinstance(metric_value, (int, float))
                    and not isinstance(metric_value, bool)
                    and math.isfinite(metric_value)
                    and low < metric_value <= high,
                    f"{metric} is invalid",
                )
        participant["recordings"].sort(key=lambda item: item["recordingIndex"])
    participants.sort(key=lambda item: item["subjectId"])
    return mode, participants


def cv_percent(values: list[float]) -> float:
    mean = statistics.fmean(values)
    return statistics.stdev(values) / mean * 100


def icc_one_way(groups: list[list[float]]) -> float | None:
    count = len(groups)
    repeats = len(groups[0])
    participant_means = [statistics.fmean(group) for group in groups]
    grand_mean = statistics.fmean(participant_means)
    between = repeats * sum((item - grand_mean) ** 2 for item in participant_means) / (count - 1)
    within = sum(
        sum((value - participant_means[index]) ** 2 for value in group)
        for index, group in enumerate(groups)
    ) / (count * (repeats - 1))
    denominator = between + (repeats - 1) * within
    if denominator <= 0 or math.isclose(denominator, 0, abs_tol=1e-12):
        return None
    return max(-1.0, min(1.0, (between - within) / denominator))


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def personal_result(participant: dict) -> dict:
    metrics = {}
    for metric in METRICS:
        values = [float(item[metric]) for item in participant["recordings"]]
        metrics[metric] = {
            "median": round(statistics.median(values), 3),
            "minimum": round(min(values), 3),
            "maximum": round(max(values), 3),
            "cvPercent": round(cv_percent(values), 3),
        }
    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "mode": "personal",
        "recordingCount": len(participant["recordings"]),
        "metrics": metrics,
        "warnings": [
            "Repeatability of eligible Brainstem rest recordings only.",
            "This does not define a normal range, diagnosis, disease risk, or treatment target.",
        ],
    }


def cohort_result(participants: list[dict]) -> dict:
    if len(participants) < MINIMUM_COHORT:
        return {
            "schema": RESULT_SCHEMA,
            "status": "insufficient_data",
            "mode": "cohort",
            "reason": "privacy_floor",
            "metrics": {},
            "warnings": ["At least 20 participants are required."],
        }
    output = {}
    for metric in METRICS:
        groups = [
            [float(recording[metric]) for recording in participant["recordings"]]
            for participant in participants
        ]
        estimate = icc_one_way(groups)
        require(estimate is not None, f"{metric} reliability is undefined")
        seed = hashlib.sha256(
            json.dumps({"metric": metric, "groups": groups}, separators=(",", ":")).encode()
        ).hexdigest()
        rng = random.Random(int(seed[:16], 16))
        sampled = []
        for _ in range(BOOTSTRAPS):
            value = icc_one_way([groups[rng.randrange(len(groups))] for _ in groups])
            if value is not None:
                sampled.append(value)
        require(len(sampled) >= 800, f"{metric} bootstrap is unstable")
        participant_cvs = [cv_percent(group) for group in groups]
        output[metric] = {
            "icc11": round(estimate, 4),
            "icc11Ci95": [round(percentile(sampled, 0.025), 4), round(percentile(sampled, 0.975), 4)],
            "medianWithinParticipantCvPercent": round(statistics.median(participant_cvs), 3),
        }
    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "mode": "cohort",
        "participantCountBand": "20 to 49" if len(participants) < 50 else "50 or more",
        "recordingsPerParticipant": 7,
        "iccModel": "ICC(1,1) balanced one-way random-effects absolute agreement",
        "metrics": output,
        "warnings": [
            "Generated methods example; not a Brainstem reference.",
            "Repeatability describes measurement consistency, not health or clinical status.",
        ],
    }


def analyze(value: object) -> dict:
    mode, participants = validate(value)
    return personal_result(participants[0]) if mode == "personal" else cohort_result(participants)
