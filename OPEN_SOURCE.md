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

The repository is public under `DataUnion-app`, uses Apache-2.0, and has private
vulnerability reporting enabled. Release candidates enter the default branch
only through pull requests that pass the local checks in CI. Verify each release
manifest against its named source commit before merging and create signed tags
only as a separate owner action.

Public visibility does not make any candidate approved, clinically valid, or
eligible for protected data.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor contract and
[SECURITY.md](SECURITY.md) for private disclosure.
