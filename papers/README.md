# Candidate queue

Only a reviewed candidate with an enabled runtime mode belongs in DeSciLab.
Signal similarity is not approval.

| Candidate | Current state | Blocking evidence | Next gate |
| --- | --- | --- | --- |
| [Resting HRV methods](resting-hrv-methods/) | E2 methods-only; local protected cohort and personal proofs complete | No disease classification; production approval and deployment absent | Independent scientific/privacy/security approval |
| [Apnea-ECG heart rate](apnea-ecg-heart-rate/) | E0; runtime disabled | Record-level evaluation, overlapping recordings, no Brainstem respiratory labels | Participant-separated public reproduction, then matching protected study |
| [Cardiovascular-event HRV](cardiovascular-event-hrv/) | E0; runtime disabled | Missing scaler/test contract, incorrect metrics, 64-feature and population mismatch | Correct public reproduction, then hypertensive 55+ outcome study |
| [Global HRV stress](stress-hrv-global/) | Reference-only | Source license absent; prior list named the wrong paper; subject data appear in both train and test | Independent CC-BY method implementation on licensed data with participant-held-out evaluation |
| In-hospital cardiac arrest HRV | Reference-only | Source license absent; ICU population/outcome unavailable in Brainstem | License or independent implementation plus matching prospective ICU study |
| EEG/ECG seizure prediction | Reference-only | Supplied source predates and does not establish identity with the named paper; patient-specific EEG/ECG labels required | Establish exact paper/source/data lineage and signal contract |
| ECG hypoglycaemia | Reference-only | Repository contains paper artifacts but no executable implementation; raw ECG and paired glucose labels required | Independent reproduction on licensed ECG+CGM data |
| Raw-ECG atrial fibrillation | Reference-only | Source license absent and input is raw single-lead ECG, not the current R-R contract | Licensed source and raw-waveform Brainstem contract |
| Raw-ECG arrhythmia | Reference-only | Source license absent and input is raw waveform | Licensed source and raw-waveform Brainstem contract |
| Sudden cardiac death SVM | Reference-only | Source license absent and repository contains a PDF rather than an executable implementation | Exact licensed implementation and matched outcome data |
| HRV sleep staging/pressure | Reference-only | Source license absent; original sleep data are restricted; repository calls itself a simple framework | Licensed implementation and participant-separated PSG-labelled reproduction |

Reference-only entries are triage findings, not validated candidates. A community
contributor may replace one with a checksum-pinned candidate package after
closing every listed gate.
