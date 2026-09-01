#!/usr/bin/env python3
"""Verify the deterministic generated NN fixture."""

from __future__ import annotations

import json
from pathlib import Path

from algorithm import analyze


ROOT = Path(__file__).resolve().parent


def main() -> None:
    source = json.loads((ROOT / "generated-fixture.json").read_text())
    expected = json.loads((ROOT / "expected-generated.json").read_text())
    if analyze(source) != expected:
        raise SystemExit("generated heart-rate fragmentation result differs")
    print(json.dumps(expected, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
