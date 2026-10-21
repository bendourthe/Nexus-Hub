# Decision: Recorded Follow-On Gaps From Pre-Template Plans Migrate at Minor Close

Status: implemented - recognition shipped in the completion checker beside the exact-template form.

Maintainers of the completion checker and plan authors use this record when a frozen plan written before the `File <scope> as a known gap <ledger>` template still has tasks whose job is to record future work as known gaps. It extends [the 2026-10-20 planned follow-on decision](2026-10-20-planned-follow-on-gaps-migrate.md) and covers which of those tasks qualify, what an entry must bind, and what stays forbidden.

**Date**: 2026-10-21. **Source**: the v4.14 minor run. Frozen tasks v4.14.2 T002 (the parked write-containment hook) and T023 (a rule left at NO_CHANGE), v4.14.3 T009, v4.14.5 T014 (the parked doctor warning) and v4.14.6 T038 (its follow-ons and Not-Settable cells) all record known gaps, and none uses the template, so each entry would have made MINOR COMPLETE v4.14 impossible. The maintainer chose to teach the checker.

## Problem

The 2026-10-20 rule derives a planned follow-on's entire entry, including its reason and next step, from a templated task and prompt. Plans frozen before that template state no reason and often record several gaps from one reconciliation task, so their entries cannot be derived. Under the old rule every such entry is a new gap that can neither migrate nor honestly be marked resolved.

## Decision

A second recognized form, for frozen recording tasks without the template:

- The task qualifies only from its frozen wording: its line names the plan's minor ledger and says it records, files, or makes a known gap; or its line reconciles known gaps including a parked item; or its own sub-task prompt says "record a known gap" or "add one entry per/for each". A task the exact template already derives never uses this form, so its reason and next step stay derived. Against the real v4.14 plans this selects exactly v4.14.2 T002/T023, v4.14.3 T009, v4.14.5 T014 and v4.14.6 T038.
- The entry binds every field it can: an OPEN planned-follow-on disposition, the version with the task's real phase and id, the plan filename, the frozen plan hash and the exact task hash, then one-line Reason and Suggested next step fields and nothing else.
- Its title names a scope of at least eight characters that the frozen plan states verbatim, so every deferred item is something the approved plan itself named, and no two entries in the minor's ledgers share a task and title.
- The existing DF-only, non-sensitive, verified-member, migration-copy and archive-reconstruction rules apply unchanged. Every other new gap stays non-deferrable, and the run's frozen approvals, migration list, and budgets are untouched.

## Alternatives considered

1. **File each follow-on directly in the next minor's ledger and mark the current entry resolved.** Rejected: it gets around the no-unapproved-deferral rule rather than changing it openly, and "resolved" would claim work that has not happened.
2. **Leave the entries as written.** Rejected: the minor could then never print MINOR COMPLETE, so the frozen plans would be unfinishable as approved.
3. **Accept any entry whose Source phase cites a plan task.** Rejected for the same reason as in the 2026-10-20 record: a run could relabel its own defects as planned work. The verbatim-scope, task-wording, and hash bindings close that.
4. **Require exactly one entry per task.** Rejected: v4.14.6 T038 mandates one entry per follow-on and per Not-Settable cell. Uniqueness is enforced per task and title instead.

## Consequences

- Pre-template plans can record their mandated follow-ons and still let their minor close.
- The reason and next step of a recorded entry are free text, so they are reviewed by people, not derived; the scope, task, plan, and hashes are still machine-checked.
- `tests/validators/test_recorded_followon_gaps.py` covers recognition and every denial case against the real frozen v4.14.2 plan.
