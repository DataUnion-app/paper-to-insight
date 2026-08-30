# Overnight heart-rate change

This package reproduces the pinned Apache-2.0 NightSignal running-median and two-consecutive-night threshold mechanics on a compact derivative of its public Fitbit sample. It then freezes a narrower Brainstem translation: compare two recent qualifying full-night sleeping-rate summaries with the median of the preceding seven.

The translation is descriptive. It does not return NightSignal's infection labels or call a threshold event an alert, illness, disease, or risk.

## Public proof

```bash
python3 reproduce.py
python3 -m unittest test_algorithm.py
```

The compact fixture contains only the first 30 nightly mean values derived from the source CSV after applying its midnight-to-06:59, zero-step filter and integer mean. Dates, raw heart-rate rows, and identifiers are intentionally omitted.

## Source boundary

- Paper: <https://pmc.ncbi.nlm.nih.gov/articles/PMC9020268/>
- Source: <https://github.com/StanfordBioinformatics/wearable-infection/tree/99b3bd7937e72d42c2670c7a259d9f9f8728dc06>
- Source licence: Apache-2.0
- Source algorithm SHA-256: `198487887166afa2c7f884d832c2c837d41f2973b684da0303ec5aa8ad54a999`
- Source Fitbit CSV SHA-256: `da5f7bbfadeebec5c0fc7e12bc22258749ea52971f68eafb35187a002470a0c1`

Public reproduction is evidence, not protected-algorithm approval or authorization for participant data.
