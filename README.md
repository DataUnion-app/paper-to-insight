# Paper to Insight

Turn a scientific paper into a reproducible, reviewable candidate for a
privacy-preserving cohort and personal Insight.

This repository is the public workbench. It contains no participant data,
credentials, approval keys, or connection to Brainstem infrastructure. Passing
its checks means **candidate**, not approved or clinically valid.

## Try it

```bash
python3 scripts/validate_candidate.py examples/minimal-methods/candidate.json
python3 -m unittest tests.test_validate_e3_receipt -v
python3 -m unittest discover -s tests -v
python3 scripts/validate_candidate.py papers/resting-hrv-methods/candidate.json
python3 papers/resting-hrv-methods/test_algorithm.py -v
python3 papers/resting-hrv-methods/reproduce.py --verify
python3 scripts/validate_candidate.py papers/resting-rr-sample-entropy/candidate.json
python3 papers/resting-rr-sample-entropy/test_algorithm.py -v
python3 papers/resting-rr-sample-entropy/reproduce.py --verify
python3 papers/apnea-ecg-heart-rate/test_source_audit.py -v
python3 papers/apnea-ecg-heart-rate/source-audit.py --verify
python3 papers/apnea-ecg-heart-rate/test_external_validate.py -v
python3 papers/apnea-ecg-heart-rate/reproduce.py --verify --cache "$PUBLIC_CACHE"
python3 papers/apnea-ecg-heart-rate/external_validate.py --verify --cache "$PUBLIC_CACHE"
python3 scripts/validate_candidate.py papers/apnea-ecg-heart-rate/candidate.json
python3 papers/cardiovascular-event-hrv/test_source_audit.py -v
python3 papers/cardiovascular-event-hrv/source-audit.py --verify
python3 scripts/validate_candidate.py papers/cardiovascular-event-hrv/candidate.json
python3 papers/stress-hrv-global/test_source_audit.py -v
python3 papers/stress-hrv-global/source-audit.py --verify
python3 scripts/validate_candidate.py papers/stress-hrv-global/candidate.json
python3 papers/in-hospital-cardiac-arrest-hrv/test_source_audit.py -v
python3 papers/in-hospital-cardiac-arrest-hrv/source-audit.py --verify
python3 scripts/validate_candidate.py papers/in-hospital-cardiac-arrest-hrv/candidate.json
python3 papers/epilepsy-hrv-anomaly/test_source_audit.py -v
python3 papers/epilepsy-hrv-anomaly/source-audit.py --verify
python3 scripts/validate_candidate.py papers/epilepsy-hrv-anomaly/candidate.json
python3 papers/ecg-hypoglycaemia/test_source_audit.py -v
python3 papers/ecg-hypoglycaemia/source-audit.py --verify
python3 scripts/validate_candidate.py papers/ecg-hypoglycaemia/candidate.json
python3 papers/atrial-fibrillation-crnn/test_source_audit.py -v
python3 papers/atrial-fibrillation-crnn/source-audit.py --verify
python3 scripts/validate_candidate.py papers/atrial-fibrillation-crnn/candidate.json
python3 papers/cardiac-arrhythmia-cnn-lstm/test_source_audit.py -v
python3 papers/cardiac-arrhythmia-cnn-lstm/source-audit.py --verify
python3 scripts/validate_candidate.py papers/cardiac-arrhythmia-cnn-lstm/candidate.json
python3 papers/sudden-cardiac-death-hrv/test_source_audit.py -v
python3 papers/sudden-cardiac-death-hrv/source-audit.py --verify
python3 scripts/validate_candidate.py papers/sudden-cardiac-death-hrv/candidate.json
python3 papers/sleep-stage-hrv-lstm/test_source_audit.py -v
python3 papers/sleep-stage-hrv-lstm/source-audit.py --verify
python3 scripts/validate_candidate.py papers/sleep-stage-hrv-lstm/candidate.json
python3 papers/sleepecg-wrn-gru/test_source_audit.py -v
python3 papers/sleepecg-wrn-gru/source-audit.py --verify
python3 scripts/validate_candidate.py papers/sleepecg-wrn-gru/candidate.json
```

The bundled Codex-compatible skill lives at
`skills/turn-paper-into-insight/SKILL.md`. Fork this repository, give an agent a
paper, DOI, source repository, or public dataset, and ask it to use
`$turn-paper-into-insight`.

Protected reviewers can validate an E3 evidence receipt with
`scripts/validate_e3_receipt.py`. The receipt contains no participant rows and
rejects self-report-only labels, participant leakage, sparse evaluation,
missing calibration/abstention, or clinical claims.

## Handoff

```text
paper + public data
  -> deterministic candidate package
  -> protected scientific/privacy/security review
  -> immutable approved algorithm
  -> purpose-bound private compute
```

A candidate proposes a disclosure-protected cohort analysis and a personal
analysis using only the authenticated participant's compatible records plus a
frozen aggregate cohort reference. Forks cannot approve, publish, or access
either mode.

See `specs/paper-insight-platform/README.md` for the implementation plan.
See `papers/README.md` for the evidence-gated candidate queue.

The first real candidate is `papers/resting-hrv-methods`. It implements selected
descriptive HRV measures in both cohort and owner-only personal modes and pins a
small public PhysioNet reproduction. It intentionally has no disease label.

`papers/resting-rr-sample-entropy` is the second runtime-eligible methods
candidate. It reproduces the PhysioNet sample-entropy method on pinned public
Fantasia intervals, then exposes one disclosure-protected cohort metric and an
owner-only comparison with an immutable aggregate reference. It also
intentionally has no disease label or clinical interpretation.

`papers/apnea-ecg-heart-rate` demonstrates an evidence-only negative path. The
current official package misses the historical Apnea-ECG headline, and its
precommitted UCDDB extension has low sensitivity. It remains E0 with both
runtime modes disabled, while DeSciLab may present the exact public evidence and
limitations without an execution or personal-result path.

`papers/cardiovascular-event-hrv` is also E0 and disabled. Its source is licensed
and paper-associated, but its scaler/test contract is incomplete and its
published metric calculations are incorrect.

`papers/stress-hrv-global` pins the corrected CC-BY paper and proves that an
independent implementation is lawful. It remains E0 and disabled because the
supplied code is unlicensed, every subject appears in training, the source-data
license chain conflicts, and Brainstem has no matching stress labels.

`papers/in-hospital-cardiac-arrest-hrv` is E0 and disabled. The paper-linked
source is unlicensed and incomplete, its data are private, and its ICU
event-prediction contract is incompatible with current Brainstem home records.

`papers/epilepsy-hrv-anomaly` is E0 and disabled. The paper's fitted model and
training data are unavailable, current Brainstem records lack continuous
video-EEG-labelled epilepsy context, and the supplied repository implements a
different EEG+ECG system.

`papers/ecg-hypoglycaemia` is E0 and disabled. The cited article is a
prospective protocol rather than a completed classifier study; its supplied
repository contains documentation but no executable model, and Brainstem lacks
the paired raw-ECG/CGM contract.

`papers/atrial-fibrillation-crnn` is E0 and disabled. The actual paper-linked
source was identified, but it is unlicensed, has no fitted model or
participant-separated validation evidence, and requires raw expert-labelled
ECG that is outside the current Brainstem contract.

`papers/cardiac-arrhythmia-cnn-lstm` is E0 and disabled. Its unlicensed source
combines the original train and test data and upsamples with replacement before
creating a new split, so the reported evaluation is not accepted.

`papers/sudden-cardiac-death-hrv` is E0 and disabled. The supplied SVM
repository is unrelated to the paper's CNN, and the paper uses its testing set
for hyperparameter selection without publishing an untouched external result.

`papers/sleep-stage-hrv-lstm` is E0 and disabled, but is the best next
Brainstem study candidate. The paper uses participant-level evaluation and
full-night HRV; promotion still needs a licensed public reproduction and
Brainstem-versus-PSG calibration.

`papers/sleepecg-wrn-gru` is a separate E1 negative result. The exact
BSD-licensed shipped model runs on an independent public PSG dataset, but its
external accuracy, kappa, and REM performance are insufficient. It remains
unavailable in DeSciLab pending a held-out Brainstem-device-versus-PSG study.

## License

Original repository code is Apache-2.0. Paper implementations, models, and
datasets retain their own licenses and must declare them in every candidate.
