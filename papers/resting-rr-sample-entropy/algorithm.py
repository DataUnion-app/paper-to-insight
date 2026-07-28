#!/usr/bin/env python3
"""Independent stdlib implementation of normalized sample entropy."""

from __future__ import annotations

import math
import statistics


EMBEDDING_DIMENSION = 2
TOLERANCE_SD = 0.2
MIN_INTERVALS = 240
MAX_INTERVALS = 900
MIN_RR_MS = 300
MAX_RR_MS = 2000


def sample_entropy(
    values: list[float],
    dimension: int = EMBEDDING_DIMENSION,
    tolerance: float = TOLERANCE_SD,
) -> dict[str, float | int] | None:
    """Match PhysioNet sampen 1.2 normalization and boundary semantics."""
    if (
        not isinstance(values, list)
        or not dimension + 2 <= len(values) <= 4096
        or dimension != 2
        or tolerance != 0.2
        or any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in values
        )
    ):
        return None

    mean = statistics.fmean(values)
    scale = math.sqrt(statistics.fmean((value - mean) ** 2 for value in values))
    if scale == 0:
        return None
    normalized = [(value - mean) / scale for value in values]

    maximum = dimension + 1
    runs = [0] * len(normalized)
    previous_runs = [0] * len(normalized)
    matches = [0] * maximum
    eligible_matches = [0] * maximum

    for left in range(len(normalized) - 1):
        remaining = len(normalized) - left - 1
        for offset in range(remaining):
            right = left + offset + 1
            if abs(normalized[right] - normalized[left]) < tolerance:
                runs[offset] = previous_runs[offset] + 1
                for length in range(min(maximum, runs[offset])):
                    matches[length] += 1
                    if right < len(normalized) - 1:
                        eligible_matches[length] += 1
            else:
                runs[offset] = 0
        previous_runs[:remaining] = runs[:remaining]

    template_matches = eligible_matches[dimension - 1]
    extended_matches = matches[dimension]
    if not template_matches or not extended_matches:
        return None
    return {
        "sampleEntropy": -math.log(extended_matches / template_matches),
        "templateMatches": template_matches,
        "extendedMatches": extended_matches,
        "intervalCount": len(values),
    }


def resting_rr_sample_entropy(values: list[float]) -> dict[str, float | int] | None:
    if (
        not isinstance(values, list)
        or not MIN_INTERVALS <= len(values) <= MAX_INTERVALS
        or any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or not MIN_RR_MS <= value <= MAX_RR_MS
            for value in values
        )
    ):
        return None
    return sample_entropy(values)
