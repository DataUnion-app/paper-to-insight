# 09 — SleepECG public external reproduction

Status: complete (2026-07-29)

## Goal

Test a licensed, shipped sleep-staging model on an independent public
PSG-labelled dataset before creating any Brainstem runtime package.

## Result

SleepECG 0.5.9's exact `wrn-gru-mesa` artifact was evaluated on all 18 SLPDB
records representing 16 participants. Split nights for the same participant
were grouped together. Inputs were checksum-pinned public heartbeat and stage
annotations.

The model executed reproducibly, but external transfer was poor:

- accuracy 0.573618;
- Cohen's kappa 0.123670;
- REM F1 0.199796;
- participant accuracy 0.291465–0.690476.

The candidate reaches `E1_public_reproduced` because the public result is
reproducible. It is not eligible for runtime review and exposes no cohort or
personal mode.

## Boundary

This is not a reproduction of Radha et al.'s four-class HRV LSTM. SleepECG uses
a different three-class model and remains a separate candidate.

Promotion requires a pre-registered, held-out Brainstem-device-versus-PSG
study, representative participants, reviewed sensitive-metadata handling, and
scientific/privacy/security approval.

