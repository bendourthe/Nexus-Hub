# Plan -- Loop-Engineering Skill Enrichment (Loopmaxxing + autoresearch adoption)

**Project**: Nexus-Hub
**Version**: v3.5.0
**Slug**: adoption-loopmaxxing-and-autoresearch
**Plan Type**: Feature / Enhancement (skill-native catalog enrichment)
**Created**: 2026-06-15
**Goal**: Enrich the existing `loop-engineering` skill and its two reference files with the six refinements surfaced by the AlphaSignal "loopmaxxing" article and the karpathy/autoresearch reference loop, with zero new skill, command, outbound call, dependency, or credential.

## Overview

This plan operationalizes the adoption plan in [docs/releases/v3/v3.5/comparisons/v3.5.0-comparison-loopmaxxing-and-autoresearch.md](../comparison-loopmaxxing-and-autoresearch.md). The comparison found that Nexus-Hub already owns the entire loop-engineering framework (shipped as `catalog/skills/workflow/loop-engineering/` in v3.3.0) and is in fact ahead of the article on its headline risks (comprehension debt, cognitive surrender, already named in the skill's Step 5). What remains are six genuine refinements, all `skill-native`: a strict-control-loop principle (the article's central thesis), a progressive-hardening lifecycle, a scalar-metric-optimization loop archetype with a per-iteration compute budget, production observability (trace-logging + stall detection), a concrete retries-then-handoff default, and naming the "loopmaxxing" anti-pattern as a recognition label.

Delivery is pure local catalog enrichment of three existing files: `catalog/skills/workflow/loop-engineering/SKILL.md` (the body), `catalog/skills/workflow/loop-engineering/references/loop-schema.md` (the schema), and `catalog/skills/workflow/loop-engineering/references/loop-library.md` (the registry). No new file, skill, or command is created. Because the skill's frontmatter (`name`, `description`, `summary_l0`, `overview_l1`) does not change, the three catalog registries (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`) require no edit; `make validate` is still run after every phase to confirm JSON integrity, the orphan-bundle audit, and the dangling-wikilink audit. Both reference files are already linked from SKILL.md, so adding content to them carries no new orphan-bundle risk.

Success looks like: the six refinements present and internally consistent across the three files, every cross-link resolving, the SKILL.md body still under the 500-line size norm, all edited content ASCII-only and conformant to the Markdown style guide, and the full validator chain green. The reverse-engineer-first ordering (passed by `/plan from-comparison`) collapses to value/effort sequencing because every item is `skill-native`; the phasing below is therefore driven by conceptual cohesion (which edits touch the same file and section).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at `docs/v3/v3.5/constitution.md` - skipping check. Recommend running `/constitution` to establish project principles. This is informational, not blocking. The plan is nonetheless aligned with the standing governance that functions as Nexus-Hub's de-facto constitution (the `AGENTS.md` MCP Registry Policy and the Reverse-Engineering Attribution Rule): every item is classified `skill-native`, introduces no outbound call / dependency / credential, and uses generic artifact naming with no upstream attribution in the distributed content.

## Phases at a Glance

| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Strict-control-loop doctrine + hardening lifecycle | The SKILL.md body teaches the deterministic-shell principle (G1) and the progressive-hardening lifecycle (G2) | Strong reasoning tier, high effort (Claude Code: Opus 4.8, high) |
| 2 | Metric-optimization archetype + per-iteration budget + oracle nuance | A new `optimize-metric-keep-best` library archetype (G5), an optional `per_iteration_budget` schema field, and the deterministic-oracle anti-pattern carve-out | Strong reasoning tier, medium effort (Claude Code: Opus 4.8, medium) |
| 3 | Observability, handoff default, loopmaxxing label | Optional `trace_log` + `progress_check` fields and a production-loops note (G3), a retries-then-handoff default + optional `handoff` field (G4), and the "loopmaxxing" recognition label (G6) | Mid reasoning tier, medium effort (Claude Code: Sonnet 4.6, medium; upshift to Opus 4.8 if cross-file consistency slips) |

The "Rec. model / effort" column is a best-effort planning-time assessment (Step 3.5), recorded as platform-agnostic tier intent plus the concretely-enumerated Claude Code model. `/implement` re-confirms each phase's recommendation against the then-current live model set before building.

## Phase 1: Strict-control-loop doctrine + hardening lifecycle

**Goal**: Teach, in the SKILL.md body, the article's central "pragmatic path" thesis (deterministic code drives the loop; the LLM is invoked only for the dynamic decisions code cannot make) and the maturity *progression* behind the existing `maturity` flag.
**Prerequisites**: None.
**Stability Gate**: SKILL.md contains a new strict-control-loop section and a documented hardening lifecycle; the body remains under 500 lines; all cross-links resolve; `make validate` (or its direct validator equivalents) is green.
**Recommended model**: Strong reasoning tier, high effort. Concrete (Claude Code): Opus 4.8, high effort. Rationale: this phase authors new governance doctrine that must stay internally consistent with the rest of the skill (Step 5, the Common Rationalizations table, the schema's anti-patterns) and with sibling skills (`agent-orchestration-primitives`, `ai-billing-safeguards`); doctrine drift is the high-risk failure mode here. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 1.1 -- Add the strict-control-loop (deterministic-shell) principle to SKILL.md

**Objective**: Add a new section to the loop-engineering SKILL.md body that teaches the deterministic-shell model (G1 / article insight P7).

**Prompt**:
> In `catalog/skills/workflow/loop-engineering/SKILL.md`, add a new section titled "## Strict Control Loops" immediately after the existing "## Scheduled-Triage Recipe" section and before "## Common Rationalizations". The section must teach the article's central thesis: the most effective loops are not open-ended agentic cycles but strict control loops where deterministic code drives the loop and handles execution and API calls, and the LLM step is reserved only for the dynamic decisions traditional code cannot make. Cover three points concisely (aim for 6-12 lines total): (1) the operator writes the desired state and the observation/check mechanism; deterministic code handles iteration, execution, and tool/API calls; (2) the LLM is invoked only at the genuinely-dynamic decision step, so a hallucinating model's blast radius is bounded by the surrounding hard-coded checks; (3) wrapping repetitive or risky steps in deterministic checks is how you "limit the blast radius". Cross-link `[[agent-orchestration-primitives]]` (cheapest-primitive discipline) and `[[ai-billing-safeguards]]` (cost bounding). Frame this as complementary to the existing host `/loop` + `/goal` driver model, NOT a replacement: the host command still drives, but the loop body should push as much as possible into deterministic code. Constraints: ASCII-only; follow `catalog/style-guides/markdown.md` (blank line before and after the heading and any list); do NOT modify the YAML frontmatter; keep the total SKILL.md body under the 500-line size norm. Acceptance: the new section exists, reads coherently against the existing Step 1-5 body, and both wikilinks resolve to existing skills.

---

#### 1.2 -- Document the progressive-hardening lifecycle

**Objective**: Turn the existing `maturity` flag into a documented progression (G2 / article insights P8, P13), in both the SKILL.md body and the schema's `maturity` field description.

**Prompt**:
> Document the progressive-hardening lifecycle in two places. (A) In `catalog/skills/workflow/loop-engineering/SKILL.md`, add a short paragraph (within the new "## Strict Control Loops" section from sub-task 1.1, or as a brief subsection right after it) stating the recommended progression: start with the minimal loop run with a human in the verification seat; run it several times to learn which steps the agent gets right consistently; then replace the LLM prompt for each consistently-correct step with deterministic code, shrinking the LLM's role over time (this is how an `experimental` loop becomes `hardened`). (B) In `catalog/skills/workflow/loop-engineering/references/loop-schema.md`, expand the `maturity` field's description row so it references this progression: `experimental` = new or unproven, run with human verification; `hardened` = repeatedly successful AND its consistently-correct steps have been moved into deterministic code. Constraints: ASCII-only; Markdown style guide; do not change the schema's field set or the worked example; keep the SKILL.md body under 500 lines; no frontmatter change. Acceptance: the lifecycle is described in the body and the `maturity` row in `loop-schema.md` reflects it; the two descriptions are consistent with each other.

---

#### 1.3 -- Testing and Stabilization

**Objective**: Validate the Phase 1 edits and iterate until stable before advancing.

**Prompt**:
> Validate the Phase 1 edits to `catalog/skills/workflow/loop-engineering/SKILL.md` and `references/loop-schema.md`. Run `make validate` if `make` is on PATH; otherwise run the underlying validators directly (this repo's documented Windows fallback): `python scripts/validate_skills.py --verbose` (JSON catalog integrity + orphan-bundle audit) and the catalog dangling-wikilink audit. Confirm: (1) the validators exit 0; (2) the orphan-bundle audit is clean (both reference files are still linked from SKILL.md - no new orphans); (3) no dangling wikilinks were introduced (`[[agent-orchestration-primitives]]` and `[[ai-billing-safeguards]]` resolve); (4) every line added in this phase is ASCII-only (no em-dashes, curly quotes, or ellipsis characters); (5) the SKILL.md body is under 500 lines. Fix any failure and re-run until all checks pass. Then run `/generate-session-history` to document Phase 1.

---

## Phase 2: Metric-optimization archetype + per-iteration budget + oracle nuance

**Goal**: Add the one loop *shape* the library lacks (scalar-metric optimization, from autoresearch), a per-iteration compute-budget field, and the deterministic-oracle carve-out to the maker-self-certifies anti-pattern.
**Prerequisites**: Phase 1 complete (the hardening-lifecycle vocabulary the new archetype's `maturity` note leans on is established there).
**Stability Gate**: `loop-library.md` contains a coherent `optimize-metric-keep-best` entry using the schema's fields; `loop-schema.md` carries an optional `per_iteration_budget` field and the oracle carve-out; validators green.
**Recommended model**: Strong reasoning tier, medium effort. Concrete (Claude Code): Opus 4.8, medium effort. Rationale: structured authoring against an existing schema (lower complexity than Phase 1's doctrine), but the deterministic-oracle carve-out is a subtle correctness point (it qualifies an existing anti-pattern without contradicting it), which keeps this on the strong tier per the no-degradation default. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 2.1 -- Add the `optimize-metric-keep-best` archetype to the loop library

**Objective**: Add a new loop-library entry expressing the scalar-metric-optimization shape (G5 / autoresearch insights R1, R2).

**Prompt**:
> In `catalog/skills/workflow/loop-engineering/references/loop-library.md`, add a new archetype `optimize-metric-keep-best` following the same YAML-in-fenced-block format as the existing five entries (`ship-pr-until-green`, `build-until-green`, `e2e-until-green`, `coverage-until-threshold`, `pr-self-review`). The archetype captures the optimize-a-scalar-metric shape: each iteration makes a change, runs a `check_command` that emits a single scalar metric, keeps the change if the metric improved, and reverts it otherwise. Use these field values as a template the operator adapts: `name: optimize-metric-keep-best`; `goal: The tracked metric is improved over the baseline and no regression is kept.`; `iteration_cap: 20`; `check_command: <project metric command emitting one scalar, e.g. a benchmark or eval score>`; `exit_condition: iteration_cap reached, or no improvement over the last N iterations (progress-check), with the best result retained.`; `driver: /loop for continuous re-runs, with manual re-invocation fallback.`; `maturity: experimental`; `agents:` Claude Code + manual fallbacks; `tags: [optimization, metric, benchmark, keep-best]`. Below the block, add a 2-4 line note: this archetype differs from the green/not-green archetypes because its exit is an optimization target, not a binary pass; it pairs with the `per_iteration_budget` and `progress_check` schema fields (added in sub-task 2.2 and Phase 3); and it is the shape exemplified by overnight ML-experiment loops. Do NOT name "autoresearch" or any external repo in the file (Reverse-Engineering Attribution Rule) - describe the pattern generically. Constraints: ASCII-only; Markdown style guide (blank line before/after the heading and the fenced block); keep the entry consistent with `loop-schema.md`. Acceptance: the new archetype renders as a peer of the existing five and uses only schema-defined fields plus the two new optional ones it forward-references.

---

#### 2.2 -- Add the `per_iteration_budget` field and the deterministic-oracle carve-out

**Objective**: Add an optional per-iteration compute-budget field (R2) and qualify the maker-self-certifies anti-pattern with the deterministic-oracle nuance (R3).

**Prompt**:
> Make two edits to `catalog/skills/workflow/loop-engineering/references/loop-schema.md`. (A) Add a new OPTIONAL field row to the Fields table: `per_iteration_budget` - "Optional hard cost ceiling for a single iteration (wall-clock, tokens, or tool calls), orthogonal to `iteration_cap` which bounds the count. Example: `5 min wall-clock per iteration`." Make clear in the cell or an adjacent line that it is optional (the nine existing fields remain the required set; this is additive so existing loop definitions stay valid). (B) In the "## Anti-Patterns" section, qualify the existing "Maker self-certifies exit" bullet with a carve-out: the maker and checker may be the same agent ONLY when the checker is a deterministic, non-LLM oracle (for example a numeric metric, an exit code, or a compiler result) - because a deterministic oracle is its own independent check; whenever the checker is itself an LLM, the maker must not be the checker. Keep the original anti-pattern intent intact; you are adding the precise boundary, not removing the rule. Constraints: ASCII-only; Markdown style guide; do not renumber or remove existing fields; the worked example may stay as-is (the new field is optional). Acceptance: `per_iteration_budget` appears as an optional field; the anti-pattern carve-out is present and does not contradict the maker-self-certifies rule; the file stays consistent with the `optimize-metric-keep-best` archetype's forward-reference.

---

#### 2.3 -- Testing and Stabilization

**Objective**: Validate the Phase 2 edits and iterate until stable.

**Prompt**:
> Validate the Phase 2 edits to `references/loop-library.md` and `references/loop-schema.md`. Run `make validate` (or the direct fallback: `python scripts/validate_skills.py --verbose` plus the dangling-wikilink audit). Confirm: (1) validators exit 0; (2) orphan-bundle audit clean (both reference files remain linked from SKILL.md); (3) the new `optimize-metric-keep-best` archetype uses only fields defined in `loop-schema.md` (the nine required plus the optional `per_iteration_budget` / `progress_check`); (4) no external repo or product name appears in either file (grep the diff for "autoresearch", "karpathy", "alphasignal" - expect zero matches); (5) all added lines are ASCII-only. Fix any failure and re-run until green. Then run `/generate-session-history` to document Phase 2.

---

## Phase 3: Observability, handoff default, loopmaxxing label

**Goal**: Add production-loop observability fields (trace-logging + stall detection), the concrete retries-then-handoff default, and the "loopmaxxing" recognition label.
**Prerequisites**: Phase 2 complete (the `progress_check` notion the `optimize-metric-keep-best` archetype forward-references is formalized here).
**Stability Gate**: `loop-schema.md` carries optional `trace_log`, `progress_check`, and `handoff` fields with a production-loops note; SKILL.md names "loopmaxxing" and the retries-then-handoff default; validators green; full skill re-read for cross-file consistency.
**Recommended model**: Mid reasoning tier, medium effort. Concrete (Claude Code): Sonnet 4.6, medium effort; upshift to Opus 4.8 if a re-read shows cross-file consistency slipping (these are the smallest, most mechanical touches, but they close out the schema so they must stay coherent with Phases 1-2). Rationale: additive optional fields plus short body edits, lower complexity than the doctrine and archetype work. `/implement` re-confirms against the then-current models and will upshift on repeated test failure per the model-routing mid-task escalation rule.

### Sub-tasks

#### 3.1 -- Add production observability fields (G3)

**Objective**: Add optional `trace_log` and `progress_check` schema fields and a production-loops note (article insights P9, P10).

**Prompt**:
> In `catalog/skills/workflow/loop-engineering/references/loop-schema.md`, add two OPTIONAL field rows to the Fields table: (1) `trace_log` - "Optional path or sink where each iteration's agent reasoning and tool calls are recorded, so a production loop's decisions can be debugged after the fact. Example: `docs/loops/<name>-trace.md`."; (2) `progress_check` - "Optional stall-detection rule that terminates the loop early when the last N iterations show no measurable progress on `check_command`, distinct from `iteration_cap` which is a hard count limit. Example: `stop if val metric has not improved for 3 iterations`." Then add a short "## Production Loops" note (4-6 lines) below the Anti-Patterns section: production loops (as opposed to one-off local loops) should set `trace_log` for observability and `progress_check` for stall detection in addition to the mandatory `iteration_cap`, because a loop that is stuck should stop on no-progress rather than burning its full cap. Keep both fields optional (the required set is unchanged). Constraints: ASCII-only; Markdown style guide; additive only. Acceptance: both fields appear as optional; the Production Loops note explains why each matters; existing loop definitions remain valid without them.

---

#### 3.2 -- Add the retries-then-handoff default and `handoff` field (G4)

**Objective**: Record the article's concrete "2-3 retries then human handoff" rule of thumb (P12) and an optional handoff-target field.

**Prompt**:
> Two edits. (A) In `catalog/skills/workflow/loop-engineering/references/loop-schema.md`, add an OPTIONAL `handoff` field row: "Optional human-review destination for items the loop cannot resolve - the inbox, queue, or assigned issue that post-cap failures route to. Example: `docs/todos.md needs-human section`." (B) In `catalog/skills/workflow/loop-engineering/SKILL.md`, in the existing "## Scheduled-Triage Recipe" section (step 7 routes needs-human items) or Step 4 of "## Instructions", add one sentence recording the rule of thumb: allow a maximum of two or three retries on a failing step before failing gracefully and handing the error to a human via the `handoff` target, rather than spending the entire `iteration_cap` on a step that is not converging. Constraints: ASCII-only; Markdown style guide; `handoff` is optional; do not duplicate the existing human-inbox routing - reference it. Acceptance: the `handoff` field exists as optional; the 2-3-retries default is stated once and ties to the existing human-inbox routing.

---

#### 3.3 -- Name "loopmaxxing" as a recognition label (G6)

**Objective**: Record the term "loopmaxxing" so the agent recognizes the anti-pattern by name (article insight P4).

**Prompt**:
> Add the term "loopmaxxing" as a recognition label without changing any existing guardrail. (A) In `catalog/skills/workflow/loop-engineering/SKILL.md`, in the "## Common Rationalizations" table, either add a row or extend the existing "loop without an exit condition" row to name the anti-pattern: open-ended `while(true)` iteration on a fuzzy goal, betting the agent will eventually converge - "loopmaxxing", the loop-era equivalent of tokenmaxxing - which our mandatory falsifiable goal, `iteration_cap`, and command-derived `exit_condition` exist precisely to prevent. (B) Optionally add a one-line cross-reference in `references/loop-schema.md`'s Anti-Patterns section tying the existing "no iteration_cap" / "vibe-based exit_condition" bullets to the named term. Constraints: ASCII-only; Markdown style guide; this is a naming/recognition aid only - introduce no new rule and weaken no existing one. Acceptance: "loopmaxxing" is defined once in the skill and tied to the existing guardrails; no guardrail text was removed or softened.

---

#### 3.4 -- Testing and Stabilization

**Objective**: Validate the Phase 3 edits, then verify the whole skill is internally consistent across all three files.

**Prompt**:
> Validate the Phase 3 edits and the skill as a whole. Run `make validate` (or the direct fallback: `python scripts/validate_skills.py --verbose` plus the dangling-wikilink audit). Confirm: (1) validators exit 0; (2) orphan-bundle audit clean; (3) no dangling wikilinks; (4) all added lines ASCII-only; (5) SKILL.md body still under 500 lines. Then do a full read-through of all three files (`SKILL.md`, `references/loop-schema.md`, `references/loop-library.md`) and verify cross-file consistency: the `optimize-metric-keep-best` archetype's forward-references to `per_iteration_budget` and `progress_check` now resolve to real schema fields; the hardening lifecycle (Phase 1), the strict-control-loop principle (Phase 1), and the production-loops note (Phase 3) do not contradict each other; the maker-self-certifies carve-out (Phase 2) is consistent with the maker/checker rule in the SKILL.md body. If the skill frontmatter's `summary_l0` / `overview_l1` still accurately describe the enriched skill, leave them unchanged and confirm no `data/` registry edit is needed; if a new headline capability (the metric-optimization archetype) materially changes the one-line summary, update `summary_l0` / `overview_l1` AND the three registries (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`) and re-run `make validate`. Fix any failure and re-run until green. Then run `/generate-session-history` to document Phase 3, and update `docs/v3/v3.5/known-gaps.md` with any deferred items.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none - no constitution file; all items skill-native with no policy violations) | | |

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed (1.1, 1.2)
- [x] Strict-control-loop section and hardening lifecycle present and coherent
- [x] SKILL.md body under 500 lines; frontmatter unchanged
- [x] Validators green; orphan-bundle and dangling-wikilink audits clean
- [x] Session history generated for Phase 1
- [x] Ready to advance to Phase 2

### Phase 2 Exit Checklist

- [x] All sub-tasks completed (2.1, 2.2)
- [x] `optimize-metric-keep-best` archetype added using schema-defined fields only
- [x] `per_iteration_budget` field and deterministic-oracle carve-out present
- [x] No external repo/product name in any reference file
- [x] Validators green
- [x] Session history generated for Phase 2
- [x] Ready to advance to Phase 3

### Phase 3 Exit Checklist

- [x] All sub-tasks completed (3.1, 3.2, 3.3)
- [x] `trace_log`, `progress_check`, `handoff` optional fields + Production Loops note present
- [x] Retries-then-handoff default stated; "loopmaxxing" named without weakening any guardrail
- [x] Full cross-file consistency read-through passed
- [x] Registry-edit decision made and validated (no edit needed - frontmatter unchanged, `summary_l0` / `overview_l1` still accurate, JSON catalogs load clean)
- [x] Validators green; SKILL.md under 500 lines (131)
- [x] Session history generated; no deferred items so no `docs/v3/v3.5/known-gaps.md` entry created
- [x] CHANGELOG `## [Unreleased]` entry added
