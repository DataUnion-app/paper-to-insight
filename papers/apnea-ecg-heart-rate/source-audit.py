#!/usr/bin/env python3
"""Freeze the checksum-pinned official Apnea-ECG method authority."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MAX_BYTES = 5_000_000
REQUIRED = {
    "apdet-source",
    "apnea-ecg-manifest",
    "apnea-ecg-paper",
    "apnea-ecg-records",
    "method-paper",
    "ucddb-manifest",
    "ucddb-records",
}
EXECUTABLES = {
    "apdet-1.0/av.c",
    "apdet-1.0/detruns.c",
    "apdet-1.0/filt.c",
    "apdet-1.0/get_apdet",
    "apdet-1.0/ht.c",
    "apdet-1.0/htavsd.c",
    "apdet-1.0/htmedfilt.c",
    "apdet-1.0/ldetrend.c",
    "apdet-1.0/linsamp.c",
    "apdet-1.0/mm.c",
    "apdet-1.0/rrlist.c",
    "apdet-1.0/smooth.c",
}
METHOD_MARKERS = (
    "NFLAG='-a N'",
    'FILT="0.2 20 -x 0.4 2.0"',
    "RESAMP=1.0",
    "DETREND=40",
    "SMOOTH=5",
    "MEDFILT=60",
    'AVSDOUT="1:00 5:00"',
    "MINLEN=15:00",
    'AMPTHRES="-0.555 1.3"',
    "AVAMP0=0.65",
    "AVAMP1=2.5",
    "SDAMP1=0.6",
    "AMPTIME0=0.006",
    "AVFREQ0=0.01",
    "AVFREQ1=0.055",
    "SDFREQ1=0.01",
    "FREQTIME0=0.7",
)


class AuditError(ValueError):
    pass


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "paper-to-insight-source-audit/2"})
    with urlopen(request, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise AuditError(f"asset exceeds {MAX_BYTES} bytes")
    return data


def load_sources(path: Path = ROOT / "public-sources.json") -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "paper-to-insight.public-sources/v1":
        raise AuditError("unsupported public-sources schema")
    assets = value.get("assets")
    if not isinstance(assets, dict) or set(assets) != REQUIRED:
        raise AuditError("public source set differs")
    return assets


def download(assets: dict) -> dict[str, bytes]:
    result = {}
    for name, item in sorted(assets.items()):
        data = fetch(item["url"])
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise AuditError(f"{name} checksum differs")
        result[name] = data
    return result


def audit(assets: dict[str, bytes]) -> dict:
    if set(assets) != REQUIRED:
        raise AuditError("audit asset set differs")

    try:
        with tarfile.open(fileobj=io.BytesIO(assets["apdet-source"]), mode="r:gz") as archive:
            members = {
                member.name: archive.extractfile(member).read()
                for member in archive.getmembers()
                if member.isfile()
            }
    except (tarfile.TarError, AttributeError, OSError) as exc:
        raise AuditError("apdet source archive is invalid") from exc

    if not EXECUTABLES.issubset(members):
        raise AuditError("official executable source set differs")
    licence = b"GNU General Public License"
    publisher = b"Free Software Foundation"
    version = b"either version 2 of the License, or (at your option) any later"
    if any(
        licence not in members[name]
        or publisher not in members[name]
        or version not in members[name]
        for name in EXECUTABLES
    ):
        raise AuditError("embedded executable licence notice differs")

    script = members["apdet-1.0/get_apdet"].decode("ascii")
    missing = [marker for marker in METHOD_MARKERS if marker not in script]
    if missing:
        raise AuditError(f"official method constants differ: {missing}")

    apnea_index = assets["apnea-ecg-records"].decode("ascii").splitlines()
    apnea_records = [name for name in apnea_index if re.fullmatch(r"[abcx][0-9]{2}", name)]
    ucddb_index = assets["ucddb-records"].decode("ascii").splitlines()
    ucddb_records = [name.removesuffix(".rec") for name in ucddb_index if name.endswith(".rec")]
    if len(apnea_records) != 70 or apnea_records[:2] != ["a01", "a02"]:
        raise AuditError("Apnea-ECG record list differs")
    if len(ucddb_records) != 25 or ucddb_records[:2] != ["ucddb002", "ucddb003"]:
        raise AuditError("UCDDB record list differs")
    if "a01.apn" not in assets["apnea-ecg-manifest"].decode("ascii"):
        raise AuditError("Apnea-ECG minute-label manifest entry is absent")
    if "ucddb002_respevt.txt" not in assets["ucddb-manifest"].decode("ascii"):
        raise AuditError("UCDDB respiratory-event manifest entry is absent")

    freeze = json.loads((ROOT / "authority-freeze.json").read_text(encoding="utf-8"))
    if freeze.get("brainstemDecision") != "withhold_personal_and_runnable_apnea_outputs":
        raise AuditError("Brainstem decision is not fail-closed")

    return {
        "schema": "paper-to-insight.source-audit/v2",
        "candidate": "brainstem.apnea-ecg-heart-rate",
        "officialSourceSha256": hashlib.sha256(assets["apdet-source"]).hexdigest(),
        "sourceRelationship": "author_reference_implementation",
        "embeddedSoftwareLicence": "GPL-2.0-or-later",
        "catalogueResourceLicence": "ODC-By-1.0",
        "licenceReviewRequiredBeforeRedistribution": True,
        "methodConstantsVerified": True,
        "apneaEcgRecords": len(apnea_records),
        "ucddbParticipants": len(ucddb_records),
        "personalApneaOutputEnabled": False,
        "runnableApneaOfferEnabled": False,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv[1:])
    if not args.verify:
        parser.error("--verify is required")
    try:
        result = audit(download(load_sources()))
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
