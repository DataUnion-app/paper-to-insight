#!/usr/bin/env python3
"""Verify the deterministic six-rate breathing fixture."""

import json
from pathlib import Path

from algorithm import analyze


ROOT = Path(__file__).resolve().parent


def main() -> None:
    source = json.loads((ROOT / "public-data.json").read_text())
    expected = json.loads((ROOT / "expected-public.json").read_text())
    if analyze(source) != expected:
        raise SystemExit("generated six-rate result differs from expected-public.json")
    print(json.dumps(expected, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
