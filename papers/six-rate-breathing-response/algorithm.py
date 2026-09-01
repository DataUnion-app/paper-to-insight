#!/usr/bin/env python3
"""Generated, descriptive six-rate paced-breathing response curve."""

from __future__ import annotations

import math
import statistics


SCHEMA = "paper-to-insight.six-rate-breathing-response/generated-v1"
RESULT_SCHEMA = "paper-to-insight.six-rate-breathing-response/result-v1"
RATES = (7.0, 6.5, 6.0, 5.5, 5.0, 4.5)
PROTOCOL = {
    "version": "brainstem.resonance-assessment/7-to-4-5-step-0-5/v1",
    "ratesCpm": list(RATES),
    "order": "descending",
    "perRateSeconds": 180,
    "analysisWindowSeconds": 120,
    "adherenceMeasured": False,
}
MINIMUM_COHORT = 20
MAX_PARTICIPANTS = 1000
MAX_SESSIONS = 7
MIN_DURATION_MS = 118_000
MAX_DURATION_MS = 122_000
MIN_RR_MS = 300
MAX_RR_MS = 2000
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


def validate_protocol(value: object) -> dict:
    protocol = exact(value, set(PROTOCOL), "protocol")
    require(protocol["version"] == PROTOCOL["version"], "protocol version differs")
    rates = protocol["ratesCpm"]
    require(
        isinstance(rates, list)
        and len(rates) == len(RATES)
        and all(
            isinstance(rate, (int, float))
            and not isinstance(rate, bool)
            and math.isfinite(rate)
            for rate in rates
        )
        and tuple(map(float, rates)) == RATES,
        "rate series differs",
    )
    require(protocol["order"] == "descending", "trial order differs")
    require(protocol["perRateSeconds"] == 180, "per-rate duration differs")
    require(protocol["analysisWindowSeconds"] == 120, "analysis window differs")
    require(protocol["adherenceMeasured"] is False, "adherence cannot be inferred")
    return {**PROTOCOL, "ratesCpm": list(RATES)}


def trial_metrics(intervals: list[float]) -> dict[str, float]:
    duration = sum(intervals)
    require(MIN_DURATION_MS <= duration <= MAX_DURATION_MS, "analysis window is invalid")
    require(len(intervals) >= 60, "R-R coverage is insufficient")
    differences = [right - left for left, right in zip(intervals, intervals[1:])]
    return {
        "meanHeartRateBpm": round(60_000 / statistics.fmean(intervals), 3),
        "rmssdMs": round(
            math.sqrt(statistics.fmean(value * value for value in differences)), 3
        ),
        "sd1Ms": round(math.sqrt(statistics.pvariance(differences) / 2), 3),
    }


def validate(value: object) -> tuple[str, dict, list[dict]]:
    root = exact(value, {"schema", "mode", "protocol", "participants"}, "input")
    require(root["schema"] == SCHEMA, "unsupported schema")
    mode = root["mode"]
    require(mode in {"personal", "cohort"}, "unsupported mode")
    protocol = validate_protocol(root["protocol"])
    participants = root["participants"]
    require(
        isinstance(participants, list) and 1 <= len(participants) <= MAX_PARTICIPANTS,
        "participant count is invalid",
    )
    require(mode != "personal" or len(participants) == 1, "personal mode needs one participant")
    seen_subjects = set()
    checked = []
    for participant_index, item in enumerate(participants):
        participant = exact(item, {"subjectId", "sessions"}, f"participant {participant_index}")
        subject_id = participant["subjectId"]
        require(
            isinstance(subject_id, str)
            and len(subject_id) == 64
            and all(char in "0123456789abcdef" for char in subject_id)
            and subject_id not in seen_subjects,
            "subjectId is invalid or duplicated",
        )
        seen_subjects.add(subject_id)
        sessions = participant["sessions"]
        require(
            isinstance(sessions, list) and 1 <= len(sessions) <= MAX_SESSIONS,
            "session count is invalid",
        )
        seen_indices = set()
        checked_sessions = []
        for session_position, item in enumerate(sessions):
            session = exact(
                item,
                {"sessionIndex", "trials"},
                f"participant {participant_index} session {session_position}",
            )
            session_index = session["sessionIndex"]
            require(
                isinstance(session_index, int)
                and not isinstance(session_index, bool)
                and 1 <= session_index <= MAX_SESSIONS
                and session_index not in seen_indices,
                "sessionIndex is invalid or duplicated",
            )
            seen_indices.add(session_index)
            trials = session["trials"]
            require(isinstance(trials, list) and len(trials) == len(RATES), "six trials are required")
            trial_rates = [trial.get("rateCpm") if isinstance(trial, dict) else None for trial in trials]
            require(
                all(
                    isinstance(rate, (int, float))
                    and not isinstance(rate, bool)
                    and math.isfinite(rate)
                    for rate in trial_rates
                )
                and tuple(map(float, trial_rates)) == RATES,
                "trial rate order differs",
            )
            curve = []
            for trial_position, (trial, expected_rate) in enumerate(zip(trials, RATES)):
                trial = exact(
                    trial,
                    {"rateCpm", "rrIntervalsMs"},
                    f"participant {participant_index} session {session_position} trial {trial_position}",
                )
                rate = trial["rateCpm"]
                require(
                    isinstance(rate, (int, float))
                    and not isinstance(rate, bool)
                    and math.isfinite(rate)
                    and float(rate) == expected_rate,
                    "trial rate differs",
                )
                intervals = trial["rrIntervalsMs"]
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
                curve.append({"rateCpm": expected_rate, **trial_metrics(list(map(float, intervals)))})
            checked_sessions.append({"sessionIndex": session_index, "curve": curve})
        checked.append(
            {
                "subjectId": subject_id,
                "sessions": sorted(checked_sessions, key=lambda session: session["sessionIndex"]),
            }
        )
    return mode, protocol, sorted(checked, key=lambda participant: participant["subjectId"])


def largest_rates(curve: list[dict], metric: str = "rmssdMs") -> list[float]:
    largest = max(point[metric] for point in curve)
    return [point["rateCpm"] for point in curve if point[metric] == largest]


def participant_curve(participant: dict) -> list[dict]:
    output = []
    for position, rate in enumerate(RATES):
        point = {"rateCpm": rate}
        for metric in METRICS:
            point[metric] = round(
                statistics.median(
                    session["curve"][position][metric] for session in participant["sessions"]
                ),
                3,
            )
        output.append(point)
    return output


def personal_result(protocol: dict, participant: dict) -> dict:
    curve = participant_curve(participant)
    sessions = [
        {
            **session,
            "largestObservedRmssdRatesCpm": largest_rates(session["curve"]),
        }
        for session in participant["sessions"]
    ]
    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "mode": "personal",
        "protocol": protocol,
        "sessionCount": len(sessions),
        "sessions": sessions,
        "medianCurve": curve,
        "largestObservedMedianRmssdRatesCpm": largest_rates(curve),
        "warnings": [
            "Descriptive response across one exact paced-breathing sequence only.",
            "Largest observed RMSSD ties are preserved; no optimal or therapeutic rate is inferred.",
            "Pacer assignment is known, but breathing adherence and respiration are not measured.",
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
            "curve": [],
            "warnings": ["At least 20 participants are required."],
        }
    participant_curves = [participant_curve(participant) for participant in participants]
    curve = []
    for position, rate in enumerate(RATES):
        point = {"rateCpm": rate}
        for metric in METRICS:
            values = [participant[position][metric] for participant in participant_curves]
            point[metric] = {
                "p25": round(percentile(values, 0.25), 3),
                "median": round(statistics.median(values), 3),
                "p75": round(percentile(values, 0.75), 3),
            }
        curve.append(point)
    medians = [{"rateCpm": point["rateCpm"], "rmssdMs": point["rmssdMs"]["median"]} for point in curve]
    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "mode": "cohort",
        "protocol": protocol,
        "participantCountBand": "20 to 49" if len(participants) < 50 else "50 or more",
        "curve": curve,
        "largestObservedCohortMedianRmssdRatesCpm": largest_rates(medians),
        "warnings": [
            "Generated methods example; not a Brainstem reference range.",
            "Each participant contributes one median curve regardless of session count.",
            "No optimal or therapeutic rate, adherence, respiration, diagnosis, or treatment effect is inferred.",
        ],
    }


def analyze(value: object) -> dict:
    mode, protocol, participants = validate(value)
    return (
        personal_result(protocol, participants[0])
        if mode == "personal"
        else cohort_result(protocol, participants)
    )
