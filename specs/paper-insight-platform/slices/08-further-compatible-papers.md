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

The global-HRV stress candidate now pins DOI `10.3390/s23115220`, not
`10.3390/s23041807`, and machine-verifies the paper, source, and aggregate
dataset-card evidence. The CC-BY method may be independently implemented, but
the supplied code is unlicensed, its derivative data license conflicts with the
linked original SWELL terms, and every subject appears in training. Runtime
remains disabled pending an unambiguously licensed participant-held-out
reproduction and a matching labelled Brainstem protocol.

The cardiovascular-event source audit is also E0: its fitted scaler and paired
test labels are absent, its prediction module is empty, and its metric
implementation is incorrect. Do not load or publish its committed model.

The in-hospital cardiac-arrest source is likewise E0. Its paper-linked
repository has no license, public data, fitted model, selected-feature manifest,
or runnable optimizer; more importantly, its ICU event contract is incompatible
with current Brainstem home data.

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
