# Progress Values Are Measured, Not Written

Summary: why `/progress` builds its snapshot with `status_snapshot.py` and why `status_report.py` rejects `unknown` in elapsed, remaining and task-count cells. Read before changing the progress renderer, the snapshot shape, or the estimate rule.

- **Status:** implemented
- **Date:** 2026-11-19
- **Scope:** `catalog/skills/workflow/implement-phase/scripts/status_snapshot.py`, `status_report.py`, `references/status-formats.md`, `references/progress-reporting.md`, `scripts/plan_status.py`

## Context

A `/progress` report for the v4.15 run showed `unknown` in every Elapsed cell, most Remaining cells and the Total row. The rules already required elapsed time from each plan branch's commits and remaining time from release history, but the snapshot was assembled by hand and the renderer accepted any text, so skipping the measurement was the easiest path. One plan also read 0 of 0 tasks because its tasks sat in a flat `## Task List` that `plan_status.py` did not count.

## Decision

1. A producer, `status_snapshot.py`, measures every number from git and the plan files. The agent's overlay carries only words and cannot set a task count, an elapsed or a remaining value.
2. The renderer rejects `unknown` in any Elapsed, Remaining or ETA and a version row without task counts, so a hand-written placeholder fails loudly instead of printing.
3. `N/A` has two meanings: not started (Elapsed) and released (Remaining).
4. With fewer than three measured releases the estimate uses the plan's own pace; only a project with no release and no finished task reads `N/A (no history yet)`.

## Alternatives considered

- **Tighten the written rule only.** Rejected: the rule already forbade the behavior, and the report still showed `unknown`. A rule the renderer does not check is advice.
- **Have the renderer read git itself.** Rejected: the renderer is a pure, host-independent formatter with tests built on fixed snapshots; mixing repository reads into it would make every rendering test depend on a git fixture.
- **Allow `unknown` with a reason, such as `unknown (no branch)`.** Rejected: every case it covered is measurable (deleted branches through merge commits, unstarted plans as `N/A`), so the escape hatch would only preserve the shortcut.
