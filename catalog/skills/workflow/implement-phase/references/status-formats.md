# Status Report Formats

Summary: the approved layouts for the compact status footer and the full status report, plus the measured-data rule for elapsed and remaining time. `/status` prints the full report on request; an active `/implement` run ends every message with the compact footer. `progress-reporting.md` owns when a report appears; this file owns how it looks.

## Compact footer

1. Emit it at the end of every message that ends while a run is in progress, after a `---` rule. It is the default.
2. First line: bold `**Status: v<X.Y>**`, then a 10-segment bar and whole percent, then task counts, then the last released version (`last released v<X.Y.Z>`, or `none released yet`), then the number of versions still to release (`N versions left`; a plan folded into another counts as none), then remaining time, separated by `&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;` because Markdown collapses plain spaces. Remaining time is always an estimate from measured history (the estimate rule below), shown as the median with the middle-half range, for example `time left: ~3.2 d (2.2-8.3 d)`. It reads `time left: unknown (fewer than 3 completed plans)` only for a project with fewer than 3 completed plans.
3. A goals block directly after the status line: the label `🎯 Goals:` and 2 to 4 bullets, one per current goal, each `<goal> - <done when> (<state>)`. Order: the run goal, the next milestone, then the active lane goals. Keep each bullet to one short line with a measurable done-when.
4. A waiting block: the waiting label, `N decisions waiting:`, and a bullet per decision, each titled so it stands alone (`#1 Approval-mode gap`). Omit the block when none are waiting.
5. A running block: the running label, `N running:`, and a bullet per running item, linked to its page, with bar, percent and a short parenthetical (`(CodeQL fix)`). A final bullet may state a shared state such as `both stopped, waiting on decision #3`. Omit the block when nothing is running.
6. End with one italic pointer line: `*Full report: /status*`.
7. A message that asks the user for a new decision shows the full report, never the compact footer. The footer lists decisions only as a reminder of ones already asked, and never carries a decision that is being asked for the first time.
8. Decision numbers restart at 1 for each new batch of open decisions; they do not continue from decisions already answered, except that a still-open decision carried over keeps its number when renumbering would confuse a reference to it.

## Full report

1. Four sections, in order, each separated from the next by a `---` rule: Status Update, Goals, Waiting on you, Running now.
2. A `&nbsp;` paragraph precedes EVERY `---` rule (after the plan table, after the Goals table and after the last decision's table), so every rule sits at the same distance from the table above.
3. Heading `## Status Update: v<X.Y> Implementation Progress`. No summary line under it; the Total row carries it.
4. One plan table with columns in this order: Version | Goals | Progress | Tasks | Elapsed | Remaining. No Status column.
5. Version is bold (`**v4.15.4**`). Goals are two short descriptive goals per plan, separated by an escaped pipe, `Goal 1 \| Goal 2`, in one cell, never extra rows (multi-row cells and `<br>` render badly).
6. Progress is a 10-segment bar (filled segment for done, empty segment for not done) plus a whole percent, not in backticks. Filled segments are `floor(percent / 10)`; the bar is always 10 segments (U+25B0 filled, U+25B1 empty). Tasks is `done/total`. The Total row is last with bold totals; its percent is summed checked over summed total, never an average of percents.
7. Remaining is the estimate from the estimate rule below: median with the middle-half range, for example `~1.2 d (0.8-3.3 d)`. Dependencies go after it, for example `~1.2 d (0.8-3.3 d), after v4.15.1`. State the estimate basis in one line under the plan table.
8. No Timing section. Table border thickness is set by the chat renderer and cannot be styled from Markdown.
9. The Waiting on you section has, per decision in numeric order, a `### <keycap> Decision #<n>: <title>` heading (a keycap number emoji for each decision, in order, as in the example), then 1 to 3 bullets that explain it so it stands alone (never a bare "Decision #1"), then an options table with columns Option | What it means | Effect, with `A (recommended)` first and `B` after. No extra spacer between a decision's table and the next decision heading.
10. The Running now section is a table with columns Item | Progress | Tasks | State | Elapsed | Remaining. Item is linked to its page (for example the pull request checks URL). Progress is the bar plus percent. Tasks is done/total checks. Elapsed is measured from the run's start. Remaining comes from observed durations of the same job.
11. All four section headings sit at the same level (`##`).
12. A message that asks the user for a new decision shows the full report, never the compact footer. The Waiting on you section of that report carries the decision details and the options tables.
13. Decision numbers restart at 1 for each new batch of open decisions; they do not continue from decisions already answered, except that a still-open decision carried over keeps its number when renumbering would confuse a reference to it.
14. The Goals section is `## 🎯 Goals`, placed right after the plan table and its `&nbsp;` plus `---` separation. It is a table with columns Goal | Scope | Done when | State. Rows in order: the run goal (Scope `run`), the next milestone such as the next release or train, then one row per active lane (Goal is the plan's goal, Scope is the plan version, not bold). Cells are short and measurable; State is a word or short phrase such as `in progress`, `waiting on decision #1` or `not started`.

## Measured data rule

Elapsed comes only from measured data: each plan's own commits on its plan branch (first commit time to now, or to the last commit when the plan is complete) and the run's observed per-release durations. An Elapsed value without a measured source prints as `unknown`, never a figure invented to fill the cell. Blocked time is reported separately from active time.

## Estimate rule

Remaining time is never `unknown` when history exists. It is estimated from measured history:

1. Days per task for each completed plan is the elapsed time between that plan's release tag and the previous release tag, divided by that plan's task count. Read the tags with `git for-each-ref --sort=creatordate --format='%(refname:short) %(creatordate:iso-strict)' refs/tags/v*` and the task count with `plan_status.py --plan <plan-file>` on the archived plan.
2. Take the median days per task and the middle half (25th to 75th percentile) across completed plans. History so far, v4.13.1 to v4.15.0: 817 tasks over 49.8 days; median 0.035 d/task, middle half 0.023-0.096.
3. Per-plan remaining is remaining tasks times days per task, shown as `~median (low-high)`, for example 34 tasks gives `~1.2 d (0.8-3.3 d)`.
4. The total divides the summed per-plan estimate by the number of active parallel lanes, then adds the CI floor (the time one full CI run takes). Show it the same way.
5. State the basis in one line under the plan table: the rate, the history it came from, the lane count and the CI floor.
6. Refresh the rate as plans release and from the per-phase start and end times workers record.
7. With fewer than 3 completed plans (a new project), print `unknown (fewer than 3 completed plans)`.

`progress-reporting.md` keeps the dependency and external-wait rules (a wait with no known duration makes a conditional estimate, such as `2-3h after API approval`).

## Worked example: compact footer

```markdown
---

**Status: v4.15** ▰▱▱▱▱▱▱▱▱▱ 11%&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;43/382 tasks&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;last released v4.15.0&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;11 versions left&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;time left: ~3.2 d (2.2-8.3 d)

🎯 Goals:
- Ship v4.15 - all 12 member plans released and v4.15 closed (in progress)
- Release v4.15.1 - PR merged and tagged (waiting on decision #3)
- Lane v4.15.2 - harness cost measured and packaged (running)

🙋 3 decisions waiting:
- #1 Approval-mode gap
- #2 Memory index lines
- #3 CI tests job at its 60-min limit (blocks the release)

🔄 2 running:
- [#641](https://github.com/bendourthe/Nexus-Hub/pull/641/checks) ▰▰▰▰▰▰▰▰▰▱ 90% (CodeQL fix)
- [#639](https://github.com/bendourthe/Nexus-Hub/pull/639/checks) ▰▰▰▰▰▰▰▰▰▱ 91% (release)
- both stopped, waiting on decision #3

*Full report: /status*
```

## Worked example: full report

The numbers are illustrative and the example lists four of a minor's plans for brevity; a real report lists every member plan.

```markdown
## Status Update: v4.15 Implementation Progress

| Version | Goals | Progress | Tasks | Elapsed | Remaining |
|---|---|---|---|---|---|
| **v4.15.0** | Trim always-loaded instructions \| Prove each cut with a behavior test | ▰▰▰▰▰▰▱▱▱▱ 60% | 18/30 | 3 d 4 h | ~0.4 d (0.3-1.2 d) |
| **v4.15.1** | Adapt the harness per model \| Record the model map | ▰▰▰▰▱▱▱▱▱▱ 40% | 10/25 | 1 d 2 h | ~0.5 d (0.3-1.4 d), after v4.15.0 |
| **v4.15.2** | Measure harness cost \| Package the engineering system | ▰▱▱▱▱▱▱▱▱▱ 15% | 6/40 | 5 h | ~1.2 d (0.8-3.3 d), after v4.15.1 |
| **v4.15.3** | Add behavior checks \| Add security review evidence | ▱▱▱▱▱▱▱▱▱▱ 0% | 0/20 | 0 | ~0.7 d (0.5-1.9 d) |
| **Total** | | ▰▰▰▱▱▱▱▱▱▱ **30%** | **34/115** | 3 d 4 h | ~0.9 d (0.7-2.1 d) |

Estimate basis: 0.035 d/task (middle half 0.023-0.096) from 817 tasks over 49.8 days, v4.13.1 to v4.15.0; 81 tasks left, 4 active lanes, plus 0.2 d CI floor.

&nbsp;

---

## 🎯 Goals

| Goal | Scope | Done when | State |
|---|---|---|---|
| Ship the v4.15 minor | run | all 4 plans released and v4.15 closed | in progress |
| Release v4.15.0 | next milestone | PR merged and tagged | 60% of tasks done |
| Trim always-loaded instructions | v4.15.0 | 30/30 tasks, behavior tests green | in progress |
| Adapt the harness per model | v4.15.1 | 25/25 tasks, model map recorded | waiting on decision #1 |
| Measure harness cost | v4.15.2 | 40/40 tasks, cost report committed | in progress |

&nbsp;

---

## 🙋 Waiting on you

### 1️⃣ Decision #1: CI tests job at its 60-min limit

- The Linux tests job runs about 48 minutes and the repository policy caps jobs at 60 minutes.
- The release cannot proceed while the job can time out.

| Option | What it means | Effect |
|---|---|---|
| A (recommended) | Split the job into parallel shards | Release unblocked; adds CI jobs |
| B | Raise the cap to 90 minutes | Release unblocked; weakens the policy |

&nbsp;

---

## 🔄 Running now

| Item | Progress | Tasks | State | Elapsed | Remaining |
|---|---|---|---|---|---|
| [#641](https://github.com/bendourthe/Nexus-Hub/pull/641/checks) | ▰▰▰▰▰▰▰▰▰▱ 90% | 9/10 checks | stopped, waiting on decision #1 | 24 min | ~3 min |
| [#639](https://github.com/bendourthe/Nexus-Hub/pull/639/checks) | ▰▰▰▰▰▰▰▰▰▱ 91% | 10/11 checks | stopped, waiting on decision #1 | 41 min | ~4 min |
```
