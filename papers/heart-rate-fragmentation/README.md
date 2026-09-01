# Heart-rate fragmentation

This candidate independently rederives the published fragmentation mechanics
on a generated sequence of already-cleaned normal-to-normal intervals. It also
downloads the checksum-pinned author materials and reproduces all three
published reference-series outputs with the original AWK program.

## Verdict: study only

The formulas and author reference are reproducible, but the current Brainstem
signal is detector R-R rather than adjudicated normal-to-normal intervals with
beat labels. The reference code uses an upper bound of 1.8 seconds while its
README documents 1.5 seconds, and the source states that no precise minimum
reliable window is known. Detector and device artifact sensitivity also remain
unvalidated.

Therefore this package is evidence for a future governed methods study. It is
not eligible for a DeSciLab cohort or personal runtime card and makes no age,
disease, risk, diagnosis, or treatment claim.

## Reproduce

```bash
python3 test_algorithm.py -v
python3 reproduce.py
python3 test_source_audit.py -v
python3 source-audit.py --verify
python3 ../../scripts/validate_candidate.py candidate.json
```

The repository contains only generated intervals and checksums. The CC-BY
paper, GPL-3.0 author code, and GPL test series remain at their original URLs
and are not redistributed here.
