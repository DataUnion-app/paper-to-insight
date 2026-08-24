# Open-source boundary

This repository is the public, agent-friendly method workbench. It lets a
contributor turn a paper and licensed public evidence into a deterministic
candidate without receiving access to Brainstem participants or infrastructure.

Passing the local checks means the package is reproducible enough to review. It
does not mean that the method is scientifically valid, clinically useful,
approved, published to DeSciLab, or allowed to run on a private cohort. Those
decisions belong to the protected scientific, privacy, and security review path.

## What belongs here

- Source references pinned to immutable revisions.
- Licence and provenance evidence.
- Small licensed public or generated fixtures.
- Deterministic reproduction, abstention, and limitation evidence.
- The reusable agent skill and validators that enforce this boundary.

Participant recordings, production endpoints, credentials, reviewer keys,
private cohort references, and approval state never belong here. Production
Crab, Marine, DeSciLab, and Ocean Node repositories are separate operational
systems; public contributors do not need them to create a candidate.

## Publication controls

Before making the repository public, the owner must enable GitHub private
vulnerability reporting, protect the default branch, require the local checks on
pull requests, and verify the release manifest against the named source commit.
Repository visibility is a human operation and is not implied by a passing
candidate or release receipt.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor contract and
[SECURITY.md](SECURITY.md) for private disclosure.
