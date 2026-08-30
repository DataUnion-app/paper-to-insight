#!/usr/bin/env python3
"""Public NightSignal reproduction plus a non-clinical Brainstem translation."""

from __future__ import annotations

import math
import statistics


SCHEMA = "paper-to-insight.overnight-heart-rate-change/public-v1"
RESULT_SCHEMA = "paper-to-insight.overnight-heart-rate-change/result-v1"
MIN_NIGHTS = 9
MAX_NIGHTS = 365
MOVEMENT_INPUT_SCHEMA = "paper-to-insight.overnight-heart-rate-movement/generated-v1"
MOVEMENT_SCHEMA = "brainstem.normalized-movement/v1"
MOVEMENT_RESULT_SCHEMA = "paper-to-insight.overnight-heart-rate-movement/result-v1"
MOVEMENT_THRESHOLD_MILLIG = 100.0
MIN_MOVEMENT_COVERAGE = 0.8
MAX_SECONDS = 43_200


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


def movement_descriptors(value: object) -> dict:
    require(isinstance(value, dict), "movement input must be an object")
    require(
        set(value) == {"schema", "movement", "heartRateBpmBySecond"},
        "movement input fields differ",
    )
    require(value["schema"] == MOVEMENT_INPUT_SCHEMA, "unsupported movement input")
    movement = value["movement"]
    require(isinstance(movement, dict), "movement must be an object")
    require(
        set(movement) == {"schema", "coverageFraction", "samples"},
        "movement fields differ",
    )
    require(movement["schema"] == MOVEMENT_SCHEMA, "unsupported movement schema")
    coverage = movement["coverageFraction"]
    require(
        isinstance(coverage, (int, float))
        and not isinstance(coverage, bool)
        and math.isfinite(coverage)
        and 0 <= coverage <= 1,
        "movement coverage is invalid",
    )
    heart_rates = value["heartRateBpmBySecond"]
    require(
        isinstance(heart_rates, list)
        and 2 <= len(heart_rates) <= MAX_SECONDS
        and all(
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and math.isfinite(item)
            and 20 <= item <= 250
            for item in heart_rates
        ),
        "heart-rate series is invalid",
    )
    samples = movement["samples"]
    require(isinstance(samples, list) and 2 <= len(samples) <= MAX_SECONDS, "samples are invalid")
    checked = []
    previous = -1
    for sample in samples:
        require(
            isinstance(sample, dict)
            and set(sample) == {"offsetSeconds", "activityMilliG"},
            "movement sample fields differ",
        )
        offset = sample["offsetSeconds"]
        activity = sample["activityMilliG"]
        require(
            isinstance(offset, int)
            and not isinstance(offset, bool)
            and previous < offset < len(heart_rates),
            "movement offset is invalid",
        )
        require(
            isinstance(activity, (int, float))
            and not isinstance(activity, bool)
            and math.isfinite(activity)
            and 0 <= activity <= 16_000,
            "movement activity is invalid",
        )
        checked.append((offset, float(activity), float(heart_rates[offset])))
        previous = offset

    if coverage < MIN_MOVEMENT_COVERAGE:
        return {
            "schema": MOVEMENT_RESULT_SCHEMA,
            "status": "insufficient_data",
            "abstentionReason": "insufficient_coverage",
            "descriptors": None,
        }

    event_count = 0
    previous_active_offset = None
    quiet_rates = []
    movement_rates = []
    for offset, activity, rate in checked:
        active = activity > MOVEMENT_THRESHOLD_MILLIG
        if active:
            if previous_active_offset != offset - 1:
                event_count += 1
            previous_active_offset = offset
            movement_rates.append(rate)
        else:
            previous_active_offset = None
            quiet_rates.append(rate)

    duration_hours = len(heart_rates) / 3600
    return {
        "schema": MOVEMENT_RESULT_SCHEMA,
        "status": "complete",
        "abstentionReason": None,
        "descriptors": {
            "movementCoverageFraction": round(float(coverage), 6),
            "movementEventCount": event_count,
            "movementEventRatePerHour": round(event_count / duration_hours, 6),
            "quietWindowProportion": round(len(quiet_rates) / len(checked), 6),
            "quietMeanHeartRateBpm": (
                round(statistics.mean(quiet_rates), 6) if quiet_rates else None
            ),
            "movementMeanHeartRateBpm": (
                round(statistics.mean(movement_rates), 6) if movement_rates else None
            ),
        },
    }
