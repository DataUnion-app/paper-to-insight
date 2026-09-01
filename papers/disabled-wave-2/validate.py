#!/usr/bin/env python3
"""Validate disabled Wave 2 evidence packages and their local bindings."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent / "packages.json"
EXPECTED_IDS = {
    "disease-linked-association", "standardised-exercise-recovery",
    "sleep-movement-regularity", "six-rate-resonance",
    "apple-health-local-composites", "ecg-arrhythmia", "sleep-apnea",
}
EXECUTION_KEYS = {
    "algorithmPolicy", "apiRoute", "participantStudy", "personalCard",
    "payment", "notification", "schedule",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class DisabledPackageError(ValueError):
    pass


def exact(value, keys, where):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise DisabledPackageError(f"{where} keys differ")
    return value


def strings(value, where, minimum=1):
    if not isinstance(value, list) or len(value) < minimum:
        raise DisabledPackageError(f"{where} is empty")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise DisabledPackageError(f"{where} contains an invalid value")
    if len(value) != len(set(value)):
        raise DisabledPackageError(f"{where} contains duplicates")
    return value


def text(value, where):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise DisabledPackageError(f"{where} is invalid")
    return value


def validate(value, verify_files=True):
    root = exact(value, {"schema", "packages"}, "$")
    if root["schema"] != "paper-to-insight.disabled-packages/v1":
        raise DisabledPackageError("unsupported schema")
    packages = root["packages"]
    if not isinstance(packages, list) or {item.get("packageId") for item in packages} != EXPECTED_IDS:
        raise DisabledPackageError("disabled package inventory differs")
    for package in packages:
        exact(
            package,
            {
                "packageId", "status", "purpose", "primarySources",
                "evidenceBindings", "missingDelta", "proposedStudy",
                "claimBoundary", "cost", "promotionGate", "blockers", "execution",
            },
            package.get("packageId", "package"),
        )
        if package["status"] != "disabled":
            raise DisabledPackageError("package must remain disabled")
        text(package["purpose"], "purpose")
        strings(package["missingDelta"], "missingDelta", 2)
        strings(package["blockers"], "blockers", 2)
        strings(package["promotionGate"], "promotionGate", 3)
        study = exact(
            package["proposedStudy"],
            {"design", "participants", "reference", "split", "retention"},
            "proposedStudy",
        )
        for key, value in study.items():
            text(value, f"proposedStudy.{key}")
        boundary = exact(package["claimBoundary"], {"allowedNow", "prohibited"}, "claimBoundary")
        strings(boundary["allowedNow"], "allowedNow", 0)
        strings(boundary["prohibited"], "prohibited")
        cost = exact(package["cost"], {"tier", "mainCosts"}, "cost")
        if cost["tier"] not in {"S", "S-M", "M", "M-L", "L"}:
            raise DisabledPackageError("invalid cost tier")
        strings(cost["mainCosts"], "mainCosts")
        execution = exact(package["execution"], EXECUTION_KEYS, "execution")
        if any(value is not False for value in execution.values()):
            raise DisabledPackageError("disabled package cannot register runtime behavior")
        sources = package["primarySources"]
        if not isinstance(sources, list) or not sources:
            raise DisabledPackageError("primary sources are required")
        for source in sources:
            exact(source, {"name", "url", "identifier", "license", "use"}, "source")
            for key, value in source.items():
                text(value, f"source.{key}")
            parsed = urlparse(source["url"])
            if parsed.scheme != "https" or not parsed.hostname or source["license"].lower() in {"unknown", "none"}:
                raise DisabledPackageError("source URL or licence is invalid")
        bindings = package["evidenceBindings"]
        if not isinstance(bindings, list) or not bindings:
            raise DisabledPackageError("evidence binding is required")
        for binding in bindings:
            exact(binding, {"path", "sha256"}, "binding")
            if not SHA256.fullmatch(binding["sha256"]):
                raise DisabledPackageError("binding digest is invalid")
            path = (ROOT / binding["path"]).resolve()
            if ROOT not in path.parents or not path.is_file():
                raise DisabledPackageError("binding path is invalid")
            if verify_files and hashlib.sha256(path.read_bytes()).hexdigest() != binding["sha256"]:
                raise DisabledPackageError("evidence binding is stale")
    return root


def main():
    value = json.loads(PACKAGE.read_text())
    validate(value)
    print(json.dumps({"schema": root_schema(value), "status": "passed", "packages": len(value["packages"])}))


def root_schema(value):
    return value.get("schema") if isinstance(value, dict) else None


if __name__ == "__main__":
    main()
