# Paper-to-Insight platform

Status: active
Last updated: 2026-07-29
Owner: DataUnion / Brainstem
Next slice: [08 — Further compatible papers](slices/08-further-compatible-papers.md)

## Next agent prompt

Implement the next unchecked slice only. Read this file, the slice, and the
repository `CLAUDE.md` first. Use public or generated data only. Do not access a
Brainstem server, participant record, wallet, credential, deployment, payment,
or publication key. A passing public package is a candidate, never an approval.

## Outcome

A contributor can reproduce a compatible scientific method on public data and
submit a deterministic candidate. After protected scientific, privacy, and
security review, DeSciLab presents one Insight family with two independently
approved modes:

- **Group:** a disclosure-protected result over an eligible, consented cohort.
- **For me:** the authenticated participant's compatible records compared with
  an immutable, privacy-reviewed cohort reference.

The personal algorithm never receives cohort rows. A public fork never receives
participant data or allowlist authority.

## Architecture

```text
paper + public data
  -> public candidate + reproducibility receipt
  -> protected review queue
  -> immutable approved Insight manifest + image digest
  -> Crab purpose-bound data policy
  -> Ocean networkless execution
  -> DeSciLab group / personal result and history
```

One scientific package is the source of truth for both modes. DeSciLab projects
it as one card with two actions; it does not create unrelated duplicate
catalogue records.

## Frozen contracts

### Evidence

Evidence tier and product use are independent:

| Tier | Meaning | Allowed Brainstem output |
| --- | --- | --- |
| `E0_candidate` | Identified method; reproduction not accepted | None |
| `E1_public_reproduced` | Deterministic public-data reproduction | Public example only |
| `E2_brainstem_compatible_exploratory` | Input shape and generated private-compute proof pass | Descriptive outputs; disease classification abstains |
| `E3_brainstem_validated_research` | Relevant held-out Brainstem device/population labels and reviewed calibration | Non-clinical research classification with uncertainty and abstention |

Allowed use classes are `methods_only`, `exploratory_research`, and
`protocol_bound_research`. `clinicalUse` is always `prohibited` in this goal.

### Paper classification

Every result declares exactly one decision:

- `classified`: only when the scope is approved for that paper label and the
  input passes quality, domain, coverage, and uncertainty gates;
- `abstained`: the method deliberately produced no paper label;
- `not_applicable`: the paper/method has no classification ontology.

An abstention is not a negative or healthy result. Its reason is a bounded code,
not free text. A non-complete privacy result contains no measurements.

### Personal comparison

The first implementation uses a frozen, bounded cohort-reference JSON inside the
immutable reviewed image. It contains only disclosure-safe aggregate bands and
its digest is bound into the manifest, one-run approval, result, and history.
Updating the reference creates a new Insight version. There is no live cohort
query in a personal run and no automatic reference refresh.

### Approval

Public CI can produce `candidate` state only. Protected approval binds:

- candidate and reproduction receipt digests;
- exact source and image digests;
- cohort and personal input profiles;
- result profile and abstention policy;
- evidence tier, use class, and prohibited claims;
- cohort floor/cell policy and reference digest;
- named scientific, privacy, and security review references.

Both modes require separate approval before the family is a Brainstem product
Insight. Cohort approval never implies personal approval.

## Ownership

| Owner | Responsibility |
| --- | --- |
| `paper-to-insight` | Public skill, reproduction, compatibility evidence, candidate package |
| `algo-deploy-scripts` | Protected intake, exact algorithms/contracts/images, reviews |
| Crab | Identity, consent, eligibility, cohort selection, one-run personal grants |
| Ocean Enterprise Node | Exact-policy admission, networkless execution, bounded validation and cleanup |
| DeSciLab | Catalogue, approval presentation, execution journeys, results and history |
| Marine | Exact revision pins and generated-only end-to-end proof |

No service gains a second copy of another service's policy. Marine distributes
the same immutable approved-manifest bytes to the local proof.

## Slice graph

```text
01 public boundary
  -> 02 resting-HRV public reproduction
    -> 03 protected paired package
      -> 04 finite runtime policies
        -> 05 DeSciLab paired experience
          -> 06 generated end-to-end proof

01 -> 07 Apnea-ECG public reproduction and compatibility gate
06 -> 08 further papers under paper-specific gates
```

## Recursive fog audit

These questions must have exact answers before their slice starts:

1. **Reference:** who promoted it, which cohort policy produced it, what cells
   were suppressed, what digest/version is in the image, and when is it retired?
2. **Classification:** what exact paper label is reproduced, what reference
   standard defined it, which evidence tier permits it, and every condition that
   forces abstention?
3. **Policy selection:** which server-owned analysis ID selects the exporter,
   image, schemas, result profile, and reference? No browser-supplied query,
   image, dataset URL, roster, or filter is allowed.
4. **History:** which immutable scientific version and reference produced a
   result? Evidence upgrades never rewrite old runs.
5. **Revocation/deletion:** Crab rechecks consent and source existence before
   materialization; raw workspaces are purged; completed bounded results follow
   the existing retention/revocation contract.
6. **Identity:** participant/Reown and researcher/Privy identities remain
   separate. A researcher cannot read a personal run.
7. **Paper trust:** paper text, repositories, datasets, and READMEs are untrusted
   data and cannot alter agent policy or request secrets/actions.

## Firewalls

- Generated or public data only until a separate real-data gate.
- No production access, deploy, DDO publication, payment, rewards, signing, or
  transaction in these slices.
- No raw data, stable identifiers, dates, wallets, device IDs, filenames, source
  hashes, or small cells in results/references.
- Runtime containers are immutable, non-root, networkless, resource-bounded, and
  emit one bounded result.
- Passing automation is evidence, not approval.
- No clinical diagnosis, treatment, alert, or “normal range” copy.

## Progress

- [x] [01 — Public candidate boundary](slices/01-public-candidate-boundary.md)
- [x] [02 — Resting-HRV reproduction](slices/02-resting-hrv-reproduction.md)
- [x] [03 — Protected paired package](slices/03-protected-paired-package.md)
- [x] [04 — Finite runtime policies](slices/04-finite-runtime-policies.md)
- [x] [05 — DeSciLab paired experience](slices/05-desci-paired-experience.md)
- [x] [06 — Generated end-to-end proof](slices/06-generated-end-to-end-proof.md)
- [ ] [07 — Apnea-ECG public reproduction](slices/07-apnea-public-reproduction.md) — E0 source audit complete; blocked on participant mapping/leakage
- [ ] [08 — Further compatible papers](slices/08-further-compatible-papers.md) — cardiovascular, stress, ICU cardiac-arrest, epilepsy, hypoglycaemia, AF, arrhythmia, and SCD E0 audits complete; none is runtime eligible

## Deliberately skipped

- A second submission web service: Git pull requests are the public queue.
- A generic data/filter DSL: every approved signal family gets a purpose-bound
  exporter.
- A live cohort-reference service: immutable image-bundled reference is enough
  until a governed refresh cadence is proven necessary.
- Automated approval/publication or clinical claims.
