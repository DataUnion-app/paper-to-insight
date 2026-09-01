#!/usr/bin/env python3
"""Generated-only heart-rate fragmentation mechanics on pre-cleaned NN intervals."""

from __future__ import annotations

import math


SCHEMA = "paper-to-insight.heart-rate-fragmentation/generated-nn-v1"
RESULT_SCHEMA = "paper-to-insight.heart-rate-fragmentation/result-v1"
MIN_INTERVALS = 50
MAX_INTERVALS = 200_000
MIN_DURATION_MS = 30_000
MAX_DURATION_MS = 172_800_000
MIN_NN_MS = 300
MAX_NN_MS = 1_500


class InputError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InputError(message)


def analyze(value: object) -> dict:
    require(isinstance(value, dict), "input must be an object")
    require(
        set(value) == {"schema", "normalToNormalIntervalsMs"},
        "input fields differ",
    )
    require(value["schema"] == SCHEMA, "unsupported schema")
    intervals = value["normalToNormalIntervalsMs"]
    require(
        isinstance(intervals, list) and MIN_INTERVALS <= len(intervals) <= MAX_INTERVALS,
        "normal-to-normal interval count is invalid",
    )
    require(
        all(
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and math.isfinite(item)
            and MIN_NN_MS < item < MAX_NN_MS
            for item in intervals
        ),
        "normal-to-normal intervals must be finite milliseconds within source bounds",
    )
    values = [float(item) for item in intervals]
    duration = sum(values)
    require(MIN_DURATION_MS <= duration <= MAX_DURATION_MS, "recording duration is invalid")

    increments = [right - left for left, right in zip(values, values[1:])]
    inflections = [
        index + 1
        for index, (left, right) in enumerate(zip(increments, increments[1:]))
        if left * right <= 0 and left != right
    ]
    if len(inflections) < 2:
        return {
            "schema": RESULT_SCHEMA,
            "status": "insufficient_data",
            "reason": "insufficient_fragmentation_boundaries",
            "metrics": {},
            "warnings": ["At least two inflection points are required."],
        }

    short = long = unchanged = 0
    for left, right in zip(inflections, inflections[1:]):
        segment = increments[left:right]
        length = len(segment)
        if all(item == 0 for item in segment):
            unchanged += length
        elif length < 3:
            short += length
        else:
            long += length

    accelerating_or_decelerating = short + long
    eligible_increments = accelerating_or_decelerating + unchanged
    eligible_intervals = inflections[-1] - inflections[0] + 1
    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "input": {
            "intervalCount": len(values),
            "durationSeconds": round(duration / 1000, 3),
            "eligibleIntervalCount": eligible_intervals,
        },
        "metrics": {
            "pipPercent": round(100 * len(inflections) / eligible_intervals, 3),
            "pnnssPercent": round(100 * short / accelerating_or_decelerating, 3)
            if accelerating_or_decelerating
            else None,
            "pnnlsPercent": round(100 * long / eligible_increments, 3)
            if eligible_increments
            else None,
        },
        "warnings": [
            "Generated methods result on pre-cleaned normal-to-normal intervals only.",
            "No Brainstem detector R-R, health, age, disease, or risk interpretation is supported.",
        ],
    }
