# Apnea-ECG heart-rate candidate

This is a blocked source audit, not a runnable Insight.

The candidate is structurally interesting because the public implementation uses
full-night beat-to-beat timing and minute labels. Brainstem can provide
beat-to-beat timing, but it does not currently provide the paper's expert
respiratory labels or a validated device/population transfer.

The inspected source is an independent personal project, not the paper authors'
reference implementation. Its cross-validation splits recording names. The
source training index also contains `c05` and `c06`; PhysioNet documents those as
overlapping versions of the same original recording. The source has no
participant identifier with which to keep every night from one person in one
split.

Therefore:

- public reproduction is not accepted;
- cohort and personal runtime modes are not proposed;
- the paper's apnea/non-apnea classification is withheld;
- this package must not appear in the DeSciLab catalogue.

Promotion requires a licensed, participant-mapped public reproduction with
predeclared metrics, followed by protected Brainstem device/population
validation against an appropriate respiratory reference standard. It would
remain non-clinical unless a separate regulated validation supports more.

## Verify

```bash
python3 papers/apnea-ecg-heart-rate/test_source_audit.py -v
python3 papers/apnea-ecg-heart-rate/source-audit.py --verify
python3 scripts/validate_candidate.py papers/apnea-ecg-heart-rate/candidate.json
```

Primary references:

- Penzel et al., *The Apnea-ECG Database*:
  <https://doi.org/10.1109/CIC.2000.898505>
- PhysioNet Apnea-ECG Database 1.0.0:
  <https://physionet.org/content/apnea-ecg/1.0.0/>
- Inspected independent implementation:
  <https://github.com/ChiQiao/Apnea-ECG/tree/aaaf046741696e1c6267f707853e6e79b31c9ae5>
