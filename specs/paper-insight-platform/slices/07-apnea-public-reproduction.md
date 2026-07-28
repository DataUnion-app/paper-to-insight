# 07 — Apnea-ECG public reproduction

## Goal

Demonstrate that a disease-relevant off-the-shelf paper can be reproduced without
overstating Brainstem transferability.

## Build

- Freeze a license-compatible Apnea-ECG implementation and PhysioNet dataset
  version/checksum.
- Reproduce its declared metric using a participant-separated split.
- Record exact preprocessing, label/reference standard, population, prevalence,
  calibration, leakage controls, and abstention behavior.
- Propose a full-night R-R contract and document Brainstem device/population
  mismatches.

## Product gate

The public package may reach `E1_public_reproduced`. Generated Brainstem contract
tests may support `E2_brainstem_compatible_exploratory`, but all apnea
classification must abstain. A personal or cohort apnea label requires relevant
held-out Brainstem-device expert labels, calibration, OOD thresholds, and
scientific/privacy/security approval at `E3`.

## Done when

The public reproduction is deterministic and the DeSciLab public example clearly
distinguishes reproduced paper performance from unavailable Brainstem validation.

