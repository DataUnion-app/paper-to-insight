# Sleep-stage HRV LSTM — promising, runtime blocked

The paper is correctly identified and checksum-pinned:

- Radha et al., *Sleep stage classification from heart-rate variability using
  long short-term memory neural networks*,
  <https://doi.org/10.1038/s41598-019-49703-y>.

This is the strongest signal-shape match in the supplied list. It uses 132 HRV
features from full-night ECG, a four-class sleep ontology, and participant-level
four-fold evaluation across 292 people and 584 nights. Brainstem's full-night
beat-to-beat recordings could support a purpose-built compatibility study.

It is not ready for classification today. The paper publishes no code, fitted
model, or complete executable feature contract, and its SIESTA PSG-labelled
data are not freely available. The supplied MATLAB repository is not linked by
the paper, has no license, uses a different six-stage ontology, calls itself a
simple framework, and includes unlicensed sample matrices that are not used
here.

Brainstem also needs participant-separated PSG-labelled calibration for its
specific device and preprocessing. Until that exists, no sleep-stage label or
health interpretation may be released.

## Next evidence gate

1. Independently reimplement the CC-BY 132-feature method using only licensed
   public data and freeze every window/feature parameter.
2. Reproduce with participant-level folds on a public PSG-labelled dataset.
3. Run a protected Brainstem-versus-PSG calibration study across relevant ages,
   devices, and sleep conditions.
4. Review a descriptive nightly-output mode separately from any clinical use.

Until then, this candidate belongs in the review queue and not DeSciLab.
