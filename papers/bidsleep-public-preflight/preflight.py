#!/usr/bin/env python3
"""Validate the frozen BIDSleep preflight without downloading signal data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SUBJECT = re.compile(r"^generated-subject-[a-z]$")
NIGHT_FILES = {"hr.csv", "motion.csv", "labels.mat"}
UPSTREAM_HOSTS = {"physionet.org", "raw.githubusercontent.com"}


class PreflightError(ValueError):
    pass


def exact(value, keys, where):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise PreflightError(f"{where} keys differ")
    return value


def validate_preflight(value):
    root = exact(
        value,
        {
            "schema", "status", "paper", "dataset", "source", "modelContract",
            "timeReference", "reproduction", "blockers", "controls", "slice12Gate",
        },
        "$",
    )
    if root["schema"] != "paper-to-insight.public-preflight/v1":
        raise PreflightError("unsupported preflight schema")
    if root["status"] != "preflight_only" or not root["blockers"]:
        raise PreflightError("preflight must remain blocked")
    dataset = root["dataset"]
    if (dataset["version"], dataset["subjects"], dataset["nights"], dataset["files"]) != (
        "1.0.0", 47, 253, 759
    ):
        raise PreflightError("dataset inventory drifted")
    for key in ("licenseSha256", "readmeSha256", "checksumManifestSha256"):
        if not SHA256.fullmatch(dataset.get(key, "")):
            raise PreflightError(f"dataset {key} is not pinned")
    source = root["source"]
    if not re.fullmatch(r"[0-9a-f]{40}", source.get("revision", "")):
        raise PreflightError("source revision is not a full commit")
    if source.get("trainedWeightsPublished") or source.get("rawToModelPreprocessorPublished"):
        raise PreflightError("source availability is overstated")
    if any(not SHA256.fullmatch(item) for item in source.get("fileSha256", {}).values()):
        raise PreflightError("source files are not pinned")
    time_reference = exact(
        root["timeReference"],
        {
            "paperTitle", "paperDoi", "sourceUrl", "revision", "licenseClaim",
            "fileSha256", "cosineFormula", "elapsedTimeFormula",
            "personalizedClockReproducible", "reportedBidsleepVariantKnown",
        },
        "$.timeReference",
    )
    time_files = time_reference.get("fileSha256", {})
    if (
        not re.fullmatch(r"[0-9a-f]{40}", time_reference.get("revision", ""))
        or set(time_files)
        != {
            "README.md", "source/constants.py",
            "source/preprocessing/time/time_based_feature_service.py",
        }
        or any(not SHA256.fullmatch(item) for item in time_files.values())
        or time_reference.get("paperDoi") != "10.1093/sleep/zsz180"
        or time_reference.get("sourceUrl") != "https://github.com/ojwalch/sleep_classifiers"
        or time_reference.get("licenseClaim") != "MIT in pinned README"
        or time_reference.get("cosineFormula")
        != "-cos((seconds_since_start - 5*3600) * 2*pi / (24*3600))"
        or time_reference.get("elapsedTimeFormula") != "seconds_since_start / 3600"
        or time_reference.get("personalizedClockReproducible") is not False
        or time_reference.get("reportedBidsleepVariantKnown") is not False
    ):
        raise PreflightError("time reference overstates public reproducibility")
    controls = root["controls"]
    if controls != {
        "generatedOrPublicOnly": True,
        "brainstemExecutionEnabled": False,
        "catalogueEntryEnabled": False,
        "participantTransferClaim": False,
        "clinicalUse": False,
    }:
        raise PreflightError("runtime or transfer control was enabled")
    reproduction = root["reproduction"]
    if not all(
        reproduction.get(key) is True
        for key in (
            "participantSeparatedSplitRequired", "nightsMayNotCrossSplits",
            "randomSeedsRequired",
        )
    ) or reproduction.get("publishedSplitReusable") is not False:
        raise PreflightError("participant split controls are incomplete")
    if root["slice12Gate"].get("decision") != "human_approval_required":
        raise PreflightError("Slice 12 gate was bypassed")
    return root


def participant_split(subject_ids, seed="bidsleep-public-reproduction-v1"):
    if len(subject_ids) < 5 or len(subject_ids) != len(set(subject_ids)):
        raise PreflightError("at least five unique subjects are required")
    ordered = sorted(
        subject_ids,
        key=lambda item: hashlib.sha256(f"{seed}\0{item}".encode()).hexdigest(),
    )
    holdout = max(1, len(ordered) // 5)
    return {
        "train": ordered[2 * holdout :],
        "validation": ordered[holdout : 2 * holdout],
        "test": ordered[:holdout],
    }


def smoke(preflight, fixture):
    validate_preflight(preflight)
    exact(fixture, {"schema", "generatedOnly", "subjects", "nightFiles", "labelEncoding"}, "fixture")
    if fixture["schema"] != "paper-to-insight.generated-bidsleep-metadata/v1" or fixture["generatedOnly"] is not True:
        raise PreflightError("fixture must be generated metadata")
    if set(fixture["nightFiles"]) != NIGHT_FILES or set(fixture["labelEncoding"]) != set("012345"):
        raise PreflightError("public file or label contract drifted")
    subjects = fixture["subjects"]
    ids = []
    nights = 0
    for subject in subjects:
        exact(subject, {"id", "nights"}, "fixture.subject")
        if not SUBJECT.fullmatch(subject["id"]) or not subject["nights"]:
            raise PreflightError("generated subject is invalid")
        if len(subject["nights"]) != len(set(subject["nights"])):
            raise PreflightError("night is duplicated")
        ids.append(subject["id"])
        nights += len(subject["nights"])
    splits = participant_split(ids)
    assigned = [item for values in splits.values() for item in values]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(ids):
        raise PreflightError("subject leakage detected")
    return {
        "schema": "paper-to-insight.bidsleep-preflight-smoke/v1",
        "status": "passed",
        "generatedOnly": True,
        "subjects": len(ids),
        "nights": nights,
        "splitCounts": {name: len(values) for name, values in splits.items()},
        "brainstemExecutionEnabled": False,
    }


def fetch_small(url, limit=5_000_000):
    with urlopen(url, timeout=30) as response:
        host = (urlparse(response.geturl()).hostname or "").lower()
        if host not in UPSTREAM_HOSTS:
            raise PreflightError("upstream redirect left the allowlist")
        body = response.read(limit + 1)
    if len(body) > limit:
        raise PreflightError("upstream metadata exceeded the byte limit")
    return body


def verify_upstream(preflight):
    validate_preflight(preflight)
    dataset = preflight["dataset"]
    dataset_files = {
        "LICENSE.txt": dataset["licenseSha256"],
        "README.md": dataset["readmeSha256"],
        "SHA256SUMS.txt": dataset["checksumManifestSha256"],
    }
    source = preflight["source"]
    source_files = {"LICENSE": source["licenseSha256"], **source["fileSha256"]}
    verified = 0
    checksum_manifest = b""
    for name, expected in dataset_files.items():
        body = fetch_small(
            f"https://physionet.org/files/bidsleep-dataset/{dataset['version']}/{name}"
        )
        if hashlib.sha256(body).hexdigest() != expected:
            raise PreflightError(f"dataset upstream hash changed: {name}")
        if name == "SHA256SUMS.txt":
            checksum_manifest = body
        verified += 1
    prefix = f"https://raw.githubusercontent.com/BIDSLabUMass/SLAMSS-IFS/{source['revision']}"
    for name, expected in source_files.items():
        if hashlib.sha256(fetch_small(f"{prefix}/{name}")).hexdigest() != expected:
            raise PreflightError(f"source upstream hash changed: {name}")
        verified += 1
    time_reference = preflight["timeReference"]
    prefix = f"https://raw.githubusercontent.com/ojwalch/sleep_classifiers/{time_reference['revision']}"
    for name, expected in time_reference["fileSha256"].items():
        if hashlib.sha256(fetch_small(f"{prefix}/{name}")).hexdigest() != expected:
            raise PreflightError(f"time reference upstream hash changed: {name}")
        verified += 1
    entries = [
        line.split(maxsplit=1)[1]
        for line in checksum_manifest.decode().splitlines()
        if len(line.split(maxsplit=1)) == 2
        and re.fullmatch(
            r"Bidslab[0-9]+/[0-9]+/(?:hr\.csv|motion\.csv|labels\.mat)",
            line.split(maxsplit=1)[1],
        )
    ]
    subjects = {item.split("/")[0] for item in entries}
    nights = {"/".join(item.split("/")[:2]) for item in entries}
    if (len(entries), len(subjects), len(nights)) != (
        dataset["files"], dataset["subjects"], dataset["nights"]
    ):
        raise PreflightError("dataset checksum inventory changed")
    return {"status": "passed", "smallFilesVerified": verified}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-upstream", action="store_true")
    args = parser.parse_args()
    preflight = json.loads((ROOT / "preflight.json").read_text())
    report = smoke(
        preflight,
        json.loads((ROOT / "generated-metadata.json").read_text()),
    )
    if args.verify_upstream:
        report["upstream"] = verify_upstream(preflight)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
