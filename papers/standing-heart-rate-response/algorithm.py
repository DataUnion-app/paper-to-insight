#!/usr/bin/env python3
"""Generated descriptive heart-rate response to standing method."""

from __future__ import annotations

import math
import statistics


SCHEMA = "paper-to-insight.standing-heart-rate-response/generated-v1"
RESULT_SCHEMA = "paper-to-insight.standing-heart-rate-response/result-v1"
MINIMUM_COHORT = 20
MAX_PARTICIPANTS = 1000
MAX_RECORDINGS = 7
MIN_DURATION_MS = 295_000
MAX_DURATION_MS = 305_000
MIN_RR_MS = 300
MAX_RR_MS = 2000


class InputError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InputError(message)


def exact(value: object, keys: set[str], where: str) -> dict:
    require(isinstance(value, dict), f"{where} must be an object")
    require(set(value) == keys, f"{where} fields differ")
    return value


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def session_metrics(intervals: list[float]) -> dict[str, float]:
    total = sum(intervals)
    require(MIN_DURATION_MS <= total <= MAX_DURATION_MS, "session duration is invalid")
    elapsed = 0.0
    rest, stand = [], []
    for interval in intervals:
        midpoint_from_end = elapsed + interval / 2 - total
        if -180_000 <= midpoint_from_end < -60_000:
            rest.append(interval)
        elif -60_000 <= midpoint_from_end <= 0:
            stand.append(interval)
        elapsed += interval
    require(sum(rest) >= 110_000, "rest window coverage is insufficient")
    require(sum(stand) >= 55_000, "stand window coverage is insufficient")
    resting = 60_000 / statistics.fmean(rest)
    standing_p95 = percentile([60_000 / item for item in stand], 0.95)
    return {
        "restingHeartRateBpm": round(resting, 3),
        "standingP95HeartRateBpm": round(standing_p95, 3),
        "responseBpm": round(standing_p95 - resting, 3),
    }


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
    checked = []
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
        require(
            isinstance(recordings, list) and 1 <= len(recordings) <= MAX_RECORDINGS,
            "recording count is invalid",
        )
        seen_indices = set()
        metrics = []
        for recording_position, item in enumerate(recordings):
            recording = exact(
                item,
                {"recordingIndex", "rrIntervalsMs"},
                f"participant {participant_index} recording {recording_position}",
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
            intervals = recording["rrIntervalsMs"]
            require(isinstance(intervals, list) and intervals, "R-R intervals are required")
            require(
                all(
                    isinstance(interval, (int, float))
                    and not isinstance(interval, bool)
                    and math.isfinite(interval)
                    and MIN_RR_MS <= interval <= MAX_RR_MS
                    for interval in intervals
                ),
                "R-R interval is invalid",
            )
            metrics.append((index, session_metrics([float(interval) for interval in intervals])))
        checked.append({"subjectId": subject_id, "metrics": [item[1] for item in sorted(metrics)]})
    return mode, sorted(checked, key=lambda item: item["subjectId"])


def participant_summary(participant: dict) -> dict:
    recordings = participant["metrics"]
    output = {}
    for metric in ("restingHeartRateBpm", "standingP95HeartRateBpm", "responseBpm"):
        values = [item[metric] for item in recordings]
        output[metric] = {
            "median": round(statistics.median(values), 3),
            "minimum": round(min(values), 3),
            "maximum": round(max(values), 3),
        }
    return output


def personal_result(participant: dict) -> dict:
    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "mode": "personal",
        "recordingCount": len(participant["metrics"]),
        "metrics": participant_summary(participant),
        "warnings": [
            "Descriptive heart-rate response to standing only.",
            "This does not assess blood pressure, diagnose POTS or orthostatic hypotension, or define a normal range.",
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
    summaries = [participant_summary(participant) for participant in participants]
    output = {}
    for metric in ("restingHeartRateBpm", "standingP95HeartRateBpm", "responseBpm"):
        values = [item[metric]["median"] for item in summaries]
        output[metric] = {
            "p25": round(percentile(values, 0.25), 3),
            "median": round(statistics.median(values), 3),
            "p75": round(percentile(values, 0.75), 3),
        }
    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "mode": "cohort",
        "participantCountBand": "20 to 49" if len(participants) < 50 else "50 or more",
        "metrics": output,
        "warnings": [
            "Generated methods example; not a Brainstem reference range.",
            "Each participant contributes one median regardless of recording count.",
        ],
    }


def analyze(value: object) -> dict:
    mode, participants = validate(value)
    return personal_result(participants[0]) if mode == "personal" else cohort_result(participants)

