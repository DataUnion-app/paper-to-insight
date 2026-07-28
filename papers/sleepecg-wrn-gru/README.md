# SleepECG WRN-GRU external reproduction

This package evaluates SleepECG 0.5.9's shipped `wrn-gru-mesa` classifier
without retraining it. The classifier predicts `NREM`, `REM`, or `WAKE` for
each 30-second epoch from beat-to-beat timing, recording start time, age, and
binary gender.

It is a separate candidate from
`brainstem.sleep-stage-hrv-lstm`: SleepECG has a different three-class
ontology and is not an implementation of Radha et al.'s four-class LSTM.

## Evidence

- Software paper: <https://doi.org/10.21105/joss.05411>
- Exact source/model release: SleepECG 0.5.9, BSD-3-Clause
- Shipped model: trained on 1,971 MESA nights; the authors report testing on
  1,000 SHHS nights with accuracy 0.75 and Cohen's kappa 0.54
- Independent public check: all 18 MIT-BIH Polysomnographic Database records,
  representing 16 participants

The public check uses the database's reviewed heartbeat annotations rather than
rerunning a detector over the 632 MB waveform bundle. It verifies every
download against PhysioNet's checksum manifest.

## Result

The exact model ran, but transfer was poor:

- accuracy: 0.573618
- Cohen's kappa: 0.123670
- REM F1: 0.199796
- participant accuracy range: 0.291465–0.690476

This is an accepted **E1 public reproduction**, not an accepted health
classifier. It is intentionally unavailable in DeSciLab.

## Reproduce

Use an isolated Python 3.11 environment:

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python "sleepecg[full]==0.5.9"
.venv/bin/python reproduce.py --verify --data-dir /tmp/sleepecg-slpdb
```

The script downloads only public `.hea`, `.ecg`, and `.st` files. It checks the
SleepECG version, embedded model digest, dataset manifest, every input file,
and the aggregate receipt before succeeding.

## Why Brainstem remains blocked

- External transfer performance is insufficient, especially for REM.
- SLPDB has only 16 all-male participants evaluated for apnea or CPAP; it is
  not representative of Brainstem users.
- The model requires age and binary gender as inputs.
- Brainstem full-night intervals have not been calibrated against this input
  pipeline.
- Brainstem recordings do not include independently scored PSG stages.

No cohort or personal classification should be published until a held-out,
participant-separated Brainstem-device-versus-PSG study reaches a
pre-registered threshold and passes scientific, privacy, and security review.

