# Decision: Parallel implementation and ordered release

Status: implemented - independent worker admission and ordered publication; integration pending
Date: 2026-10-18
Author: Ben Dourthe
Template: Nygard

## Problem

A minor-version run contains several member plans. The earlier member gate required the preceding plan to be PLAN COMPLETE before the next could start, including release and cleanup. Independent plans therefore waited on unrelated hosted checks, release work and worktree cleanup. Manual parallel launch guidance could not overcome the native admission gate.

The maintainer requested concurrent implementation where dependencies and scopes permit, while retaining sequential releases. This requires separate implementation and publication admission, reusable parent authority and verifiable evidence after worker retirement.

## Decision

Use two native admissions under the existing signed minor record. record member-implement-start reserves a canonical linked worktree, approved branch, immutable implementation base, explicit semantic dependencies and exclusive read/write claims. Dependencies require the actual prerequisite merged commits in that base. Independent members do not wait for unrelated releases. The bounded coordinator dispatches the active harness agent tools as capacity opens; unsupported tools, unknown compatibility or unavailable worktrees produce an explicit serial fallback.

Keep record member-start as ordered publication admission. Every predecessor native predicate except cleanup must pass, including its own member gate, published release and green merged integration. Require a fresh live integration tip containing the previous release tag. Refresh the unpublished worker onto that tip. Exact coordinator write claims may then be admitted only when they conflict with no other active semantic claim. Apply and test pending shared implementation tasks before full final validation and the first push; hosted checks precede merge and release.

Workers own implementation, focused tests, plan-specific evidence and local phase commits. The coordinator owns shared ledgers, release metadata, aggregate trackers, signed state mutations and publication. A shared implementation task remains unchecked while its proposed change is unapplied. Generic broad validation reads a pinned isolated snapshot during implementation and is re-established on the refreshed final tree; genuine semantic read/write conflicts still block admission. The [completed-plan validation decision](2026-10-18-complete-plan-validation-cadence.md) retains ownership of testing cadence.

Claims stay occupied across interruption, failure and implementation-ready waiting until an actual merge is verified in integration. Active worker identity and changed paths are checked; historical merged contributions remain constrained by the signed scopes after legitimate worker removal. Native cleanup KEEP decisions for active controllers or workers are preserved. Cleanup remains required by the final minor verdict and does not gate the next member publication.

The [completion contract](../../../../catalog/skills/workflow/implement-phase/references/completion-contract.md) owns native admission and completion predicates, [plan-queue-assessment](../../../../catalog/skills/workflow/plan-queue-assessment/SKILL.md) owns compatibility, [multi-agent-coordinator](../../../../catalog/skills/orchestration/multi-agent-coordinator/SKILL.md) owns write-scope design, and [implement-phase](../../../../catalog/skills/workflow/implement-phase/SKILL.md) owns execution. No separate scheduling runtime is introduced.

## Alternatives considered

- **Wait for each release and cleanup before implementation.** Simple ordering, but serializes independent work and makes cleanup delay production. Rejected.
- **Implement and release all members concurrently.** Maximizes concurrency but loses version order and makes release provenance ambiguous. Rejected.
- **Launch separate standalone plan runs.** Reuses existing invocations but duplicates approval and spending authority and loses aggregate coordination. Rejected.
- **Bound independent implementation under one coordinator and keep publication ordered.** Selected. It exposes explicit ownership and waiting states while preserving release order and the full final gates.

## Consequences

- Eligible plans may progress while earlier members wait for release. Conflicting or dependent work remains ordered; no speed improvement is promised before actual execution.
- Existing schema-1 records and legacy schema-2 records without implementation claims retain their signature behavior. New native claims add signed controller binding; install the matching checker and minor helper together before the first reservation. Older readers cannot verify the extended signed state and must not be used after admission. No approval, nonce, frozen plan hash, aggregate budget or original run baseline is replaced.
- Worktrees provide workflow separation within the existing same-user trust model. They are not an operating-system security boundary. Shared budgets, review and stabilization limits apply to the entire run.
- Final validation is repeated only for invalidated scopes under its owning policy. Current required hosted checks and green merged integration still bind every release. The native checker, not a worker status message, decides completion.
