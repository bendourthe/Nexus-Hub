# Decision: Planned Follow-On Gaps Migrate at Minor Close

Status: implemented - recognition shipped in the completion checker; first used by v4.14.1.

Maintainers of the completion checker and plan authors use this record when a plan task's deliverable is a known gap that names future work. It covers which entries count as a planned follow-on, how they reach the next minor, and what stays forbidden.

**Date**: 2026-10-20. **Source**: v4.14.1 tasks T004 and T005, which file the lower-direction modifier and the raise-direction measurement as known gaps owned by a later instrument.

## Problem

A minor run closes only when every open gap in its ledger is resolved or migrates to the next minor. Migration was allowed only for ids in the run's frozen `gap-migration` list, taken at the start, because a gap created during the run is usually a defect the run itself introduced, and deferring it would let a run declare itself done while leaving its own breakage behind.

Some plans, though, deliberately file future work as a gap: a task whose whole job is "record this as a known gap for a later version". That entry is the task's deliverable, not a defect, but it is new during the run, so it could never migrate and the minor could never close.

## Decision

The checker recognizes a planned follow-on and lets the minor close migrate it, as an open item, to the next minor's `.0` section. Recognition is narrow:

- Only a `DF` entry derived by `planned_followon_entry` from a verified minor member's exact frozen plan qualifies. The plan must contain exactly one `File ... as a known gap <ledger>` task for it, with matching phase, sub-step, and prompt, and explicit Reason and Suggested next step fields.
- The entry's heading and whole body must equal the derived canonical text: an OPEN planned-follow-on disposition, the version, phase, and task, the plan filename, the frozen plan hash, the task hash, and the prompt's reason and next step. Any extra, altered, duplicated, or sensitive content disqualifies it.
- The member's pending-carry check and the minor's migration check use the same classifier, and one shared copy validator checks every new or reused target copy before any write and again during verification. The copy stays OPEN with its canonical body.
- After the minor's archive moves the plan, the original plan is reconstructed only from the member's signed publication-start commit, in the canonical archive layout with no active source tree, so archived entries keep their original hashes.

Nothing else changes: the 83 frozen migration ids, the approval classes, budgets, retry and publication limits, and the rule that an ordinary new gap never migrates.

## Alternatives considered

1. **Add the new ids to the run's `gap-migration` list.** Rejected: that list is signed into the run record at approval time. Editing it mid-run would forge an approval, and a fresh approval round for two recording tasks would reset frozen budgets.
2. **Resolve the entries instead of migrating them.** Rejected: the work they describe needs an instrument a later version builds, so marking them resolved would claim work that has not happened.
3. **File the gaps directly in the next minor's ledger.** Rejected: the frozen tasks name the current minor's ledger as their deliverable, so the task evidence would not match the plan, and the next minor's ledger is outside the run's write scope.
4. **Exempt every gap whose Source phase names a plan task.** Rejected: that is exactly the loophole the no-new-defect rule closes; a run could relabel its own defects as planned work. Binding to the canonical body and task hash closes it.

## Consequences

- A plan can now file future work as a gap and still let its minor close, as long as the entry is the exact text its frozen task produces.
- Any hand edit to such an entry, including a useful one, removes its eligibility; corrections belong in a new gap in the next minor after migration.
- The checker fails closed on every unsupported or ambiguous form. One known effect: an empty, untracked leftover folder at an active source path blocks archive-time reconstruction until it is removed.
- `tests/validators/test_planned_followon_gaps.py` covers recognition, denial cases, the migration copy, archive reconstruction, and write preflight against the real modules.
