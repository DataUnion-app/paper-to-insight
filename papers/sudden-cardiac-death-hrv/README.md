# Sudden-cardiac-death HRV CNN — runtime blocked

The cited paper is correctly identified and checksum-pinned:

- Nindrea et al., *Accurate Prediction of Sudden Cardiac Death Based on Heart
  Rate Variability Analysis Using Convolutional Neural Network*,
  <https://doi.org/10.3390/medicina59081394>.

The supplied 2019 repository is not the 2023 paper's implementation. It is
titled as an SVM project and contains only a README and an unlicensed PDF,
whereas the paper describes a 1D-CNN Wavenet. No code, fitted model, split
manifest, or reproducibility receipt is available.

The paper uses six five-minute segments from each of 115 subjects across five
diagnostic groups. The SCD recordings come from the thirty minutes before
ventricular fibrillation. It reports an 80/20 distribution but also says grid
search selected hyperparameters by performance on the testing set, so there is
no untouched test result. Later segment evaluation reuses the same subject
groups.

Brainstem five-minute R-R recordings can express the eight linear HRV features,
but the cohort has no matched diagnostic groups or ventricular-fibrillation
event timing. Signal shape alone cannot support an SCD classification.

## Next evidence gate

1. Independently implement the CC-BY method from a frozen feature contract.
2. Reproduce on participant-separated data with an untouched external test set.
3. Validate prospectively in a relevant clinical population with adjudicated
   event timing.
4. Treat any owner-facing risk result as a separately regulated clinical
   product.

Until then, this candidate belongs in the review queue and not DeSciLab.
