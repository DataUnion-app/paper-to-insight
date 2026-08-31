#!/usr/bin/env python3
"""Train and evaluate the frozen public-only paper-derived BIDSleep model."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from paper_lstm import CLASSES, PaperLSTM, load_public_night, seed_everything, sha256


SCHEMA = "paper-to-insight.bidsleep-public-reproduction/v1"
REPORTED_METRICS = {
    "accuracy": 0.7104,
    "sensitivity": 0.6998,
    "specificity": 0.8902,
    "precision": 0.6983,
    "weightedF1": 0.7079,
    "weightedMcc": 0.5599,
}
REPRODUCTION_TOLERANCE = 0.02
RWL_FACTOR = np.asarray(
    [
        [0.0, 1.0, 1.0, 1.0],
        [0.5, 0.0, 0.5, 1.0],
        [1.0, 0.5, 0.0, 0.5],
        [0.5, 1.0, 1.0, 0.0],
    ],
    dtype=np.float32,
)


def rwl_matrices(class_counts: np.ndarray) -> tuple[torch.Tensor, torch.Tensor]:
    counts = np.asarray(class_counts, dtype=np.float64)
    if counts.shape != (len(CLASSES),) or not np.isfinite(counts).all() or np.any(counts <= 0):
        raise ValueError("all four train-only class counts must be positive")
    priors = counts / counts.sum()
    false_negative = np.diag(1.0 / priors).astype(np.float32)
    ratios = np.sqrt(priors[:, None] / priors[None, :]).astype(np.float32)
    false_positive = ratios * RWL_FACTOR
    return torch.from_numpy(false_negative), torch.from_numpy(false_positive)


def masked_rwl_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    release_mask: torch.Tensor,
    false_negative: torch.Tensor,
    false_positive: torch.Tensor,
) -> torch.Tensor:
    selected_logits = logits[release_mask]
    selected_labels = labels[release_mask]
    if not len(selected_labels):
        raise ValueError("training batch has no released labels")
    false_negative = false_negative.to(selected_logits.device)
    false_positive = false_positive.to(selected_logits.device)
    one_hot = F.one_hot(selected_labels, len(CLASSES)).to(selected_logits.dtype)
    probabilities = F.softmax(selected_logits, dim=1).clamp(1e-5, 1 - 1e-5)
    fn_for_label = one_hot @ false_negative
    fp_for_label = one_hot @ false_positive
    rwl = -(
        0.25 * fn_for_label * probabilities.log()
        + 0.5 * fp_for_label * (1 - probabilities).log()
    ).sum()
    cross_entropy = F.cross_entropy(selected_logits, selected_labels, reduction="sum")
    return cross_entropy + 0.01 * rwl


def _ratio(numerator: float, denominator: float):
    return numerator / denominator if denominator else None


def metrics_from_logits(logits: torch.Tensor, labels: torch.Tensor) -> dict:
    if logits.ndim != 2 or logits.shape[1] != len(CLASSES) or labels.shape != logits.shape[:1]:
        raise ValueError("metrics require [epochs,4] logits and matching labels")
    predictions = logits.argmax(dim=1)
    confusion = torch.zeros(len(CLASSES), len(CLASSES), dtype=torch.int64)
    for truth, prediction in zip(labels.cpu(), predictions.cpu()):
        confusion[int(truth), int(prediction)] += 1
    total = int(confusion.sum())
    if not total:
        raise ValueError("metrics require at least one label")
    per_class = {}
    f1_values = []
    mcc_values = []
    sensitivity_values = []
    specificity_values = []
    precision_values = []
    supports = []
    for index, name in enumerate(CLASSES):
        tp = int(confusion[index, index])
        fn = int(confusion[index].sum()) - tp
        fp = int(confusion[:, index].sum()) - tp
        tn = total - tp - fn - fp
        support = tp + fn
        sensitivity = _ratio(tp, tp + fn)
        specificity = _ratio(tn, tn + fp)
        precision = _ratio(tp, tp + fp)
        f1 = _ratio(2 * tp, 2 * tp + fp + fn)
        denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        mcc = _ratio(tp * tn - fp * fn, denominator)
        per_class[name] = {
            "support": support,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "precision": precision,
            "f1": f1,
            "mccOneVsRest": mcc,
        }
        supports.append(support)
        f1_values.append(f1 or 0.0)
        mcc_values.append(mcc or 0.0)
        sensitivity_values.append(sensitivity or 0.0)
        specificity_values.append(specificity or 0.0)
        precision_values.append(precision or 0.0)
    if any(support == 0 for support in supports):
        raise ValueError("paper metrics require support for all four classes")
    inverse_weights = np.reciprocal(np.asarray(supports, dtype=np.float64))
    inverse_weights /= inverse_weights.sum()
    probabilities = F.softmax(logits, dim=1)
    confidence, predicted = probabilities.max(dim=1)
    correct = predicted.eq(labels).to(torch.float32)
    ece = 0.0
    for lower in torch.linspace(0, 0.9, 10):
        selected = (confidence > lower) & (confidence <= lower + 0.1)
        if selected.any():
            ece += float(selected.float().mean() * (correct[selected].mean() - confidence[selected].mean()).abs())
    one_hot = F.one_hot(labels, len(CLASSES)).to(probabilities.dtype)
    return {
        "epochs": total,
        "confusionTruthByPrediction": confusion.tolist(),
        "accuracy": float(confusion.diag().sum() / total),
        "sensitivity": float(np.mean(sensitivity_values)),
        "specificity": float(np.mean(specificity_values)),
        "precision": float(np.mean(precision_values)),
        "weightedF1": float(inverse_weights @ f1_values),
        "weightedMcc": float(inverse_weights @ mcc_values),
        "metricWeighting": "normalized inverse test-class frequency as stated in paper Table IV",
        "calibration": {
            "expectedCalibrationError10Bins": ece,
            "multiclassBrier": float(torch.square(probabilities - one_hot).sum(dim=1).mean()),
        },
        "perClass": per_class,
    }


def load_partition(root: Path, plan: dict, name: str) -> list[dict]:
    if plan.get("schema") != "paper-to-insight.bidsleep-public-plan/v2":
        raise ValueError("public plan schema is invalid")
    if plan.get("assignment", {}).get("status") != "reconstructed_from_published_counts":
        raise ValueError("public subject assignment is not frozen")
    nights = plan.get("partitions", {}).get(name, {}).get("nights")
    if not isinstance(nights, list) or not nights:
        raise ValueError(f"partition {name} is empty")
    records = []
    for night in nights:
        night_path = Path(night)
        if night_path.is_absolute() or len(night_path.parts) != 2 or any(
            part in ("", ".", "..") for part in night_path.parts
        ):
            raise ValueError(f"partition {name} has an unsafe night identity")
        folder = root / night
        values = load_public_night(folder / "aligned.npz", folder / "aligned.receipt.json")
        signal, covariates, labels, sequence_mask, release_mask, receipt = values
        if f"{receipt['publicIdentity']['subject']}/{receipt['publicIdentity']['night']}" != night:
            raise ValueError(f"public identity differs for {night}")
        records.append(
            {
                "night": night,
                "subject": night.split("/", 1)[0],
                "signal": signal,
                "covariates": covariates,
                "labels": labels,
                "sequenceMask": sequence_mask,
                "releaseMask": release_mask,
            }
        )
    return records


def _batch(records: list[dict], indices: list[int], device: torch.device):
    def tensor(key):
        return torch.from_numpy(np.stack([records[index][key] for index in indices])).to(device)

    return (
        tensor("signal"),
        tensor("covariates"),
        tensor("labels"),
        tensor("sequenceMask"),
        tensor("releaseMask"),
    )


def train_class_counts(records: list[dict]) -> np.ndarray:
    counts = np.zeros(len(CLASSES), dtype=np.int64)
    for record in records:
        counts += np.bincount(
            record["labels"][record["releaseMask"]], minlength=len(CLASSES)
        )
    if np.any(counts <= 0):
        raise ValueError("training partition is missing a class")
    return counts


def evaluate(model, records, batch_size, device, temperature=1.0):
    model.eval()
    all_logits = []
    all_labels = []
    per_night = []
    with torch.no_grad():
        for start in range(0, len(records), batch_size):
            indices = list(range(start, min(start + batch_size, len(records))))
            signal, covariates, labels, sequence_mask, release_mask = _batch(records, indices, device)
            logits = model(signal, covariates, sequence_mask) / temperature
            for offset, index in enumerate(indices):
                selected_logits = logits[offset][release_mask[offset]].cpu()
                selected_labels = labels[offset][release_mask[offset]].cpu()
                all_logits.append(selected_logits)
                all_labels.append(selected_labels)
                per_night.append(
                    {
                        "night": records[index]["night"],
                        "accuracy": float(
                            selected_logits.argmax(dim=1).eq(selected_labels).float().mean()
                        ),
                        "epochs": len(selected_labels),
                    }
                )
    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels)
    return logits, labels, sorted(per_night, key=lambda item: (item["accuracy"], item["night"]))


def fit_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    log_temperature = torch.zeros((), requires_grad=True)
    optimizer = torch.optim.LBFGS([log_temperature], lr=0.1, max_iter=50, line_search_fn="strong_wolfe")

    def closure():
        optimizer.zero_grad()
        loss = F.cross_entropy(logits / log_temperature.exp(), labels)
        loss.backward()
        return loss

    optimizer.step(closure)
    return float(log_temperature.detach().exp().clamp(0.05, 20.0))


def run(args) -> dict:
    seed_everything(args.seed)
    plan_path = args.plan.resolve()
    plan = json.loads(plan_path.read_text())
    train_records = load_partition(args.converted_root, plan, "train")
    validation_records = load_partition(args.converted_root, plan, "validation")
    test_records = load_partition(args.converted_root, plan, "test")
    subjects = {
        name: {record["subject"] for record in records}
        for name, records in (
            ("train", train_records),
            ("validation", validation_records),
            ("test", test_records),
        )
    }
    if any(subjects[a] & subjects[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise ValueError("subject leakage detected after tensor loading")
    device_name = args.device
    if device_name == "auto":
        device_name = "mps" if torch.backends.mps.is_available() else "cpu"
    device = torch.device(device_name)
    model = PaperLSTM().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    class_counts = train_class_counts(train_records)
    fn_weights, fp_weights = rwl_matrices(class_counts)
    best = {"weightedF1": -1.0, "epoch": 0, "state": None, "metrics": None}
    history = []
    started = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        model.train()
        order = list(range(len(train_records)))
        random.Random(args.seed + epoch).shuffle(order)
        epoch_loss = 0.0
        epoch_labels = 0
        for start in range(0, len(order), args.batch_size):
            indices = order[start : start + args.batch_size]
            signal, covariates, labels, sequence_mask, release_mask = _batch(
                train_records, indices, device
            )
            optimizer.zero_grad(set_to_none=True)
            logits = model(signal, covariates, sequence_mask, labels, release_mask)
            loss = masked_rwl_loss(logits, labels, release_mask, fn_weights, fp_weights)
            loss.backward()
            optimizer.step()
            released = int(release_mask.sum())
            epoch_loss += float(loss.detach().cpu())
            epoch_labels += released
        validation_logits, validation_labels, _ = evaluate(
            model, validation_records, args.batch_size, device
        )
        validation_metrics = metrics_from_logits(validation_logits, validation_labels)
        history.append(
            {
                "epoch": epoch,
                "trainLossPerReleasedLabel": epoch_loss / epoch_labels,
                "validationAccuracy": validation_metrics["accuracy"],
                "validationWeightedF1": validation_metrics["weightedF1"],
            }
        )
        if validation_metrics["weightedF1"] > best["weightedF1"]:
            best = {
                "weightedF1": validation_metrics["weightedF1"],
                "epoch": epoch,
                "state": {name: value.detach().cpu().clone() for name, value in model.state_dict().items()},
                "metrics": validation_metrics,
            }
        if epoch == 1 or epoch % args.progress_every == 0 or epoch == args.epochs:
            print(json.dumps(history[-1], sort_keys=True), flush=True)
    model.load_state_dict(best["state"])
    model.to(device)
    validation_logits, validation_labels, validation_nights = evaluate(
        model, validation_records, args.batch_size, device
    )
    temperature = fit_temperature(validation_logits, validation_labels)
    test_logits, test_labels, test_nights = evaluate(model, test_records, args.batch_size, device)
    calibrated_test_metrics = metrics_from_logits(test_logits / temperature, test_labels)
    uncalibrated_test_metrics = metrics_from_logits(test_logits, test_labels)
    args.output.mkdir(parents=True, exist_ok=True)
    weights_path = args.output / "paper-lstm-weights.pt"
    torch.save(
        {
            "schema": "paper-to-insight.bidsleep-paper-lstm-weights/v1",
            "stateDict": best["state"],
            "bestEpoch": best["epoch"],
            "seed": args.seed,
            "planSha256": sha256(plan_path),
            "variant": "paper_lstm_freq_cosine_time_v1",
        },
        weights_path,
    )
    metric_deltas = {
        name: calibrated_test_metrics[name] - value for name, value in REPORTED_METRICS.items()
    }
    receipt = {
        "schema": SCHEMA,
        "status": (
            "within_predeclared_accuracy_tolerance"
            if abs(metric_deltas["accuracy"]) <= REPRODUCTION_TOLERANCE
            else "reported_accuracy_not_reproduced"
        ),
        "publicOnly": True,
        "planSha256": sha256(plan_path),
        "variant": "paper_lstm_freq_cosine_time_v1",
        "seed": args.seed,
        "device": str(device),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "platform": platform.platform(),
        },
        "experiment": {
            "subjects": {name: len(value) for name, value in subjects.items()},
            "nights": {
                "train": len(train_records),
                "validation": len(validation_records),
                "test": len(test_records),
            },
            "epochs": args.epochs,
            "batchSize": args.batch_size,
            "optimizer": "Adam",
            "learningRate": args.learning_rate,
            "bestValidationEpoch": best["epoch"],
            "trainClassCounts": class_counts.tolist(),
            "loss": "source-derived RWL with train-only class priors and ratio-consistent FP matrix",
            "elapsedSeconds": time.perf_counter() - started,
        },
        "calibration": {
            "method": "validation-only scalar temperature",
            "temperature": temperature,
        },
        "reportedMetrics": REPORTED_METRICS,
        "predeclaredAbsoluteTolerance": REPRODUCTION_TOLERANCE,
        "metricDeltas": metric_deltas,
        "validation": metrics_from_logits(validation_logits / temperature, validation_labels),
        "test": calibrated_test_metrics,
        "testUncalibrated": uncalibrated_test_metrics,
        "failureAnalysis": {
            "worstValidationNights": validation_nights[:10],
            "worstTestNights": test_nights[:10],
        },
        "weightsSha256": sha256(weights_path),
        "history": history,
        "reconstructionChoices": [
            "paper-described LSTMs replace the conflicting public-source GRUs",
            "Time is the public simple cosine proxy; the unavailable personalized clock is excluded",
            "RWL class priors are computed from released training labels only",
            "the source deep-to-REM ratio typo is replaced by the ratio-consistent published matrix pattern",
            "Adam state persists across epochs rather than being recreated by the conflicting notebook",
            "all train nights are used; the notebook's drop-last data loss is not reproduced",
            "the best epoch is selected by validation weighted F1 before one test evaluation",
        ],
        "claims": {
            "brainstemTransferValidated": False,
            "brainstemExecutionEnabled": False,
            "catalogueEntryEnabled": False,
            "clinicalUse": False,
        },
    }
    receipt_path = args.output / "reproduction-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(receipt_path)}, sort_keys=True))
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("converted_root", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=0.00015)
    parser.add_argument("--seed", type=int, default=20260831)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--device", choices=("auto", "cpu", "mps"), default="auto")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.progress_every < 1:
        parser.error("epochs, batch size, and progress interval must be positive")
    run(args)


if __name__ == "__main__":
    main()
