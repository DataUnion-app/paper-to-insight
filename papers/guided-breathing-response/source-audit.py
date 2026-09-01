#!/usr/bin/env python3
"""Checksum-pinned audit of the guided-breathing methods review."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MAX_BYTES = 5_000_000


class AuditError(ValueError):
    pass


def load_and_download() -> bytes:
    value = json.loads((ROOT / "public-sources.json").read_text(encoding="utf-8"))
    if value.get("schema") != "paper-to-insight.public-sources/v1" or set(value.get("assets", {})) != {"paper-full-text"}:
        raise AuditError("public source set differs")
    item = value["assets"]["paper-full-text"]
    request = Request(item["url"], headers={"User-Agent": "paper-to-insight-source-audit/1"})
    with urlopen(request, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise AuditError("paper size or checksum differs")
    return data


def audit(data: bytes) -> dict:
    text = data.decode()
    required = (
        "10.1007/s10484-023-09582-6",
        "Creative Commons Attribution 4.0 International License",
        "there is still a lack of a <italic>gold standard</italic>",
        "inhalation and exhalation rate",
        "monitoring whether participants/patients breathe at the correct ratio is crucial",
        "plan for artifact prevention and data analysis",
    )
    if not all(marker in text for marker in required):
        raise AuditError("paper evidence differs")
    return {
        "schema": "paper-to-insight.source-audit/v1",
        "candidate": "brainstem.guided-breathing-response",
        "paperLicense": "CC-BY-4.0",
        "paperFullTextPinned": True,
        "paperRelationship": "reporting_and_protocol_context",
        "promotionStatus": "promote",
        "eligibleForProtectedRuntimeReview": True,
        "promotionScope": "exact_protocol_descriptive_heart_rate_only",
        "unavailableSignals": ["measured_breathing_adherence", "respiratory_volume"],
        "prohibitedInterpretations": [
            "optimal_resonance_frequency",
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
