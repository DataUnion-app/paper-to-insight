# Sleep measure reliability — generated candidate

This independent Apache-2.0 example turns repeated nightly measurements into a
participant-level reliability curve. It is motivated by published work showing
that minimum nights are metric- and threshold-specific. It does not reproduce
the paper's consumer device, population, or dataset and therefore remains an
`E0_candidate`.

The fixture has twenty generated participants with seven generated nightly
sleep-duration values each. Participants—not nights—are the resampling unit.
The result uses ICC(1,1), participant-level bootstrap intervals, and a
twenty-participant release floor. No participant rows or identifiers are
returned.

Run:

```bash
python3 test_algorithm.py -v
python3 reproduce.py --verify
python3 ../../scripts/validate_candidate.py candidate.json
```

The output describes repeatability only. It is not a Brainstem cohort
reference, normal range, health assessment, risk estimate, or diagnosis.

