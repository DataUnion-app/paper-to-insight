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


def parse_signal_manifest(body):
    entries = {}
    for line in body.decode().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        digest, path = parts
        match = re.fullmatch(
            r"(Bidslab[0-9]+/[1-9][0-9]*)/(hr\.csv|motion\.csv|labels\.mat)",
            path,
        )
        if not match:
            if path.startswith("Bidslab"):
                raise PreflightError(f"unsupported signal manifest path: {path}")
            continue
        if not SHA256.fullmatch(digest) or path in entries:
            raise PreflightError("signal manifest hash or path is invalid")
        entries[path] = digest
    if not entries:
        raise PreflightError("signal manifest contains no nights")
    return entries


def assemble_public_plan(preflight, entries, seed="bidsleep-public-reproduction-v1"):
    validate_preflight(preflight)
    nights = {}
    for path, digest in entries.items():
        night, name = path.rsplit("/", 1)
        if name in nights.setdefault(night, {}):
            raise PreflightError("night contains a duplicate file")
        nights[night][name] = digest
    if any(set(files) != NIGHT_FILES for files in nights.values()):
        raise PreflightError("night file set is incomplete")
    subjects = {night.split("/", 1)[0] for night in nights}
    dataset = preflight["dataset"]
    if (len(entries), len(subjects), len(nights)) != (
        dataset["files"], dataset["subjects"], dataset["nights"]
    ):
        raise PreflightError("public inventory count differs")

    split = participant_split(sorted(subjects), seed)
    owner = {subject: name for name, values in split.items() for subject in values}
    partitions = {}
    for name in ("train", "validation", "test"):
        partition_subjects = sorted(split[name])
        partition_nights = sorted(
            night for night in nights if owner[night.split("/", 1)[0]] == name
        )
        partitions[name] = {"subjects": partition_subjects, "nights": partition_nights}
    assigned_nights = [night for partition in partitions.values() for night in partition["nights"]]
    if len(assigned_nights) != len(set(assigned_nights)) or set(assigned_nights) != set(nights):
        raise PreflightError("night leakage detected")

    benchmark_night = min(
        partitions["train"]["nights"],
        key=lambda night: hashlib.sha256(f"{seed}\0benchmark\0{night}".encode()).hexdigest(),
    )
    prefix = f"https://physionet.org/files/bidsleep-dataset/{dataset['version']}"
    benchmark_files = {
        name: {
            "sha256": nights[benchmark_night][name],
            "url": f"{prefix}/{benchmark_night}/{name}",
        }
        for name in sorted(NIGHT_FILES)
    }
    return {
        "schema": "paper-to-insight.bidsleep-public-plan/v1",
        "status": "metadata_only",
        "dataset": {"doi": dataset["doi"], "version": dataset["version"]},
        "splitSeed": seed,
        "counts": {"subjects": len(subjects), "nights": len(nights), "files": len(entries)},
        "partitions": partitions,
        "benchmark": {"night": benchmark_night, "partition": "train", "files": benchmark_files},
        "controls": {
            "signalFilesDownloaded": False,
            "downloadApproved": False,
            "modelVariantSelected": False,
            "brainstemExecutionEnabled": False,
        },
    }


def build_public_plan(preflight, checksum_manifest):
    expected = preflight["dataset"]["checksumManifestSha256"]
    if hashlib.sha256(checksum_manifest).hexdigest() != expected:
        raise PreflightError("dataset checksum manifest hash changed")
    return assemble_public_plan(preflight, parse_signal_manifest(checksum_manifest))


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
    public_plan = build_public_plan(preflight, checksum_manifest)
    committed_plan_path = ROOT / "public-plan.json"
    if public_plan != json.loads(committed_plan_path.read_text()):
        raise PreflightError("committed public plan drifted")
    return {
        "status": "passed",
        "smallFilesVerified": verified,
        "publicPlanSha256": hashlib.sha256(committed_plan_path.read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-upstream", action="store_true")
    parser.add_argument("--public-plan-output", type=Path)
    args = parser.parse_args()
    preflight = json.loads((ROOT / "preflight.json").read_text())
    report = smoke(
        preflight,
        json.loads((ROOT / "generated-metadata.json").read_text()),
    )
    if args.verify_upstream:
        report["upstream"] = verify_upstream(preflight)
    if args.public_plan_output:
        dataset = preflight["dataset"]
        manifest = fetch_small(
            f"https://physionet.org/files/bidsleep-dataset/{dataset['version']}/SHA256SUMS.txt"
        )
        plan = build_public_plan(preflight, manifest)
        args.public_plan_output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
        report["publicPlan"] = {
            "status": plan["status"],
            "subjects": plan["counts"]["subjects"],
            "nights": plan["counts"]["nights"],
        }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
