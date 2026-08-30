#!/usr/bin/env python3
"""Independent generated-data example for participant-level sleep reliability."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics


SCHEMA = "paper-to-insight.sleep-measure-reliability/generated-v1"
MINIMUM_PARTICIPANTS = 20
NIGHTS = 7
BOOTSTRAPS = 2_000


class InputError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InputError(message)


def validate(value):
    require(isinstance(value, dict), "input must be an object")
    require(set(value) == {"schema", "metric", "participantNights"}, "input fields differ")
    require(value["schema"] == SCHEMA, "unsupported schema")
    require(value["metric"] == "sleepDurationHours", "unsupported metric")
    groups = value["participantNights"]
    require(isinstance(groups, list) and len(groups) <= 1_000, "participant groups are invalid")
    for group in groups:
        require(isinstance(group, list) and len(group) == NIGHTS, "each participant needs seven nights")
        require(
            all(
                isinstance(item, (int, float))
                and not isinstance(item, bool)
                and math.isfinite(item)
                and 0 < item <= 24
                for item in group
            ),
            "nightly values are invalid",
        )
    return value


def icc_one_way(groups):
    participant_means = [statistics.fmean(group) for group in groups]
    grand = statistics.fmean(participant_means)
    between = NIGHTS * sum((mean - grand) ** 2 for mean in participant_means) / (len(groups) - 1)
    within = sum(
        sum((value - participant_means[index]) ** 2 for value in group)
        for index, group in enumerate(groups)
    ) / (len(groups) * (NIGHTS - 1))
    denominator = between + (NIGHTS - 1) * within
    if denominator <= 0 or math.isclose(denominator, 0, abs_tol=1e-12):
        return None
    return max(-1.0, min(1.0, (between - within) / denominator))


def reliability(single_night, nights):
    denominator = 1 + (nights - 1) * single_night
    return None if denominator <= 0 else nights * single_night / denominator


def percentile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return values[lower]
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def analyze(value):
    groups = sorted(validate(value)["participantNights"])
    if len(groups) < MINIMUM_PARTICIPANTS:
        return {
            "schema": "paper-to-insight.sleep-measure-reliability/result-v1",
            "status": "insufficient_data",
            "reason": "privacy_floor",
            "metrics": [],
            "warnings": ["At least 20 participants are required."],
        }
    estimate = icc_one_way(groups)
    if estimate is None:
        return {
            "schema": "paper-to-insight.sleep-measure-reliability/result-v1",
            "status": "insufficient_data",
            "reason": "model_uncertainty",
            "metrics": [],
            "warnings": ["The generated measurements do not support a reliability estimate."],
        }
    seed_bytes = json.dumps(groups, separators=(",", ":")).encode()
    rng = random.Random(int(hashlib.sha256(seed_bytes).hexdigest()[:16], 16))
    bootstraps = []
    for _ in range(BOOTSTRAPS):
        sample = [groups[rng.randrange(len(groups))] for _ in groups]
        sample_estimate = icc_one_way(sample)
        if sample_estimate is not None:
            bootstraps.append(sample_estimate)
    require(len(bootstraps) >= 1_600, "too few valid bootstrap estimates")
    curve = []
    minimum = None
    for night_count in range(1, NIGHTS + 1):
        distribution = [
            transformed
            for item in bootstraps
            if (transformed := reliability(item, night_count)) is not None
        ]
        require(len(distribution) >= 1_600, "too few valid transformed estimates")
        point = reliability(estimate, night_count)
        low, high = percentile(distribution, 0.025), percentile(distribution, 0.975)
        curve.append({
            "nights": night_count,
            "estimate": round(point, 4),
            "ci95": [round(low, 4), round(high, 4)],
        })
        if minimum is None and low >= 0.80:
            minimum = night_count
    return {
        "schema": "paper-to-insight.sleep-measure-reliability/result-v1",
        "status": "complete",
        "participantCountBand": "20 to 49" if len(groups) < 50 else "50 or more",
        "metric": "sleepDurationHours",
        "iccModel": "ICC(1,1) balanced one-way random-effects absolute agreement",
        "reliabilityByNights": curve,
        "minimumNightsForLowerCi80": minimum if minimum is not None else "not_established_within_7",
        "warnings": [
            "Generated methods example only; not a Brainstem reference.",
            "Reliability describes repeatability, not health, risk, or diagnosis.",
        ],
    }

