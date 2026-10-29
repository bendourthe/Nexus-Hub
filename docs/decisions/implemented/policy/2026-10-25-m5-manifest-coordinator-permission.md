# Decision: M5 manifest coordinator permission

Status: implemented - A captured M5-only permission enables later manifest registration through ordinary publication admission.

## Problem

M5 implementation was admitted without a write claim for `MANIFEST.sha256`. Its frozen plan does not name that generated file literally, so the existing publication coordinator validator cannot register it. Editing the original signed claims would erase the admission boundary.

## Decision

Keep original implementation claims immutable. The dedicated `permit-manifest` round supports only `bendourthe/Nexus-Hub`, minor `v4.14`, member `v4.14.5` and literal `MANIFEST.sha256`. A genuine captured decision appends one signed, immutable permission bound to the frozen plan, original implementation, controller, owner session and fresh record generation. Existing capture and native writer protocols consume the answer.

The permission stays dormant until ordinary `member-start` registers the path. M4 release and back-merge, integration identity, original-scope cleanliness and conflict checks remain required. The preactivation check rejects earlier unclaimed edits. A dormant permission creates no reservation. Accepted provenance remains verifiable after legitimate resume or controller handoff.

The separate plan-named files `configs/platform-defaults.json` and `docs/policy/platform-defaults-levers.md` already have an ordinary publication coordinator route. Register those files before edits at the normal M5 turn; this decision adds no permission for them.

## Alternatives considered

- Edit the original worker claims: rejected because it would rewrite immutable admission history.
- Add the manifest to every member or all coordinator paths: rejected because the reviewed omission is M5-specific.
- Treat implementation approval or a blocker answer as permission: rejected because neither is the bound, single-use native capture required for this action.
- Continue without a repair: rejected because M5 cannot register the generated manifest through the existing literal-plan rule.

## Consequences

The repair adds one narrowly scoped native decision and its regression coverage. Delivery requires qualified matching native helpers, and the actual run still needs its own genuine captured permission. Release, archive, spending, retry and review requirements stay independent. Frozen plans, original claims and budgets remain unchanged. The [completion contract](../../../../catalog/skills/workflow/implement-phase/references/completion-contract.md) owns the operational rule.
