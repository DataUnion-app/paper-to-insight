# 02 — Resting-HRV reproduction

Status: complete (2026-07-28)

## Goal

Create the first complete dual-mode candidate using a methods-only Insight that
fits existing resting R-R data and makes no disease claim.

## Method

Implement one shared pure calculation owner for:

- input quality/artifact sensitivity;
- raw and corrected SDNN and RMSSD;
- Poincaré SD1/SD2;
- entropy only after its parameters and fixture tolerance are fixed.

Cohort and personal wrappers consume the same calculations. Personal comparison
uses a frozen public/generated reference. `paperClassification.decision` is
`not_applicable`.

## Inputs

- Cohort: exact generated participants, at least 20, compatible resting R-R only.
- Personal: one generated participant's compatible resting R-R records only.
- No wallet, stable participant ID, device ID, date, filename, or raw cohort row
  in a reference/result.

## Verification

- Accepted public/reference calculations match declared tolerances.
- Raw/corrected fixtures expose artifact sensitivity.
- Low-quality, incompatible, or insufficient coverage inputs abstain.
- Cohort 19 abstains; cohort 20 completes; every visible cell meets its floor.
- Repeated runs are byte-identical and outputs are bounded.

## Done when

The public candidate, receipt, cohort fixture, personal fixture, reference, and
tests validate with one command.

Entropy is deliberately deferred because the candidate has no reviewed parameter
set or public tolerance fixture for it. The accepted slice implements SDNN,
RMSSD, SD1, and SD2.
