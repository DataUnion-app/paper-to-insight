# Atrial-fibrillation CRNN — runtime blocked

The actual paper-linked implementation is
`yruffiner/ecg-classification`, not the supplied `awerdich/physionet`
repository:

- Zihlmann, Perekrestenko, and Tschannen, *Convolutional Recurrent Neural
  Networks for Electrocardiogram Classification*,
  <https://doi.org/10.48550/arXiv.1710.06122>.

The paper and source classify 9–60 second, 300 Hz, single-lead raw ECG into
normal rhythm, atrial fibrillation, other rhythm, or noisy. The author
repository has no software license, so its code is audit evidence only and is
not copied or adapted here. It also contains no fitted model, and the hidden
challenge test set needed to reproduce the reported score is unavailable.

The committed cross-validation split stratifies recording IDs. It has no
participant identity with which to prove participant-separated validation.
Current Brainstem C2D contracts expose R-R-derived records rather than the
paper's raw ECG morphology, and they have no expert rhythm labels.

## Next evidence gate

1. Obtain a licensed implementation or independently reimplement the method.
2. Reproduce it on licensed raw ECG with participant-separated splits and an
   external expert-labelled test set.
3. Add a calibrated purpose-bound raw-ECG Brainstem contract.
4. Validate any owner-facing rhythm result as a separately regulated clinical
   product.

Until then, this candidate belongs in the review queue and not DeSciLab.
