# Decision: Canonicalize the implement full driver token

Status: implemented - `/implement <plan> full` is the canonical full-plan invocation while `in-full` remains a compatibility alias

## Problem

Nexus-Hub accepted both `in-full` and `full` as whole-token driver modes for running every incomplete plan phase, but its command contract, skill, runbook, catalog metadata, README, and interactive guide presented `in-full` as canonical. The longer form was harder to teach and less natural to type, while the shorter form already worked and was the phrase users expected from the full-plan workflow.

Changing only the guide would create a documentation split: users could learn `full`, but the command and implementation skill would still describe another canonical form. Removing `in-full` would avoid that split but would break existing prompts, saved workflows, and continuation instructions.

## Decision

Nexus-Hub presents `/implement <plan> full` as the canonical full-plan driver mode everywhere the interface is taught or described. The exact whole token `in-full` remains accepted and documented as a compatibility alias.

The parser contract remains positional and unchanged in scope: a driver mode is a later whole token, never the first plan selector, and a plan slug that merely contains `full` is not interpreted as a mode. `phase-by-phase` and the one-phase default retain their existing behavior. Tests assert the canonical wording across the command, skill, runbook, registry, README, and interactive guide while also guarding against reversal back to the old presentation.

## Alternatives considered

- **Keep `in-full` canonical and teach `full` only as an alias.** Rejected because it preserves the more awkward primary invocation even though the concise token already expresses the user's intent and is already supported.
- **Remove `in-full` immediately.** Rejected because saved prompts, documentation links, and continuation text may still use it. The compatibility cost is negligible because both tokens already resolve to the same driver loop.
- **Accept any token containing `full`.** Rejected because a plan slug can legitimately contain that substring. Substring matching would make plan resolution ambiguous and could start an unintended multi-phase run.
- **Rename the driver mode in the guide only.** Rejected because a teaching surface that disagrees with the command, skill, metadata, and README creates interface drift and weakens the repository's cross-surface contract.

## Consequences

- New documentation and examples use the shorter `/implement <plan> full` form.
- Existing `in-full` invocations continue to work without migration steps or deprecation warnings.
- The command, skill body, runbook, registry metadata, README, and interactive guide must stay aligned on which token is canonical.
- The parser still needs exact-token tests so a slug containing `full` cannot be mistaken for a driver mode.
