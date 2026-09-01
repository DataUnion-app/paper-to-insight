#!/usr/bin/env python3
"""Generate a deterministic six-rate breathing response fixture."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from algorithm import PROTOCOL, RATES, SCHEMA, analyze


ROOT = Path(__file__).resolve().parent


def trial(rate: float, participant: int, session: int) -> dict:
    mean_rr = 890 + participant * 2 + session
    amplitude = 24 + max(0, 45 - abs(rate - 6.0) * 22)
    intervals = []
    elapsed = 0
    while elapsed < 120_000:
        interval = round(mean_rr + amplitude * math.sin(len(intervals) * math.pi / 5))
        intervals.append(interval)
        elapsed += interval
    return {"rateCpm": rate, "rrIntervalsMs": intervals}


def session(participant: int, index: int) -> dict:
    return {
        "sessionIndex": index,
        "trials": [trial(rate, participant, index) for rate in RATES],
    }


def fixture() -> dict:
    participants = []
    for index in range(20):
        participants.append(
            {
                "subjectId": hashlib.sha256(f"generated-six-rate-subject-{index}".encode()).hexdigest(),
                "sessions": [session(index, 1), session(index, 2)],
            }
        )
    return {
        "schema": SCHEMA,
        "mode": "cohort",
        "protocol": PROTOCOL,
        "participants": participants,
    }


def main() -> None:
    value = fixture()
    (ROOT / "public-data.json").write_text(json.dumps(value, separators=(",", ":")) + "\n")
    (ROOT / "expected-public.json").write_text(json.dumps(analyze(value), indent=2) + "\n")


if __name__ == "__main__":
    main()
