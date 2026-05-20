---
description: Cross-artifact consistency, coverage, and ambiguity analyzer for a feature directory. Reads spec.md / plan.md / tasks.md (and the project constitution if present), emits a severity-tagged findings table plus a coverage summary. Read-only - never modifies files.
---

# Analyze Spec

Run a read-only cross-artifact analysis on a feature's spec, plan, and tasks. The command surfaces duplication, ambiguity, underspecification, constitution-misalignment, and coverage gaps - it never modifies any file.

This command drives the `cross-artifact-analyzer` skill end-to-end. It loads the artifacts, runs six detection passes, assigns severity per the documented heuristic, and writes the findings to stdout (or to a report file if `--output <path>` is provided). Finding IDs are deterministic across reruns so users can cite them in follow-up work.

## How to Run This Command

- `/analyze-spec` - default. Resolves the latest feature directory under `docs/<version>/plans/` (or `specs/<NNN>-*/` if that layout exists from Phase 7 of the adoption plan).
- `/analyze-spec <path>` - explicit feature directory or plan file path.
- `/analyze-spec --output docs/<version>/analyze-spec-<slug>.md` - write the report to a file in addition to stdout.

The command is strictly read-only. It does not write to the feature directory, the constitution file, or any tracked file other than the optional `--output` report.

---

## Step 1: Resolve the Feature Directory

1. Detect the current version from the most recent git tag, `CHANGELOG.md` heading, or root manifest. Normalize to the `v` prefix form (e.g., `v2.1.0`).
2. Resolve the feature directory in this priority order:
    1. The argument `<path>` if provided. If it points to a file (e.g., `docs/v2.1.0/plans/adoption-spec-kit.md`), use the file's parent directory as the feature root and treat the file itself as the in-plan artifact.
    2. `.specify/feature.json` `feature_directory` field if it exists at repo root.
    3. The most recently modified `specs/<NNN>-*/` directory.
    4. The most recently modified `docs/<version>/plans/<slug>.md` (treated as a self-contained plan + spec).
3. Report the resolved location and confirm with the user before proceeding. If no candidate is found, abort with the message: "No feature directory or plan file found. Run `/generate-plan` first, or pass an explicit `<path>` argument."

---

## Step 2: Load Minimal Context From Each Artifact

Load only the sections that the detection passes need. Do not load full file bodies if the analyzer can work from headings + first-paragraph excerpts.

| Artifact | Sections to load |
|---|---|
| `spec.md` | Overview, Functional Requirements (full table), Success Criteria (full table), User Stories (titles + Priority + Acceptance Scenarios), Edge Cases |
| `plan.md` | Architecture overview, Data Model references, Phase list with goals, Technical constraints / cross-cutting constraints, Complexity Tracking table if present |
| `tasks.md` | Task ID, Description, Phase grouping, `[P]` parallel markers, `[US#]` story labels, file paths |
| Constitution | `docs/<version>/constitution.md` (recommended location) or `CONSTITUTION.md` at root. If absent, mark constitution alignment pass as N/A. |

For self-contained plans (where `spec.md` / `tasks.md` do not exist as separate files), parse the equivalent sections from the plan body itself:

- Functional Requirements -> the prompts and goals inside each phase's sub-tasks.
- Success Criteria -> the Stability Gate text at the top of each phase.
- Tasks -> the `- [ ] T###` lines (or the sub-task headings if Phase 6 task format has not yet been applied).

---

## Step 3: Run the Six Detection Passes

Run all six passes in order. Collect findings into a single list; assign category-prefixed IDs (`D1, D2, ...` for duplication, `A1, A2, ...` for ambiguity, `U1, U2, ...` for underspecification, `C1, C2, ...` for constitution alignment, `G1, G2, ...` for coverage gaps, `I1, I2, ...` for inconsistency). IDs are assigned in the order findings are emitted by each pass, sorted within a category by the line number they reference in the source artifact - this is what makes IDs deterministic across reruns.

### Pass 1: Duplication

- Detect FRs that overlap in capability (e.g., two FRs both stating "System MUST authenticate users" with different IDs).
- Detect tasks that target the same file with overlapping descriptions.
- Detect user stories that describe the same flow with different priorities.

### Pass 2: Ambiguity

- Detect vague adjectives without measurable thresholds: `fast`, `scalable`, `secure`, `intuitive`, `simple`, `efficient`, `robust`, `reliable`. Each occurrence in an FR or SC is a finding unless the same sentence contains a numeric threshold or a definition.
- Detect unresolved `[NEEDS CLARIFICATION: ...]` markers - if more than 3 are present, raise an additional finding because the spec violates the 3-marker hard limit from the `project-constitution` skill body.
- Detect placeholder leakage: `[ALL_CAPS_IDENTIFIER]`, `TBD`, `TODO`, `XXX`, `<...>` inside content sections (not inside code fences).

### Pass 3: Underspecification

- Detect functional requirements without acceptance criteria or Independent Test text.
- Detect success criteria that are not measurable (no number, no boolean condition, no explicit pass/fail signal).
- Detect user stories without Acceptance Scenarios (Given / When / Then format).
- Detect tasks without file paths (post Phase 6 of the adoption-spec-kit plan, every task should reference at least one path).

### Pass 4: Constitution Alignment

- If the constitution file exists: for each MUST principle, scan spec + plan + tasks for explicit or implicit violations. Emit a finding for each PASS / FAIL / N/A determination with a one-sentence justification.
- If the constitution file does not exist: emit a single informational finding: "No constitution file found at `docs/<version>/constitution.md` - skipping alignment pass. Run `/constitution` to establish principles." This is N/A, not CRITICAL.

### Pass 5: Coverage Gaps

- For each FR-### in spec.md, list the tasks that implement it (match by FR-ID mention in task description, by file-path overlap with FR scope, or by user-story label if the FR is scoped to a single story).
- For each SC-### in spec.md, list the tasks that contribute to it (success criteria often span multiple tasks - look for at least one).
- Emit a finding for each FR / SC with **zero** matching tasks.
- Also emit a finding for each task that references no FR / SC / US (a task with no parent requirement is an orphan).

### Pass 6: Inconsistency

- Terminology drift: detect entities named differently in spec vs. plan vs. tasks (e.g., spec says "User", plan says "Account", tasks say "Member").
- Conflicting requirements: detect FRs that contradict each other or contradict a constitution principle.
- Ordering contradictions: detect phase dependencies that the task list violates (e.g., task T010 references a model that task T020 creates).

---

## Step 4: Assign Severity Per Finding

| Severity | Heuristic |
|---|---|
| CRITICAL | Constitution MUST violation (Pass 4 FAIL on a MUST principle). Zero-coverage core requirement (Pass 5 finding on an FR that is also referenced in a user-story acceptance scenario). Direct contradiction between two FRs (Pass 6). |
| HIGH | Duplicates that materially confuse scope (Pass 1). Ambiguous security or performance requirements (Pass 2 hit on `secure` / `fast` in an FR that has no measurable threshold). Untestable acceptance scenarios (Pass 3 on a P1 user story). Constitution N/A turned to FAIL after closer reading. |
| MEDIUM | Terminology drift (Pass 6). Missing non-functional task coverage (Pass 5 on an SC that is operational like observability or rollback). Underspecified P2 / P3 user stories. |
| LOW | Style or wording issues. Placeholder leakage on optional sections. Ambiguous adjectives in narrative prose (Overview, Preamble) where measurability is not expected. |

A single finding can be promoted up the severity ladder if the analyst's judgment is that the listed heuristic understates the risk. Demotion is not permitted - if a finding matches a CRITICAL heuristic, it stays CRITICAL.

---

## Step 5: Emit the Report

The report is a compact Markdown document with three tables and a Next Actions section. Cap the Findings table at 50 rows; if more findings exist, emit the top 50 by severity (CRITICAL > HIGH > MEDIUM > LOW; within a severity, by ID order) and append a one-line overflow summary: `... N additional findings omitted; rerun with --verbose for the full list.`

### Report skeleton

```markdown
# /analyze-spec report

**Feature directory**: <resolved path>
**Run date**: YYYY-MM-DD
**Constitution file**: <path or "(none)">
**Plan file**: <path>
**Spec file**: <path or "(self-contained in plan)">
**Tasks file**: <path or "(self-contained in plan)">

## Findings

| ID | Severity | Category | Location | Finding | Suggested next step |
|---|---|---|---|---|---|
| C1 | CRITICAL | Constitution Alignment | docs/v2.1.0/constitution.md principle 3; plan phase 5 | Plan introduces an unsigned outbound call; violates principle "All outbound calls MUST be authenticated". | Add an auth step to phase 5 sub-task 5.2 OR amend the constitution. |
| A1 | HIGH | Ambiguity | spec.md FR-007 | "System MUST be fast" - no measurable threshold. | Define an explicit latency budget (e.g., p95 < 200 ms). |
| G1 | HIGH | Coverage Gaps | spec.md SC-003 | Success criterion has zero matching tasks. | Add a task that produces the artifact SC-003 references. |
| ... | | | | | |

## Coverage Summary

| Requirement key | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | Yes | T012, T014 | |
| FR-002 | Yes | T015 | |
| FR-003 | No | - | No task references FR-003 - emitted finding G2. |
| SC-001 | Yes | T020 | |
| SC-002 | No | - | No task references SC-002 - emitted finding G3. |

## Metrics

| Metric | Value |
|---|---|
| Total requirements (FR + SC) | N |
| Total tasks | M |
| Coverage % (requirements with at least one task) | XX% |
| Ambiguity count | A |
| Duplication count | D |
| Critical issues count | C |
| High issues count | H |
| Medium issues count | M |
| Low issues count | L |

## Next Actions

Ranked from most-impactful to least:

1. Resolve every CRITICAL finding before merging the plan.
2. For each HIGH finding in ambiguity or coverage: rewrite the underlying FR / SC / task to remove the ambiguity or add the missing coverage.
3. Reconcile terminology drift (Pass 6) by picking one canonical name per entity and applying it across spec + plan + tasks.
4. Re-run `/analyze-spec` after edits; finding IDs are stable so resolved items will disappear from the new run.

## Offer Remediation

This analyzer is read-only. It modifies no files. Any remediation requires user approval.

If the user wants to fix findings interactively, recommend:

- `/clarify-spec` for ambiguity and underspecification findings on the spec itself (sequential 5-question loop with recommended-option tables; ships in Phase 5 of the adoption-spec-kit plan).
- `/constitution` (or `/constitution amend`) when constitution-alignment findings reflect intentional scope expansion that the constitution should accommodate.
- Direct edits to plan / tasks for coverage gaps and ordering contradictions; re-run `/analyze-spec` to verify.
```

End the run by stating explicitly: **"This analyzer is read-only. It modifies no files. Any remediation requires user approval."** This single line is mandatory output regardless of how the report was rendered.

---

## Step 6: Determinism Contract

Finding IDs MUST be stable across reruns when the underlying artifacts are unchanged. Two contract rules enforce this:

1. **Within-category ordering**: findings within each category are sorted by the line number they reference in the source artifact (spec.md line < plan.md line < tasks.md line if the same finding spans multiple artifacts). Identical line numbers break ties by file name in ASCII order.
2. **No timestamps or hashes in IDs**: IDs use only the category prefix + a monotonic integer starting at 1 per category per run. The `Run date` field captures the timestamp; IDs do not.

If a user reruns the command after fixing finding `A1` and adding a new ambiguity, the new finding becomes `A2` (not `A1`) - the resolved `A1` is simply absent from the new report. This stability lets users cite finding IDs in commit messages and follow-up tasks.

---

## Step 7: Done

Report:

```
/analyze-spec complete.

Findings: C critical, H high, M medium, L low (T total)
Coverage: XX% of requirements have at least one task
Overflow: <N additional findings omitted, or "none">

Report written to: <path if --output, else "stdout only">
```

Recommend next command:

- If CRITICAL findings exist: address them before any other follow-up.
- If only HIGH ambiguity findings exist: `/clarify-spec` to drive the sequential 5-question loop.
- If only coverage gaps exist: edit `tasks.md` (or the plan's in-line task list) to add the missing tasks, then rerun this command.
- If no findings exist: the feature is ready for implementation - run `/implement-phase <slug> phase-1`.

---

## Behavior Guarantees

- **Read-only**: the command MUST NOT write to spec.md, plan.md, tasks.md, constitution.md, or any file under the feature directory. The only writable target is the optional `--output <path>` report.
- **Deterministic IDs**: finding IDs are stable across reruns when inputs are unchanged (see Step 6).
- **Constitution-aware but constitution-optional**: behavior degrades gracefully when no constitution file exists; the alignment pass emits an informational N/A rather than failing the run.
- **Overflow-safe**: never emits more than 50 rows in the Findings table; the overflow summary points users at `--verbose` for the full list.
