#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from algorithm import analyze


HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = analyze(json.loads((HERE / "public-data.json").read_text()))
    if args.verify:
        expected = json.loads((HERE / "expected-public.json").read_text())
        if result != expected:
            raise SystemExit("generated reproduction differs from expected-public.json")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

