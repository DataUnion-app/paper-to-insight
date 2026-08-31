#!/usr/bin/env python3
"""Paper-derived SLAMSS-IFS LSTM port and one-night public benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import resource
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


SCHEMA = "paper-to-insight.bidsleep-paper-lstm-benchmark/v1"
VARIANT = "paper_lstm_freq_cosine_time_v1"
CLASSES = ("wake", "light", "deep", "rem")
SEED = 20260831


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_everything(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class PaperLSTM(nn.Module):
    """Minimum architecture stated in Song et al., DOI 10.1109/TBME.2025.3612158."""

    def __init__(self) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        channels = 2
        for index in range(5):
            layers.append(nn.Conv1d(channels, 128, 5, padding=2))
            if index < 4:
                layers.append(nn.LeakyReLU())
            if index == 0:
                layers.append(nn.MaxPool1d(6, stride=6))
            if index == 3:
                layers.append(nn.MaxPool1d(5, stride=5))
            channels = 128
        layers.append(nn.Dropout(0.5))
        self.cnn = nn.Sequential(*layers)
        self.intra_lstm = nn.LSTM(
            2, 32, num_layers=2, batch_first=True, bidirectional=True, dropout=0.5
        )
        self.intra_fc = nn.Sequential(nn.Linear(64, 128), nn.Dropout(0.5))
        self.encoder = nn.LSTM(258, 96, batch_first=True)
        self.encoder_dropout = nn.Dropout(0.2)
        self.attention_energy = nn.Linear(192, 96)
        self.attention_score = nn.Linear(96, 1, bias=False)
        self.decoder = nn.LSTMCell(100, 96)
        self.decoder_dropout = nn.Dropout(0.2)
        self.classifier = nn.Linear(454, len(CLASSES))

    def _features(self, signal: torch.Tensor, covariates: torch.Tensor) -> torch.Tensor:
        if signal.ndim != 4 or signal.shape[2:] != (30, 2):
            raise ValueError("signal must have shape [batch, epochs, 30, 2]")
        if covariates.shape != (*signal.shape[:2], 2):
            raise ValueError("covariates must have shape [batch, epochs, 2]")
        batch, epochs = signal.shape[:2]
        flattened = signal.reshape(batch, epochs * 30, 2)
        cnn = self.cnn(flattened.transpose(1, 2)).transpose(1, 2)
        if cnn.shape[1] != epochs:
            raise ValueError("CNN did not preserve one feature vector per epoch")
        intra, _ = self.intra_lstm(signal.reshape(batch * epochs, 30, 2))
        intra = self.intra_fc(intra[:, -1]).reshape(batch, epochs, 128)
        return torch.cat((cnn, intra, covariates), dim=-1)

    def forward(
        self,
        signal: torch.Tensor,
        covariates: torch.Tensor,
        sequence_mask: torch.Tensor,
        teacher_labels: torch.Tensor | None = None,
        teacher_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        features = self._features(signal, covariates)
        if sequence_mask.shape != signal.shape[:2] or not sequence_mask.bool().any(dim=1).all():
            raise ValueError("every sequence needs at least one valid epoch")
        lengths = sequence_mask.sum(dim=1)
        expected = torch.arange(signal.shape[1], device=signal.device).unsqueeze(0) < lengths.unsqueeze(1)
        if not torch.equal(sequence_mask.bool(), expected):
            raise ValueError("sequence mask must be a left-aligned contiguous prefix")
        if (teacher_labels is None) != (teacher_mask is None):
            raise ValueError("teacher labels and mask must be supplied together")
        if teacher_labels is not None and (
            teacher_labels.shape != sequence_mask.shape or teacher_mask.shape != sequence_mask.shape
        ):
            raise ValueError("teacher labels and mask must match the sequence")
        packed = nn.utils.rnn.pack_padded_sequence(
            features, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        encoded, (hidden, cell) = self.encoder(packed)
        encoded, _ = nn.utils.rnn.pad_packed_sequence(
            encoded, batch_first=True, total_length=signal.shape[1]
        )
        encoded = self.encoder_dropout(encoded)
        hidden = hidden[-1]
        cell = cell[-1]
        previous = torch.zeros(signal.shape[0], len(CLASSES), device=signal.device)
        outputs = []
        attention_mask = ~sequence_mask.bool()
        for index in range(signal.shape[1]):
            repeated = hidden.unsqueeze(1).expand(-1, encoded.shape[1], -1)
            scores = self.attention_score(
                torch.tanh(self.attention_energy(torch.cat((encoded, repeated), dim=-1)))
            ).squeeze(-1)
            scores = scores.masked_fill(attention_mask, torch.finfo(scores.dtype).min)
            context = torch.bmm(F.softmax(scores, dim=1).unsqueeze(1), encoded).squeeze(1)
            hidden, cell = self.decoder(torch.cat((previous, context), dim=-1), (hidden, cell))
            hidden = self.decoder_dropout(hidden)
            logits = self.classifier(
                torch.cat((hidden, context, previous, features[:, index]), dim=-1)
            )
            outputs.append(logits)
            if teacher_labels is None:
                previous = F.one_hot(logits.argmax(dim=-1), len(CLASSES)).to(logits.dtype)
            else:
                predicted = F.one_hot(logits.argmax(dim=-1), len(CLASSES)).to(logits.dtype)
                teacher = F.one_hot(teacher_labels[:, index], len(CLASSES)).to(logits.dtype)
                previous = torch.where(teacher_mask[:, index].unsqueeze(1), teacher, predicted)
        return torch.stack(outputs, dim=1)


def load_public_night(archive: Path, receipt_path: Path, epochs: int = 1200):
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("schema") != "paper-to-insight.bidsleep-aligned-night/v2":
        raise ValueError("aligned-night receipt schema is invalid")
    if receipt.get("brainstemExecutionEnabled") is not False:
        raise ValueError("benchmark accepts public-only aligned nights")
    if sha256(archive) != receipt.get("outputSha256"):
        raise ValueError("aligned archive hash does not match its receipt")
    with np.load(archive, allow_pickle=False) as values:
        signal = values["signal_1hz"].astype(np.float32)
        frequency = values["epoch_freq_hr_stats"][:, 0].astype(np.float32)
        cosine_time = values["epoch_time_candidates"][:, 0].astype(np.float32)
        labels = values["stage_four"].astype(np.int64)
        mask = values["stage_mask"].astype(bool)
    source_epochs = len(labels)
    if not 1 <= source_epochs <= epochs or signal.shape != (source_epochs * 30, 2):
        raise ValueError("aligned archive has incompatible shapes")
    for channel in range(2):
        finite = np.isfinite(signal[:, channel])
        if finite.sum() < 2:
            raise ValueError("aligned signal channel lacks finite evidence")
        mean = signal[finite, channel].mean()
        std = signal[finite, channel].std()
        if not np.isfinite(std) or std == 0:
            raise ValueError("aligned signal channel has zero variance")
        signal[finite, channel] = (signal[finite, channel] - mean) / std
        signal[~finite, channel] = 0
    padded_signal = np.zeros((epochs, 30, 2), dtype=np.float32)
    padded_covariates = np.zeros((epochs, 2), dtype=np.float32)
    padded_labels = np.zeros(epochs, dtype=np.int64)
    sequence_mask = np.zeros(epochs, dtype=bool)
    release_mask = np.zeros(epochs, dtype=bool)
    padded_signal[:source_epochs] = signal.reshape(source_epochs, 30, 2)
    padded_covariates[:source_epochs, 0] = frequency
    padded_covariates[:source_epochs, 1] = cosine_time
    padded_labels[:source_epochs] = labels
    sequence_mask[:source_epochs] = True
    release_mask[:source_epochs] = mask
    return (
        padded_signal,
        padded_covariates,
        padded_labels,
        sequence_mask,
        release_mask,
        receipt,
    )


def benchmark(archive: Path, receipt_path: Path, output: Path, device_name: str) -> dict:
    seed_everything()
    signal, covariates, labels, sequence_mask, release_mask, source_receipt = load_public_night(
        archive, receipt_path
    )
    if device_name == "auto":
        device_name = "mps" if torch.backends.mps.is_available() else "cpu"
    device = torch.device(device_name)
    model = PaperLSTM().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.00015)
    signal_tensor = torch.from_numpy(signal).unsqueeze(0).to(device)
    covariate_tensor = torch.from_numpy(covariates).unsqueeze(0).to(device)
    label_tensor = torch.from_numpy(labels).unsqueeze(0).to(device)
    sequence_mask_tensor = torch.from_numpy(sequence_mask).unsqueeze(0).to(device)
    release_mask_tensor = torch.from_numpy(release_mask).unsqueeze(0).to(device)
    started = time.perf_counter()
    optimizer.zero_grad(set_to_none=True)
    logits = model(
        signal_tensor,
        covariate_tensor,
        sequence_mask_tensor,
        label_tensor,
        release_mask_tensor,
    )
    loss = F.cross_entropy(logits[release_mask_tensor], label_tensor[release_mask_tensor])
    loss.backward()
    optimizer.step()
    if device.type == "mps":
        torch.mps.synchronize()
    elapsed = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() != "Darwin":
        peak_rss *= 1024
    report = {
        "schema": SCHEMA,
        "status": "passed",
        "publicOnly": True,
        "variant": VARIANT,
        "sourceAlignedArchiveSha256": sha256(archive),
        "publicIdentity": source_receipt["publicIdentity"],
        "seed": SEED,
        "device": str(device),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "platform": platform.platform(),
        },
        "architecture": {
            "epochs": int(signal.shape[0]),
            "subEpochSamples": 30,
            "signalChannels": ["ihr_bpm_zscore", "acceleration_magnitude_g_zscore"],
            "epochCovariates": ["accepted_ihr_hz", "simple_cosine_clock_proxy"],
            "cnn": "5x Conv1d(128,kernel=5); max-pool 6 then 5; dropout=0.5",
            "intraEpoch": "2-layer bidirectional LSTM hidden=32; FC=128; dropout=0.5",
            "encoderDecoder": "LSTM hidden=96; additive attention; dropout=0.2; skip connection",
            "classes": list(CLASSES),
            "parameters": sum(value.numel() for value in model.parameters()),
        },
        "benchmark": {
            "batchSize": 1,
            "optimizationSteps": 1,
            "learningRate": 0.00015,
            "loss": "masked_cross_entropy_resource_probe",
            "lossValue": float(loss.detach().cpu()),
            "wallSeconds": elapsed,
            "peakRssBytes": int(peak_rss),
            "logitsShape": list(logits.shape),
            "sourceEpochs": int(sequence_mask.sum()),
            "releasedLabels": int(release_mask.sum()),
        },
        "reconstructionChoices": [
            "paper LSTMs replace the conflicting public-source GRUs",
            "Time is the public five-hour-shifted cosine proxy because personalized step input is absent",
            "teacher forcing uses only the previous released label and a zero start token; unreleased labels use the prior prediction",
            "the resource probe uses masked cross entropy; the full training loss remains to be frozen",
        ],
        "claims": {
            "reportedResultReproduced": False,
            "sourceImplementationReproduced": False,
            "brainstemTransferValidated": False,
            "brainstemExecutionEnabled": False,
            "catalogueEntryEnabled": False,
            "clinicalUse": False,
        },
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--device", choices=("auto", "cpu", "mps"), default="auto")
    args = parser.parse_args()
    benchmark(args.archive, args.receipt, args.output, args.device)


if __name__ == "__main__":
    main()
