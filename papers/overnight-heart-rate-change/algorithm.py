#!/usr/bin/env python3
"""Public NightSignal reproduction plus a non-clinical Brainstem translation."""

from __future__ import annotations

import math
import statistics


SCHEMA = "paper-to-insight.overnight-heart-rate-change/public-v1"
RESULT_SCHEMA = "paper-to-insight.overnight-heart-rate-change/result-v1"
MIN_NIGHTS = 9
MAX_NIGHTS = 365


class InputError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InputError(message)


def validate(value: object) -> list[float]:
    require(isinstance(value, dict), "input must be an object")
    require(set(value) == {"schema", "nightlyMeanBpm"}, "input fields differ")
    require(value["schema"] == SCHEMA, "unsupported schema")
    nights = value["nightlyMeanBpm"]
    require(
        isinstance(nights, list) and MIN_NIGHTS <= len(nights) <= MAX_NIGHTS,
        "night count is invalid",
    )
    require(
        all(
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and math.isfinite(item)
            and 30 <= item <= 180
            for item in nights
        ),
        "nightly mean is invalid",
    )
    return [float(item) for item in nights]


def analyze(value: object) -> dict:
    nights = validate(value)

    # The pinned source floors each nightly average and each inclusive cumulative
    # median before testing the published +3/+4 bpm two-night thresholds.
    source_nights = [int(item) for item in nights]
    source_baselines = [
        int(statistics.median(source_nights[: index + 1]))
        for index in range(len(source_nights))
    ]
    source_differences = [
        item - source_baselines[index]
        for index, item in enumerate(source_nights)
    ]
    threshold3 = [
        index + 1
        for index in range(1, len(source_differences))
        if source_differences[index - 1] >= 3 and source_differences[index] >= 3
    ]
    threshold4 = [
        index + 1
        for index in range(1, len(source_differences))
        if source_differences[index - 1] >= 4 and source_differences[index] >= 4
    ]

    # Brainstem keeps the comparison descriptive and prevents the compared
    # nights from moving their own baseline.
    baseline = statistics.median(nights[-9:-2])
    previous_difference = nights[-2] - baseline
    latest_difference = nights[-1] - baseline

    return {
        "schema": RESULT_SCHEMA,
        "status": "complete",
        "sourceReproduction": {
            "nightCount": len(nights),
            "finalInclusiveMedianBpm": source_baselines[-1],
            "threshold3TwoNightEventOrdinals": threshold3,
            "threshold4TwoNightEventOrdinals": threshold4,
        },
        "brainstemTranslation": {
            "baselineNightCount": 7,
            "comparisonNightCount": 2,
            "baselineMedianBpm": round(baseline, 3),
            "previousDifferenceBpm": round(previous_difference, 3),
            "latestDifferenceBpm": round(latest_difference, 3),
            "consecutiveIncreaseAtLeast3Bpm": (
                previous_difference >= 3 and latest_difference >= 3
            ),
            "consecutiveIncreaseAtLeast4Bpm": (
                previous_difference >= 4 and latest_difference >= 4
            ),
        },
        "warnings": [
            "Descriptive change from a personal baseline only.",
            "This does not detect infection, illness, disease, or health risk.",
            "The public wearable sample does not validate a Brainstem device.",
        ],
    }
