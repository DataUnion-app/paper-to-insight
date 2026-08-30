# Candidate queue

Only a reviewed candidate with an enabled runtime mode belongs in DeSciLab.
Signal similarity is not approval.

| Candidate | Current state | Blocking evidence | Next gate |
| --- | --- | --- | --- |
| [Resting HRV methods](resting-hrv-methods/) | E2 methods-only; local protected cohort and personal proofs complete | No disease classification; production approval and deployment absent | Independent scientific/privacy/security approval |
| [Resting R-R sample entropy](resting-rr-sample-entropy/) | E2 methods-only; local protected cohort and personal proofs complete | Descriptive complexity metric only; production approval and deployment absent | Independent scientific/privacy/security approval |
| [Sleep measure reliability](sleep-measure-reliability/) | E0 generated teaching candidate; runtime disabled | Generated values only; no Brainstem cohort reference or device validation | Governed protected cohort run and independent scientific/privacy/security review |
| [Apnea-ECG heart rate](apnea-ecg-heart-rate/) | E0; runtime disabled | Record-level evaluation, overlapping recordings, no Brainstem respiratory labels | Participant-separated public reproduction, then matching protected study |
| [Cardiovascular-event HRV](cardiovascular-event-hrv/) | E0; runtime disabled | Missing scaler/test contract, incorrect metrics, 64-feature and population mismatch | Correct public reproduction, then hypertensive 55+ outcome study |
| [Global HRV stress](stress-hrv-global/) | E0; runtime disabled | Source license absent; derivative data license conflicts with original; prior list named the wrong paper; every subject appears in training | Independent CC-BY method implementation on unambiguously licensed data with participant-held-out evaluation |
| [In-hospital cardiac arrest HRV](in-hospital-cardiac-arrest-hrv/) | E0; runtime disabled | Source license, data, model, feature manifest, and runnable training contract absent; ICU population/outcome unavailable in Brainstem | Licensed complete reproduction plus matching prospective ICU study |
| [Epileptic-seizure HRV anomaly detection](epilepsy-hrv-anomaly/) | E0; runtime disabled | Paper model/data unavailable; continuous video-EEG-labelled epilepsy context absent; supplied source is a different EEG+ECG system | Exact licensed reproduction and prospective specialist-adjudicated epilepsy study |
| [ECG hypoglycaemia](ecg-hypoglycaemia/) | E0; runtime disabled | Cited article is a prospective protocol; repository contains no executable model; raw ECG and paired CGM labels absent | Completed result paper, participant-separated reproduction, and matching protected study |
| [Raw-ECG atrial fibrillation CRNN](atrial-fibrillation-crnn/) | E0; runtime disabled | Actual paper source is unlicensed; no fitted model or participant-separated split; raw expert-labelled ECG absent | Licensed reproduction on external participant-separated ECG, then a calibrated raw-waveform Brainstem contract |
| [Raw-ECG cardiac arrhythmia CNN-LSTM](cardiac-arrhythmia-cnn-lstm/) | E0; runtime disabled | Source unlicensed; original train/test boundary discarded; duplicate leakage after pre-split upsampling; claimed PCA disabled | Leakage-free participant-separated external reproduction plus a calibrated raw-waveform Brainstem contract |
| [Sudden cardiac death HRV CNN](sudden-cardiac-death-hrv/) | E0; runtime disabled | Supplied SVM repository is unrelated and document-only; paper selects on its testing set; matched diagnostic/event labels absent | Independent participant-separated reproduction with untouched external clinical validation |
| [HRV sleep-stage LSTM](sleep-stage-hrv-lstm/) | E0; runtime disabled; highest-priority follow-up | Paper model/data unavailable; supplied unlicensed framework uses a different ontology; Brainstem-versus-PSG calibration absent | Independent public reproduction, then protected participant-separated PSG calibration |
| [SleepECG WRN-GRU](sleepecg-wrn-gru/) | E1 public reproduction; runtime disabled | Independent SLPDB result has accuracy 0.573618, kappa 0.123670, and REM F1 0.199796; population and Brainstem-device calibration absent | Pre-registered held-out Brainstem-device-versus-PSG validation |

Every entry from the supplied list now has a checksum-pinned candidate package.
Resting HRV and resting R-R sample entropy have paired local runtime modes.
SleepECG demonstrates that a licensed off-the-shelf model can be reproduced yet
still fail the runtime gate; contributors can advance any package only by
closing its listed evidence gates.
