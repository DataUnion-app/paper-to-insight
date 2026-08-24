# Protected E3 validation gate

Use `scripts/validate_e3_receipt.py` only after an E2 candidate enters a
separately governed, pre-registered Brainstem validation study.

The receipt is metadata, never participant rows or labels. It binds the exact
candidate, algorithm image, study protocol, exact dataset schema, device and population contracts,
participant-separated split, power plan, non-self-report reference standard,
calibration, missingness, artifacts, abstention policy and independent
scientific/privacy/security approvals. Reviewer identities are represented by
receipt-scoped pseudonym digests; public labels cannot carry participant,
patient, wallet, device, recording, user or email identifiers.

Self-report may support recruitment or stratification. It cannot by itself
promote disease classification to E3. A passing receipt permits only
non-clinical research output: a relative indicator with uncertainty and
abstention plus language to consider professional evaluation. It never permits
diagnosis or treatment.
