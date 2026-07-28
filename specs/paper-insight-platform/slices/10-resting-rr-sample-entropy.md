# 10 — Resting R-R sample entropy paired Insight

Status: complete locally (2026-07-29); production unapproved

## Goal

Promote the first further paper-compatible method only after a deterministic
public reproduction and the same finite cohort, personal, provenance, and
privacy gates as the first Insight.

## Scientific boundary

The candidate implements sample entropy with the published PhysioNet defaults
`m=2` and `r=0.2` after per-recording normalization. Public Fantasia R-R
intervals are checksum-pinned and produce the expected public receipt.

This is an E2 methods-only result:

- no disease, condition, risk, or normal-range classification;
- cohort output is a median over at least 20 eligible participants;
- personal output uses at most four owner-only compatible recordings;
- the personal comparison uses an image-bundled aggregate reference with
  digest `4b1ba8cac0de4c2adb61f85dae56cd796feda9e388739e30d395ed3dfe592813`;
- artifact intervals cause exclusion or abstention instead of correction.

## Runtime proof

The protected implementation binds candidate manifest
`65002ab13f02f812c611085c0295b81dc90ec7ffacc79f9ff4927e81e9070bdd`
to exact cohort and personal schemas. Crab selects consented compatible records
and emits job-scoped pseudonyms only for cohort compute. Ocean runs the pinned
image without network access and validates one bounded result. DeSciLab exposes
the two modes under one “Resting rhythm complexity” family with separate
histories.

Generated-only local proof covers:

- complete cohort result at the disclosure floor;
- owner-only personal result against the frozen reference;
- wrong image, manifest, reference, policy, and result rejection;
- consent withdrawal and source deletion;
- Node restart and retained-result recovery;
- cross-participant denial and one-use capabilities;
- no input identifiers, intervals, logs, or workspace residue.

## Release gate

The protected proposal intentionally remains pending. Production requires
independent scientific, privacy, and security review, an immutable release
receipt and image digest, approved runtime configuration, and a separate
deployment decision. Passing this local slice is evidence, not approval.
