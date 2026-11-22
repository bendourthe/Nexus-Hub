---
description: Show the full implementation progress report for a run, a minor, or one plan, read-only. Use to "show progress", "show status", "how far along is the run", "show implementation progress", "what is running", "full progress", "full status". SKIP - starting or resuming work (use /implement) and shipping a release (use /update release).
---

# /progress Command

Print the full progress report for an implementation run, a minor, or a single plan. `/progress` has no scopes. It only reads and reports.

Usage: `/progress [vX.Y | vX.Y.Z | plan-path | plan-slug]`

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). It holds no logic beyond argument resolution.

## Read-only guarantee

`/progress` starts no work. It changes no file and no run state, spawns no worker, runs no test, and enters no release scope. It never reads or enters the implementation driver (`implement-phase` SKILL.md, runbook, approval or release sequences).

## Resolution

- No argument: use the current run's scope.
- A `vX.Y` target shows every member plan of that minor; a `vX.Y.Z`, plan path or plan slug target shows every phase of that plan. An explicit target can report an idle plan without starting it.
- Several plausible runs: list their identifiers and ask which.
- No run: say `No active implementation run` and accept an explicit plan target.
- Extra or malformed arguments: print the usage line above and stop. Never fall back to another command.

## Delegation

Read these two references directly:

      (any invocation) -> implement-phase/references/progress-reporting.md (scope, evidence, remaining time)
                       -> implement-phase/references/status-formats.md (presentation)

- [progress-reporting.md](../skills/workflow/implement-phase/references/progress-reporting.md) owns scope, evidence (task counts from `plan_status.py --plan`, elapsed time from each plan branch's own commits) and remaining-time rules.
- [status-formats.md](../skills/workflow/implement-phase/references/status-formats.md) owns the layouts.

Always print the FULL report, never the compact footer. Build the snapshot with `implement-phase/scripts/status_snapshot.py --repo <repo> --scope <target>`, which measures task counts, elapsed and remaining time from git and the plan files; never write those values by hand. A report never prints `unknown`: `N/A` means not started (Elapsed) or done (Remaining). The report opens with the four-row release table (last release, next release, next release ETA, whole-scope implementation); never reuse the whole-minor estimate as the next-release ETA.

Verbatim output rule: run `implement-phase/scripts/status_report.py` with event `request` for the full report (event `checkpoint` or `turn-end` with a prior receipt for the compact report), print its stdout verbatim with no code fence and no text before or after it (only a one-line error if the renderer fails), and never hand-write a status table. Natural-language "full progress" and "full status" use this same read-only path. During an `/implement` run the compact report appears only at reporting boundaries; the footer rule is in `progress-reporting.md`, and the footer points here with `*Full report: /progress*`. `/update status` is a forwarding alias for this command; the old `/status` alias was removed in v4.15.5.
