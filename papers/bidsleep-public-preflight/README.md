# BIDSleep public reproduction preflight

This package audits a public Apple-Watch sleep-staging reproduction before any
large download or training run. It is not a Brainstem Insight, study, catalogue
entry, trained model, or transfer-validation result.

## Frozen evidence

- Paper: Song et al., *AI-Driven Sleep Staging Using Instantaneous Heart Rate
  and Accelerometry: Insights From an Apple Watch Study*, DOI
  `10.1109/TBME.2025.3612158`. The paper reports four 30-second classes and 71%
  overall accuracy in 47 healthy adults.
- Dataset: PhysioNet BIDSleep `1.0.0`, DOI `10.13026/a0sy-7t69`, published
  12 May 2026 under ODC-By 1.0. Its official checksum manifest contains 759
  signal/label files: 253 nights from 47 subjects. PhysioNet reports 5.9 GB ZIP
  and 27.9 GB expanded.
- Source: `BIDSLabUMass/SLAMSS-IFS` commit
  `088e363873b4ac5b27bc23fb038abc052889698c`, tree
  `9a69685b694571e2f92f6c30fda3ce5422239638`, BSD-3-Clause. Exact dataset,
  licence, README, notebook, and model-file SHA-256 values are in
  `preflight.json`.

## What the public data contains

Each night has Apple Watch PPG heart rate at roughly 0.2 Hz, three-axis wrist
accelerometry in g, and Dreem labels. The corrected expert label is the
reference. Labels are Wake, N1, N2, N3, REM, or Unknown on 30-second epochs.
All nights from one subject must remain in exactly one train, validation, or
test partition.

## Source audit

The published notebooks do not consume the public files. They consume
author-generated MAT files containing `hr`, `hr2`, `act`, `clock`, `time`,
`hz`, and `stg_cor_cln`; the converter that creates those fields is absent.
The model then expects 1,200 epochs, 30 paired sub-epoch samples per epoch,
five epoch covariates, and four output classes. Unknown labels are masked; N1
and N2 are merged into the light class.

The source cannot reproduce as committed:

- training/validation are author-local directories with no published subject
  split manifest;
- no weights are published and checkpoint saving is commented out;
- the testing notebook passes three covariate channels into a convolution that
  expects five;
- output buffers assume 64 validation nights, execution assumes two GPUs, and
  paths are absolute;
- the README lists Python 3.7, PyTorch 1.9, NumPy 1.21, SciPy 1.6, CUDA 11.8,
  and CuDNN 8.2, but provides no install lock;
- the 1,000-epoch training loop has no Python, NumPy, PyTorch, loader, or CUDA
  seeds and recreates Adam optimizers each epoch.

The reproduction must therefore port preprocessing and training rather than
claim the notebooks already run.

## Smallest honest next run

1. Reserve at least 100 GB scratch space.
2. Download and verify PhysioNet `1.0.0` only after human approval.
3. Convert one public night with an explicit timestamp/label alignment receipt.
4. Freeze a subject-level split manifest before tensor generation.
5. Run one seeded epoch on one GPU and record peak memory, wall time, and output
   shapes.
6. Use that receipt to approve or reject the full training budget. Do not infer
   full GPU hours before this benchmark.

Only after a reproducible public result may a separate paired
Brainstem-versus-EEG study be proposed. Apple Watch PPG/motion performance does
not transfer automatically to Brainstem R-R or device movement.

## Tiny generated smoke

No signal data is downloaded by this command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 papers/bidsleep-public-preflight/preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 papers/bidsleep-public-preflight/test_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 papers/bidsleep-public-preflight/preflight.py \
  --verify-upstream
```

The smoke test validates the official file/label metadata, creates a
deterministic subject-only split over generated identifiers, and fails if a
Brainstem runtime, catalogue entry, transfer claim, clinical use, or Slice 12
gate is enabled.
The optional upstream check downloads only eight pinned public metadata/source
files under a 5 MB per-file limit; it does not download any night recording.
