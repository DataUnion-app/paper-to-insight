# Cardiovascular-event HRV candidate

This is a blocked source audit, not a runnable Insight.

The inspected repository is associated with the paper and is MIT licensed. It
contains models and synthetic HRV tables, but not a complete reproducible
inference contract:

- the model expects 64 features produced with Kubios Premium 3.4.1;
- the fitted scaler is not serialized;
- the production prediction module is empty;
- the real test labels needed to pair with the committed scaled test features
  are not included;
- the evaluator calculates ROC AUC from thresholded labels rather than
  probabilities;
- its confusion-matrix arguments make the reported "sensitivity" negative
  predictive value and the reported "specificity" precision.

Brainstem also has neither the paper's hypertensive 55+ population restriction
nor the adjudicated 12-month cardiovascular/cerebrovascular outcome labels.
Signal overlap alone cannot support the paper's classification.

Therefore both runtime modes and the paper classification remain withheld, and
this package must not appear in the DeSciLab catalogue. Promotion requires a
complete participant-level public reproduction, an open exact feature contract,
a frozen scaler, corrected metrics, and protected validation in a matching
Brainstem study population.

## Verify

```bash
python3 papers/cardiovascular-event-hrv/test_source_audit.py -v
python3 papers/cardiovascular-event-hrv/source-audit.py --verify
python3 scripts/validate_candidate.py papers/cardiovascular-event-hrv/candidate.json
```

Primary references:

- Goretti et al., *Deep Learning for Risky Cardiovascular and Cerebrovascular
  Event Prediction in Hypertensive Patients*:
  <https://doi.org/10.3390/app15031178>
- PhysioNet SHAREE Database 1.0.0:
  <https://physionet.org/content/shareedb/1.0.0/>
- Inspected source:
  <https://github.com/alexsalman/Heart-Rate-Variability/tree/acda0446d9996314005a7d20492369d5212f4ac5>
