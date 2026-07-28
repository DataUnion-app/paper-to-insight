# Global HRV stress — independently reproducible, runtime blocked

This candidate preserves the method and the blockers separately.

The CC-BY paper is:

- Dahal, Bogue-Jimenez, and Doblas, *Global Stress Detection Framework
  Combining a Reduced Set of HRV Features and Random Forest Model*,
  <https://doi.org/10.3390/s23115220>.

It is not the previously listed *Cross Dataset Analysis for Generalizability
of HRV-Based Stress Detection Models* (DOI `10.3390/s23041807`).

The paper permits an independent implementation of its eight-feature Random
Forest method. The supplied repository at commit
`4d1568c274fddc25de1b2c6f2416a82197a5d603` has no source license, so none of
its code is copied or adapted here.

The source audit also verifies that every subject contributes data to both
training and testing. The reported result therefore does not establish
performance for a new participant. The aggregate Kaggle card says CC0, while
the linked original SWELL dataset currently states CC-BY-NC-SA-4.0; that
license chain needs legal resolution before a distributable or commercial
model is trained from the derivative.

Brainstem resting R-R recordings can support some of the paper's HRV features,
but they do not carry the controlled stress/no-stress protocol labels used by
the paper. A stress label, probability, score, or proxy therefore remains
withheld in both cohort and personal modes.

## Next evidence gate

1. Reimplement the paper method without the unlicensed notebook.
2. Use a dataset with an unambiguous compatible license.
3. Evaluate with whole participants held out and report calibration and
   uncertainty, not only accuracy.
4. Run a protected Brainstem protocol with context labels and a relevant
   device/population.

Until those gates pass, this package belongs in the review queue and not the
DeSciLab catalogue.
