---
name: cross-artifact-analyzer
description: "Cross-artifact consistency, coverage, and ambiguity analyzer for a feature directory containing spec.md, plan.md, and tasks.md (plus the optional project constitution). Read-only - emits a severity-tagged findings table, a coverage matrix, and a metrics block; never modifies any file. Use whenever the user wants to audit a feature directory before implementation, check whether a spec is ready to plan, verify that every requirement has a task, surface ambiguity in functional requirements or success criteria, run a coverage gap analysis, check alignment of a plan against the project constitution, or get a deterministic findings report that the team can cite by ID. Trigger phrases include \"analyze the spec\", \"is this spec ready\", \"do all requirements have tasks\", \"coverage check\", \"ambiguity check\", \"spec-plan-tasks consistency\", \"cross-artifact analysis\", \"constitution alignment check on this plan\", \"find gaps in this feature\". Cross-links to `[[project-constitution]]`, `[[ambiguity-detector]]`, `[[spec-driven-development]]`, `[[implementation-plan]]`, and `[[known-gaps-tracker]]`. SKIP: full code-review of an implementation (use `[[code-quality]]` + `[[security-review]]`), single-file lint passes, runtime profiling, or test execution."
summary_l0: "Read-only cross-artifact analyzer for feature directories; emits severity-tagged findings, coverage matrix, and constitution-alignment verdicts"
overview_l1: "This skill drives the `/analyze-spec` command end-to-end. It loads minimal context from a feature directory's spec.md, plan.md, and tasks.md (plus the project constitution at docs/<version>/constitution.md if present), then runs six detection passes: Duplication (overlapping FRs, tasks, user stories), Ambiguity (vague adjectives without measurable thresholds, unresolved [NEEDS CLARIFICATION] markers, placeholder leakage), Underspecification (requirements without acceptance criteria, tasks without file paths), Constitution Alignment (PASS / FAIL / N/A per MUST principle), Coverage Gaps (requirements without tasks, tasks without parents), and Inconsistency (terminology drift, conflicting requirements, ordering contradictions). Each finding gets a deterministic ID (A1, D1, U1, C1, G1, I1) and a severity (CRITICAL / HIGH / MEDIUM / LOW). The report contains a Findings table, a Coverage Summary table, and a Metrics block. It is strictly read-only. Finding IDs stay stable across reruns so resolved items disappear and new items get the next integer per category."
---

# Cross-Artifact Analyzer

Run a deterministic, read-only consistency, coverage, and ambiguity check across a feature's spec, plan, tasks, and optional project constitution. The skill produces a structured Markdown report with severity-tagged findings - it never modifies any file in the feature directory.

## When to Use This Skill

- When the user wants to **audit a feature directory before implementation** to surface gaps before they cost rework.
- When the user asks **"is this spec ready to plan?"** or **"is this plan ready to implement?"**.
- When the user wants to **verify that every functional requirement (FR-###) and success criterion (SC-###) has at least one task** in `tasks.md`.
- When the user wants to **surface ambiguity** in functional requirements or success criteria (vague adjectives without measurable thresholds, unresolved `[NEEDS CLARIFICATION]` markers, placeholder leakage).
- When the user wants to **check alignment of a plan against the project constitution** without re-running `/generate-plan`.
- When the user wants a **deterministic findings report that the team can cite by ID** in commits, follow-up tasks, and review comments.

**When NOT to use**:

- For full code-review of an implementation - use `[[code-quality]]`, `[[security-review]]`, and the rest of the code-review category.
- For single-file lint passes - use the language-specific cleanup skills (`[[python-cleanup]]`, `[[javascript-cleanup]]`, ...).
- For runtime profiling or performance analysis - use `[[performance-review]]`.
- For test execution or coverage measurement of code - use the testing skills.

This skill operates on **specification artifacts**, not on running code.

## Inputs

| Input | Required? | Source |
|---|---|---|
| Feature directory path | Optional | Argument to `/analyze-spec`, else resolved via `.specify/feature.json`, else latest under `specs/<NNN>-*/` or `docs/<version>/plans/<slug>.md`. |
| `spec.md` | Recommended | Under the feature directory. If absent, the analyzer parses equivalent sections from the plan body itself. |
| `plan.md` | Required | Under the feature directory. For self-contained plans, this is the plan file itself. |
| `tasks.md` | Recommended | Under the feature directory. If absent, parse the `- [ ] T###` lines from the plan body. |
| Constitution | Optional | `docs/<version>/constitution.md` (recommended location) or `CONSTITUTION.md` at root. If absent, Pass 4 emits an informational N/A. |

## Instructions

### 1. Resolve the feature directory

Honor the argument from `/analyze-spec`. If none, walk this priority order:

1. `.specify/feature.json` `feature_directory` field (written by `/generate-plan --specs-layout` once Phase 7 of the adoption-spec-kit plan ships).
2. The most recently modified `specs/<NNN>-*/` directory.
3. The most recently modified `docs/<version>/plans/<slug>.md` (treat as a self-contained plan + spec).

If no candidate is found, abort with: **"No feature directory or plan file found. Run `/generate-plan` first, or pass an explicit `<path>` argument."**

### 2. Load minimal context

Read only what the detection passes need. Aim to keep total input under ~3000 tokens per artifact:

- `spec.md`: Overview, Functional Requirements (full table), Success Criteria (full table), User Stories (titles + Priority + Acceptance Scenarios), Edge Cases.
- `plan.md`: Architecture overview, Data Model references, Phase list with goals, Technical / cross-cutting constraints, Complexity Tracking table if present.
- `tasks.md`: Task ID, Description, Phase grouping, `[P]` parallel markers, `[US#]` story labels, file paths.
- Constitution: full file - it is small enough that excerpting risks missing a principle.

For self-contained plans (no separate `spec.md` / `tasks.md`):

- Functional Requirements -> prompts and goals inside each phase's sub-tasks.
- Success Criteria -> Stability Gate text at the top of each phase.
- Tasks -> `- [ ] T###` lines, or sub-task headings if Phase 6 strict task format has not yet been applied.

### 3. Run the six detection passes

Pass 1: **Duplication**. Detect overlapping FRs (different IDs, same capability), overlapping tasks (same file path + overlapping description), and overlapping user stories (same flow with different priorities).

Pass 2: **Ambiguity**. Detect vague adjectives in FR / SC text (`fast`, `scalable`, `secure`, `intuitive`, `simple`, `efficient`, `robust`, `reliable`) without a measurable threshold in the same sentence. Detect unresolved `[NEEDS CLARIFICATION: ...]` markers; if more than 3 are present, raise an additional finding (violates the 3-marker hard limit established in `[[project-constitution]]`). Detect placeholder leakage outside code fences: `[ALL_CAPS_IDENTIFIER]`, `TBD`, `TODO`, `XXX`, `<...>`.

Pass 3: **Underspecification**. Detect FRs without acceptance criteria or Independent Test text. Detect SCs that are not measurable (no number, boolean, or explicit pass/fail signal). Detect user stories without Given / When / Then acceptance scenarios. Detect tasks without file paths (post Phase 6 of the adoption-spec-kit plan, every task should reference at least one path).

Pass 4: **Constitution Alignment**. If the constitution file exists, scan each MUST principle against spec + plan + tasks and emit PASS / FAIL / N/A with a one-sentence justification. If the file does not exist, emit a single informational finding: **"No constitution file found at `docs/<version>/constitution.md` - skipping alignment pass. Run `/constitution` to establish principles."** This is N/A, not CRITICAL.

Pass 5: **Coverage Gaps**. For each FR-###, list matching tasks (matched by FR-ID mention, by file-path overlap with FR scope, or by user-story label if the FR is scoped to one story). For each SC-###, list contributing tasks (at least one task should produce the artifact the SC measures). Emit a finding for every FR / SC with zero matching tasks AND for every task that references no FR / SC / US (orphan task).

Pass 6: **Inconsistency**. Detect terminology drift (same concept named differently across artifacts - e.g., spec "User", plan "Account", tasks "Member"). Detect conflicting requirements (two FRs that contradict each other or contradict a constitution principle). Detect ordering contradictions (a task references something a later task creates).

### 4. Assign severity

| Severity | Heuristic |
|---|---|
| CRITICAL | Constitution MUST violation. Zero-coverage core requirement (FR also referenced in a user-story acceptance scenario). Direct contradiction between two FRs. |
| HIGH | Material duplication of scope. Ambiguity in security or performance FR without a measurable threshold. Untestable acceptance scenario on a P1 user story. |
| MEDIUM | Terminology drift. Missing non-functional task coverage (operational SC like observability, rollback). Underspecified P2 / P3 user stories. |
| LOW | Style or wording issues. Placeholder leakage in optional sections. Ambiguous adjectives in narrative prose where measurability is not expected. |

Promotion up the severity ladder is allowed when analyst judgment outranks the heuristic. Demotion is not allowed.

### 5. Assign deterministic IDs

- Category prefixes: `D` (duplication), `A` (ambiguity), `U` (underspecification), `C` (constitution alignment), `G` (coverage gap), `I` (inconsistency).
- Within each category, sort findings by the line number they reference in the source artifact (spec < plan < tasks if a finding spans artifacts). ASCII filename order breaks line-number ties.
- Number monotonically starting at 1 per category per run: `A1, A2, A3, ...`.
- No timestamps or hashes in IDs; the `Run date` field captures the timestamp. This is what makes IDs stable across reruns - rerun after fixing `A1` and the new ambiguity finding will be `A2` (not a reused `A1`).

### 6. Emit the report

Format per the template used by `/spec analyze`: header block + Findings table (50-row cap with overflow summary) + Coverage Summary table + Metrics block + Next Actions + the mandatory closing statement **"This analyzer is read-only. It modifies no files. Any remediation requires user approval."**

The report is written to stdout by default; if the command was invoked with `--output <path>`, also write it to that path. Do not write to any file under the feature directory.

### 7. Recommend remediation paths (do not perform them)

After the report, recommend the appropriate next command:

- Ambiguity / underspecification on the spec -> `/clarify-spec` (sequential 5-question loop with recommended-option tables; ships in Phase 5 of the adoption-spec-kit plan).
- Constitution-alignment findings that reflect intentional scope expansion -> `/constitution amend`.
- Coverage gaps -> direct edit of `tasks.md` (or the plan's in-line task list), then rerun `/analyze-spec`.
- Ordering contradictions -> reorder phases or split tasks; rerun.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is just a small feature, I don't need a cross-artifact analyzer" | Small features still benefit because the analyzer takes seconds to run and surfaces the kind of mismatches (FR with no task, SC that is not measurable) that small-feature plans drift into precisely because reviewers skip the audit. The cost of running it is ~30 seconds; the cost of finding a coverage gap mid-implementation is hours. |
| "The plan was generated by /generate-plan, it must be consistent" | `/generate-plan` produces a plan from a goal description; it does not cross-check the plan against an existing spec or constitution. If the spec was authored before the plan and the plan deviates, only this analyzer catches it. |
| "I'll just read the spec carefully myself" | Human readers miss terminology drift (Pass 6), unresolved `[NEEDS CLARIFICATION]` markers buried in long FR tables (Pass 2), and ordering contradictions (Pass 6) because those defects do not jump out of prose. The analyzer's checklist is exhaustive in a way prose reading is not. |
| "The constitution alignment pass will always say PASS - this project's constitution is too high-level to violate" | If that is true, you have a constitution problem, not an analyzer problem. Pass 4's purpose is exactly to surface the gap between "principle is too vague to violate" and "principle has been violated but the violation is invisible". Run the analyzer and adjust the constitution if every plan trivially passes. |
| "I'll just delete a finding if I disagree with it" | Findings are the analyzer's evidence; deleting one without addressing it loses the audit trail. Promote the finding's severity to make it actionable, or amend the constitution / spec to make the finding obsolete on the next run. The analyzer does not write to your artifacts; it only reports - you control the response. |
| "I'll skip rerun after fixes - the IDs will be different anyway" | IDs are deterministic across reruns: fix `A1`, rerun, and the new ambiguity (if any) becomes `A2`, not a recycled `A1`. The contract exists precisely so users can cite finding IDs in commits and follow-up tasks without worrying about renumber churn. |

## Verification

- [ ] The analyzer produces a Markdown report containing all three required tables: Findings, Coverage Summary, Metrics.
- [ ] Every finding has a category-prefixed ID (`A#`, `D#`, `U#`, `C#`, `G#`, or `I#`).
- [ ] Every finding has a severity (CRITICAL / HIGH / MEDIUM / LOW), a location (file + line or section), a finding text, and a suggested next step.
- [ ] The Findings table is capped at 50 rows; if more findings exist, an overflow summary line is appended.
- [ ] The Coverage Summary table lists every FR-### and SC-### from the spec with a Has Task? column populated.
- [ ] The Metrics block reports Total Requirements, Total Tasks, Coverage %, Ambiguity Count, Duplication Count, and per-severity issue counts.
- [ ] Constitution Alignment pass emits PASS / FAIL / N/A per MUST principle when the constitution file exists, or the informational "no constitution file found" N/A when absent.
- [ ] Finding IDs are stable across reruns on unchanged inputs (manual check: run twice, diff the reports - only timestamps should differ).
- [ ] The report ends with the mandatory closing line: "This analyzer is read-only. It modifies no files. Any remediation requires user approval."
- [ ] No file under the feature directory is modified during the run. The only writable target is the optional `--output <path>` report.

## Related Skills

- `[[project-constitution]]` - sources the MUST / SHOULD principles consumed by Pass 4 (Constitution Alignment).
- `[[ambiguity-detector]]` - shares the vague-adjective and `[NEEDS CLARIFICATION]` detection logic; this analyzer applies it cross-artifact while `[[ambiguity-detector]]` operates per-text.
- `[[spec-driven-development]]` - defines the FR-### / SC-### / user-story-priority conventions that Passes 3 and 5 rely on.
- `[[implementation-plan]]` - produces the plans this analyzer audits; the Constitution Check + Complexity Tracking sections it emits are what Pass 4 reads.
- `[[idea-refine]]` - precursor when an analyzer run reveals the underlying problem statement is itself unclear.
- `[[known-gaps-tracker]]` - findings the user opts to defer rather than fix land in `docs/<version>/known-gaps.md` as `BG-*` (bug) or `DF-*` (deferred) items.
- `[[final-report]]` - sibling code-review skill; this analyzer focuses on specification artifacts, `[[final-report]]` consolidates findings from a full code review.
