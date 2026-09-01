#!/usr/bin/env python3
"""Checksum-pinned audit of two public resonance-assessment sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MAX_BYTES = 5_000_000
ASSETS = {"practical-guide-full-text", "brief-exercise-full-text"}


class AuditError(ValueError):
    pass


def load_and_download() -> dict[str, bytes]:
    value = json.loads((ROOT / "public-sources.json").read_text(encoding="utf-8"))
    if value.get("schema") != "paper-to-insight.public-sources/v1" or set(value.get("assets", {})) != ASSETS:
        raise AuditError("public source set differs")
    output = {}
    for name, item in value["assets"].items():
        request = Request(item["url"], headers={"User-Agent": "paper-to-insight-source-audit/1"})
        with urlopen(request, timeout=30) as response:
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise AuditError(f"{name} size or checksum differs")
        output[name] = data
    return output


def audit(assets: dict[str, bytes]) -> dict:
    if set(assets) != ASSETS:
        raise AuditError("source evidence differs")
    guide = assets["practical-guide-full-text"].decode()
    brief = assets["brief-exercise-full-text"].decode()
    guide_markers = (
        "10.3389/fnins.2020.570400",
        "Creative Commons Attribution License (CC BY)",
        "6.5 to 4.5 breaths per min",
        "2-min intervals from 6.5 to 4.5 bpm",
    )
    brief_markers = (
        "10.1007/s10484-025-09687-0",
        "Creative Commons Attribution 4.0 International License",
        "Initially, participants were asked to breath at a rate of 7.0",
        "decreased by increments of 0.5",
        "respiration belt and three-lead ECG sensors",
        "visually inspected for artifacts",
    )
    if not all(marker in guide for marker in guide_markers) or not all(
        marker in brief for marker in brief_markers
    ):
        raise AuditError("paper evidence differs")
    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.six-rate-breathing-response",
        "paperLicenses": ["CC-BY-4.0", "CC-BY-4.0"],
        "paperFullTextsPinned": True,
        "paperRelationship": "protocol_and_limitation_context",
        "promotionStatus": "hold",
        "eligibleForProtectedRuntimeReview": False,
        "resolvedDelta": "generated_response_curve_and_all_ties_rule",
        "blockedRuntimeBy": [
            "no versioned full-curve mobile upload",
            "no measured breathing adherence or respiration",
            "no repeat-session Brainstem evaluation",
        ],
        "prohibitedInterpretations": [
            "optimal_or_therapeutic_rate",
            "treatment_effect",
            "autonomic_diagnosis",
        ],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv[1:])
    if not args.verify:
        parser.error("--verify is required")
    try:
        result = audit(load_and_download())
        expected = json.loads((ROOT / "expected-audit.json").read_text(encoding="utf-8"))
        if result != expected:
            raise AuditError("audit result differs from expected-audit.json")
    except (AuditError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
