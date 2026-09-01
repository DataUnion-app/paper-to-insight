# Six-rate paced-breathing response curve

This generated E0 methods package freezes one descriptive response curve for
the Brainstem mobile assessment already shared by iOS and Android: 7.0, 6.5,
6.0, 5.5, 5.0, then 4.5 breaths per minute. Each rate lasts 180 seconds; only
the final 120 seconds of raw R-R intervals are analyzed.

For each rate, the package recomputes mean heart rate, RMSSD, and SD1. It
preserves every exact tie for the largest observed RMSSD rather than selecting
one “best,” “optimal,” or therapeutic rate. Cohort mode gives every participant
one median curve and enforces a 20-participant disclosure floor.

```bash
python3 generate_fixture.py
python3 reproduce.py
python3 -m unittest test_algorithm.py
python3 -m unittest test_source_audit.py
python3 source-audit.py --verify
```

The checksum-pinned CC-BY papers use stepped breathing protocols and also
measure respiration/adherence and inspect artifacts. Current Brainstem mobile
code assigns a pacer but does not measure actual respiration, and neither app
uploads the complete six-rate curve. Therefore this package remains generated
only and ineligible for protected runtime review.

## Promotion hold

A versioned mobile producer must upload one complete curve, preserve exact
trial order and analysis windows, and carry explicit “adherence not measured”
provenance. A repeated-session Brainstem methods study must then evaluate curve
stability. Until those gates close, there is no DeSciLab card, participant-data
run, diagnostic interpretation, treatment claim, or optimal-frequency claim.
