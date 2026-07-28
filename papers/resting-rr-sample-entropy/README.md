# Resting R–R sample entropy

This candidate independently implements the sample-entropy estimator described
by Richman and Moorman and verifies it against PhysioNet's `sampen` 1.2
reference output.

The fixed method is:

- five-minute resting R–R intervals;
- embedding dimension `m = 2`;
- tolerance `r = 0.2` after population-standard-deviation normalization;
- strict pointwise distance `< r`, matching the reference C implementation;
- no interpolation or deletion of artifact intervals.

Any recording with an interval outside 300–2000 ms, fewer than 240 intervals,
non-matching declared duration, zero variance, or no template matches abstains.
Eligible recordings are summarized per participant before any cohort aggregate
is created.

## Meaning

Sample entropy describes short-term irregularity in a time series. This package
does not define a healthy value, diagnose disease, infer biological age, or
recommend treatment. The paper has no participant classification ontology, so
every complete result reports `paperDecision: not_applicable`.

## Public reproduction

```sh
python3 test_algorithm.py -v
python3 reproduce.py --verify
```

The reproduction checks:

- PhysioNet's 1,024-value test vector against its published `m = 2` output;
- the first complete five-minute window of one older and one younger healthy
  resting Fantasia record;
- immutable checksums for every downloaded source.

The Fantasia values demonstrate deterministic execution only. Two public
records are not a normative reference and do not validate a Brainstem device.

## Proposed protected modes

- **Group:** median participant sample entropy for at least 20 eligible people.
- **For me:** the authenticated participant's median sample entropy compared
  with a frozen disclosure-safe aggregate middle band.

Both modes require separate scientific, privacy, and security review before
publication.

