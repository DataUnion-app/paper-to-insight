# ECG hypoglycaemia detection — runtime blocked

The cited article is correctly identified and checksum-pinned:

- Cappiello et al., *Artificial intelligence for non-invasive glycaemic-events
  detection via ECG in a paediatric population: study protocol*,
  <https://doi.org/10.1007/s12553-022-00719-x>.

This is a protocol, not a completed classifier study. Its Results section says
data collection and model development were expected later. It proposes
five-to-fifteen-minute raw-ECG excerpts paired with continuous-glucose-monitor
readings from 64 paediatric type-1-diabetes participants.

The supplied Apache-2.0 repository is not an executable implementation of that
protocol. It predates the article and contains only a README, PDF, DOCX, and
license. The README describes a separate DenseNet feature-extraction experiment
on five-minute, 250 Hz raw ECG from the D1NAMO dataset; no code, fitted model,
split manifest, metrics receipt, or inference contract is present.

The current Brainstem C2D contract does not provide raw ECG morphology paired
with CGM reference values or a validated paediatric type-1-diabetes population.
Neither a cohort glycaemic result nor an owner-facing classification is
scientifically supported.

## Next evidence gate

1. Identify the completed study and a licensed implementation, or independently
   implement a frozen method from a published result paper.
2. Reproduce it with participant-separated raw ECG and time-aligned CGM labels.
3. Add a purpose-bound raw-ECG/CGM Brainstem study contract with calibrated
   device and population evidence.
4. Treat any glucose alerting use as a separately regulated clinical product.

Until then, this candidate belongs in the review queue and not DeSciLab.
