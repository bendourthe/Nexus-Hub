# Status Report Formats

Summary: the approved layouts for the compact status footer and the full status report, plus the measured-data rule for elapsed and remaining time. `/progress` prints the full report on request; an active `/implement` run uses compact reports at the boundaries owned by `progress-reporting.md`. `progress-reporting.md` owns when a report appears; this file owns how it looks.

## Compact report

The canonical output is produced by [status_report.py](../scripts/status_report.py) from the evidence snapshot documented in [progress-reporting.md](progress-reporting.md). Do not hand-compose a shorter substitute. Cadence belongs to that reference; this file owns presentation.

1. Start with `## Progress Update` (no scope suffix; the scope sits in the last table row label). Below it show a table with an empty header row (`| | |`) so only four rows appear, labels bold and values plain: Last release, Next release, Next release ETA and `Full <scope> implementation (<N> versions left)`. The last value reads `progress: <bar> <percent>% (<done>/<total> tasks)   ·   ETA: <whole-scope estimate>`, with three literal spaces on each side of the middle dot (no `&nbsp;`; some renderers collapse the spaces, which is accepted). The bar is 10 `▰`/`▱` segments. This keeps the next-release ETA distinct from the whole-scope estimate.
2. A zero-task scope reads `N/A`, never 100%. A report never prints `unknown`; the measured values rule below says where each number comes from. Percentages and totals are derived from all rows, never from invented or stale counts. The compact report omits Elapsed and the Source line; the full report shows Elapsed in the version table and the Source line at the end. The snapshot still accepts `confidence`, `basis` and `observed_at`, but no report line prints them.
3. Always show `### 🎯 Goals`, `### 🙋 Decisions waiting` and `### 🔄 Running`, in that order, each preceded by a `---` rule and followed by bullets. Empty sections keep the heading with `None.`, `No decisions waiting.` or `Nothing running.`. Renderer fonts are host-controlled; do not promise identical pixel sizes.
4. Goals are bullets `goal - done when (state)`. Include the run goal, next known milestone and active lanes where applicable.
5. Each decision is a `#### 1️⃣ Decision #1: <title>` subheading followed directly by the Option / What it means / Effect table, then the snapshot's optional `reply` line such as `Reply A, B or C`, so the user can answer from the compact report; only the explanation bullet that the full report shows above the table is omitted. A decision with no options prints its title and `Options not supplied`, never a bare reply instruction. A newly requested decision still uses the full report with its explanation.
6. Running items are bullets `name: state`, with a bar and percent after the name when task counts are known and an optional observed HTTP(S) link on the name. Unknown liveness is stated explicitly, never converted to zero by guesswork.
7. End with the italic pointer `*Full report: /progress, or ask for "full progress".*`. Natural language ("full progress", and "full status" as a synonym) works on hosts without slash-command support. Missing observations stay visible; they do not justify dropping a section.

## Full report

Start with `## Progress Update`, then `### 🚀 Release status` directly above the same four-row release table the compact report uses (see Release table), then `### 📊 Version progress` directly above the detailed per-version table. The compact report has no such subheadings. The per-version table with columns Version (bold), Goals, Progress (`▰`/`▱` bar plus percent), Tasks, Elapsed and Remaining and a bold Total row; a dependency is appended to Remaining, for example `~1.2 d (after v4.15.2)`. Every later section is preceded by a `---` rule and uses an H3 heading, the same level as the compact report: `### 🎯 Goals` (a Goal, Scope, Done when, State table), `### 🙋 Decisions waiting` and `### 🔄 Running` (an Item, Progress, Tasks, State, Elapsed, Remaining table). Each decision is a `#### 1️⃣ Decision #1: <title>` subheading, a bullet with the plain-language detail (recommendation and why), and an Option / What it means / Effect table; `meaning` is optional in the snapshot and prints `-` when absent. Empty sections use `No decisions waiting.` and `Nothing running.`. The report ends with the short italic Source line. Never append a compact report to a full one.

The shared renderer escapes evidence text before inserting it into Markdown, so a plan title cannot introduce a heading, HTML, a link or extra table cells. It writes entities (`&#36;`, `&#91;`, `&#42;`), never backslash escapes: Codex reads `\(`...`\)` and `$...$` as LaTeX math, which run words together. Only table pipes use `\|`. Parentheses pass through unchanged. Font, table border and exact spacing are controlled by each product; identical semantic Markdown is the supported presentation contract.

## Release table

Both reports open with the same table: an empty header row (`| | |`), bold labels and plain values, in this order: Last release, Next release, Next release ETA and `Full <scope> implementation (<N> versions left)`. The last value reads `progress: <bar> <percent>% (<done>/<total> tasks)   ·   ETA: <whole-scope estimate>`, with three literal spaces on each side of the middle dot (no `&nbsp;`; some renderers collapse the spaces, which is accepted). With nothing left to release, Next release reads `none (all released)` and its ETA `N/A`. Confidence, Basis, As of and Elapsed are never rows or lines in the report; Elapsed appears only in the version table.

## Rendering rules

These rules are the contract for every agent and platform; the renderer enforces them and the producer of the snapshot must respect them.

- Never emit a bare `$` or a backslash before a parenthesis or bracket. Hosts read backslash-paren pairs and `$...$` as LaTeX math and run the words together. Any whitespace-delimited token that contains `$`, `*`, `_`, `[`, `]`, a backslash, a backtick, `&`, `<` or `>` is written as a code span such as `$38.36` or `my_var`, with edge punctuation left outside, which no client treats as math or markup. The renderer writes no HTML entities, so raw text never shows `&#..;`. Parentheses pass through unchanged and render as plain text. Only a table pipe is written `\|`.
- Table cells are capped at 48 characters (decision option text at 72, so the choices stay readable). A cell over the cap first loses a trailing parenthetical (`4 h 54 min (first plan commit ...)` becomes `4 h 54 min`), then is cut at a word boundary and ends with `...`; it is never cut mid-word or inside a parenthesis. The producer still shortens State, Elapsed and Remaining text. No cell holds a paragraph or a line break.
- Tables are padded so source columns align, headers are plain labels, Version cells are bold, progress is a 10-segment `▰`/`▱` bar plus percent (never `#` bars), and the Total row is bold.
- Every heading, table and list has a blank line before and after it, and sections are separated by a `---` rule.
- In the full report the Source line is a short italic footer capped at 100 characters; the compact report omits it.
- No output contains `&nbsp;` or any `&#..;` entity, because some clients print them literally. Spacing comes from blank lines and `---` rules only.
- Printing: run `scripts/status_report.py` (event `request` for full, `checkpoint` or `turn-end` with a prior receipt for compact), print its stdout verbatim with no code fence and no text before or after it (only a one-line error if the renderer fails), and never hand-write a status table. This is the Verbatim output rule that `/progress` and `progress-reporting.md` repeat.

## Measured data rule

Every number in a report is measured, so no cell ever reads `unknown`. Build the snapshot with [status_snapshot.py](../scripts/status_snapshot.py), which reads git and the plan files: `python <skill-folder>/scripts/status_snapshot.py --repo <repo> --scope <vX.Y|vX.Y.Z> [--overlay <notes.json>]`. The overlay carries only what git cannot know (goals, decisions, running items with a `started_at` time, a state or dependency per version, the next-release condition); it cannot set a task count, an elapsed or a remaining value. The renderer rejects a snapshot that contains `unknown` in any Elapsed, Remaining or ETA, or a version row without task counts.

- Tasks: every `T<n>` checkbox in the plan, read from the plan branch, or from the integration branch once released.
- Elapsed: the plan branch's own commits, first commit to now, or to the last commit once released. A deleted branch is found through its merge commit. A plan with no commits of its own has not started and reads `N/A`.
- Remaining: a released plan reads `N/A`. So `N/A` has exactly two meanings: not started (Elapsed) and done (Remaining). A running item without tasks, such as a CI job, reads `N/A` for Progress and Tasks.

Blocked time is reported separately from active time.

## Estimate rule

Remaining time is estimated from measured history (the producer applies this rule):

1. Days per task for each completed plan is the elapsed time between that plan's release tag and the previous release tag, divided by that plan's task count, over the 10 most recent releases that have a plan.
2. Take the median days per task and the middle half (25th to 75th percentile) across completed plans. History so far, v4.13.1 to v4.15.0: 817 tasks over 49.8 days; median 0.035 d/task, middle half 0.023-0.096.
3. Per-plan remaining is remaining tasks times days per task, shown as `~median (low-high)`, for example 34 tasks gives `~1.2 d (0.8-3.3 d)`.
4. The total divides the summed per-plan estimate by the number of active parallel lanes (started plans with open tasks). Show it the same way.
5. State the basis in one line under the plan table: the rate, the history it came from, the lane count and the CI floor.
6. Refresh the rate as plans release and from the per-phase start and end times workers record.
7. With fewer than 3 measured releases, use the plan's own pace (elapsed time divided by tasks done). Only a project with no release and no finished task reads `N/A (no history yet)`.

`progress-reporting.md` keeps the dependency and external-wait rules (a wait with no known duration makes a conditional estimate, such as `2-3h after API approval`).

## Worked examples

Both examples are the exact renderer output for [status-snapshot.json](status-snapshot.json), an illustrative fixture and never live evidence. `tests/skills/test_status_command_contract.py` fails when either block differs from the renderer, so regenerate them with `python <skill-folder>/scripts/status_report.py --input references/status-snapshot.json --event request` after any renderer change (the compact block comes from `render(snapshot, "compact")`).

### Full

````markdown
## Progress Update

### 🚀 Release status

| | |
|---|---|
| **Last release** | v1.2.0 |
| **Next release** | v1.3.0 |
| **Next release ETA** | ~2.2 d (1.6-4.0 d) |
| **Full v1.3 implementation** (1 version left) | progress: ▰▱▱▱▱▱▱▱▱▱ 16% (3/19 tasks)   ·   ETA: ~2.2 d (1.6-4.0 d) |

### 📊 Version progress

| Version     | Goals            | Progress           | Tasks    | Elapsed    | Remaining              |
| ----------- | ---------------- | ------------------ | -------- | ---------- | ---------------------- |
| **Phase 1** | Package profiles | ▰▱▱▱▱▱▱▱▱▱ 16%     | 3/19     | 13 min     | ~2.2 d (1.6-4.0 d)     |
| **Total**   |                  | **▰▱▱▱▱▱▱▱▱▱ 16%** | **3/19** | **13 min** | **~2.2 d (1.6-4.0 d)** |

---

### 🎯 Goals

| Goal      | Scope | Done when             | State   |
| --------- | ----- | --------------------- | ------- |
| Ship v1.3 | run   | All 19 tasks verified | running |

---

### 🙋 Decisions waiting

No decisions waiting.

---

### 🔄 Running

Nothing running.

*Source: example/plan.md (illustrative fixture, not live evidence)*
````

### Compact

````markdown
## Progress Update

| | |
|---|---|
| **Last release** | v1.2.0 |
| **Next release** | v1.3.0 |
| **Next release ETA** | ~2.2 d (1.6-4.0 d) |
| **Full v1.3 implementation** (1 version left) | progress: ▰▱▱▱▱▱▱▱▱▱ 16% (3/19 tasks)   ·   ETA: ~2.2 d (1.6-4.0 d) |

---

### 🎯 Goals

- Ship v1.3 - All 19 tasks verified (running)

---

### 🙋 Decisions waiting

No decisions waiting.

---

### 🔄 Running

Nothing running.

*Full report: /progress, or ask for "full progress".*
````

### Compact with a decision

````markdown
## Progress Update

| | |
|---|---|
| **Last release** | v1.2.0 |
| **Next release** | v1.3.0 |
| **Next release ETA** | ~2.2 d (1.6-4.0 d) |
| **Full v1.3 implementation** (1 version left) | progress: ▰▱▱▱▱▱▱▱▱▱ 16% (3/19 tasks)   ·   ETA: ~2.2 d (1.6-4.0 d) |

---

### 🎯 Goals

- Ship v1.3 - All 19 tasks verified (running)

---

### 🙋 Decisions waiting

#### 1️⃣ Decision #1: Keep the Claude Code and Codex split across restarts

| Option          | What it means                             | Effect                                                      |
| --------------- | ----------------------------------------- | ----------------------------------------------------------- |
| A (recommended) | Experiment, then build the opt-in restore | Split survives restarts, if a public API allows it (~2-3 h) |
| B               | Experiment only                           | Written finding, no code                                    |
| C               | Defer                                     | Recorded as a v4.15.8 follow-up                             |

Reply A, B or C

---

### 🔄 Running

Nothing running.

*Full report: /progress, or ask for "full progress".*
````
