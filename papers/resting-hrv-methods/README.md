# Resting HRV methods

This is a methods-only candidate based on the 1996 Task Force HRV measurement
standard (DOI `10.1161/01.CIR.93.5.1043`). It calculates SDNN, RMSSD, and
Poincaré SD1/SD2 from five-minute resting R-R interval sequences.

It does not classify a disease, produce a risk score, define a clinical normal
range, or offer medical advice.

## Public check

```bash
python3 reproduce.py --verify
python3 test_algorithm.py -v
```

The reproduction downloads only the checksum-pinned `O1` and `Y1` interval files
from PhysioNet Fantasia v1.0.0. The data are not committed. Fantasia is available
under ODC-By-1.0; the generated output retains its attribution.

## Quality rule

The candidate removes intervals outside 300–2000 ms and abstains when more than
5% are removed or fewer than 180 remain. This explicit compatibility screen is
part of this implementation; it is not presented as a Task Force clinical rule.

## Two modes

- Cohort: medians across at least 20 compatible participants.
- Personal: owner-only compatible recordings compared with a frozen aggregate
  reference. “Within the reference middle band” is descriptive, not normal.

The reference produced by this public candidate is a review candidate. It does
not become a Brainstem reference without protected privacy/science approval.

