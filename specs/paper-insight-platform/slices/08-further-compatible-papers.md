# 08 — Further compatible papers

Status: active (2026-07-29)

## Goal

Add papers only through the same candidate and dual-scope gates.

## Order

1. **HRV stress:** requires prospective context/stress labels and a
   held-out-participant/device micro-study before classification.
2. **Sleep staging:** reproduce on public PSG labels, then calibrate the
   Brainstem full-night signal/device before personal labels.
3. **Cardiovascular-event methods:** dedicated protocol and representative
   labelled population.
4. **Epilepsy, hypoglycaemia, AF/arrhythmia:** blocked until the required
   EEG/CGM/raw-ECG signals and labels exist.

An incompatible paper remains a useful public compatibility report; it is not
forced into the catalogue.

The supplied OIRL repository maps to DOI `10.3390/s23115220`, not
`10.3390/s23041807`. It has no source license and cannot be copied. A lawful next
attempt may independently implement the CC-BY paper method, but only after the
WESAD/SWELL input license and immutable participant mapping are proven. Use
participant-held-out evaluation rather than the paper's per-subject 70:30 split.

The cardiovascular-event source audit is also E0: its fitted scaler and paired
test labels are absent, its prediction module is empty, and its metric
implementation is incorrect. Do not load or publish its committed model.

## Per-paper checks

- license and immutable public source/data;
- participant-separated reproduction and leakage tests;
- exact Brainstem signal/window/preprocessing compatibility;
- explicit population/device/reference-standard mismatch;
- bounded cohort privacy and owner-only personal input;
- paper-specific classification ontology and closed abstention set;
- scope-specific human approval.

## Refresh and subscriptions

Do not add automatic personal reruns in this goal. First persist compatibility
and immutable history. A later subscription slice may react to a new compatible
record only after payment, recurring authorization, rate/cost bounds, reference
versioning, and notification ownership are decided.

## Done when

Each added paper has a public candidate and either a justified protected
dual-mode release or an explicit, machine-readable block reason.
