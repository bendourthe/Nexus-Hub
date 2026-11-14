# Status Report Formats

Summary: the approved layouts for the compact status footer and the full status report, plus the measured-data rule for elapsed and remaining time. `/status` prints the full report on request; an active `/implement` run ends every message with the compact footer. `progress-reporting.md` owns when a report appears; this file owns how it looks.

## Compact footer

1. Emit it at the end of every message that ends while a run is in progress, after a `---` rule. It is the default.
2. First line: bold `**Status: v<X.Y>**`, then a 10-segment bar and whole percent, then task counts, then the last released version (`last released v<X.Y.Z>`, or `none released yet`), then the number of versions still to release (`N versions left`; a plan folded into another counts as none), then remaining time, separated by `&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;` because Markdown collapses plain spaces. Remaining time shows a figure only when the measured data rule below supplies one; otherwise it reads `time left: not measured yet`.
3. A waiting block: the waiting label, `N decisions waiting:`, and a bullet per decision, each titled so it stands alone (`#1 Approval-mode gap`). Omit the block when none are waiting.
4. A running block: the running label, `N running:`, and a bullet per running item, linked to its page, with bar, percent and a short parenthetical (`(CodeQL fix)`). A final bullet may state a shared state such as `both stopped, waiting on decision #3`. Omit the block when nothing is running.
5. End with one italic pointer line: `*Full report: /status*`.
6. A message that asks the user for a new decision shows the full report, never the compact footer. The footer lists decisions only as a reminder of ones already asked, and never carries a decision that is being asked for the first time.
7. Decision numbers restart at 1 for each new batch of open decisions; they do not continue from decisions already answered, except that a still-open decision carried over keeps its number when renumbering would confuse a reference to it.

## Full report

1. Three sections, in order, each separated from the next by a `---` rule: Status Update, Waiting on you, Running now.
2. A `&nbsp;` paragraph precedes EVERY `---` rule (after the plan table and after the last decision's table), so both rules sit at the same distance from the table above.
3. Heading `## Status Update: v<X.Y> Implementation Progress`. No summary line under it; the Total row carries it.
4. One plan table with columns in this order: Version | Goals | Progress | Tasks | Elapsed | Remaining. No Status column.
5. Version is bold (`**v4.15.4**`). Goals are two short descriptive goals per plan, separated by an escaped pipe, `Goal 1 \| Goal 2`, in one cell, never extra rows (multi-row cells and `<br>` render badly).
6. Progress is a 10-segment bar (filled segment for done, empty segment for not done) plus a whole percent, not in backticks. Filled segments are `floor(percent / 10)`; the bar is always 10 segments (U+25B0 filled, U+25B1 empty). Tasks is `done/total`. The Total row is last with bold totals; its percent is summed checked over summed total, never an average of percents.
7. Dependencies go in Remaining, for example `~1.5 d (after v4.15.2)`.
8. No Timing section. State an estimate's basis only when it changes. Table border thickness is set by the chat renderer and cannot be styled from Markdown.
9. The Waiting on you section has, per decision in numeric order, a `### <keycap> Decision #<n>: <title>` heading (a keycap number emoji for each decision, in order, as in the example), then 1 to 3 bullets that explain it so it stands alone (never a bare "Decision #1"), then an options table with columns Option | What it means | Effect, with `A (recommended)` first and `B` after. No extra spacer between a decision's table and the next decision heading.
10. The Running now section is a table with columns Item | Progress | Tasks | State | Elapsed | Remaining. Item is linked to its page (for example the pull request checks URL). Progress is the bar plus percent. Tasks is done/total checks. Elapsed is measured from the run's start. Remaining comes from observed durations of the same job.
11. All three section headings sit at the same level (`##`).
12. A message that asks the user for a new decision shows the full report, never the compact footer. The Waiting on you section of that report carries the decision details and the options tables.
13. Decision numbers restart at 1 for each new batch of open decisions; they do not continue from decisions already answered, except that a still-open decision carried over keeps its number when renumbering would confuse a reference to it.

## Measured data rule

Elapsed and Remaining come only from measured data: each plan's own commits on its plan branch (first commit time to now, or to the last commit when the plan is complete) and the run's observed per-task and per-release durations. A value without a measured source prints as `unknown`, never an estimate invented to fill the cell. Blocked time is reported separately from active time. The existing remaining-time rules in `progress-reporting.md` (ranges, dependency chain, no division by agent count) stand and supply the Remaining values.

## Worked example: compact footer

```markdown
---

**Status: v4.15** ▰▱▱▱▱▱▱▱▱▱ 11%&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;43/382 tasks&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;last released v4.15.0&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;11 versions left&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;time left: not measured yet

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
| **v4.15.0** | Trim always-loaded instructions \| Prove each cut with a behavior test | ▰▰▰▰▰▰▱▱▱▱ 60% | 18/30 | 3 d 4 h | ~1 d |
| **v4.15.1** | Adapt the harness per model \| Record the model map | ▰▰▰▰▱▱▱▱▱▱ 40% | 10/25 | 1 d 2 h | ~1.5 d (after v4.15.0) |
| **v4.15.2** | Measure harness cost \| Package the engineering system | ▰▱▱▱▱▱▱▱▱▱ 15% | 6/40 | 5 h | ~3 d (after v4.15.1) |
| **v4.15.3** | Add behavior checks \| Add security review evidence | ▱▱▱▱▱▱▱▱▱▱ 0% | 0/20 | 0 | unknown |
| **Total** | | ▰▰▰▱▱▱▱▱▱▱ **30%** | **34/115** | 3 d 4 h | ~5-6 d |

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
