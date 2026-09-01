# Disabled Wave 2 evidence packages

These seven packages turn near-compatible ideas into exact research deltas. They
are not executable candidates. Every runtime switch is false, every package has
at least two unresolved blockers, and promotion requires new evidence plus
scientific, privacy, security, and ethics review.

| Package | Cost | First missing step |
| --- | --- | --- |
| Disease-linked association | M | collect separately dated outcomes under a prospective protocol |
| Standardised exercise recovery | S-M | freeze exercise, workload, exertion end, and recovery windows |
| Sleep movement regularity | M | freeze movement provenance and choose a movement metric or collect sleep/wake states |
| Six-rate resonance | S-M | upload one complete versioned six-rate curve |
| Apple Health/local composites | M | choose one formula and freeze provenance, units, and owner |
| ECG/arrhythmia | L | obtain consistent calibrated ECG plus expert labels |
| Sleep apnea | L | collect paired Brainstem and PSG respiratory reference nights |

Validate the inventory and its immutable local evidence bindings with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 papers/disabled-wave-2/validate.py
PYTHONDONTWRITEBYTECODE=1 python3 papers/disabled-wave-2/test_validate.py
```

The validator fails if a package is removed, promoted out of `disabled`, loses
its blockers or promotion gates, changes a bound evidence file without updating
review, or enables an algorithm policy, API route, participant study, personal
card, payment, notification, or schedule.

The six-rate package now binds a generated response curve and an all-exact-ties
rule. It remains disabled because neither app uploads a versioned complete
curve, respiration/adherence are unmeasured, and no repeated Brainstem session
has established stability.
