# Global HRV stress — reference-only

This source cannot yet become a candidate package.

The supplied repository at commit
`4d1568c274fddc25de1b2c6f2416a82197a5d603` contains a README and one
notebook but no source license. Its README checksum is
`65b82bcadcf1d58e814fffe01b07ac6f66dd9a4a453adcb82e4f6230071253a0`;
the notebook checksum is
`569a29e902699fe58f8b0d419c4ddb64fb9663e193e628b7e2a6845c84139305`.
No source code is copied here.

The repository corresponds to:

- Dahal, Bogue-Jimenez, and Doblas, *Global Stress Detection Framework
  Combining a Reduced Set of HRV Features and Random Forest Model*,
  <https://doi.org/10.3390/s23115220>.

It does **not** correspond to the previously listed
*Cross Dataset Analysis for Generalizability of HRV-Based Stress Detection
Models* (<https://doi.org/10.3390/s23041807>).

The paper is CC BY 4.0, so its described method may be independently
reimplemented with attribution. The source notebook may not be copied or adapted
without a license. The paper's per-subject 70:30 split also puts data from every
subject into global training and individual testing; it is not evidence for a
new participant. Brainstem has no stress labels or matching activity/context
protocol.

## Block reasons

```json
[
  "license_unverified",
  "participant_split_leakage",
  "reference_labels_missing",
  "population_or_device_unvalidated"
]
```

The next lawful experiment is an independent implementation of the eight
published HRV features and Random Forest on explicitly licensed public data,
using participant-held-out and cross-dataset evaluation. Any Brainstem stress
classification must still abstain until a protected labelled protocol validates
the device, population, context, calibration, and uncertainty.
