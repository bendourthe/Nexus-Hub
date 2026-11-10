# Decision: Captured Minor Scope Amendments

Status: implemented - Add exact new minor members through captured approval and authenticated history while preserving existing authority.

## Problem

An active minor run freezes its initial member plans. Resume changes session ownership without expanding that membership, while a second run refuses to replace a live run. Later approved plans therefore need an explicit admission operation. Editing the signed record, reusing an old approval, or silently treating every newly discovered plan as approved would lose the boundary between the original consent and new work. This record explains that boundary for maintainers changing native approval, signing, archive and completion consumers.

## Decision

The native `record render --action amend-minor` and `record amend-minor` operations bind an exact additional member list to a new genuinely captured current-session decision. The page includes each integrated plan's hash, branch, target, release, tag, action classes and cleanup scope, plus any exact additional gap migration reasons and named high-risk IDs. It also binds the current record bytes, nonce, original member digest, controller identity, repository and push route, integration commit, preceding amendment history and unchanged resource limits. Rendering and consumption both verify the current admission conditions; failed observations refuse admission.

The amendment transaction preserves original member dictionaries, approvals, blockers, claims and resource limits. Accepted pages and capture provenance form immutable authenticated history. Added members have separate mutable operational state so normal native implementation, ordered publication, archive/refreeze and controller handoff can continue afterward. Their projections carry only their own explicit grants and captured context. They do not inherit original unattended policies, correction authority or historical v4.15 task aliases. Amendment does not resolve a blocker or replace normal worker admission.

Conditional signing covers the amendment fields while retaining the original signing payload for records without those fields. Every participating reader or writer explicitly opts into the amendment protocol. A coherent older bundle cannot authenticate the extended payload, and partial bundles refuse before modifying native state or archive paths. All eight affected helper consumers are qualified together. Delivery uses the verified merged helper bytes and backups; source fixtures do not authorize a real run amendment or prove installed continuation.

## Alternatives considered

| Alternative | Disposition |
|---|---|
| Edit the original member list or reuse the initial approval | Rejected because neither action captures consent for the exact new plans and grants. |
| Retire the active run and create a replacement | Rejected because it would require transferring existing claims, history, blockers and limits into a separate authority lifecycle. The existing run can preserve them directly. |
| Make resume discover and adopt new plans | Rejected because session ownership continuation and scope expansion are separate decisions. |
| Include mutable implementation state inside immutable accepted pages | Rejected because normal publication, archive and handoff would invalidate the approval history. |
| Let older readers ignore amendment fields | Rejected because cleanup, archive, runner and completion checks could operate on different member sets. Explicit participation and conditional authentication provide a refusal boundary. |
| Re-sign every legacy record with a globally changed payload | Rejected because unamended records need no new protocol and retain their existing compatibility. |

## Consequences

Maintainers must qualify and deliver the participating helper bundle together. New conditional fields and writer transitions need regression coverage for stale capture, replay, partial installation, original authority preservation and later operational writes. Genuine native continuation remains a separate installed-runtime step after protected integration and verified delivery.

The run retains its original blockers and aggregate spending and retry limits. Adding a member grants no installation authority, no unrelated worktree deletion, and no permission to migrate a path-bound worker without the existing supported handoff and ownership checks. The bounded historical v4.15 compatibility remains tied to its original five-member identity.
