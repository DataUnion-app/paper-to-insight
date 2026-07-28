# Cardiac-arrhythmia CNN-LSTM — runtime blocked

The paper-linked repository and source are checksum-pinned:

- Rahman, Rahman, and Haque, *Automated Detection of Cardiac Arrhythmia
  Based on a Hybrid CNN-LSTM Network*,
  <https://doi.org/10.1007/978-981-16-8774-7_32>.

The method classifies raw ECG heartbeat segments into five rhythm classes. The
repository has no software license and publishes no fitted model.

More importantly, the committed evaluation is invalid for promotion. It
concatenates the supplied training and test CSVs, upsamples classes with
replacement, and only then creates a random 90/10 split. Exact duplicates can
therefore occur on both sides, and the original test boundary is discarded.
The source also comments out the PCA that the paper and README claim as part of
the method.

Current Brainstem contracts do not supply the required raw ECG morphology or
expert beat labels. The reported 98–99% accuracy is not accepted as public
reproduction evidence.

## Next evidence gate

1. Independently implement the method or obtain licensed complete source.
2. Split by participant before resampling, feature learning, or augmentation.
3. Reproduce on an untouched external expert-labelled raw-ECG test cohort.
4. Add and calibrate a purpose-bound raw-ECG Brainstem study contract.

Until then, this candidate belongs in the review queue and not DeSciLab.
