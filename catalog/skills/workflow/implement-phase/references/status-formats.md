# Status Report Formats

Summary: the approved layouts for the compact status footer and the full status report, plus the measured-data rule for elapsed and remaining time. `/status` prints the full report on request; an active `/implement` run uses compact reports at the boundaries owned by `progress-reporting.md`. `progress-reporting.md` owns when a report appears; this file owns how it looks.

## Compact report

The canonical output is produced by [status_report.py](../scripts/status_report.py) from the evidence snapshot documented in [progress-reporting.md](progress-reporting.md). Do not hand-compose a shorter substitute. Cadence belongs to that reference; this file owns presentation.

1. Use `## Status: <scope>` as a real Markdown heading on its own line. Place a blank line before and after it. Below it, show bold Last released and Next release versions on separate lines. The Next release line includes Release ETA; follow it with confidence, estimate basis and any blocking condition. Label the overall estimate Whole <scope> completion so it cannot be mistaken for the next release ETA. Then show a 10-segment ASCII bar, whole task percentage, done/total tasks and versions left. Keep the title separate so it renders larger than the metric text.
2. Include the observation timestamp with timezone, elapsed time and evidence source. A zero-task scope reads `N/A`, never 100%; unknown counts remain unknown. Percentages and totals are derived from all rows, never from invented or stale counts.
3. Always show `### Goals`, `### Decisions` and `### Running`, in that order, with a blank line before and after each heading. Heading markers are not bold text or inline labels. Renderer fonts are host-controlled; do not promise identical pixel sizes.
4. Goals are short bullets with goal, measurable done-when and state. Include the run goal, next known milestone and active lanes where applicable.
5. Decisions are bullets with stable ids and standalone titles. When empty, print `No decisions waiting.`. A newly requested decision uses the full report with its explanation and options.
6. Running items are bullets with name, optional observed HTTP(S) link, measured task/check progress and state. When empty, print `Nothing running.`. Unknown liveness is stated explicitly, never converted to zero by guesswork.
7. End with `*Full report: /status, or ask for "full status".*`. Natural language works on hosts without slash-command support. Missing observations stay visible; they do not justify dropping a section.

## Full report

Use the same prominent Last released, Next release / Release ETA, confidence/basis/condition and Whole <scope> completion lines as compact status, along with the Status title, timestamp, totals and evidence source, followed by a table containing every scoped plan or phase and a Total row. Columns are Plan / phase, Goals, Progress / tasks, State, Elapsed, Remaining and Dependency. Follow it with the estimate basis and the same spaced `### Goals`, `### Decisions` and `### Running` headings. Goals use Goal, Scope, Done when and State columns. Each decision has a `#### Decision <id>: <title>` heading, plain-language detail and an Option / Effect table; the detail carries the recommendation and why. Running uses Item, Progress / tasks, State, Elapsed and Remaining columns. Empty sections use the same explicit messages as the compact report. Never append a compact report to a full one.

The shared renderer escapes evidence text before inserting it into Markdown, so a plan title cannot introduce a heading, HTML or extra table cells. Font, table border and exact spacing are controlled by each product; identical semantic Markdown is the supported presentation contract.

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

## Example generation

Use [status-snapshot.json](status-snapshot.json) as an illustrative fixture with `--event request` for full output. For compact output, supply a prior receipt for that fixture and advance its observation time to the next interval with `--event turn-end`. The fixture is never live evidence. This keeps examples tied to executable output instead of maintaining another handwritten layout.
