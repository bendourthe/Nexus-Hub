# Checker Fix Plan Review

Planning evidence for maintainers reviewing the v4.15.4 checker fix before implementation. Covers the consumer handoff disposition, release placement, independent review findings, preservation constraints, validation, and the remaining maintainer confirmation.

**Date**: 2026-10-18
**Plan**: [Checker Evidence and Diagnostics](../plans/v4.15.4-checker-evidence-and-diagnostics.md)
**Scope**: Planning only; no runtime, installer, consumer-repository, or signed-record edits.
**Baseline**: Checkout d577e11037b25647aa466da4c01e1ecdadfe6aeb; recorded origin/develop 8b32922ca573fb57546611267b88246c1064f1e4. Confirmation fetched origin and fast-forwarded develop to 3415ddb697d2edb03e0d1c9c4ddadfe86c708bc2. The inspected checker sources have no additional changes after the reviewed 8b32922ca integration baseline.

## Goal and Cut Lines

Five phases and 23 implementation tasks protect evidence, accept legitimate checker inputs, report missing approval coverage, improve read-only diagnosis, and detect archive hazards before movement. The goal does not include historical-ledger cutoffs, test-failure waivers, record rebasing, prompt-capture redesign, cleanup exemptions, automatic non-Markdown rewrites, or cross-worktree mutation. Handbook CRLF normalization is already fixed and retained as a regression boundary.

The source handoff is Downloads/v2.15.0-nexus-hub-checker-handoff.md. Its 13 numbered items are reproduced as dispositions in the plan; no dependency on this untracked source is required for implementation. The earlier review's temporary CLI reproductions are prior-turn evidence, not new implementation qualification.

## Placement

The first draft used the free v4.14.7 patch. Independent feasibility and scope lenses demonstrated that this would interfere with the existing frozen seven-member run: completion_minor.new_members scans every same-minor plan, explicitly ignores Status for added plans, and reports unapproved unshipped members; check_minor then returns BLOCKED: new-member-not-approved. minor_close also rejects unchecked tasks and queued plans outside membership.

The unapproved new draft was therefore re-placed to v4.15.4 and the temporary v4.14.7 path removed after edit-guard checks. No existing plan was renumbered. Recorded origin/develop reserves v4.15.0 through v4.15.2 as plans and v4.15.3 as a comparison adoption target; no v4.15.4 plan or tag was found. The queue enumerator reports 33 plans after adding this draft, with 32 predecessor/candidate rows in the plan and seven unresolved undeclared memberships. The slot was revalidated against fetched origin at confirmation; future run membership is revalidated before implementation/publication.

## Review Coverage

Seven independent lenses ran: coherence, feasibility, product, scope-guardian, design, security, and adversarial. Technical path/record boundaries justified design, security, and adversarial coverage. No lens was skipped. Reviews were read-only; the author applied corrections. Findings were deduplicated by location/root cause, cross-lens agreement was retained, and the confidence gate was applied last. No low-confidence finding was suppressed or retained as filler.

| Severity | Lens | Location | Finding | Confidence | Disposition |
|---|---|---|---|---|---|
| P1 | Feasibility, scope | Placement | Same-minor draft blocks the frozen run regardless of Draft status. | 100 | Resolved: moved only this new draft to v4.15.4; targeted feasibility recheck returned no remaining findings. |
| P2 | Coherence | T011 | Operational-reference classification was undefined. | 100 | Resolved: initial JSON/attributes support, protected historical inputs, informational mentions, and unsupported-input limits are explicit. Targeted coherence recheck passed. |
| P2 | Coherence | T008/T011 | Bounded diagnostics lacked measurable limits. | 100 | Resolved: time, output, record, and file-size limits plus interruptible fallback, deterministic omissions, and fail-closed incomplete archive inventory are specified. Targeted coherence recheck passed. |
| P2 | Product | T011-T013 | Archive refusal lacked recovery and a successful end-to-end case. | 75 | Resolved: remedies preserve sealed receipts; rerun after explicit live-source correction and prove archive success, operational path resolution, and handbook freshness where applicable. |
| P2 | Design | T011/T013 | Evidence byte preservation conflicted with existing Markdown repair. | 100 | Resolved in draft: raw non-Markdown/JSON preservation and the existing Markdown navigation exception are separate; a Markdown receipt regression and transformation counts are required. Targeted design recheck returned no remaining findings. |

The two lenses reporting the placement defect describe one root cause, not two defects. Five unique findings resulted from six raw reports; all are addressed in the draft. All targeted rechecks returned no remaining findings. READY for maintainer confirmation: 0 unresolved P0/P1 findings; 0 unresolved P2 findings. This is not implementation approval.

## Considered but Rejected

- Blocker creation changes a record while detail promises byte equality: these are explicitly separate operations; only diagnostic calls promise record equality.
- The mandatory final phase appears to authorize unrelated refactors and gap fixes: explicit scope controls make unrelated findings report-only and require a plan delta for proven installer changes.
- Related-worktree diagnostics could transfer authority: the plan forbids rekeying, session adoption, baseline inheritance, redirected writes, and mutation, and verifies controller scope first.
- A new generic archive engine might be necessary: existing tracked inventory, repair transaction, and refusal boundaries are sufficient for bounded preflight/reporting.
- Ordinary hard-link aliases might mutate a protected evidence inode: the current Unicode writer uses temporary-file atomic replacement. Explicit hard-link, symlink, and junction controls are still required by the plan.
- Tampered detail could expose trusted-looking approval scope: the plan permits only verification failure and independent repository facts when record integrity is unproven.
- Item selectors might approve new gaps: they record missing authority only; unknown IDs, foreign sessions, and frozen-scope changes remain rejected.
- Early native installer qualification might force intermediate remote CI: isolated local proofs and existing terminal platform jobs remain separate, with no non-final push.

## Planning Validation

- Strict structure check: five phases; 23 unique sequential T001-T023 checklist tasks; final template expanded; ASCII text; rejected same-minor draft absent.
- Queue enumeration: exit 0; 33 plans including the new draft. Existing queue inventory before the draft: 32 plans, exit 0, no unreadable files.
- Documentation colocation: exit 0, no comparison/adoption mismatches.
- Documentation group: python scripts/ci/run.py --profile full --only docs --quiet; exit 0; 10 passed, 0 failed, 0 skipped, 0 advisory in 12.0 seconds. Its active-minor convention check alone does not qualify this future plan; the independent structure and scoped checks above cover the new file directly.
- Model map: all four public provider catalogs re-read; candidate validate/diff/render passed, no reclassified IDs; five phase scores match the plan. Host availability and the Composer Fast alias are explicitly revalidated later.
- Scoped Unicode sanitation passed with zero repairs after review; repeat against the finalized plan, review, and tracker before committing.

These are planning checks. No implementation regression suite, full runtime gate, deployed behavior, or remote integration result is claimed.

## Tracker Preservation

The default edit guard refused docs/todos.md because its current bytes differ from an earlier stored baseline. Its current content was retained. The diff adds or updates the refresh date, one-minute usage-alert fix, Gemini monitor completion, integration and cleanup records, the open Cursor writer issue, queued memory/settings/context plans, and the integration-branch planning rule. Those are existing tracker changes and are not replaced by this task.

The maintainer confirmed on 2026-10-18. The same-session diff was reviewed and docs/todos.md accepted through edit_guard.py before mutation. That acceptance retained all current additions; the clean integration branch was then fast-forwarded and re-recorded. Only the confirmed queued-plan entry was added on top of current upstream content. This is the one acceptance used by this task.

The global guard's pruning pass also stalled on an unrelated stored record read. A bounded diagnostic identified prune as the location. Only the newly created plan and review artifact use a fresh private task-specific store through the helper's supported NEXUS_EDIT_GUARD_DIR option. After confirmation the guard's own cmd_diff/cmd_accept/cmd_check/cmd_record handlers were used against the original global store without its stalled pruning housekeeping. All fingerprint, exact-diff/session checks, and audit logging remained active. No records or baselines were edited manually.

## Confirmation Gate

The implementation-plan skill requires maintainer confirmation of the phase breakdown before final generation/commit/publication. The user-edit-preservation skill requires agreement before accepting a detected change. That confirmation was received on 2026-10-18 for v4.15.4 scope/placement/phases and the additive tracker entry. Planning artifacts may now be committed and published through the planning workflow. Implementation and runtime publication remain unauthorized.
