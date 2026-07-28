# Paper to Insight

Turn a scientific paper into a reproducible, reviewable candidate for a
privacy-preserving cohort and personal Insight.

This repository is the public workbench. It contains no participant data,
credentials, approval keys, or connection to Brainstem infrastructure. Passing
its checks means **candidate**, not approved or clinically valid.

## Try it

```bash
python3 scripts/validate_candidate.py examples/minimal-methods/candidate.json
python3 -m unittest discover -s tests -v
python3 scripts/validate_candidate.py papers/resting-hrv-methods/candidate.json
python3 papers/resting-hrv-methods/test_algorithm.py -v
python3 papers/resting-hrv-methods/reproduce.py --verify
python3 papers/apnea-ecg-heart-rate/test_source_audit.py -v
python3 papers/apnea-ecg-heart-rate/source-audit.py --verify
python3 scripts/validate_candidate.py papers/apnea-ecg-heart-rate/candidate.json
python3 papers/cardiovascular-event-hrv/test_source_audit.py -v
python3 papers/cardiovascular-event-hrv/source-audit.py --verify
python3 scripts/validate_candidate.py papers/cardiovascular-event-hrv/candidate.json
```

The bundled Codex-compatible skill lives at
`skills/turn-paper-into-insight/SKILL.md`. Fork this repository, give an agent a
paper, DOI, source repository, or public dataset, and ask it to use
`$turn-paper-into-insight`.

## Handoff

```text
paper + public data
  -> deterministic candidate package
  -> protected scientific/privacy/security review
  -> immutable approved algorithm
  -> purpose-bound private compute
```

A candidate proposes a disclosure-protected cohort analysis and a personal
analysis using only the authenticated participant's compatible records plus a
frozen aggregate cohort reference. Forks cannot approve, publish, or access
either mode.

See `specs/paper-insight-platform/README.md` for the implementation plan.

The first real candidate is `papers/resting-hrv-methods`. It implements selected
descriptive HRV measures in both cohort and owner-only personal modes and pins a
small public PhysioNet reproduction. It intentionally has no disease label.

`papers/apnea-ecg-heart-rate` demonstrates the failure path. Its pinned source
audit finds record-level evaluation and an overlapping-record leak, so it remains
an E0 candidate with both runtime modes disabled. It is not published to
DeSciLab.

`papers/cardiovascular-event-hrv` is also E0 and disabled. Its source is licensed
and paper-associated, but its scaler/test contract is incomplete and its
published metric calculations are incorrect.

## License

Original repository code is Apache-2.0. Paper implementations, models, and
datasets retain their own licenses and must declare them in every candidate.
