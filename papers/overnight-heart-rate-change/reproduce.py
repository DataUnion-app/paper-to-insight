#!/usr/bin/env python3
"""Run and verify the pinned public overnight-heart-rate fixture."""

from __future__ import annotations

import json
from pathlib import Path

from algorithm import analyze


ROOT = Path(__file__).resolve().parent


def main() -> None:
    source = json.loads((ROOT / "public-data.json").read_text())
    expected = json.loads((ROOT / "expected-public.json").read_text())
    result = analyze(source)
    if result != expected:
        raise SystemExit("public reproduction differs from expected-public.json")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
