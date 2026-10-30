# Implementation Progress Reporting

Summary: the shared progress-report contract for active `/implement` runs and read-only `/update status` requests. Coordinators use it to show task progress, observed worker activity, elapsed time, dependencies, estimates and efficiency decisions without changing completion or authorization rules.

## Entry points and cadence

- At implementation start or resume, emit an initial report and record the reporting interval, default 60 minutes. Honor a user-requested interval in ordinary language without adding a new implement mode token.
- During active work, check whether a report is due at task boundaries and when yielding from long-running tools. Emit at least once per interval when the host permits delivery, plus at phase completion, a new or cleared blocker, a material scope change, or a material change to the remaining-time estimate. Combine simultaneous triggers into one report. This cadence supplements ordinary short progress messages; it does not replace them.
- A host without timed callbacks cannot guarantee an exact hourly message while a tool blocks or the session is suspended. State that limitation once, report at the first available checkpoint, and show the actual timestamp and any missed interval. Do not install a scheduler, busy-poll, or claim delivery while inactive.
- One coordinator emits the consolidated report. Workers supply brief observations through the existing coordination channel; do not have every worker print duplicate tables or interrupt useful work solely to collect status. Report partial or stale observations rather than waiting indefinitely for a worker.
- `/update status [vX.Y|vX.Y.Z|plan-path|plan-slug]` emits one report immediately from available evidence. With no target, use the current run's scope. If multiple runs are plausible, list their identifiers and ask which; if none exists, say `No active implementation run` and accept an explicit plan target. An explicit target can report an idle plan without starting it. Reject extra or malformed arguments with usage, not a release fallback.
- Status-only entry reads this reference directly, bypassing the implementation pre-flight, approval, driver and release sequences. It does not start or resume work, spawn agents, change task marks, update trackers, mutate signed records, run builds/tests, or publish anything. Efficiency suggestions are advisory in this mode.

## Evidence and scope

1. Resolve the repository and run identity first. For a minor run, use the completion contract's member inventory, retaining already released and waiting members. Without an active run, resolve the requested minor through the same membership owner; do not silently substitute unrelated queued plans. For a specific plan, include every phase, including completed and not-started phases. Distinguish an empty scope from an unreadable inventory.
2. Obtain task counts with `python ~/.nexus-hub/scripts/plan_status.py --plan <plan-file>` in each authoritative worker worktree, or the integrated/archive copy for a retired worker. In a source checkout the equivalent is `python scripts/plan_status.py --plan <plan-file>`. Record the source and observation time; do not use a stale coordinator copy when a worker owns newer marks. If unavailable, report counts as unknown and name the missing source rather than inventing parser output.
3. Compute each row's task progress as `100 * checked / total`, rounded to a whole percent; display `checked/total` alongside it. Zero tasks means `N/A`, never 100%. Aggregate by summing checked and total tasks across the scope, not by averaging percentages. These are task-count percentages, not effort estimates. Deferred validation tasks remain unchecked. If tasks were added, removed or reopened, explain the denominator change or regression since the last report.
4. Read available native worker handles and the coordinator's existing run observations. Count unique workers currently executing work as active, and allocated but idle workers awaiting dependencies as waiting. Keep coordinator count separate; never infer agents from branches, claims or planned parallelism. A completed worker is not active, and an unassigned blocked plan has zero workers, not an invented standby agent. Unknown or old liveness is labeled unknown/stale with its observation time.
5. For each row, use observed start, pause, resume and completion timestamps from existing run observations or phase history. Show elapsed wall time since first observed start, including waits; freeze it at completion. Show known waiting duration separately where useful. A never-started row has zero elapsed; missing history is unknown or explicitly `observed this session only`. Do not infer active effort from commit dates or multiply elapsed time by worker count. Overall elapsed is the run's wall time, not the sum of overlapping rows.
6. Name the blocking task/phase/plan and its owner, the condition that releases the wait, and whether another eligible task is available. Distinguish dependency wait, approval wait, environment blocker, and implementation-ready waiting for ordered publication. Task completion and release readiness remain separate: even 100% task marks do not imply `PLAN COMPLETE` or `MINOR COMPLETE`; only the completion contract supplies those verdicts.

## Remaining time

Estimate a range per unfinished row from remaining work, observed comparable task durations, integration work and required validation. Name the basis and confidence briefly. Never extrapolate a task percentage as though tasks have equal cost. Where observations are insufficient, say `unknown` and state what observation would improve the estimate.

For the whole scope, estimate the remaining dependency chain and constrained worker capacity, including sequential integration/release work. Do not sum all parallel rows or divide by the agent count. Separate implementation ETA from end-to-end completion ETA when release, approval or external waits are unresolved. An external wait with no known duration makes an unconditional completion ETA unknown; a conditional estimate must say, for example, `2-3h after API approval`. Revise estimates visibly and explain material movement rather than preserving an obsolete promise.

## Report format

Use one timestamped headline, one row per plan for `vX.Y` or one row per phase for a specific plan, then at most three short bullets. Keep all rows; shorten names rather than omit idle members. Do not print a second legacy phase table at the same boundary: reuse its generated counts in this report. Links may carry detailed evidence beyond the compact report.

```text
Status vX.Y | as of <time and timezone> | tasks <done>/<total> (<percent>%)
Elapsed <wall time> | workers <active> active / <waiting> waiting | coordinator <count>
Remaining implementation <range/confidence> | end-to-end <range or unknown>

| Plan / phase | Tasks (%) | State | Workers active / waiting | Elapsed | Remaining estimate | Next / dependency |
| ... | ... | ... | ... | ... | ... | ... |

- Since last report: <completed work and task-count delta, or no measurable change and why>.
- Next: <next actions, longest dependency chain, named wait owner and unblock condition>.
- Efficiency: <decision made or advisory suggestion, reason, deferred checks and their trigger>.
```

At an initial report, replace the delta with `Initial observation`. During implementation, retain the compact observation and next report due time in the existing coordinator/session history at normal durable checkpoints so compaction or handoff can resume it. Do not create a parallel task ledger or add reporting fields to signed authority records. Read-only status requests do not persist anything. Missing historical observations remain visible after resume.

## Efficiency review

At each periodic report and blocker transition, review where elapsed time went using available observations: implementation, focused checks, rework and waiting. Unknown timings stay unknown. Choose one concrete adjustment or state why the current allocation remains appropriate.

- Check whether additional independent work can shorten the longest dependency chain. Compatibility belongs to `plan-queue-assessment`, worker scoping to `multi-agent-coordinator`, isolation to `using-git-worktrees`, and admission/authority to the completion contract. Within the active run's existing scope, capacity and spend limits, admit or reassign eligible workers through those owners. Never launch another run for an already claimed plan, overlap file ownership, parallelize dependent phases, or treat this review as expanded authority. When capacity or safe work is absent, state the limiting dependency instead of spawning idle agents.
- Revisit test timing through `cicd-integration` and the runbook's Phase 4. Prefer focused checks that can catch defects in current changes; batch broad tests whose inputs are still changing until the recorded final-validation trigger. Record deferred task IDs, affected inputs and the final destination. Reuse evidence only while its relevant inputs remain unchanged. Do not rerun builds or suites just to produce a status report.
- Retain explicit earlier acceptance checks, safety-critical prerequisites, known-failure repairs, required phase gates and final comprehensive validation. A later rewrite is not sufficient reason to ignore a present defect that blocks dependent work. Avoid both repeated broad testing and unverified accumulation of broken implementation.

## Ownership

This reference owns reporting cadence, scope, metrics and presentation. `plan_status.py` owns parsing phase task counts; the implementation runbook owns execution and test timing; `cicd-integration` owns test selection and evidence reuse; the completion contract owns authority and terminal verdicts. Reports observe these owners and do not redefine their gates.
