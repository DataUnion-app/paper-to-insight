# 01 — Public candidate boundary

Status: complete (2026-07-28)

## Goal

A fresh fork can assess a paper and emit a deterministic candidate package
without Brainstem access or credentials.

## Build

- Repository policy, contribution/security documents, and Apache-2.0 license for
  original repository code. Third-party code/data retain their own terms.
- `$turn-paper-into-insight` workflow.
- Exact candidate manifest and evidence receipt schemas.
- One stdlib validator and one command that validates the bundled example.
- CI that runs without production secrets or publishing permission.

## Candidate must declare

- immutable paper/source/data references, licenses, and digests;
- exact claim, labels/reference standard, population, prevalence, and split;
- signals, units, sampling, windowing, preprocessing, and missing fields;
- public reproduction command, seed, metric, tolerance, and receipt;
- Brainstem compatibility/mismatch and maximum evidence tier;
- proposed cohort/personal profiles, abstention rules, and prohibited claims.

The manifest has exact keys and `approvalState: candidate`. Any approval claim,
mutable source, unknown license, private URL, credential, or participant
identifier fails.

## Verification

- Two validations are byte-identical.
- Prompt-injection text remains inert metadata.
- Unsafe examples fail for missing license, mutable source, forged approval,
  private endpoint, and identifier canary.
- The skill passes `quick_validate.py`.

## Done when

The public repository has its first commit and CI-equivalent local checks pass.
No protected repository is changed in this slice.
