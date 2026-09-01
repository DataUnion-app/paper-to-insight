# Guided-breathing response

This generated methods package describes heart-rate dynamics during a guided
breathing session. Historical compatibility requires an `exercise` record,
raw R-R intervals, and the complete finite protocol tuple `(rateCPM, ih, ip,
eh, ep)`. Different tuples are never pooled.

Mean heart rate is `60000 / mean R-R`. RMSSD is the root mean square of
successive R-R differences. SD1 is the population standard deviation of those
differences divided by `sqrt(2)`. Each participant contributes one median and,
when repeated matched sessions exist, one latest-minus-earliest change.

```bash
python3 generate_fixture.py
python3 reproduce.py
python3 -m unittest test_algorithm.py
python3 -m unittest test_source_audit.py
python3 source-audit.py --verify
```

The source literature shows why exact protocol reporting and pace-matched HRV
interpretation matter. This package does not measure adherence or respiration,
and it does not claim stress reduction, treatment effect, an optimal breathing
rate, autonomic diagnosis, or a clinical normal range.

Generated reproduction is evidence, not protected-algorithm approval or
authorization for participant data.

## Promotion verdict

The checksum-pinned CC-BY review requires exact protocol reporting, breathing
adherence monitoring, and an artifact plan; it also states that no gold
standard protocol exists. Exact-protocol heart-rate descriptors are promoted
to protected runtime review. Resonance, adherence, treatment, and autonomic
interpretations remain excluded.
