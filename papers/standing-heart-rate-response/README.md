# Heart-rate response to standing

This generated methods package recomputes a descriptive response from the
five-minute protocol already used by both Brainstem apps: 120 seconds warm-up,
120 seconds rest, and 60 seconds standing. It uses the last three minutes,
recomputes every value from R-R intervals, and never trusts the uploaded mobile
`postureScore`.

The resting measure is `60000 / mean R-R`. The standing measure is the 95th
percentile of per-beat heart rate, chosen in advance to reduce the influence of
a single extreme accepted interval. Their difference is the response. Cohort
mode first takes each participant's median so additional recordings do not add
weight.

## Generated proof

```bash
python3 generate_fixture.py
python3 reproduce.py
python3 -m unittest test_algorithm.py
python3 -m unittest test_source_audit.py
python3 source-audit.py --verify
```

## Boundary

The practical active-stand method described in
<https://pubmed.ncbi.nlm.nih.gov/31076939/> also uses continuous beat-to-beat
blood pressure. Brainstem does not collect that signal. This package therefore
does not assess orthostatic blood pressure, POTS, orthostatic hypotension,
diagnosis, screening, or a clinical normal range.

Generated reproduction is evidence, not protected-algorithm approval or
authorization for participant data.

## Promotion verdict

The checksum-pinned public paper record confirms that the clinical active-stand
method focuses on three minutes of standing and continuous beat-to-beat blood
pressure. Its full text is not openly licensed in the audited source. The
independently defined heart-rate-only descriptor is promoted only to protected
runtime review; blood-pressure and clinical interpretations remain excluded.
