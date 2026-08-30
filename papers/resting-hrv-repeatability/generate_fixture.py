#!/usr/bin/env python3
"""Generate the deterministic CC0 participant-grouped methods fixture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OFFSETS = (-1.0, 0.4, -0.3, 0.8, -0.7, 0.5, 0.0)
BASES = {
    "heartRateBpm": 58.0,
    "sdnnMs": 42.0,
    "rmssdMs": 38.0,
    "sd1Ms": 27.0,
    "sd2Ms": 53.0,
}
SCALES = {
    "heartRateBpm": 1.0,
    "sdnnMs": 1.8,
    "rmssdMs": 2.1,
    "sd1Ms": 1.5,
    "sd2Ms": 2.3,
}


def generated() -> dict:
    participants = []
    for participant_index in range(20):
        recordings = []
        for recording_index, offset in enumerate(OFFSETS, start=1):
            recording = {"recordingIndex": recording_index}
            for metric, base in BASES.items():
                between_person = participant_index * SCALES[metric] * 0.35
                within_person = offset * SCALES[metric]
                recording[metric] = round(base + between_person + within_person, 3)
            recordings.append(recording)
        participants.append({
            "subjectId": hashlib.sha256(f"generated-{participant_index}".encode()).hexdigest(),
            "recordings": recordings,
        })
    return {
        "schema": "paper-to-insight.resting-hrv-repeatability/generated-v1",
        "mode": "cohort",
        "participants": participants,
    }


if __name__ == "__main__":
    (ROOT / "public-data.json").write_text(json.dumps(generated(), indent=2, sort_keys=True) + "\n")
