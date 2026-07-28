# In-hospital cardiac-arrest HRV — runtime blocked

The paper and its linked author implementation are correctly identified and
checksum-pinned:

- Lee, Yang, and Ryu, *Real-time machine learning model to predict
  in-hospital cardiac arrest using heart rate variability in ICU*,
  <https://doi.org/10.1038/s41746-023-00960-2>.

The paper is CC BY 4.0, but the linked repository has no software license. Its
training data are not public. The repository contains only a README and a
training script: no dataset, fitted model, selected-feature manifest, or saved
hyperparameters. The script also references an undefined optimization function
and undefined hyperparameter variables before training.

This is not a model for a generally healthy home cohort. Its classification
unit is a five-minute ICU ECG epoch, and its reference standard is a documented
cardiac-arrest event 0.5–24 hours later. Brainstem does not currently collect
that ICU context or outcome label. Signal similarity therefore cannot justify
either a cohort risk result or an owner-facing classification.

## Next evidence gate

1. Obtain a licensed, complete inference package or independently reimplement
   the CC-BY method.
2. Reproduce the selected 33-feature model on licensed, patient-separated ICU
   ECG and event data.
3. Validate calibration prospectively in a matching clinical population.
4. Treat any future clinical deployment as a separately regulated product.

Until then, this candidate belongs in the review queue and not DeSciLab.
