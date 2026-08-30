#!/usr/bin/env python3
"""Generate the deterministic posture methods fixture and expected result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from algorithm import SCHEMA, analyze


ROOT = Path(__file__).resolve().parent


def phase(duration_ms: int, bpm: float) -> list[int]:
    count = round(duration_ms / (60_000 / bpm))
    interval, remainder = divmod(duration_ms, count)
    return [interval + 1] * remainder + [interval] * (count - remainder)


def recording(resting_bpm: float, response_bpm: float, index: int) -> dict:
    intervals = (
        phase(120_000, resting_bpm + 2)
        + phase(120_000, resting_bpm)
        + phase(60_000, resting_bpm + response_bpm)
    )
    return {"recordingIndex": index, "rrIntervalsMs": intervals}


def fixture() -> dict:
    participants = []
    for index in range(20):
        resting = 56 + index * 0.6
        response = 10 + index % 6
        participants.append({
            "subjectId": hashlib.sha256(f"generated-subject-{index}".encode()).hexdigest(),
            "recordings": [
                recording(resting, response, 1),
                recording(resting + 0.5, response + 0.5, 2),
            ],
        })
    return {"schema": SCHEMA, "mode": "cohort", "participants": participants}


def main() -> None:
    value = fixture()
    (ROOT / "public-data.json").write_text(json.dumps(value, indent=2) + "\n")
    (ROOT / "expected-public.json").write_text(json.dumps(analyze(value), indent=2) + "\n")


if __name__ == "__main__":
    main()

