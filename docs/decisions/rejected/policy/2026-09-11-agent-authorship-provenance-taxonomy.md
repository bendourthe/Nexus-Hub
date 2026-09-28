# Decision: Require an agent-authorship provenance taxonomy

Status: rejected - Do not require Human-authored, Autonomous agent-authored, or Hybrid labels with agent and model disclosure on every contribution.

## Problem

An external comparison proposed classifying every contribution by authorship and requiring each pull request to disclose the agent and model involved. The proposal would make generated assistance visible at the contribution boundary, but it would also create a second authorship policy while Nexus-Hub's attribution work was standardizing Git history and platform defaults around the configured human identity.

## Proposal

Add a mandatory provenance field to contribution records with one of three values: Human-authored, Autonomous agent-authored, or Hybrid. Require agent and model disclosure for every contribution in either agent-authored class, and treat omission as a failed contribution gate.

## Alternatives considered

| Option | Benefits | Costs and verdict |
|---|---|---|
| Adopt the three-class taxonomy and mandatory disclosure | Makes the producing tool explicit on every contribution | Conflicts with the in-flight sole-contributor attribution policy, which removes agent identities and mapped trailers from Git history. Rejected. |
| Keep human Git attribution but require agent/model metadata outside Git history | Separates repository authorship from process provenance | Creates a second mandatory ledger with no current consumer or retention contract. Rejected until a concrete audit requirement exists. |
| Preserve the verification claim only | Prevents generated work from being described as human-authored or independently verified when only the producing agent reviewed it | Compatible with human Git attribution because it governs evidence claims, not identity display. Adopted separately in `verification-before-completion`. |
| Keep the current attribution policy without a new taxonomy | Maintains one enforceable identity contract across installers and supported platforms | Does not expose model provenance per contribution. Selected because the repository has no requirement that justifies the conflicting metadata surface. |

## Consequences

Git authorship continues to use the configured human identity, and contributions do not acquire mandatory agent/model labels. Review and release evidence must still describe what was actually verified and must not call same-agent review independent. A future regulatory or audit requirement for model provenance must reopen this decision and define the storage, retention, privacy, and reconciliation contract before adding a new field.
