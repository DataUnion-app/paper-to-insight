#!/usr/bin/env python3
"""Generate deterministic guided-breathing methods fixtures."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from algorithm import SCHEMA, analyze


ROOT = Path(__file__).resolve().parent
PROTOCOL = {"rateCPM": 6.0, "ih": 5.0, "ip": 0.0, "eh": 5.0, "ep": 0.0}


def recording(mean_rr: float, amplitude: float, index: int, protocol: dict = PROTOCOL) -> dict:
    intervals = []
    elapsed = 0.0
    while elapsed < 180_000:
        interval = round(mean_rr + amplitude * math.sin(len(intervals) * math.pi / 5))
        intervals.append(interval)
        elapsed += interval
    return {
        "recordingIndex": index,
        "recordType": "exercise",
        "protocol": protocol,
        "rrIntervalsMs": intervals,
    }


def fixture() -> dict:
    participants = []
    for index in range(20):
        participants.append({
            "subjectId": hashlib.sha256(f"generated-breathing-subject-{index}".encode()).hexdigest(),
            "recordings": [
                recording(880 + index * 3, 28 + index % 4, 1),
                recording(878 + index * 3, 30 + index % 4, 2),
            ],
        })
    return {"schema": SCHEMA, "mode": "cohort", "protocol": PROTOCOL, "participants": participants}


def main() -> None:
    value = fixture()
    (ROOT / "public-data.json").write_text(json.dumps(value, indent=2) + "\n")
    (ROOT / "expected-public.json").write_text(json.dumps(analyze(value), indent=2) + "\n")


if __name__ == "__main__":
    main()
