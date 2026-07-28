# Candidate contract

The canonical machine-readable contract is `schemas/candidate.v1.schema.json`;
the stdlib enforcement is `scripts/validate_candidate.py`.

## Evidence ceiling

Public packages stop at `E2_brainstem_compatible_exploratory`. Only protected
review using relevant Brainstem-labelled data may promote a package to
Brainstem-validated research. No tier here authorizes clinical use.
At that protected tier, reviewers may permit a clearly non-clinical research
classification with calibration, uncertainty, and abstention; public candidates
cannot grant that permission.

## Classification

Preserve the paper's exact labels and reference standard. Separately declare what
Brainstem may return:

- descriptive method: `not_applicable`;
- prediction, association, or intervention at public evidence tiers: `abstained`;
- never reinterpret `abstained` as negative, normal, or healthy.

Do not expose the withheld classification as a probability, risk score, chart, or
free-text proxy.

## Dual modes

Cohort output is aggregate-only and every visible cell meets the declared floor.
Personal input contains only owner-authorized records. Its comparison reference
is bounded aggregate JSON, human-reviewed, immutable, and digest-bound. It
contains no cohort rows or stable identifiers.

Protected review owns the reference's approval authority, source cohort policy,
minimum cells, version, digest, expiry/supersession, and differencing review. A
minimum of 20 alone is not sufficient for subgroups or repeated releases.

## Block reasons

Use one or more of: `license_unverified`, `source_mutable`,
`paper_implementation_identity_unproven`, `public_reproduction_failed`,
`participant_split_leakage`, `brainstem_contract_missing`,
`required_signal_missing`, `reference_labels_missing`,
`population_or_device_unvalidated`, `output_not_bounded`,
`privacy_not_demonstrated`, or `claim_exceeds_evidence`.

## Package state

`approvalState` must be `candidate`. Protected systems re-derive approval from
their own review records and exact digests; public metadata is never trusted as
approval.
