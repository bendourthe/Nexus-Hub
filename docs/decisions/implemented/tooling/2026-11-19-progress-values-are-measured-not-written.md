# Decision: Progress report values are measured, never written by hand

Status: implemented - `/progress` builds its snapshot with `status_snapshot.py`, and `status_report.py` rejects `unknown` in any elapsed, remaining or task-count cell.
Date: 2026-11-19
Author: Ben Dourthe
Template: Nygard

## Problem

A `/progress` report for the v4.15 run showed `unknown` in every Elapsed cell, most Remaining cells and the Total row. The rules already required elapsed time from each plan branch's commits and remaining time from release history, but the agent assembled the snapshot by hand and the renderer accepted any text, so skipping the measurement was the easiest path. One plan also read 0 of 0 tasks because its tasks sat in a flat `## Task List` ahead of its phases, which `plan_status.py` did not count.

## Decision

- A producer, `implement-phase/scripts/status_snapshot.py`, measures every number from git and the plan files. The agent's overlay carries only words (goals, decisions, running items, states) and cannot set a task count, an elapsed or a remaining value.
- The renderer rejects `unknown` in any Elapsed, Remaining or ETA, and a version row without task counts, so a hand-written placeholder fails with an error naming the producer instead of printing.
- `N/A` has two meanings: not started (Elapsed) and released (Remaining).
- With fewer than three measured releases the estimate uses the plan's own pace; only a project with no release and no finished task reads `N/A (no history yet)`.
- `plan_status.py` counts tasks listed before the first phase heading.

## Alternatives considered

- **Tighten the written rule only.** Rejected: the rule already forbade the behavior and the report still showed `unknown`. A rule the renderer does not check is advice.
- **Have the renderer read git itself.** Rejected: the renderer is a pure, host-independent formatter whose tests use fixed snapshots; repository reads would make every rendering test depend on a git fixture.
- **Allow `unknown` with a reason, such as `unknown (no branch)`.** Rejected: every case it covered is measurable (a deleted branch through its merge commit, an unstarted plan as `N/A`), so the escape hatch would only preserve the shortcut.

## Consequences

- A hand-written snapshot that still uses `unknown` now fails to render. That failure is intended and names the fix.
- Reports cost one producer run (a few seconds of read-only git calls) before rendering.
- The release-rate estimate is only as good as the recent release history; a burst of fast releases narrows the range, and the basis line says where the rate came from.
