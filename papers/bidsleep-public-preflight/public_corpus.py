#!/usr/bin/env python3
"""Verify, extract, and convert the approved public BIDSleep corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path, PurePosixPath

from converter import convert_night, sha256
from preflight import assemble_public_plan, parse_signal_manifest, validate_preflight


SCHEMA = "paper-to-insight.bidsleep-public-corpus/v1"
DEFAULT_EXPANDED_LIMIT = 35_000_000_000


def load_contract(manifest_path: Path, preflight_path: Path, plan_path: Path):
    preflight = json.loads(preflight_path.read_text())
    validate_preflight(preflight)
    manifest = manifest_path.read_bytes()
    if hashlib.sha256(manifest).hexdigest() != preflight["dataset"]["checksumManifestSha256"]:
        raise ValueError("public checksum manifest hash changed")
    entries = parse_signal_manifest(manifest)
    plan = json.loads(plan_path.read_text())
    if assemble_public_plan(preflight, entries) != plan:
        raise ValueError("public plan differs from the pinned manifest")
    return preflight, entries, plan


def signal_member_name(name: str, expected: set[str]) -> str | None:
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"unsafe ZIP member: {name}")
    for index, part in enumerate(path.parts):
        if part.startswith("Bidslab"):
            candidate = "/".join(path.parts[index:])
            return candidate if candidate in expected else None
    return None


def safe_target(root: Path, name: str) -> Path:
    root = root.resolve()
    current = root
    parts = PurePosixPath(name).parts
    for part in parts[:-1]:
        current /= part
        if current.is_symlink():
            raise ValueError(f"extraction path contains a symlink: {name}")
        current.mkdir(exist_ok=True)
    target = current / parts[-1]
    if target.is_symlink() or target.with_suffix(target.suffix + ".part").is_symlink():
        raise ValueError(f"extraction target is a symlink: {name}")
    return target


def extract_verified(
    archive_path: Path,
    entries: dict[str, str],
    raw_root: Path,
    expanded_limit: int,
) -> dict:
    if raw_root.is_symlink():
        raise ValueError("raw extraction root may not be a symlink")
    raw_root.mkdir(parents=True, exist_ok=True)
    selected = {}
    declared_bytes = 0
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            signal_name = signal_member_name(info.filename, set(entries))
            if info.is_dir() or signal_name is None:
                continue
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"ZIP symlink is not allowed: {info.filename}")
            if signal_name in selected:
                raise ValueError(f"duplicate ZIP member for {signal_name}")
            declared_bytes += info.file_size
            if declared_bytes > expanded_limit:
                raise ValueError("public signal files exceed the expanded-size limit")
            selected[signal_name] = info
        missing = set(entries) - set(selected)
        if missing:
            raise ValueError(f"ZIP is missing {len(missing)} public signal files")

        extracted_bytes = 0
        reused = 0
        for index, name in enumerate(sorted(entries), 1):
            target = safe_target(raw_root, name)
            expected_hash = entries[name]
            if target.is_file():
                if sha256(target) != expected_hash:
                    raise ValueError(f"existing extracted file hash differs: {name}")
                reused += 1
                extracted_bytes += target.stat().st_size
                continue
            temporary = target.with_suffix(target.suffix + ".part")
            digest = hashlib.sha256()
            written = 0
            with archive.open(selected[name]) as source, temporary.open("wb") as destination:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    written += len(chunk)
                    extracted_bytes += len(chunk)
                    if extracted_bytes > expanded_limit:
                        raise ValueError("extracted files exceed the expanded-size limit")
                    digest.update(chunk)
                    destination.write(chunk)
            if written != selected[name].file_size or digest.hexdigest() != expected_hash:
                raise ValueError(f"extracted file failed its public hash: {name}")
            os.replace(temporary, target)
            if index == 1 or index % 25 == 0 or index == len(entries):
                print(json.dumps({"extracted": index, "files": len(entries)}), flush=True)
    return {
        "files": len(entries),
        "declaredBytes": declared_bytes,
        "extractedBytes": extracted_bytes,
        "reusedFiles": reused,
    }


def convert_verified(
    raw_root: Path,
    converted_root: Path,
    entries: dict[str, str],
    plan: dict,
) -> dict:
    nights = [
        night
        for partition in ("train", "validation", "test")
        for night in plan["partitions"][partition]["nights"]
    ]
    if len(nights) != len(set(nights)):
        raise ValueError("public plan repeats a night")
    output_hashes = {}
    reused = 0
    for index, night in enumerate(nights, 1):
        subject, night_id = night.split("/", 1)
        source = raw_root / subject / night_id
        destination = converted_root / subject / night_id / "aligned"
        destination.parent.mkdir(parents=True, exist_ok=True)
        receipt_path = destination.with_suffix(".receipt.json")
        archive_path = destination.with_suffix(".npz")
        expected_inputs = {
            name: entries[f"{night}/{name}"] for name in ("hr.csv", "labels.mat", "motion.csv")
        }
        if receipt_path.is_file() and archive_path.is_file():
            receipt = json.loads(receipt_path.read_text())
            if (
                receipt.get("inputSha256") == expected_inputs
                and receipt.get("outputSha256") == sha256(archive_path)
            ):
                reused += 1
                output_hashes[night] = receipt["outputSha256"]
                continue
            raise ValueError(f"existing conversion differs for {night}")
        receipt = convert_night(source, destination, subject, night_id)
        if receipt["inputSha256"] != expected_inputs:
            raise ValueError(f"converted inputs failed the public manifest for {night}")
        output_hashes[night] = receipt["outputSha256"]
        if index == 1 or index % 10 == 0 or index == len(nights):
            print(json.dumps({"converted": index, "nights": len(nights)}), flush=True)
    return {"nights": len(nights), "reusedNights": reused, "outputSha256": output_hashes}


def write_receipt(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("preflight", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("raw_root", type=Path)
    parser.add_argument("converted_root", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--expanded-limit", type=int, default=DEFAULT_EXPANDED_LIMIT)
    args = parser.parse_args()
    if args.expanded_limit < 1:
        parser.error("expanded limit must be positive")
    preflight, entries, plan = load_contract(args.manifest, args.preflight, args.plan)
    extraction = extract_verified(args.archive, entries, args.raw_root, args.expanded_limit)
    conversion = convert_verified(args.raw_root, args.converted_root, entries, plan)
    receipt = {
        "schema": SCHEMA,
        "status": "verified_and_converted",
        "publicOnly": True,
        "dataset": preflight["dataset"],
        "archiveSha256": sha256(args.archive),
        "manifestSha256": sha256(args.manifest),
        "planSha256": sha256(args.plan),
        "extraction": extraction,
        "conversion": conversion,
        "claims": {
            "brainstemTransferValidated": False,
            "brainstemExecutionEnabled": False,
            "catalogueEntryEnabled": False,
            "clinicalUse": False,
        },
    }
    write_receipt(args.receipt, receipt)
    print(json.dumps({"status": receipt["status"], "receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
