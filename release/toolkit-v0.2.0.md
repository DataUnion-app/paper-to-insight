# Paper-to-Insight toolkit v0.2.0 release candidate

This branch starts at signed tag `v0.1.0` and adds one independently written,
generated-data teaching package for repeated-measure reliability. It does not
contain Brainstem participant data, protected algorithms, cohort references,
runtime pins, endpoints, receipts, credentials, BIDSleep corpus/model files, or
publication approval.

## Positive allowlist

Only these paths may differ from `v0.1.0`:

- `.github/workflows/verify.yml`
- `NOTICE`
- `README.md`
- `papers/README.md`
- `papers/sleep-measure-reliability/`
- `release/toolkit-v0.2.0.md`
- `release/toolkit-v0.2.0.sha256`
- `skills/turn-paper-into-insight/SKILL.md`

`toolkit-v0.2.0.sha256` is an ordered SHA-256 manifest of every tracked file
except itself. A release owner can verify it with:

```sh
sha256sum --check release/toolkit-v0.2.0.sha256
```

## Reproducible gates

```sh
git merge-base --is-ancestor v0.1.0 HEAD
git diff --name-only v0.1.0..HEAD
python3 -m unittest discover -s tests -v
python3 scripts/validate_candidate.py papers/sleep-measure-reliability/candidate.json
python3 papers/sleep-measure-reliability/test_algorithm.py -v
python3 papers/sleep-measure-reliability/reproduce.py --verify
```

The workflow targets the repository's actual default branch,
`feature/paper-insight-platform`, and grants only `contents: read`. No tag,
GitHub release, visibility, or default-branch change is part of this candidate.

## Recorded verification

- 19 root validator tests passed.
- 15 paper test files passed.
- 14 candidate manifests validated.
- All three executable public/generated reproductions matched their frozen
  outputs.
- The release-branch history contains 211 text blobs, no binary blobs, no blob
  over 1 MiB, and no high-confidence credential pattern match.
- The current tree has no high-confidence credential pattern match.
