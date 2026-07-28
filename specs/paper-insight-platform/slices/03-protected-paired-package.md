# 03 — Protected paired package

Status: complete (2026-07-29)
Protected revision: `algo-deploy-scripts@b72a14886e474aad54360d8971d7a9167026e3d6`

## Goal

Import the public candidate into the existing protected review queue and produce
one immutable dual-mode Brainstem package. Do not add an upload service.

## Build

- Checksum/path/symlink-safe operator import into `algo-deploy-scripts`.
- Pending proposal containing candidate/reproduction digests, evidence/use class,
  two exact input profiles, one result contract/profile set, abstention rules,
  cohort privacy policy, frozen reference digest, and three review references.
- One immutable non-root, networkless image consuming only the two exact schemas.
- `brainstem.approved-insight/v1` emitted only after the existing manual review
  and release gates.

## Result contract

Introduce `brainstem.insight-result/v1` for paper-derived Insights while reusing
the existing bounded metric/chart/table primitives. It adds:

- `analysisId`, `scope`, evidence tier, use class, and approved-manifest digest;
- paper identity and `classified | abstained | not_applicable`;
- bounded abstention code;
- algorithm/input/reference provenance.

`insufficient_data` and `failed` contain no metrics, chart, table, or
classification. Existing `brainstem.c2d-result/v1` remains supported only as a
named migration seam for already-built Insights.

## Verification

Reject traversal, symlinks, extra files, stale digests, unknown licenses,
self-approval, missing reproduction, tier escalation, mutable images, network
access, extra outputs, and results over 256 KiB.

## Done when

The protected package is reviewable and passes all generated gates. It remains
unpublished and unallowlisted unless humans separately approve it.
