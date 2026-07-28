# Candidate queue

Only a reviewed candidate with an enabled runtime mode belongs in DeSciLab.
Signal similarity is not approval.

| Candidate | Current state | Blocking evidence | Next gate |
| --- | --- | --- | --- |
| [Resting HRV methods](resting-hrv-methods/) | E2 methods-only; local protected cohort and personal proofs complete | No disease classification; production approval and deployment absent | Independent scientific/privacy/security approval |
| [Apnea-ECG heart rate](apnea-ecg-heart-rate/) | E0; runtime disabled | Record-level evaluation, overlapping recordings, no Brainstem respiratory labels | Participant-separated public reproduction, then matching protected study |
| [Cardiovascular-event HRV](cardiovascular-event-hrv/) | E0; runtime disabled | Missing scaler/test contract, incorrect metrics, 64-feature and population mismatch | Correct public reproduction, then hypertensive 55+ outcome study |
| [Global HRV stress](stress-hrv-global/) | E0; runtime disabled | Source license absent; derivative data license conflicts with original; prior list named the wrong paper; every subject appears in training | Independent CC-BY method implementation on unambiguously licensed data with participant-held-out evaluation |
| [In-hospital cardiac arrest HRV](in-hospital-cardiac-arrest-hrv/) | E0; runtime disabled | Source license, data, model, feature manifest, and runnable training contract absent; ICU population/outcome unavailable in Brainstem | Licensed complete reproduction plus matching prospective ICU study |
| [Epileptic-seizure HRV anomaly detection](epilepsy-hrv-anomaly/) | E0; runtime disabled | Paper model/data unavailable; continuous video-EEG-labelled epilepsy context absent; supplied source is a different EEG+ECG system | Exact licensed reproduction and prospective specialist-adjudicated epilepsy study |
| [ECG hypoglycaemia](ecg-hypoglycaemia/) | E0; runtime disabled | Cited article is a prospective protocol; repository contains no executable model; raw ECG and paired CGM labels absent | Completed result paper, participant-separated reproduction, and matching protected study |
| Raw-ECG atrial fibrillation | Reference-only | Source license absent and input is raw single-lead ECG, not the current R-R contract | Licensed source and raw-waveform Brainstem contract |
| Raw-ECG arrhythmia | Reference-only | Source license absent and input is raw waveform | Licensed source and raw-waveform Brainstem contract |
| Sudden cardiac death SVM | Reference-only | Source license absent and repository contains a PDF rather than an executable implementation | Exact licensed implementation and matched outcome data |
| HRV sleep staging/pressure | Reference-only | Source license absent; original sleep data are restricted; repository calls itself a simple framework | Licensed implementation and participant-separated PSG-labelled reproduction |

Reference-only entries are triage findings, not validated candidates. A community
contributor may replace one with a checksum-pinned candidate package after
closing every listed gate.
