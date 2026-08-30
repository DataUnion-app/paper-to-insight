# Brainstem Insight Wave 2 ranking

Status: implementation decision record, 2026-08-30. This document does not
approve participant-data use, publication, deployment, recruitment, or a
health claim.

## Decision

Build the next wave in this order:

1. descriptive active-stand response;
2. guided-breathing response;
3. sleep heart-rate plus movement descriptors;
4. reusable cohort reference groups and recording-quality evidence;
5. a public-only BIDSleep reproduction.

The first two can use existing records without changing the mobile apps. The
third is likely compatible with many existing sleep records but needs a frozen
movement contract. BIDSleep is valuable research infrastructure, not the next
personal Insight: its public repository does not contain trained weights and
its Apple Watch inputs must not be assumed to transfer to Brainstem.

## Cost scale

These are planning ranges, not vendor quotations. Engineering assumes one
developer familiar with the repositories. External cost excludes ordinary
local hardware and staff salaries.

| Size | Engineering | Likely external cost | Typical limiting factor |
| --- | --- | ---: | --- |
| XS | up to 2 days | under USD 50 | generated-data proof |
| S | 2–5 days | under USD 100 | cross-repository integration |
| M | 1–2 weeks | USD 100–1,000 | public reproduction or new collection |
| L | 3–8 weeks | USD 1,000–10,000 | calibration or partner study |
| XL | multiple months | over USD 10,000 | clinical labels and prospective validation |

## Ranked backlog

Do-ability is 5 (can be built from today's contract) to 1 (blocked by missing
inputs or labels). Validation cost is kept separate from software cost because
a small implementation can still require an expensive scientific study.

| Rank | Candidate | Do-ability | Software | Validation | Existing-data value | Current decision |
| ---: | --- | :---: | :---: | :---: | --- | --- |
| 1 | Active-stand/posture response | 5 | S | S–M | About 688 posture recordings in the last verified production inventory | Build a descriptive candidate now |
| 2 | Guided-breathing response | 5 | S | S–M | Historical guided sessions are identifiable inside the exercise records | Build after posture |
| 3 | Sleep heart-rate plus movement descriptors | 4 | M | M | About 2,401 sleep recordings in the last verified inventory | Build descriptive measures; no sleep stages |
| 4 | Cohort reference groups | 4 | S | S | Reusable across existing and future Insights | Build as a shared result layer, not a standalone Insight |
| 5 | Recording quality and device repeatability | 4 | S–M | S–M | Makes every later result easier to trust | Build alongside ranks 1–3 |
| 6 | BIDSleep public sleep-staging reproduction | 3 | M–L | L for Brainstem transfer | No participant-data dependency for the public proof | Reproduce and retrain publicly; keep participant output disabled |
| 7 | Survey-linked disease association | 3 technically | S–M | L–XL | Valuable only after enough dated labels accrue | Prepare the protocol; do not infer disease from device data |
| 8 | Standardised exercise recovery | 2 | M | M–L | Generic historical exercise records are not a frozen exercise protocol | Add a prospective subtype and recovery protocol first |
| 9 | Six-rate resonance response | 2 | M | M–L | Complete curves are currently local-only; the verified corpus had one resonance record | Add a versioned full-curve upload before analysis |
| 10 | Apple Health composites | 2 | M | M | iOS-only and currently local-only | Defer until a separate consent and cross-platform plan exists |
| 11 | ECG/arrhythmia methods | 1 | L | XL | ECG availability and labels are inconsistent | Requires a condition-specific labelled study |
| 12 | Sleep-apnea classification | 1 | L | XL | Prior public external transfer was negative; no Brainstem PSG/AHI labels | Requires a paired PSG partner study |

## 1. Active-stand/posture response

### Existing contract

Both apps run the same five-minute sequence:

- 120 seconds warm-up;
- 120 seconds resting/relaxation;
- 60 seconds standing.

Both upload a `posture` record with raw R–R intervals and a `postureScore`.
The current mobile score is maximum standing heart rate minus mean resting
heart rate. The last three minutes of a complete record therefore contain the
canonical analysis windows: rest `[-180s, -60s)` and stand `[-60s, 0s)`.

### Minimum build

- accept only complete `posture` records whose valid R–R coverage reaches both
  windows;
- recompute the score server-side rather than trusting the uploaded value;
- report resting heart rate, peak standing heart rate, heart-rate rise, and
  repeatability across sessions;
- make missing coverage, impossible intervals, and imported/mis-typed records
  abstain;
- compare only against disclosure-safe frozen cohort summaries;
- call it **heart-rate response to standing**, not an active-stand diagnostic.

### Success proof

Generated fixtures must prove window boundaries, unit conversion, artifact
abstention, participant-equal cohort aggregation, minimum-cell protection, and
that no wallet or raw record reaches the result. Historical app and canonical
scores can then be compared without treating equality as scientific
validation.

### Boundary

Brainstem does not collect continuous beat-to-beat blood pressure. The
clinical active-stand method uses both blood pressure and heart rate, so this
candidate must not claim orthostatic hypotension, POTS, diagnosis, or clinical
screening. Source: <https://pubmed.ncbi.nlm.nih.gov/31076939/>.

## 2. Guided-breathing response

### Existing contract

Both apps upload guided-breathing sessions under `type=exercise`. Compatible
records contain raw R–R intervals plus a finite `rateCPM` and phase fields
`ih`, `ip`, `eh`, and `ep`. They may also contain `averageHR`, `rsa`, `lnLF`,
and `sf`. Those structural fields distinguish a guided-breathing session from
generic exercise without relying on a title or user-entered label.

### Minimum build

- define historical compatibility as `type=exercise`, raw R–R, finite
  `rateCPM`, and all four finite phase fields;
- recompute the selected time-domain and response measures from raw R–R;
- stratify or abstain when pace or phase timings differ rather than silently
  pooling different protocols;
- report within-person change and repeatability, plus participant-equal cohort
  summaries;
- add `exerciseSubtype=guided_breathing` and `protocolVersion` to future mobile
  uploads, while retaining the historical structural rule;
- do not claim stress reduction, treatment effect, or autonomic diagnosis.

### Success proof

Generated fixtures must prove that generic exercise is excluded, incompatible
pace/phase protocols are not pooled, uploaded derived metrics cannot override
canonical calculations, and repeated records from one participant do not
dominate the cohort.

Method reporting is a known weakness in the literature; a 2023 review found
that many HRV-biofeedback studies did not report enough protocol detail for
replication. Sources: <https://pubmed.ncbi.nlm.nih.gov/36917418/> and
<https://pmc.ncbi.nlm.nih.gov/articles/PMC7578229/>. Paced breathing also
changes HRV measurement properties, so comparisons must remain
protocol-matched: <https://pubmed.ncbi.nlm.nih.gov/29863781/>.

## 3. Sleep heart-rate plus movement descriptors

### Minimum build

- freeze the timestamp, units, axes, sample-rate, missingness, and device
  provenance contract for movement;
- recompute a small set of prespecified nocturnal heart-rate and movement-event
  measures from raw input;
- report within-person trends and protected participant-equal cohort
  distributions;
- keep app-derived sleep stages outside the result until cross-platform golden
  vectors establish formula parity;
- abstain when movement and R–R streams cannot be aligned.

This is a descriptive signal-quality and trend Insight, not sleep staging,
sleep quality, or disorder screening. It should reuse the existing overnight
heart-rate candidate rather than introduce a parallel baseline owner.

## 4. Cohort reference groups

This is shared infrastructure for ranks 1–3, not another algorithm.

- permit all-participant, age-band, gender, and geographic-region references
  only when the field is present and the cell passes the disclosure floor;
- never label the existing `region` field as ethnicity;
- use deterministic broadening when a requested cell is too small;
- bind the cohort snapshot, inclusion contract, and algorithm version to every
  result so later reruns remain interpretable;
- protect repeated releases against differencing, not only each individual
  response;
- let the participant see why a narrower comparison was broadened without
  exposing cell counts below the floor.

## 5. Recording quality and device repeatability

- expose coverage, artifact/abstention reasons, device family when reliably
  known, and repeated-session consistency;
- treat missing historical device provenance as unknown, never inferred;
- keep quality as evidence attached to an Insight result rather than a single
  universal reputation score;
- let each method define which quality dimensions matter.

This work is valuable even when a health method is not: it identifies which
records are suitable for which analyses and supports progressive evidence
about devices and protocols.

## 6. BIDSleep public proof

[BIDSleep v1.0.0](https://physionet.org/content/bidsleep-dataset/1.0.0/)
contains 253 nights from 47 adults, with Apple Watch intermittent heart rate
and accelerometry aligned to expert-corrected Dreem EEG labels. It is available
under ODC-By 1.0 and is approximately 5.9 GB compressed / 27.9 GB expanded.
Participant-level splits are mandatory.

The linked [SLAMSS-IFS source](https://github.com/BIDSLabUMass/SLAMSS-IFS)
is BSD-3-Clause; the source snapshot reviewed for this decision was commit
`088e363873b4ac5b27bc23fb038abc052889698c`. It does **not** ship trained model
weights. Its test notebook points to author-local weight paths, and its pinned
software stack is old. The honest minimum is therefore:

1. reproduce preprocessing against the pinned public dataset;
2. port and retrain with participant-level splits;
3. publish weights, environment, metrics, calibration, and failure analysis;
4. keep Brainstem personal/cohort modes disabled;
5. only consider Brainstem transfer after a paired Brainstem-versus-EEG study.

Brainstem R–R is higher resolution than the dataset's intermittent heart rate,
and Brainstem movement sampling/placement is not Apple Watch accelerometry.
More input does not remove that domain shift.

## Build slices

### Slice A — posture candidate

Add the public/generated reproduction, exact input contract, canonical
algorithm, adversarial tests, claim boundary, and disabled candidate entry.
Then carry it through protected algorithm, Crab export, Node result policy,
DeSciLab personal/cohort UI, and generated local proof. No participant data.

### Slice B — guided-breathing candidate

Repeat Slice A using the historical structural selector. Add the two explicit
fields to forward mobile uploads, but do not make the new app version a
condition for historical compatible records.

### Slice C — sleep plus movement descriptors

First freeze and test the movement contract. Build only descriptors supported
by the actual aligned streams. Do not call this sleep staging.

### Slice D — BIDSleep reproduction

Download public data only after setting a roughly 28 GB storage allowance and
a compute budget. Keep this slice isolated from participant infrastructure and
publish a negative result if reproduction or external validation fails.

## What can proceed without another human decision

- generated/public fixtures and algorithms for Slices A and B;
- candidate metadata and claim boundaries;
- protected-schema and disclosure-policy tests;
- disabled DeSciLab catalogue entries;
- generated local end-to-end runs;
- the BIDSleep preprocessing audit without downloading the full dataset.

## Human decisions before real use

- approve the participant-facing wording **heart-rate response to standing**;
- approve which guided-breathing pace/phase combinations constitute one
  comparable protocol;
- approve each real-data cohort/personal scope and its result disclosure;
- set a download/GPU budget before the full BIDSleep reproduction;
- commission paired reference measurements before any sleep-stage, apnea, or
  other clinical interpretation.

