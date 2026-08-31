# BIDSleep public reproduction preflight

This package audits and reproduces a public Apple-Watch sleep-staging paper. It
is not a Brainstem Insight, study, catalogue entry, transfer-validation result,
or clinical model.

## Frozen evidence

- Paper: Song et al., *AI-Driven Sleep Staging Using Instantaneous Heart Rate
  and Accelerometry: Insights From an Apple Watch Study*, DOI
  `10.1109/TBME.2025.3612158`, PMCID `PMC12931632`. The paper reports four
  30-second classes and 71% overall accuracy in 47 healthy adults.
- Dataset: PhysioNet BIDSleep `1.0.0`, DOI `10.13026/a0sy-7t69`, published
  12 May 2026 under ODC-By 1.0. Its official checksum manifest contains 759
  signal/label files: 253 nights from 47 subjects. PhysioNet reports 5.9 GB ZIP
  and 27.9 GB expanded.
- Source: `BIDSLabUMass/SLAMSS-IFS` commit
  `088e363873b4ac5b27bc23fb038abc052889698c`, tree
  `9a69685b694571e2f92f6c30fda3ce5422239638`, BSD-3-Clause. Exact dataset,
  licence, README, notebook, and model-file SHA-256 values are in
  `preflight.json`.
- Time reference: Walch et al., DOI `10.1093/sleep/zsz180`, and its
  `ojwalch/sleep_classifiers` commit
  `7f2b521b3778b8cc2dd1cf2f013fef360e006958`. This pins the published
  five-hour-shifted cosine proxy and elapsed-hours calculation.

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
- the paper describes `Freq` and `Time`, training supplies five epoch channels,
  and testing supplies three to a convolution that expects five;
- the paper describes LSTM components while the pinned implementation uses GRUs;
- the public BIDSleep files contain no longitudinal step series for the
  personalised circadian model, and the paper does not identify which time
  variant produced the reported result;
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
4. Freeze a subject-level split manifest before tensor generation. Preserve the
   paper's 31/5/11 subject counts while labelling the deterministic identities as
   reconstructed because the author assignments are not published.
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
files, three pinned time-reference files, and two bounded GitHub metadata
responses under a 5 MB per-response limit. It fails if the cited repository's
`main` HEAD changes or a release appears, forcing a re-audit instead of silently
missing a newly published model. It does not download any night recording.

## Public participant split plan

The metadata-only v2 plan reads the official pinned checksum manifest, assigns
all 253 nights by their 47 subjects to the paper's 31/5/11 train/validation/test
counts, and selects one training night for a future benchmark. Because the paper
does not publish subject identities, the plan labels its hash-ordered assignment
as a reconstruction. It also pins the paper's five-fold cross-validation,
optimizer, learning rate, batch size, 500-epoch schedule, and evaluation metrics.
It records URLs and hashes but neither downloads nor authorizes signal data:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 papers/bidsleep-public-preflight/preflight.py \
  --verify-upstream --public-plan-output /tmp/bidsleep-public-plan.json
```

`public-plan.json` is the committed deterministic receipt. The earlier 29/9/9
v1 plan is superseded. Upstream verification fails if regenerating v2 from the
pinned manifest produces any difference.

## Generated converter checkpoint

`converter.py` implements the parts of the paper's preprocessing that are fully
specified by the public paper and dataset: per-channel 3-sigma filtering,
1 Hz linear interpolation without extrapolation, acceleration vector magnitude,
per-epoch pre-interpolation heart-rate sample frequency, and four-class label
mapping. It writes a deterministic compressed archive plus a provenance
receipt.
`generated-converter-receipt.json` freezes the resulting contract from a
deterministic generated 600-epoch night; its archive hash is reproduced twice
by the focused test fixture.

The output deliberately states `modelReady: false`. It now includes the exact
public cosine clock candidate and elapsed-hours candidate from the cited 2019
implementation. The personalised clock still requires unpublished longitudinal
step input, while the BIDSleep paper, training notebook, and testing notebook
disagree on the epoch-channel count. The converter therefore produces a
transparent aligned public intermediate rather than choosing an undocumented
model variant. No public signal night is needed for its generated tests:

```sh
python3 -m venv /tmp/bidsleep-converter
/tmp/bidsleep-converter/bin/pip install -r \
  papers/bidsleep-public-preflight/requirements-converter.txt
/tmp/bidsleep-converter/bin/python \
  papers/bidsleep-public-preflight/test_converter.py
```

## Public paper-LSTM benchmark

After explicit human approval, the exact three pinned `Bidslab40/6` files were
downloaded and verified. The real public night converted to 691 epochs with 688
released labels. `paper_lstm.py` selects the paper-derived architecture rather
than the conflicting GRU source: five CNN layers, a two-layer bidirectional
intra-epoch LSTM, `Freq`, the public simple-cosine `Time` proxy, an LSTM
encoder/decoder with attention, and a skip connection.

`public-benchmark-receipt.json` records the first MPS resource probe: one
1,200-epoch padded public night, batch size 1, one Adam step at learning rate
0.00015, 3.27 seconds wall time, 565 MB peak RSS, and logits shape
`[1,1200,4]`. This is a compute and shape proof, not a reproduced result. The
reported loss remains unreproduced until the full train-only weighting contract
is frozen.

`reproduce.py` freezes that remaining public-only contract: the source-derived
RWL loss is rebuilt from released training labels, the reconstructed 31/5/11
subject split is checked again after tensor loading, the best epoch is selected
on validation weighted F1, scalar calibration uses validation logits only, and
the test partition is evaluated once. Paper-table metrics use macro sensitivity,
specificity, and precision plus normalized inverse-class-frequency F1 and MCC;
all six reported values and deltas are retained. It refuses unsafe partition paths and
writes weights plus a receipt that states whether the reported accuracy was
reproduced within the predeclared absolute tolerance. This runner still does
not authorize Brainstem transfer, catalogue publication, study activation, or
clinical use. A hash-bound checkpoint is written after every epoch; `--resume`
continues only when the plan, variant, seed, device, epoch count, batch size,
and learning rate are unchanged.

`public_corpus.py` is the bounded corpus bridge. It verifies the pinned official
manifest and reconstructed split, rejects unsafe or symlinked ZIP paths, hashes
every signal file while extracting, and converts every night with resumable
hash checks. Its default 35 GB expanded-signal ceiling stays within the approved
100 GB temporary-storage budget.

The complete public corpus passed that bridge on 31 August 2026. All 759
manifest files and all 253 converted-night archives matched their receipts.
The converter's v2 receipt makes source anomalies explicit: timestamps are
stable-sorted, exact duplicates are averaged, at most one numeric incomplete
final CSV row is discarded, unequal Dreem/expert label tails are aligned to the
expert timeline, and nights longer than 1,200 epochs use the first 1,200 epochs
as the released notebooks do. `public-corpus-audit.json` binds the full local
receipt hash and aggregate repair counts without committing the 28 GB public
working copy.

The frozen 500-epoch participant-separated MPS run then completed on all 253
public nights. Validation-only selection chose epoch 448 and validation-only
temperature fitting produced `5.890388488769531`. The held-out 11-subject test
partition reached 37.08% accuracy, versus the paper's 71.04%, outside the
predeclared absolute tolerance of 2 percentage points. Deep-sleep sensitivity
was 3.65% and REM sensitivity was 22.24%. The result is therefore an honest
negative reproduction and must not be offered as a Brainstem Insight.
`public-reproduction-audit.json` records the split, environment, metrics,
confusion matrix, artifact hashes, failure summary, and disabled claims. The
full local receipt is hash-bound by that audit and can be regenerated from the
public corpus with the command below.

```sh
/opt/homebrew/anaconda3/bin/python3.12 \
  papers/bidsleep-public-preflight/public_corpus.py \
  /approved/public/bidsleep-1.0.0.zip \
  /approved/public/SHA256SUMS.txt \
  papers/bidsleep-public-preflight/preflight.json \
  papers/bidsleep-public-preflight/public-plan.json \
  /approved/public/raw /approved/public/converted \
  /approved/public/corpus-receipt.json
```

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  papers/bidsleep-public-preflight/test_paper_lstm.py
python3 papers/bidsleep-public-preflight/paper_lstm.py \
  /approved/public/Bidslab40/6/aligned.npz \
  /approved/public/Bidslab40/6/aligned.receipt.json \
  /tmp/bidsleep-paper-lstm-benchmark.json --device mps
```
