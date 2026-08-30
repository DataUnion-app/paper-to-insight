#!/usr/bin/env python3
"""Generated descriptive guided-breathing response method."""

from __future__ import annotations

import math
import statistics


SCHEMA = "paper-to-insight.guided-breathing-response/generated-v1"
RESULT_SCHEMA = "paper-to-insight.guided-breathing-response/result-v1"
MINIMUM_COHORT = 20
MAX_PARTICIPANTS = 1000
MAX_RECORDINGS = 7
MIN_DURATION_MS = 120_000
MAX_DURATION_MS = 1_800_000
MIN_RR_MS = 300
MAX_RR_MS = 2000
PROTOCOL_FIELDS = {"rateCPM", "ih", "ip", "eh", "ep"}
METRICS = ("meanHeartRateBpm", "rmssdMs", "sd1Ms")


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


def protocol_tuple(value: object, where: str) -> tuple[float, ...]:
    protocol = exact(value, PROTOCOL_FIELDS, where)
    values = tuple(protocol[key] for key in ("rateCPM", "ih", "ip", "eh", "ep"))
    require(
        all(
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and math.isfinite(item)
            for item in values
        ),
        f"{where} must be finite",
    )
    rate, inhale, inhale_pause, exhale, exhale_pause = map(float, values)
    require(2 <= rate <= 30, f"{where} rate is invalid")
    require(inhale > 0 and exhale > 0, f"{where} active phases are invalid")
    require(inhale_pause >= 0 and exhale_pause >= 0, f"{where} pauses are invalid")
    require(
        abs((inhale + inhale_pause + exhale + exhale_pause) - (60 / rate)) <= 0.1,
        f"{where} phases do not match rate",
    )
    return rate, inhale, inhale_pause, exhale, exhale_pause


def session_metrics(intervals: list[float]) -> dict[str, float]:
    duration = sum(intervals)
    require(MIN_DURATION_MS <= duration <= MAX_DURATION_MS, "session duration is invalid")
    require(len(intervals) >= 3, "R-R coverage is insufficient")
    differences = [right - left for left, right in zip(intervals, intervals[1:])]
    rmssd = math.sqrt(statistics.fmean(item * item for item in differences))
    sd1 = math.sqrt(statistics.pvariance(differences) / 2)
    return {
        "meanHeartRateBpm": round(60_000 / statistics.fmean(intervals), 3),
        "rmssdMs": round(rmssd, 3),
        "sd1Ms": round(sd1, 3),
    }


def validate(value: object) -> tuple[str, dict, list[dict]]:
    root = exact(value, {"schema", "mode", "protocol", "participants"}, "input")
    require(root["schema"] == SCHEMA, "unsupported schema")
    mode = root["mode"]
    require(mode in {"personal", "cohort"}, "unsupported mode")
    expected_protocol = protocol_tuple(root["protocol"], "input protocol")
    participants = root["participants"]
    require(
        isinstance(participants, list) and 1 <= len(participants) <= MAX_PARTICIPANTS,
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
                {"recordingIndex", "recordType", "protocol", "rrIntervalsMs"},
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
            require(recording["recordType"] == "exercise", "record is not an exercise")
            require(
                protocol_tuple(recording["protocol"], "recording protocol") == expected_protocol,
                "recording protocol differs",
            )
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
    return mode, dict(zip(("rateCPM", "ih", "ip", "eh", "ep"), expected_protocol)), sorted(
        checked, key=lambda item: item["subjectId"]
    )


def participant_summary(participant: dict) -> dict:
    recordings = participant["metrics"]
    output = {}
    for metric in METRICS:
        values = [item[metric] for item in recordings]
        output[metric] = {
            "median": round(statistics.median(values), 3),
            "minimum": round(min(values), 3),
            "maximum": round(max(values), 3),
            "changeLatestMinusEarliest": round(values[-1] - values[0], 3)
            if len(values) > 1
            else None,
        }
    return output


def personal_result(protocol: dict, participant: dict) -> dict:
    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "mode": "personal",
        "protocol": protocol,
        "recordingCount": len(participant["metrics"]),
        "metrics": participant_summary(participant),
        "warnings": [
            "Descriptive response during one matched guided-breathing protocol only.",
            "This does not measure breathing adherence or diagnose, treat, or define an optimal rate.",
        ],
    }


def cohort_result(protocol: dict, participants: list[dict]) -> dict:
    if len(participants) < MINIMUM_COHORT:
        return {
            "schema": RESULT_SCHEMA,
            "status": "insufficient_data",
            "mode": "cohort",
            "protocol": protocol,
            "reason": "privacy_floor",
            "metrics": {},
            "warnings": ["At least 20 participants are required."],
        }
    summaries = [participant_summary(participant) for participant in participants]
    output = {}
    for metric in METRICS:
        values = [item[metric]["median"] for item in summaries]
        changes = [
            item[metric]["changeLatestMinusEarliest"]
            for item in summaries
            if item[metric]["changeLatestMinusEarliest"] is not None
        ]
        output[metric] = {
            "p25": round(percentile(values, 0.25), 3),
            "median": round(statistics.median(values), 3),
            "p75": round(percentile(values, 0.75), 3),
            "changeLatestMinusEarliest": {
                "p25": round(percentile(changes, 0.25), 3),
                "median": round(statistics.median(changes), 3),
                "p75": round(percentile(changes, 0.75), 3),
            }
            if len(changes) >= MINIMUM_COHORT
            else None,
        }
    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "mode": "cohort",
        "protocol": protocol,
        "participantCountBand": "20 to 49" if len(participants) < 50 else "50 or more",
        "metrics": output,
        "warnings": [
            "Generated methods example; not a Brainstem reference range.",
            "Each participant contributes one median and one matched-session change.",
        ],
    }


def analyze(value: object) -> dict:
    mode, protocol, participants = validate(value)
    return (
        personal_result(protocol, participants[0])
        if mode == "personal"
        else cohort_result(protocol, participants)
    )
