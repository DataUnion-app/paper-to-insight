#!/usr/bin/env python3
"""Convert one BIDSleep-shaped public night into an auditable aligned archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np


SCHEMA = "paper-to-insight.bidsleep-aligned-night/v1"
FILES = ("hr.csv", "motion.csv", "labels.mat")
SUBJECT = re.compile(r"^(?:Bidslab[0-9]+|generated-subject-[a-z])$")
NIGHT = re.compile(r"^(?:[1-9][0-9]*|generated-night-[a-z0-9-]+)$")
HR_HEADERS = {
    ("timestamp", "hr"),
    ("timestamp", "ihr"),
    ("timestamp", "heart_rate"),
    ("time", "hr"),
}
MOTION_HEADERS = {
    ("timestamp", "x", "y", "z"),
    ("time", "x", "y", "z"),
}


class ConverterError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def read_csv(path: Path, width: int, allowed_headers: set[tuple[str, ...]]) -> np.ndarray:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.reader(handle) if row and any(cell.strip() for cell in row)]
    if not rows:
        raise ConverterError(f"{path.name} is empty")
    try:
        [float(cell) for cell in rows[0]]
    except ValueError:
        if tuple(_header(cell) for cell in rows.pop(0)) not in allowed_headers:
            raise ConverterError(f"{path.name} has an unsupported header")
    if not rows or any(len(row) != width for row in rows):
        raise ConverterError(f"{path.name} must contain exactly {width} columns")
    try:
        values = np.asarray([[float(cell) for cell in row] for row in rows], dtype=np.float64)
    except ValueError as error:
        raise ConverterError(f"{path.name} contains a non-numeric value") from error
    if not np.isfinite(values).all():
        raise ConverterError(f"{path.name} contains a non-finite value")
    timestamps = values[:, 0]
    if np.any(np.diff(timestamps) <= 0):
        raise ConverterError(f"{path.name} timestamps must be strictly increasing")
    if width == 2 and np.any(values[:, 1] <= 0):
        raise ConverterError("heart rate must be positive")
    return values


def parse_rec_start(value) -> float:
    flattened = np.asarray(value).squeeze()
    if flattened.size != 1:
        raise ConverterError("recStart must be scalar")
    item = flattened.item()
    if isinstance(item, bytes):
        item = item.decode("utf-8")
    if isinstance(item, str):
        try:
            local = datetime.strptime(item.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError as error:
            raise ConverterError("recStart string must be YYYY-MM-DD HH:MM:SS") from error
        result = local.replace(tzinfo=ZoneInfo("America/New_York")).timestamp()
    else:
        result = float(item)
    if not math.isfinite(result) or not 946_684_800 <= result < 4_102_444_800:
        raise ConverterError("recStart is not an unambiguous Unix timestamp")
    return result


def load_labels(path: Path) -> tuple[float, np.ndarray, np.ndarray]:
    try:
        from scipy.io import loadmat
    except ImportError as error:
        raise ConverterError("scipy from requirements-converter.txt is required") from error
    values = loadmat(path)
    required = {"recStart", "dreem_label", "expert_label"}
    if not required.issubset(values):
        raise ConverterError("labels.mat is missing a required variable")
    dreem = _labels(values["dreem_label"], "dreem_label")
    expert = _labels(values["expert_label"], "expert_label")
    if dreem.shape != expert.shape:
        raise ConverterError("label arrays differ in length")
    return parse_rec_start(values["recStart"]), dreem, expert


def _labels(value, name: str) -> np.ndarray:
    labels = np.asarray(value).reshape(-1)
    if not np.issubdtype(labels.dtype, np.number) or not np.isfinite(labels).all():
        raise ConverterError(f"{name} must be finite numeric labels")
    if np.any(labels != np.floor(labels)) or np.any((labels < 0) | (labels > 5)):
        raise ConverterError(f"{name} must contain only integers 0 through 5")
    return labels.astype(np.uint8)


def _without_outliers(timestamps: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    means = values.mean()
    deviations = values.std()
    z = np.divide(
        values - means,
        deviations,
        out=np.zeros_like(values),
        where=deviations != 0,
    )
    keep = np.abs(z) <= 3
    if keep.sum() < 2:
        raise ConverterError("outlier removal left fewer than two samples")
    return timestamps[keep], values[keep]


def _validate_series(value: np.ndarray, width: int, name: str) -> None:
    if value.ndim != 2 or value.shape[1] != width or len(value) < 2:
        raise ConverterError(f"{name} must be an Nx{width} array")
    if not np.isfinite(value).all() or np.any(np.diff(value[:, 0]) <= 0):
        raise ConverterError(f"{name} values must be finite with increasing timestamps")
    if name == "heart rate" and np.any(value[:, 1] <= 0):
        raise ConverterError("heart rate must be positive")


def convert_arrays(
    hr: np.ndarray,
    motion: np.ndarray,
    rec_start: float,
    dreem_labels: np.ndarray,
    expert_labels: np.ndarray,
    *,
    minimum_epochs: int = 600,
    maximum_epochs: int = 1200,
) -> dict[str, np.ndarray]:
    _validate_series(hr, 2, "heart rate")
    _validate_series(motion, 4, "motion")
    if dreem_labels.shape != expert_labels.shape or dreem_labels.ndim != 1:
        raise ConverterError("label arrays must be matching vectors")
    epochs = len(expert_labels)
    if not minimum_epochs <= epochs <= maximum_epochs:
        raise ConverterError(f"night must contain {minimum_epochs} to {maximum_epochs} epochs")
    if np.any((expert_labels < 0) | (expert_labels > 5)) or np.any(
        (dreem_labels < 0) | (dreem_labels > 5)
    ):
        raise ConverterError("labels must contain only 0 through 5")

    hr_time, hr_values = _without_outliers(hr[:, 0], hr[:, 1])
    motion_series = [
        _without_outliers(motion[:, 0], motion[:, axis]) for axis in range(1, 4)
    ]
    grid = rec_start + np.arange(epochs * 30, dtype=np.float64)
    ihr = np.interp(grid, hr_time, hr_values, left=np.nan, right=np.nan)
    axes = np.column_stack(
        [
            np.interp(grid, timestamps, values, left=np.nan, right=np.nan)
            for timestamps, values in motion_series
        ]
    )
    acceleration = np.sqrt(np.square(axes).sum(axis=1))
    signal = np.column_stack((ihr, acceleration)).astype(np.float32)
    signal_valid = np.isfinite(signal).all(axis=1)

    epoch_start = rec_start + np.arange(epochs, dtype=np.float64) * 30
    epoch_index = np.floor((hr_time - rec_start) / 30).astype(np.int64)
    accepted = epoch_index[(epoch_index >= 0) & (epoch_index < epochs)]
    frequency = np.bincount(accepted, minlength=epochs).astype(np.float32) / 30.0
    reshaped_hr = ihr.reshape(epochs, 30)
    covered = np.isfinite(reshaped_hr).all(axis=1)
    hr_mean = np.full(epochs, np.nan, dtype=np.float32)
    hr_std = np.full(epochs, np.nan, dtype=np.float32)
    hr_mean[covered] = reshaped_hr[covered].mean(axis=1)
    hr_std[covered] = reshaped_hr[covered].std(axis=1)
    epoch_evidence = np.column_stack((frequency, hr_mean, hr_std)).astype(np.float32)
    elapsed_seconds = np.arange(epochs, dtype=np.float64) * 30
    cosine_clock = -np.cos((elapsed_seconds - 5 * 3600) * 2 * np.pi / (24 * 3600))
    time_candidates = np.column_stack((cosine_clock, elapsed_seconds / 3600)).astype(np.float32)

    stage_four = np.asarray([0, 1, 1, 2, 3, 0], dtype=np.uint8)[expert_labels]
    epoch_signal_valid = signal_valid.reshape(epochs, 30).all(axis=1)
    stage_mask = (expert_labels != 5) & epoch_signal_valid
    return {
        "signal_1hz": signal,
        "signal_valid": signal_valid,
        "epoch_freq_hr_stats": epoch_evidence,
        "epoch_time_candidates": time_candidates,
        "epoch_start_unix": epoch_start,
        "stage_original": expert_labels.astype(np.uint8),
        "stage_four": stage_four,
        "stage_mask": stage_mask,
        "dreem_stage_original": dreem_labels.astype(np.uint8),
    }


def write_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name in sorted(arrays):
            payload = io.BytesIO()
            np.save(payload, arrays[name], allow_pickle=False)
            entry = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, payload.getvalue())


def convert_night(night: Path, output: Path, subject_id: str, night_id: str) -> dict:
    if not SUBJECT.fullmatch(subject_id) or not NIGHT.fullmatch(night_id):
        raise ConverterError("public subject or night identity is invalid")
    missing = [name for name in FILES if not (night / name).is_file()]
    if missing:
        raise ConverterError(f"night is missing: {', '.join(missing)}")
    hr = read_csv(night / "hr.csv", 2, HR_HEADERS)
    motion = read_csv(night / "motion.csv", 4, MOTION_HEADERS)
    rec_start, dreem, expert = load_labels(night / "labels.mat")
    arrays = convert_arrays(hr, motion, rec_start, dreem, expert)
    archive = output.with_suffix(".npz")
    receipt_path = output.with_suffix(".receipt.json")
    write_npz(archive, arrays)
    epochs = len(expert)
    receipt = {
        "schema": SCHEMA,
        "status": "converted",
        "dataset": {"doi": "10.13026/a0sy-7t69", "version": "1.0.0", "license": "ODC-By-1.0"},
        "publicIdentity": {"subject": subject_id, "night": night_id},
        "inputSha256": {name: sha256(night / name) for name in FILES},
        "outputSha256": sha256(archive),
        "arrays": {name: {"shape": list(value.shape), "dtype": str(value.dtype)} for name, value in sorted(arrays.items())},
        "counts": {
            "epochs": epochs,
            "fullyCoveredEpochs": int(arrays["signal_valid"].reshape(epochs, 30).all(axis=1).sum()),
            "releasedLabels": int(arrays["stage_mask"].sum()),
        },
        "transform": {
            "outlierRule": "absolute population z-score <= 3 per source channel",
            "interpolation": "linear 1 Hz anchored at recStart; no extrapolation",
            "acceleration": "sqrt(x^2+y^2+z^2) after interpolation",
            "fourClassLabels": "Wake, Light(N1+N2), Deep(N3), REM; Unknown masked",
            "cosineClock": "-cos((seconds_since_start - 5*3600) * 2*pi / (24*3600))",
            "elapsedTime": "seconds_since_start / 3600",
        },
        "arrayColumns": {
            "epoch_freq_hr_stats": ["accepted_ihr_hz", "ihr_mean_bpm", "ihr_std_bpm"],
            "epoch_time_candidates": ["cosine_clock_proxy", "elapsed_hours"],
            "signal_1hz": ["ihr_bpm", "acceleration_magnitude_g"],
        },
        "modelReady": False,
        "unsupportedAuthorFields": ["personalized_circadian_clock"],
        "modelBoundary": (
            "paper=2 epoch channels; training source=5; "
            "testing source=3 into a 5-channel convolution"
        ),
        "brainstemExecutionEnabled": False,
        "catalogueEntryEnabled": False,
        "participantTransferClaim": False,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("night", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--subject-id", required=True)
    parser.add_argument("--night-id", required=True)
    args = parser.parse_args()
    report = convert_night(args.night, args.output, args.subject_id, args.night_id)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
