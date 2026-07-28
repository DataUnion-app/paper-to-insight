# 04 — Finite runtime policies

## Goal

Lift the one-personal-Insight literal without creating a plugin system.

## Crab

Replace hard-coded resting-heart constants with a finite, server-owned approved
policy map after the second personal policy exists. Each entry binds:

- analysis/scientific version;
- built-in exporter ID;
- exact image/input/result profiles;
- evidence manifest and cohort-reference digests;
- one-run approval wording and permitted scope.

Use analysis-addressed challenge/grant routes. The client analysis ID is only a
lookup key. The grant binds the whole policy; it cannot choose records, filters,
image, reference, or URL. Keep explicit exporter functions rather than a query
DSL.

## Ocean Node

Resolve `{analysisId, grant}` against a finite configured policy list, then
require Crab's claimed grant to match every binding before fetch. Preserve exact
image allowlisting, single checksum fetch, RAM-backed input, network denial,
resource/result bounds, cleanup, retention, and purge behavior.

## Cohort

Reuse the existing resting-R-R cohort exporter for the first methods Insight.
Bind release and job to analysis/manifest/image policy. A reviewed cohort result
may become a reference candidate, never an automatic reference.

## Verification

Unknown analysis, cross-analysis grant, replay, expiry, wrong image/schema/
profile/reference, cross-owner access, consent withdrawal, deletion, source
drift, or extra fields fail closed. Two generated policies run independently.

## Personal claim contract

The BFF starts a run with only `{ analysisId, grant }`. Node selects one
configured compute environment by `analysisId`; duplicate configured IDs fail
startup. Crab's claim response must exactly bind:

- `analysisId`, `algorithmVersion`, image digest, input schema and input policy;
- result schema and result profile;
- candidate-manifest, approved-manifest and cohort-reference digests, using
  `null` only for the named legacy overview;
- evidence tier, use class, `clinicalUse: prohibited`, recording limit and Node
  audience.

Node compares every field to its selected server configuration before fetching
the dataset. The browser cannot provide or override any bound field.

## Done when

Existing resting-heart behavior and the new methods Insight both pass consumer
tests through the same finite policy owner.
