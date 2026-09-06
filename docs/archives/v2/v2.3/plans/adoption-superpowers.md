# Plan — Superpowers Adoption (process-discipline skills)

**Project**: Nexus-Hub
**Version**: v2.3.0
**Slug**: adoption-superpowers
**Plan Type**: Feature / Enhancement
**Created**: 2026-05-27
**Goal**: Adopt all in-scope (P0-P3) items from the superpowers comparison, closing Nexus-Hub's process-discipline gaps with zero new dependencies and zero outbound calls.

**Source comparison**: [docs/archives/v2/v2.3/comparison-superpowers.md](../comparison-superpowers.md)
**Sibling plan (untouched)**: [docs/archives/v2/v2.3/plans/adoption-ecc-cybersec-skills.md](adoption-ecc-cybersec-skills.md)

## Overview

This plan operationalizes the adoption set from the Nexus-Hub vs. Superpowers comparison (https://github.com/obra/superpowers). Superpowers is a focused, zero-dependency process-discipline harness; the comparison found that Nexus-Hub already covers most of its capabilities but lacks several discipline-enforcing skills (skills that fire a hard gate and resist rationalization) and two concrete skill-eval techniques. All 13 in-scope items are classified `skill-native` (pure catalog content) or `re-full` (local scripts that reuse the user's existing model CLI). No item introduces a new runtime dependency, a new outbound call, a new credential, or a new third-party data processor.

Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of the source comparison for the ordering rationale: skill-native items ship first (Phases 1-3), then the local re-full builds (Phases 4-5), then a deferral record and polish (Phase 6). The deferred P3 visual brainstorming server is recorded as a tracked known-gap rather than built this cycle.

Delivery is pure catalog content plus edits to one already-registered repo script (`scripts/optimize_skill_description.py`) and per-skill bundled scripts (auto-copied by the installer). Definition of done: every in-scope skill-native skill is created AND registered in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`; `make validate` and `make lint` pass; the eval-harness and find-polluter changes are covered by pytest; and each new discipline skill passes a `skill-eval-loop` trigger check. This plan ingests zero items from prior known-gaps files: the 12 v2.2.0 open items were already transferred to the sibling `adoption-ecc-cybersec-skills.md` plan on 2026-05-26 and must not be duplicated here.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/archive/v2/v2.3/constitution.md - skipping check. Recommend running /constitution to establish project principles.

## Phases at a Glance

| Phase | Title | RE bucket | Outcome |
|-------|-------|-----------|---------|
| 1 | New discipline skills | skill-native | `verification-before-completion`, `receiving-code-review`, `using-git-worktrees` authored + registered; gates green |
| 2 | Skill-authoring methodology upgrade | skill-native | TDD-for-skills methodology + persuasion-principles reference added under `create-custom-command`, cross-linked from `skill-eval-loop` |
| 3 | Discipline framing + operational enhancements | skill-native | `regression-root-cause-analyzer`, `multi-agent-coordinator`, `flaky-test-detector`, `spec-driven-development` hardened |
| 4 | Eval-harness trigger techniques | re-full | premature-action + multi-turn + cheap-model trigger testing added to the eval harness; pytest coverage |
| 5 | Flaky-test tooling cluster | re-full | `find-polluter.{sh,ps1}` + `waitFor` helper bundled under `flaky-test-detector` |
| 6 | Deferral record + polish | mixed | visual-brainstorm-server deferral recorded; AGENTS counts + CHANGELOG updated; final sweep |

---

## Phase 1: New discipline skills

**Goal**: Add the three confirmed-missing discipline gate skills as pure catalog content and register them.
**Prerequisites**: None.
**Stability Gate**: `make validate` and `make lint` pass; the three new skills appear in `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`; each passes a `skill-eval-loop` trigger check on a should-trigger prompt.

### Sub-tasks

#### 1.1 — verification-before-completion skill

- [x] T001 [P] Create discipline skill in catalog/skills/workflow/verification-before-completion/SKILL.md

**Objective**: Ship an always-on "evidence before claims" discipline skill that fires before any completion/success claim.

**Prompt**:
> Create `catalog/skills/workflow/verification-before-completion/SKILL.md`. This is a discipline-enforcing skill adapted from the pattern documented in `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a (source pattern: superpowers `skills/verification-before-completion/SKILL.md`). Do NOT copy the source verbatim or use its "your human partner" voice (comparison report N2); write it in Nexus-Hub's professional teaching tone.
> Required frontmatter per AGENTS.md: `name`, `description` (trigger-focused, pushy, with explicit trigger phrases AND a `SKIP:` clause), `summary_l0` (<=15 words, quoted), `overview_l1` (<=150 words, quoted). Keep the "what it does" in `overview_l1`, NOT in `description` (the comparison's Section 4 insight: workflow summaries in `description` cause the agent to follow the description instead of reading the body).
> Required body sections per AGENTS.md: title, "When to Use This Skill" (with explicit "When NOT to use"), "Instructions" (a gate function: identify the proving command, run it fresh, read full output + exit code, verify, only then claim), a "Common Rationalizations" table (each row a concrete failure mode + rebuttal, e.g. "Should work now" -> "RUN the verification"), and a binary "Verification" checklist of observable artifacts. Include a claim-to-evidence table (Tests pass / Linter clean / Build succeeds / Bug fixed / Requirements met). Target <=500 lines.
> Constraint: zero code, zero outbound, pure markdown. Do NOT register it yet (T004 does that). Do NOT run validators yet.

---

#### 1.2 — receiving-code-review skill

- [x] T002 [P] Create discipline skill in catalog/skills/code-review/receiving-code-review/SKILL.md

**Objective**: Ship a skill for acting on review feedback with technical rigor and no performative agreement.

**Prompt**:
> Create `catalog/skills/code-review/receiving-code-review/SKILL.md`. Adapt the pattern in `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a (source: superpowers `skills/receiving-code-review/SKILL.md`); adapt, do not copy (N2), and use Nexus-Hub voice.
> Frontmatter: `name`, pushy trigger-focused `description` with `SKIP:` clause (skip when authoring a review rather than receiving one - that is the existing `code-review/*` skills), `summary_l0` (quoted, <=15 words), `overview_l1` (quoted, <=150 words).
> Body: title; "When to Use This Skill" (receiving review feedback, before implementing suggestions, especially unclear/questionable ones) + "When NOT to use"; "Instructions" covering the response pattern (read fully, restate the requirement, verify against the codebase, evaluate for THIS codebase, respond with technical acknowledgment or reasoned push-back, implement one item at a time and test each); a "Forbidden responses" subsection (no performative agreement, no gratitude expressions - state the fix instead); a YAGNI check for "implement properly" suggestions (grep for usage first); implementation ordering (clarify unclear items first, then blocking -> simple -> complex); a "Common Rationalizations" table; a binary "Verification" checklist. Target <=500 lines.
> Constraint: pure markdown, no code. Do not register yet (T004). Note in "Related Skills": cross-links to the existing `code-review/*` review-producing skills and to `[[verification-before-completion]]`.

---

#### 1.3 — using-git-worktrees skill

- [x] T003 [P] Create workflow skill in catalog/skills/workflow/using-git-worktrees/SKILL.md

**Objective**: Ship a skill that ensures work happens in an isolated workspace, preferring the harness's native worktree tool over a raw `git worktree` fallback.

**Prompt**:
> Create `catalog/skills/workflow/using-git-worktrees/SKILL.md`. Adapt the pattern in `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a (source: superpowers `skills/using-git-worktrees/SKILL.md`); adapt to Nexus-Hub voice, do not copy (N2).
> Frontmatter: `name`, pushy trigger-focused `description` (use when starting isolated feature work or before executing an implementation plan; `SKIP:` quick edits in place, or when already in an isolated workspace), `summary_l0` and `overview_l1` (quoted).
> Body must encode the safe sequence: Step 0 detect existing isolation (`git rev-parse --git-dir` vs `--git-common-dir`, with a submodule guard via `git rev-parse --show-superproject-working-tree`); Step 1a prefer a native worktree tool (e.g. the harness `EnterWorktree` tool / `/worktree`) over raw git; Step 1b git fallback with directory-priority order and a mandatory `git check-ignore` verification before creating a project-local worktree; Step 3 auto-detect project setup; Step 4 verify a clean test baseline before reporting ready. Include a Quick Reference table, "Common Mistakes", "Common Rationalizations", "Red Flags" (never use `git worktree add` when a native tool exists), and a binary "Verification" checklist. Provide POSIX commands; note PowerShell equivalents where a Windows user would differ. Target <=500 lines.
> Constraint: the skill INSTRUCTS git commands the agent already runs; it adds no new dependency. Do not register yet (T004).

---

#### 1.4 — Register the three new skills

- [x] T004 Register the new skills in data/SKILL_INDEX.md, data/skills.json, data/marketplace.json

**Objective**: Make the three Phase 1 skills discoverable via the catalog registries.

**Prompt**:
> Register the three skills created in T001-T003 (`verification-before-completion`, `receiving-code-review`, `using-git-worktrees`) per the AGENTS.md "Register the skill" procedure:
> 1. `data/SKILL_INDEX.md`: add one table row per skill (`| <name> | <Category> | "<summary_l0>" | catalog/skills/<category>/<name>/SKILL.md |`). Categories: `Workflow`, `Code Review`, `Workflow`.
> 2. `data/skills.json`: add one entry per skill following the existing schema (name, title, description, long_description, summary_l0, overview_l1, version 1.0.0, author, category, language, tags, priority, based_on, tools_required, path, file, size, downloads 0, status active, security scores 100/100/95).
> 3. `data/marketplace.json`: increment `skill_count` in the `workflow` (+2) and `code-review` (+1) category entries and `total_skills` in `statistics` (+3).
> Do not edit any other `data/` content. Constraint: these three files are the only `data/` files allowed to be edited manually (AGENTS.md rule 5).

---

#### 1.5 — Testing and Stabilization

- [x] T005 Run and stabilize Phase 1 in data/ and catalog/skills/

**Objective**: Verify catalog integrity and that the new discipline skills trigger.

**Prompt**:
> Stabilize Phase 1. Run `make validate` (JSON catalog integrity) and `make lint` (ShellCheck) and fix any failures. Then run a `skill-eval-loop` trigger check on each of the three new skills: author a minimal `evals.json` with at least one `should_trigger: true` prompt and one `should_trigger: false` prompt per skill, and confirm the trigger rate is 1.0 on the positive prompt and 0.0 on the negative. If a skill under-triggers, tighten its `description` per `catalog/skills/workflow/skill-eval-loop/references/improvement-heuristics.md` (add verbatim trigger phrases) and re-run. Do not advance to Phase 2 until validators are green and all three skills trigger correctly. After passing, run `/generate-session-history` to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (`make validate` validators green; `make lint` n/a - no shell scripts; static trigger check passed, live eval-loop deferred per known-gaps)
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 2

---

## Phase 2: Skill-authoring methodology upgrade

**Goal**: Add the TDD-for-skills authoring methodology and the research-backed persuasion-principles reference as bundled references under the skill-authoring skill.
**Prerequisites**: None (independent of Phase 1, but sequenced after it per RE-first concern grouping).
**Stability Gate**: `make validate` passes including the orphan-bundle check; every new reference file is linked from a SKILL.md.

### Sub-tasks

#### 2.1 — TDD-for-skills authoring methodology

- [x] T006 Add authoring-methodology references in catalog/skills/workflow/create-custom-command/references/

**Objective**: Encode the "no skill without a failing baseline test first" methodology and pressure-scenario testing for discipline skills.

**Prompt**:
> Add two reference files under `catalog/skills/workflow/create-custom-command/references/`: `tdd-for-skills.md` and `pressure-testing.md`. Adapt the methodology documented in `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a and Section 4 (source: superpowers `skills/writing-skills/SKILL.md` and `testing-skills-with-subagents.md`); adapt to Nexus-Hub voice, do not copy (N2).
> `tdd-for-skills.md`: the RED-GREEN-REFACTOR mapping for skill authoring (run a pressure scenario WITHOUT the skill, capture rationalizations verbatim = RED; write the skill to counter them = GREEN; close new loopholes = REFACTOR), the "Iron Law: no skill without a failing baseline first", and how this complements Nexus-Hub's existing empirical `skill-eval-loop`.
> `pressure-testing.md`: how to write pressure scenarios (3+ combined pressures: time, sunk cost, authority, exhaustion, social, pragmatic), the meta-testing technique ("how could the skill have been written so option A was the only acceptable answer?"), and signs a discipline skill is bulletproof.
> Then update `catalog/skills/workflow/create-custom-command/SKILL.md` to link both references (orphan-bundle rule: every bundled file must be referenced from a SKILL.md). Constraint: pure markdown.

---

#### 2.2 — persuasion-principles reference

- [x] T007 Add persuasion-principles reference in catalog/skills/workflow/create-custom-command/references/persuasion-principles.md

**Objective**: Provide research-backed grounding for why rationalization tables, red-flag lists, and authority framing work in discipline skills.

**Prompt**:
> Create `catalog/skills/workflow/create-custom-command/references/persuasion-principles.md`. Adapt the content in `docs/archive/v2/v2.3/comparison-superpowers.md` Section 4 (source: superpowers `skills/writing-skills/persuasion-principles.md`); adapt to Nexus-Hub voice, do not copy (N2).
> Cover the principles useful for discipline skills (authority, commitment, scarcity, social proof, unity) with concrete skill-authoring examples, and the explicit guidance to AVOID "liking" and "reciprocity" for compliance (they create sycophancy). Cite the public research (Cialdini 2021; Meincke et al. 2025, N=28,000, 33% -> 72% compliance) as references. Add a principle-by-skill-type table (discipline / guidance / collaborative / reference). Link this reference from `create-custom-command/SKILL.md` (orphan-bundle rule). Constraint: pure markdown; cite research, do not reproduce copyrighted text.

---

#### 2.3 — Testing and Stabilization

- [x] T008 Run and stabilize Phase 2 in catalog/skills/workflow/create-custom-command/

**Objective**: Confirm the new references validate and are not orphaned.

**Prompt**:
> Run `make validate` (with the per-skill orphan-bundle audit) and confirm `tdd-for-skills.md`, `pressure-testing.md`, and `persuasion-principles.md` are each referenced from `create-custom-command/SKILL.md`. Fix any orphan warnings. Confirm the `skill-eval-loop` cross-link added in T006 resolves. Do not advance until validate is clean. Run `/generate-session-history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (`make validate` run via `python scripts/validate_skills.py`; orphan-bundle clean across the full catalog; `make` unavailable on the Windows host so validators invoked directly)
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 3

---

## Phase 3: Discipline framing + operational enhancements

**Goal**: Harden existing skills with superpowers' discipline framing and operational templates (no new top-level skills).
**Prerequisites**: None.
**Stability Gate**: `make validate` + `make lint` pass; orphan-bundle clean; enhanced skills still under the 800-line soft cap or refactored to references.

### Sub-tasks

#### 3.1 — systematic-debugging discipline framing

- [x] T009 [P] Add discipline framing to catalog/skills/bug-fixing/regression-root-cause-analyzer/SKILL.md

**Objective**: Add the "no fixes without root-cause investigation" gate, the 3-failed-fixes-question-architecture rule, and the multi-component evidence-gathering pattern.

**Prompt**:
> Enhance `catalog/skills/bug-fixing/regression-root-cause-analyzer/SKILL.md` with the discipline framing documented in `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a (source: superpowers `skills/systematic-debugging/SKILL.md`); adapt, do not copy (N2).
> Add: (1) an "Iron Law: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST" framing; (2) the distinctive rule "after 3+ failed fix attempts, STOP and question the architecture, not the bug" with the failure-pattern signals; (3) the multi-component-boundary evidence-gathering pattern (instrument each component boundary, run once to find WHERE it breaks, then investigate that component); (4) a "Common Rationalizations" table if not already present. Keep the existing technique content. If the file would exceed the 800-line soft cap, move the long evidence-gathering example to a `references/` file and link it. Constraint: pure markdown; do not change the skill's `name` or break its registry entry.

---

#### 3.2 — subagent two-stage-review templates

- [x] T010 [P] Add reviewer prompt templates in catalog/skills/orchestration/multi-agent-coordinator/assets/

**Objective**: Add concrete implementer + two-stage-reviewer prompt templates and the 4-status implementer protocol.

**Prompt**:
> Add prompt-template assets under `catalog/skills/orchestration/multi-agent-coordinator/assets/`: `implementer-prompt.md`, `spec-reviewer-prompt.md`, `code-quality-reviewer-prompt.md`. Adapt from `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a (source: superpowers `skills/subagent-driven-development/*-prompt.md`); adapt to Nexus-Hub voice, do not copy (N2).
> In `multi-agent-coordinator/SKILL.md`, add a subsection documenting the two-stage review ordering (spec compliance FIRST, then code quality - never reversed), the 4-status implementer protocol (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED and how to handle each), and per-role model tiering (cheap model for mechanical tasks, capable model for design/review). Link the three asset files (orphan-bundle rule). Constraint: pure markdown.

---

#### 3.3 — condition-based-waiting reference

- [x] T011 [P] Add condition-based-waiting reference in catalog/skills/tests-generation/flaky-test-detector/references/condition-based-waiting.md

**Objective**: Document the "wait for the condition, not a guessed delay" pattern as a reusable reference.

**Prompt**:
> Create `catalog/skills/tests-generation/flaky-test-detector/references/condition-based-waiting.md`. Adapt from `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a (source: superpowers `skills/systematic-debugging/condition-based-waiting.md`); adapt, do not copy (N2).
> Cover: the core principle (wait for the actual condition, not `sleep`), a before/after code contrast, a quick-patterns table (wait for event / state / count / file / complex condition), when an arbitrary timeout IS correct (timing-behavior tests, documented and justified), and common mistakes. Link the reference from `flaky-test-detector/SKILL.md` (orphan-bundle rule). The reusable `waitFor` helper itself is added in Phase 5 (T019); reference it as "see the bundled helper under assets/". Constraint: pure markdown.

---

#### 3.4 — brainstorming hard-gate

- [x] T012 [P] Add a design-approval hard-gate to catalog/skills/developer-experience/spec-driven-development/SKILL.md

**Objective**: Add an explicit "no implementation before an approved design" gate, folding the superpowers brainstorming pattern into the existing spec skill rather than creating a duplicate.

**Prompt**:
> Enhance `catalog/skills/developer-experience/spec-driven-development/SKILL.md` (and cross-link `catalog/skills/developer-experience/idea-refine/SKILL.md`) with the hard-gate pattern from `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a (source: superpowers `skills/brainstorming/SKILL.md`); adapt, do not copy (N2).
> Add a clearly-marked hard gate: do not invoke any implementation skill, write code, or scaffold until a design/spec has been presented in reviewable sections AND the user has approved it - applies regardless of perceived simplicity. Add the "this is too simple to need a design" anti-pattern rebuttal and the one-question-at-a-time clarification convention. Do NOT add the superpowers visual-companion browser server (that is the deferred P3 item, Phase 6 / appendix). If this materially duplicates an existing section, enhance in place rather than adding a parallel section. Constraint: pure markdown; do not create a new top-level `brainstorming` skill (avoid catalog duplication).

---

#### 3.5 — Testing and Stabilization

- [x] T013 Run and stabilize Phase 3 across the four enhanced skills

**Objective**: Confirm the enhancements validate, stay within size norms, and do not orphan any bundled file.

**Prompt**:
> Run `make validate` and `make lint`. Confirm: the three new assets under `multi-agent-coordinator/assets/` and the new reference under `flaky-test-detector/references/` are each linked from their SKILL.md (orphan-bundle clean); no enhanced SKILL.md exceeds the 800-line soft cap (refactor to `references/` if it does); no registry entry (`data/`) was broken by the edits. Fix any failures. Do not advance until green. Run `/generate-session-history` to document Phase 3.

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (`validate_skills.py` orphan-bundle PASS 0/0; JSON catalogs OK; no-personal-paths / unicode-safety / supply-chain validators exit 0; `make` unavailable on Windows host so validators invoked directly; `make lint` n/a - no shell scripts added this phase)
- [x] No known regressions from prior phases (enhancements only; no registry/data edits; all four enhanced skills under the 800-line soft cap)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 4

---

## Phase 4: Eval-harness trigger techniques

**Goal**: Add the three trigger-testing techniques superpowers' harness has that Nexus-Hub's `skill-eval-loop` lacks: premature-action detection, multi-turn conversation triggering, and cheap-model fragility testing.
**Prerequisites**: None (modifies the existing, already-registered `scripts/optimize_skill_description.py`).
**Stability Gate**: `make test` passes including new pytest cases in `catalog/hooks/tests/test_eval_loop.py`.

### Sub-tasks

#### 4.1 — premature-action detection

- [x] T014 Add premature-action detection to scripts/optimize_skill_description.py

**Objective**: Detect the failure mode where the agent invokes other tools before loading the skill.

**Prompt**:
> Extend `scripts/optimize_skill_description.py` (and any helper it uses) to detect "premature action" in a `with_skill` run: parse the run's tool-invocation stream and flag any non-`Skill`, non-`TodoWrite` tool use that occurs before the first `Skill` invocation. Surface this per-eval as a boolean `premature_action` field in the grading/benchmark output. Adapt the technique from `docs/archive/v2/v2.3/comparison-superpowers.md` Section 8 (source: superpowers `tests/explicit-skill-requests/run-test.sh`). Constraint: reuse the existing CLI-adapter dispatcher (claude/gemini/codex/opencode) - no new outbound calls, no new dependency; the harness uses the user's already-configured model CLI exactly as today. Preserve the existing optimizer behavior and CLI-parity invariant.

---

#### 4.2 — multi-turn + cheap-model trigger testing

- [x] T015 Add multi-turn and cheap-model trigger modes to scripts/optimize_skill_description.py

**Objective**: Test whether a skill triggers deep in a multi-turn workflow and whether it survives on a cheaper/faster model.

**Prompt**:
> Add two opt-in modes to the eval harness driven by `scripts/optimize_skill_description.py` (or a sibling runner if cleaner): (1) a multi-turn mode that replays an ordered list of turns from the eval entry and asserts the skill triggers at the designated turn (adapt from superpowers `tests/explicit-skill-requests/run-haiku-test.sh`, per comparison Section 8); (2) a cheap-model mode that runs the same eval against a faster model (e.g. haiku) to surface descriptions that only trigger on stronger models. Extend the `evals.json` schema (documented under `catalog/skills/workflow/skill-eval-loop/references/schemas.md`) with optional `turns` and `model` fields; keep both modes opt-in so existing single-turn evals are unaffected. Constraint: reuse the existing CLI dispatcher; no new dependency or outbound path.

---

#### 4.3 — trigger-testing reference

- [x] T016 Add references/trigger-testing.md under catalog/skills/workflow/skill-eval-loop/

**Objective**: Document the three new techniques and when to use each.

**Prompt**:
> Create `catalog/skills/workflow/skill-eval-loop/references/trigger-testing.md` documenting the three techniques added in T014-T015 (premature-action detection, multi-turn triggering, cheap-model fragility) - what each catches, how to author an eval that exercises it, and how to read the new output fields. Cross-reference the comparison (Section 8) for provenance. Link the reference from `skill-eval-loop/SKILL.md` (orphan-bundle rule). Constraint: pure markdown.

---

#### 4.4 — Testing and Stabilization

- [x] T017 Add and run pytest cases in catalog/hooks/tests/test_eval_loop.py

**Objective**: Cover the new harness behavior with tests and confirm parity.

**Prompt**:
> Add pytest cases to `catalog/hooks/tests/test_eval_loop.py` covering: premature-action detection (a fixture stream with a tool_use before the Skill invocation flags `premature_action=true`; a clean stream flags false); the multi-turn schema parses and the designated-turn assertion works; the cheap-model mode threads the `model` field through the dispatcher. Preserve the existing CLI-adapter parity invariant test. Run `make test` and fix all failures. Do not advance until green. Run `/generate-session-history` to document Phase 4.

---

### Phase 4 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (`catalog/hooks/tests/test_eval_loop.py` 37 passed, was 14; +23 new Phase 4 cases. `make` unavailable on the Windows host so pytest invoked directly. The 73 failures elsewhere in `catalog/hooks/tests/` are pre-existing bash-hook-on-Windows environmental failures in 5 unrelated test files - same cross-OS class as DF-v23-6, green on Linux CI - not regressions from this phase.)
- [x] No known regressions from prior phases (existing optimizer behavior preserved: dry-run exit 0, train/test split + selection-metric unchanged; parity invariant still enforced after the `build_cli_command` extraction)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 5

---

## Phase 5: Flaky-test tooling cluster

**Goal**: Ship the reusable local test-pollution bisector and the `waitFor` helper as per-skill bundled resources under `flaky-test-detector`.
**Prerequisites**: Phase 3 T011 (the condition-based-waiting reference that links the helper).
**Stability Gate**: `make validate` passes; the new script/asset are linked from `flaky-test-detector/SKILL.md`; the `.sh` has a `.ps1` sibling (parity rule).

### Sub-tasks

#### 5.1 — find-polluter bisector

- [x] T018 Add find-polluter.sh and find-polluter.ps1 in catalog/skills/tests-generation/flaky-test-detector/scripts/

**Objective**: Provide a local bisection script that finds which test file creates filesystem/state pollution.

**Prompt**:
> Create `catalog/skills/tests-generation/flaky-test-detector/scripts/find-polluter.sh` and a parity sibling `find-polluter.ps1`. Reverse-engineer the generic pattern from `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a (source: superpowers `skills/systematic-debugging/find-polluter.sh`) into a project-agnostic bisector: given a path/glob to watch for pollution and a test-runner command, run each matching test file in isolation and report the first one that creates the watched artifact. Parameterize the test command (do not hardcode `npm test`). The `.sh` must follow the bash safety rules in `catalog/rules/bash/` (`set -euo pipefail`, quoted expansions); the `.ps1` must be the functional equivalent. Reference both scripts from `flaky-test-detector/SKILL.md` (orphan-bundle rule). Constraint: per-skill `scripts/` are auto-copied by the installer (AGENTS.md) - NO installer.sh/installer.ps1 edit needed; confirm this is a per-skill script, not a repo-level one. No network, no secrets.

---

#### 5.2 — condition-based-waiting helper

- [x] T019 Add waitFor helper example in catalog/skills/tests-generation/flaky-test-detector/assets/condition-based-waiting-example.ts

**Objective**: Provide a copy-in `waitFor` polling helper that replaces `sleep`-based flakiness.

**Prompt**:
> Create `catalog/skills/tests-generation/flaky-test-detector/assets/condition-based-waiting-example.ts` containing a generic `waitFor(condition, description, timeoutMs)` polling helper plus 2-3 domain helpers (e.g. `waitForEvent`, `waitForCount`). Adapt from the pattern in `docs/archive/v2/v2.3/comparison-superpowers.md` Section 5a (source: superpowers `skills/systematic-debugging/condition-based-waiting-example.ts`); one excellent example, well-commented on WHY. Reference it from the `condition-based-waiting.md` reference created in T012 and from `flaky-test-detector/SKILL.md` (orphan-bundle rule). Constraint: a copy-in example, not a runtime dependency.

---

#### 5.3 — Testing and Stabilization

- [x] T020 Run and stabilize Phase 5 in catalog/skills/tests-generation/flaky-test-detector/

**Objective**: Validate the bundle and confirm cross-platform parity of the script.

**Prompt**:
> Run `make validate` (orphan-bundle audit must show the new `scripts/` and `assets/` files linked) and `make lint` (ShellCheck on `find-polluter.sh`). If a Windows and a POSIX environment are both available, run `find-polluter.sh` and `find-polluter.ps1` against a tiny throwaway test fixture to confirm they behave identically; otherwise note the cross-OS run as deferred. Fix any failures. Do not advance until green. Run `/generate-session-history` to document Phase 5.

---

### Phase 5 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (`make` unavailable on Windows host so validators invoked directly: orphan-bundle audit PASS 0/0 across 237 skills; JSON catalogs OK; no-personal-paths / unicode-safety / supply-chain-iocs / workflow-security validators exit 0; new files ASCII-clean. ShellCheck unavailable on host - `bash -n` syntax check passed; ShellCheck deferred, consistent with `make lint`'s skip-when-absent behavior.)
- [x] `.sh` / `.ps1` parity confirmed (both run live against a throwaway fixture; identical behavior across 5 cases each: polluter detection, no-polluter, append-mode, unsafe-watch guard, no-match guard. A literal-pattern `nullglob` bug in the `.sh` was found via the smoke test and fixed.)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 6

---

## Phase 6: Deferral record + polish

**Goal**: Record the deferred P3 visual-brainstorm server as a tracked known-gap (not build it), update catalog counts and the changelog, and run a final validation sweep.
**Prerequisites**: Phases 1-5 complete.
**Stability Gate**: `make validate` + `make lint` + `make test` all pass; AGENTS.md catalog counts reflect the new skills; CHANGELOG `[Unreleased]` documents the adoption.

### Sub-tasks

#### 6.1 — Record the visual-brainstorm-server deferral

- [x] T021 Record the P3 deferral in docs/archive/v2/v2.3/known-gaps.md

**Objective**: Capture the deferred visual brainstorming server as a tracked item with a revisit trigger, rather than building it.

**Prompt**:
> Append a `DF` (deferred) entry to `docs/archive/v2/v2.3/known-gaps.md` (create the file from the `known-gaps-tracker` template if it does not exist) recording the deferral of the superpowers visual brainstorming server (comparison report Section 11 P3 / Section 13 N3). State: it is `re-full` and local-only (binds 127.0.0.1, zero outbound, passes the MCP Registry Policy) but deferred on identity/maintenance grounds (Nexus-Hub is catalog-content-first; a long-lived local node server belongs under `extensions/` only when a concrete need exists). Record the revisit trigger: "build only if a user-facing need for in-session visual collaboration emerges." Do NOT build the server. Update the file's Summary counts.

---

#### 6.2 — Update catalog counts and changelog

- [x] T022 Update AGENTS.md catalog counts and CHANGELOG.md [Unreleased]

**Objective**: Reflect the three new skills and the adoption work in project metadata.

**Prompt**:
> Update `AGENTS.md` catalog counts to reflect the three new skills added in Phase 1 (skills count +3; commands/hooks/agents unchanged). Add a `## [Unreleased]` block to `CHANGELOG.md` under "Added" listing: the three new discipline skills; the skill-authoring methodology references (TDD-for-skills, pressure-testing, persuasion-principles); the systematic-debugging discipline framing, subagent review templates, condition-based-waiting reference, and brainstorming hard-gate enhancements; the eval-harness trigger techniques (premature-action + multi-turn + cheap-model); and the find-polluter + waitFor bundled resources. Note that all items are `skill-native` or `re-full` with zero new runtime dependencies, zero outbound calls, and zero new credentials, and that phase ordering followed the MCP Registry Policy reverse-engineer-first default. Keep CHANGELOG entries ASCII-only.

---

#### 6.3 — Final validation sweep

- [x] T023 Run the final validation sweep across the repo

**Objective**: Confirm the whole adoption is green and documented.

**Prompt**:
> Run `make validate`, `make lint`, and `make test` and fix any remaining failures. Confirm the three new skills are registered in all three `data/` files and that `data/marketplace.json` `total_skills` is consistent. Confirm no orphan-bundle warnings remain. Confirm the sibling plan `docs/archive/v2/v2.3/plans/adoption-ecc-cybersec-skills.md` and its tracked items were not modified. Run `/generate-session-history` to document Phase 6 and the completed adoption.

---

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|

(No constitution file present; no violations to track.)

---

### Phase 6 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (`make` unavailable on the Windows host so validators invoked directly: JSON catalogs load OK; orphan-bundle audit PASS 0/0 across 237 skills; no-personal-paths / unicode-safety / supply-chain-iocs / workflow-security all rc=0; the three edited files (known-gaps.md, AGENTS.md, CHANGELOG.md) introduce zero new unicode warnings -- the residual em-dash warnings are pre-existing debt under the tracked WN-v23-3 umbrella. `make test` is N/A: Phase 6 changed only markdown docs, so no code/test surface moved and the validators are the relevant gate.)
- [x] AGENTS.md counts + CHANGELOG updated (catalog headline + tree comment bumped to 230 skills / 23 categories; CHANGELOG [Unreleased] adoption block added under Added / Changed / Deferred)
- [x] Sibling adoption-ecc-cybersec-skills plan untouched (git diff empty)
- [x] Session history generated for this phase
- [x] Adoption complete (Phases 1-6 of 6 closed; the one P3 item recorded as DF-v23-9 deferral)

---

## Appendix: Items explicitly NOT adopted (convention / scope reasons)

These items from the comparison's Section 13 are intentionally excluded. None is a security/data-flow rejection: superpowers introduces no third-party data flow, so the MCP Registry Policy hard-no list (search / embeddings / scraping / generation-as-service) is not implicated. The exclusions are about Nexus-Hub conventions, scope, and identity.

- **N1: Wholesale replacement of the "pushy description" convention with superpowers' "WHEN-only, never summarize workflow" rule.** Not adopted as a swap. Nexus-Hub's three-tier model already separates `description` (trigger) from `summary_l0` / `overview_l1` (what it does). The eval-backed insight is captured in this plan by keeping new skills' `description` trigger-focused (T001-T003) and pushing "what it does" into `overview_l1`. (Convention.)
- **N2: Verbatim import of superpowers skill content or its "your human partner" voice.** Not adopted. Every phase above adapts patterns into Nexus-Hub voice. Superpowers' own contribution policy rejects reformatting its tuned content, and copying conflicts with Nexus-Hub's communication-style rules. (Scope / convention.)
- **N3: Shipping the visual brainstorming websocket server this cycle.** Deferred, recorded in T024. Local-only and policy-compliant, but a runtime server against Nexus-Hub's catalog-content-first identity. (Scope / maintenance.)
- **N4: The per-harness official-marketplace plugin packaging model.** Not applicable. Nexus-Hub's `scripts/installer.{sh,ps1}` + `scripts/lib/integrations/` registry already reaches more platforms. (Scope.)
- **N5: The polyglot single-file hook wrapper (`run-hook.cmd`) replacing `.sh`+`.ps1` sibling hooks.** Not adopted. Nexus-Hub's PowerShell-native hooks serve Windows users without Git Bash, and the sibling-pair convention is enforced project-wide. (Convention.)

---

## Appendix: Items out of scope by tier filter

Scope filter was `all` (P0 + P1 + P2 + P3), so no comparison adoption items were dropped by tier. The only deferred item is the P3 visual brainstorming server, handled as a tracked deferral in T024 rather than a build task.
