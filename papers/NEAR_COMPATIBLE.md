# Near-compatible Brainstem methods

This is the review queue for methods that are scientifically interesting but do **not** yet satisfy the Brainstem input, protocol, evidence, or claim contract. It is not an executable registry and nothing here is approved for participant data, publication, or deployment.

## Sleep staging from heart rate and movement

- **Primary lead:** [BIDSleep](https://physionet.org/content/bidsleep-dataset/1.0.0/), 253 nights from 47 adults with Apple Watch heart rate/accelerometry aligned to Dreem EEG labels.
- **What already fits:** Brainstem can collect full-night R-R/heart-rate and movement-like payloads.
- **Exact delta:** versioned, timestamp-aligned XYZ acceleration with units/sample rate/time basis; trusted capture-time provenance; licensed model or independent reproduction; participant-held-out Brainstem-versus-EEG calibration.
- **Potential study:** paired Brainstem and PSG/Dreem validation with participant-level splits.
- **Do not claim yet:** sleep stage, sleep quality, sleep disorder, or clinical screening.

## Six-rate resonance response

- **Primary lead:** [Practical resonance-frequency assessment guide](https://pmc.ncbi.nlm.nih.gov/articles/PMC7578229/) and a [7.0-to-4.5 breaths/minute protocol](https://pmc.ncbi.nlm.nih.gov/articles/PMC12081530/).
- **What already fits:** both apps can run paced breathing; current local resonance sessions use 7.0, 6.5, 6.0, 5.5, 5.0, and 4.5 cycles/minute.
- **Exact delta:** upload the complete six-rate session under one protocol version; freeze one cross-platform response rule; retain trial order, phase timing, adherence, and artifact evidence; add respiration/phase synchrony or explicitly accept its absence.
- **Potential study:** repeatability of the strongest response across sessions and devices.
- **Do not claim yet:** optimal therapeutic frequency, autonomic diagnosis, or treatment recommendation.

## Guided-breathing response

- **What already fits:** Android uploads pace, phase timings, average heart rate, lnLF, and RSA-like metrics with raw R-R.
- **Exact delta:** explicit `exerciseSubtype`; common iOS/Android protocol version; canonical server-side calculation; phase/adherence contract; historical-record disambiguation.
- **Potential study:** within-person descriptive response across matched breathing protocols.
- **Do not claim yet:** stress reduction, treatment effect, or clinical autonomic status.

## Active-stand response

- **Primary lead:** [Active stand practical guide](https://pubmed.ncbi.nlm.nih.gov/31076939/).
- **What already fits:** posture recordings contain R-R/heart-rate and app-guided rest/stand phases.
- **Exact delta:** explicit phase markers and timing; aligned iOS/Android protocol; canonical server calculation; device/protocol provenance. Clinical interpretation additionally needs continuous beat-to-beat blood pressure, which Brainstem does not collect.
- **Potential study:** descriptive heart-rate rise and recovery repeatability.
- **Do not claim yet:** orthostatic hypotension, POTS, diagnosis, or clinical active-stand result.

## NightSignal disease-labelled use

- **Primary lead:** [Mishra et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC9020268/) and the [Apache-2.0 implementation](https://github.com/StanfordBioinformatics/wearable-infection).
- **What already fits:** full-night R-R permits a compact nightly sleeping-rate summary and personal running baseline.
- **Exact delta:** paired symptom and adjudicated diagnostic-test dates; prospective protocol; population/device calibration; prespecified sensitivity/specificity evaluation.
- **Potential study:** association between descriptive baseline departures and separately collected outcomes.
- **Do not claim yet:** infection, COVID-19, illness alert, screening, or risk. The runnable Brainstem translation remains descriptive only.

## Sleep-apnea methods

- **What already fits:** some full-night R-R/heart-rate and occasional ECG are structurally related to published inputs.
- **Exact delta:** PSG respiratory/apnea labels; exact ECG/R-R provenance and sampling; participant-held-out device validation; licensed source/model chain; age/population matching.
- **Potential study:** paired Brainstem-plus-PSG feasibility and external validation.
- **Do not claim yet:** apnea probability, screening, diagnosis, or personal risk.

## ECG classifiers

- **What already fits:** some records contain raw ECG.
- **Exact delta:** consistent ECG availability; frozen sample rate/leads/units/device provenance; expert labels; artifact policy; participant-level train/validation/test split; source/model licences.
- **Potential study:** condition-specific feasibility after the exact label and population are approved.
- **Do not claim yet:** atrial fibrillation, arrhythmia, epilepsy, hypoglycaemia, cardiac arrest, sudden death, or any other clinical class.

## Exercise recovery

- **What already fits:** generic `exercise` records can contain R-R and heart rate.
- **Exact delta:** explicit exercise subtype and intensity; exertion end marker; recovery windows; device/protocol parity; exclusion of paced-breathing records currently sharing the type.
- **Potential study:** within-person heart-rate recovery repeatability for one frozen exercise protocol.
- **Do not claim yet:** fitness age, disease risk, prognosis, or treatment recommendation.

## Demographic cohort comparisons

- **What already fits:** self-reported year, gender, and `region` exist on some accounts.
- **Exact delta:** validate year semantics and missingness; stop labelling `region` as ethnicity; define voluntary study questions if ethnicity is actually needed; purpose-specific consent; minimum-cell and repeated-release differencing review.
- **Potential study:** participant-equal descriptive comparisons with deterministic broadening and cells of at least 20.
- **Do not claim yet:** normative range, causal demographic effect, ethnicity result derived from region, or individual health status.

## Apple Health and local-only composites

- **What already fits:** mobile apps calculate additional local measures and can read platform health data.
- **Exact delta:** versioned upload contract; provenance and units; cross-platform owner; reviewed formula; user-purpose consent; missingness and device-family policy.
- **Potential study:** feasibility and repeatability of one explicitly selected measure.
- **Do not claim yet:** any result based only on an unversioned mobile formula or local field name.

## Promotion rule

A row moves out of this file only after it has a primary/licensed source, exact input/protocol contract, public or generated reproduction, protected algorithm review, claim boundary, abstention policy, and a separately approved personal/cohort/study scope. Moving it never activates real data or deployment.
