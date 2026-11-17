# Status Report Formats

Summary: the approved layouts for the compact status footer and the full status report, plus the measured-data rule for elapsed and remaining time. `/status` prints the full report on request; an active `/implement` run uses compact reports at the boundaries owned by `progress-reporting.md`. `progress-reporting.md` owns when a report appears; this file owns how it looks.

## Compact report

The canonical output is produced by [status_report.py](../scripts/status_report.py) from the evidence snapshot documented in [progress-reporting.md](progress-reporting.md). Do not hand-compose a shorter substitute. Cadence belongs to that reference; this file owns presentation.

1. Open with a `---` rule, then one bold status line: `**Status: <scope>**`, a 10-segment `▰`/`▱` bar with the whole-task percentage, done/total tasks, `last released <version>` and versions left, separated by `&nbsp;` gaps around a middle dot. Below it show the two-column header table described under Header table, so the Next release ETA cannot be mistaken for the Whole <scope> completion estimate.
2. Include the observation timestamp with timezone, elapsed time and evidence source. A zero-task scope reads `N/A`, never 100%; unknown counts remain unknown. Percentages and totals are derived from all rows, never from invented or stale counts.
3. Always show the goals, decisions and running parts, in that order, each introduced by its emoji label line: `🎯 Goals:`, `🙋 N decisions waiting:` and `🔄 N running:`. Renderer fonts are host-controlled; do not promise identical pixel sizes.
4. Goals are short bullets with goal, measurable done-when and state. Include the run goal, next known milestone and active lanes where applicable.
5. Decisions are bullets with stable ids and standalone titles. When empty, print `🙋 No decisions waiting.`. A newly requested decision uses the full report with its explanation and options.
6. Running items are bullets with name, optional observed HTTP(S) link, a bar with percent and state. When empty, print `🔄 Nothing running.`. Unknown liveness is stated explicitly, never converted to zero by guesswork.
7. End with `*Full report: /status, or ask for "full status".*`. Natural language works on hosts without slash-command support. Missing observations stay visible; they do not justify dropping a section.

## Full report

Start with `## Status Update: <scope> Implementation Progress`, then the header table, then one table with every scoped plan or phase and a bold Total row. Columns are Version (bold), Goals, Progress (`▰`/`▱` bar plus percent), Tasks, Elapsed and Remaining; a dependency is appended to Remaining, for example `~1.2 d (after v4.15.2)`. Follow it with the estimate basis. Every later section is preceded by a `&nbsp;` paragraph and a `---` rule and uses an H2 heading: `## 🎯 Goals` (Goal, Scope, Done when, State), `## 🙋 Waiting on you` and `## 🔄 Running now` (Item, Progress, Tasks, State, Elapsed, Remaining). Each decision is a `### 1️⃣ Decision #1: <title>` subheading, a bullet with the plain-language detail (recommendation and why), and an Option / What it means / Effect table; `meaning` is optional in the snapshot and prints `-` when absent. Empty sections use `No decisions waiting.` and `Nothing running.`. Never append a compact report to a full one.

The shared renderer escapes evidence text before inserting it into Markdown, so a plan title cannot introduce a heading, HTML, a link or extra table cells. It writes entities (`&#36;`, `&#91;`, `&#42;`), never backslash escapes: Codex reads `\(`...`\)` and `$...$` as LaTeX math, which run words together. Only table pipes use `\|`. Parentheses pass through unchanged. Font, table border and exact spacing are controlled by each product; identical semantic Markdown is the supported presentation contract.

## Header table

Both reports show the release facts as a two-column `Field | Value` table, never as run-on lines. Rows in order: Last released (bold version), Versions left, Next release (bold version), Release ETA, Blocked by (omitted when the condition is `none`), Confidence, Basis, Whole <scope>, As of, Elapsed. Keep each value short. Long explanations belong in the `Estimate basis:` line under the full table or are cut.

## Rendering rules

These rules are the contract for every agent and platform; the renderer enforces them and the producer of the snapshot must respect them.

- Never emit `$` or a backslash before a parenthesis or bracket. Hosts read `\(`...`\)` and `$...$` as LaTeX math and run the words together (for example an Elapsed value with a parenthetical, or a spend such as 38.36 of 500 dollars). The renderer writes `&#36;` for a dollar sign, `&#91;`/`&#93;` for brackets, `&#42;` for an asterisk, `&#96;` for a backtick, `&#92;` for a backslash and `&#95;` for a word-edge underscore. Parentheses pass through unchanged and render as plain text. Only a table pipe is written `\|`.
- Table cells are capped at 48 characters and end with `...` when cut; the producer shortens State, Elapsed and Remaining text instead of relying on the cap. No cell holds a paragraph or a line break.
- Tables are padded so source columns align, headers are plain labels, Version cells are bold, progress is a 10-segment `▰`/`▱` bar plus percent (never `#` bars), and the Total row is bold.
- Every heading, table and list has a blank line before and after it, and sections are separated by a `&nbsp;` paragraph and a `---` rule.
- The Source line is a short italic footer capped at 100 characters.

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

## Worked examples

Both examples are the exact renderer output for [status-snapshot.json](status-snapshot.json), an illustrative fixture and never live evidence. `tests/skills/test_status_command_contract.py` fails when either block differs from the renderer, so regenerate them with `python <skill-folder>/scripts/status_report.py --input references/status-snapshot.json --event request` after any renderer change (the compact block comes from `render(snapshot, "compact")`).

### Full

````markdown
## Status Update: v1.3 Implementation Progress

| Field         | Value                                   |
| ------------- | --------------------------------------- |
| Last released | **v1.2.0**                              |
| Versions left | 1 version                               |
| Next release  | **v1.3.0**                              |
| Release ETA   | unknown (no comparable release history) |
| Confidence    | unknown                                 |
| Basis         | No observed release durations           |
| Whole v1.3    | unknown (no comparable history)         |
| As of         | 2026-11-16T12:00:00Z                    |
| Elapsed       | 13 min                                  |

| Version     | Goals            | Progress           | Tasks    | Elapsed    | Remaining                           |
| ----------- | ---------------- | ------------------ | -------- | ---------- | ----------------------------------- |
| **Phase 1** | Package profiles | ▰▱▱▱▱▱▱▱▱▱ 16%     | 3/19     | 13 min     | unknown                             |
| **Total**   |                  | **▰▱▱▱▱▱▱▱▱▱ 16%** | **3/19** | **13 min** | **unknown (no comparable history)** |

Estimate basis: No comparable completed plans

&nbsp;

---

## 🎯 Goals

| Goal      | Scope | Done when             | State   |
| --------- | ----- | --------------------- | ------- |
| Ship v1.3 | run   | All 19 tasks verified | running |

&nbsp;

---

## 🙋 Waiting on you

No decisions waiting.

&nbsp;

---

## 🔄 Running now

Nothing running.

*Source: example/plan.md (illustrative fixture, not live evidence)*
````

### Compact

````markdown
---

**Status: v1.3** ▰▱▱▱▱▱▱▱▱▱ 16%&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;3/19 tasks&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;last released v1.2.0&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;1 version left

| Field         | Value                                   |
| ------------- | --------------------------------------- |
| Last released | **v1.2.0**                              |
| Versions left | 1 version                               |
| Next release  | **v1.3.0**                              |
| Release ETA   | unknown (no comparable release history) |
| Confidence    | unknown                                 |
| Basis         | No observed release durations           |
| Whole v1.3    | unknown (no comparable history)         |
| As of         | 2026-11-16T12:00:00Z                    |
| Elapsed       | 13 min                                  |

🎯 Goals:

- Ship v1.3 - All 19 tasks verified (running)

🙋 No decisions waiting.

🔄 Nothing running.

*Source: example/plan.md (illustrative fixture, not live evidence)*

*Full report: /status, or ask for "full status".*
````
