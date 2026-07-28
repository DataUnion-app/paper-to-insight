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

The epileptic-seizure HRV candidate is E0. The paper does not publish its
fitted MSPC model or training data, and Brainstem lacks continuous awake
monitoring with specialist-adjudicated video-EEG labels. The supplied
BSD-licensed repository is a different patient-specific EEG+ECG deep-learning
system and is not implementation provenance for the paper.

The ECG hypoglycaemia candidate is E0. The cited paper is a prospective study
protocol, not a completed classifier, and its supplied repository contains
only documents. Current Brainstem contracts also lack raw ECG paired with CGM
reference values.

The atrial-fibrillation CRNN candidate is E0. The actual author source differs
from the supplied repository, has no software license or fitted model, and
splits recording IDs without participant identity. Current Brainstem contracts
also lack its raw expert-labelled ECG input.

The cardiac-arrhythmia CNN-LSTM candidate is E0. Its unlicensed source
concatenates the original train and test sets, upsamples with replacement, and
then creates a random split; it also leaves the claimed PCA commented out.

The sudden-cardiac-death HRV candidate is E0. Its supplied SVM repository
predates and does not implement the paper's CNN, while the paper describes
selecting hyperparameters on its testing set and has no untouched external
validation.

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
