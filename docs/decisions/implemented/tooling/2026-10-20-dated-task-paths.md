# Decision: Dated Task Paths Match One Real Date

Status: implemented - the completion checker matches a `YYYY-MM-DD` task path to one dated file.

Plan authors and completion-checker maintainers use this record when a task's deliverable is a dated file, such as a decision record, whose date is not known when the plan is frozen.

**Date**: 2026-10-20. **Source**: v4.14.1 task T018, which names `docs/decisions/proposed/policy/YYYY-MM-DD-raise-only-verification-effort.md`.

## Problem

The checker counts a task as done when a commit since the run's start touched the path at the end of its line. A plan that creates a dated record must name it by template, because the date is chosen when the record is written. No file can carry the literal `YYYY-MM-DD` name (the decision-record validator requires a real date), and a frozen plan cannot be edited, so such a task could never be met.

## Decision

A task path containing the token `YYYY-MM-DD` exactly once is a template. It is met when exactly one changed file since the run's start has a real calendar date (`YYYY-MM-DD` with a valid month and day) in that place and matches the rest of the path. Zero matches or several matches are unmet. Every other path keeps the exact-path rule.

## Alternatives considered

1. **Commit a file with the literal placeholder name.** Rejected: the decision-record validator refuses it, and a stub file would be clutter that claims a deliverable it is not.
2. **Edit the frozen plan to the real path.** Rejected: the frozen plan hash is the run's authority; changing it invalidates the approval.
3. **Treat a placeholder path as always met once ticked.** Rejected: a ticked box with no file behind it would pass, which is the evidence gap the path rule exists to close.

## Consequences

- A dated-record task completes only when its file actually landed; a second dated file with the same name tail makes it unmet rather than guessing.
- The rule is literal: only the exact token `YYYY-MM-DD`, once per path. Other placeholder forms (`<date>`, `{date}`) still need an exact path.
- `tests/validators/test_check_plan_completion.py::test_a_dated_task_path_matches_exactly_one_real_date` covers one match, none, two, and an invalid date.
