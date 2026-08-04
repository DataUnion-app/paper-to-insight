# Official Apnea-ECG method evidence

This package freezes the official PhysioNet `apdet` method and the two public
datasets used for reproduction and external evaluation. It is evidence, not a
runnable or personal health Insight.

The official source archive is checksum-pinned but not vendored. PhysioNet's
catalogue labels the hosted resource ODC-By-1.0, while all executable source
files in the archive state GPL-2.0-or-later. Redistribution of source, binaries,
or a container remains blocked pending human licence review.

The historical paper is also not treated as a perfect benchmark. Its printed
amplitude coefficients differ from the corrected official software, the
PhysioNet page contains inconsistent result counts, and the original parameters
were optimized across combined datasets. The current package therefore reports
the result it actually obtains and never tunes to recover a headline number.

On the current public learning labels, the checksum-pinned official package
produces 13,825/17,045 correct minute decisions (81.1088%) and 24/30 correct
non-borderline record decisions at the paper's 5% threshold. The paper reports
13,985/17,045 and 26/30. This is a successful execution of the frozen package,
but not an exact reproduction of the historical headline; it remains a failed
reproduction gate. Public test labels are not available in the current package,
so its historical test result is not re-created or implied.

The unchanged method was then tested under the precommitted UCDDB plan. Twenty-
three of 25 participants were evaluated; two were withheld because their public
sleep-stage files contain code `8`, outside the declared `0..7` domain. Across
9,553 evaluated minutes, accuracy was 77.1799%, sensitivity 27.4923%,
specificity 95.8387%, and balanced accuracy 61.6655%. Participant-macro
sensitivity was 17.1856%. This is an important negative transfer result: the
high specificity does not make the method suitable for screening or negative
reassurance. No outcome threshold or adaptation rule was changed after the
external result was inspected.

UCDDB supplies ECG, not annotated normal-to-normal intervals, so the frozen
external adaptation used checksum-locked ECG files and a predeclared XQRS
detector. The resulting detector R-R intervals are not proven NN intervals and
do not validate the different Brainstem input or population.

Brainstem recordings do not contain the respiratory/PSG reference signals
needed to establish apnea or hypopnea. Personal labels, scores, probabilities,
AHI estimates, screening statements, and negative reassurance remain withheld.

## Verify

```bash
python3 papers/apnea-ecg-heart-rate/test_source_audit.py -v
python3 papers/apnea-ecg-heart-rate/source-audit.py --verify
python3 papers/apnea-ecg-heart-rate/reproduce.py --verify \
  --cache ~/Library/Caches/brainstem-public-reproduction
python3 papers/apnea-ecg-heart-rate/external_validate.py --verify \
  --cache ~/Library/Caches/brainstem-public-reproduction
```

Primary references:

- [Official `apdet` 1.0.0 resource](https://physionet.org/content/apdet/1.0.0/)
- [Method paper](https://physionet.org/files/challenge-2000/1.0.0/papers/00898634.pdf)
- [Apnea-ECG 1.0.0](https://physionet.org/content/apnea-ecg/1.0.0/)
- [UCDDB 1.0.0](https://physionet.org/content/ucddb/1.0.0/)
