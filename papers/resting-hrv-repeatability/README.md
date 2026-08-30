# Resting HRV repeatability

This methods-only package translates published one-week test/retest work into a generated, participant-grouped example for eligible five-minute Brainstem rest recordings. It uses heart rate, SDNN, RMSSD, SD1, and SD2 already owned by the reviewed resting-HRV method.

It does not reproduce the paper's laboratory ECG/respiration acquisition or claim that ordinary Brainstem field recordings have the same reliability. Seven recordings are a bounded product window, not a universal scientific minimum.

## Generated proof

```bash
python3 generate_fixture.py
python3 reproduce.py
python3 -m unittest test_algorithm.py
```

The cohort method is participant-equal, reports ICC(1,1) with a deterministic participant bootstrap, and refuses to release below 20 generated participants. Personal mode reports only the owner's median, range, and coefficient of variation.

## Sources

- Data descriptor: <https://pmc.ncbi.nlm.nih.gov/articles/PMC11698850/>
- Reliability analysis: <https://doi.org/10.1088/1361-6579/adae51>
- HRV interpretation safeguards: <https://pubmed.ncbi.nlm.nih.gov/42495990/>

Generated reproduction is evidence, not protected-algorithm approval or authorization for participant data.
