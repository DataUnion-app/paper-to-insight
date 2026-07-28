# Epileptic-seizure HRV anomaly detection — runtime blocked

The paper is correctly identified and checksum-pinned:

- Yamakawa et al., *Wearable Epileptic Seizure Prediction System with
  Machine-Learning-Based Anomaly Detection of Heart Rate Variability*,
  <https://doi.org/10.3390/s20143987>.

The paper is CC BY 4.0 and describes an eight-index, three-minute HRV window
monitored by a six-component multivariate statistical process-control model.
It does not publish the fitted loading matrix, scaling parameters, training
data, or an implementation. Those model parameters came from interictal data
from fourteen refractory-epilepsy patients and a prior study.

The supplied `akaraspt/epilepsy-system` repository is licensed BSD-3-Clause,
but it is not the paper's implementation. It predates the paper, describes a
different patient-specific EEG+ECG deep-learning system, requires the
restricted Epilepsiae dataset, and has no provenance link from the paper.

Brainstem R-R recordings can represent some of the required HRV inputs, but
the paper evaluates continuous awake monitoring in diagnosed epilepsy
patients. Seizure onset and clean interictal periods were adjudicated by
specialists using video-EEG. Current Brainstem recordings do not provide that
population, temporal coverage, or reference standard.

## Next evidence gate

1. Obtain or independently reconstruct the exact fitted MSPC model from
   licensed, participant-separated epilepsy data.
2. Freeze the R-R quality, three-minute feature, scaling, and alert contracts.
3. Validate prospectively against specialist-adjudicated video-EEG in the
   intended population, including false-alert burden in daily life.
4. Treat any future alerting use as a separately regulated clinical product.

Until then, this candidate belongs in the review queue and not DeSciLab.
