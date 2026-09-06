# Plan -- Adopt the /teach skill as session-teach-back

**Project**: Nexus-Hub
**Version**: v3.2.0
**Slug**: adoption-teach
**Plan Type**: Feature / Enhancement
**Created**: 2026-06-05
**Goal**: Ship one new `workflow` skill, `session-teach-back`, that adds a Socratic mastery-confirmation loop for the human operator by composing the existing `session-query` extractor and `dev-progress-tracker` checklist pattern with a new quiz loop -- zero new dependency, credential, or outbound call.

## Overview

This plan adopts all six items from the comparison report [`docs/releases/v3/v3.2/comparisons/v3.2.0-comparison-teach.md`](../comparison-teach.md), which analyzed the viral `/teach` skill (`alexknowshtml/claude-skills`) against Nexus-Hub. The report found that `/teach` is a genuine net-new capability (an interactive Socratic quiz that confirms the human understood what a session produced) but is `skill-native` under the MCP Registry Policy: its two hardest pieces already exist in the catalog as separate skills. `session-query` ships a script-first, cross-platform, zero-outbound JSONL session extractor that is strictly better than `/teach`'s inline `grep`, and `dev-progress-tracker` is the persistent dated-checklist pattern. The only genuinely missing parts are the Socratic loop itself, the "restate your understanding first" calibration move, the multiple-choice discipline, and the teach-someone-else mode.

The work collapses into a single new skill at `catalog/skills/workflow/session-teach-back/SKILL.md`. Nothing here introduces a new runtime dependency, outbound call, credential, MCP entry, or `scripts/<name>.py` installer artifact -- the skill folder is auto-copied recursively by both installers. Two of `/teach`'s specific defaults are adapted rather than adopted: auto-commit-and-push of the checklist is reclassified to opt-in (off by default) to respect the `git-guardrails` hook and the global "outward-facing git requires confirmation" rule (N1), and the hard-coded `sessions/teaching/` path plus `America/New_York` timezone are replaced with catalog-convention placement and platform-neutral dating (N2). The capability triggers by phrase as a skill; it does NOT add a 15th slash command, which would regress the v3.0.0 command consolidation.

Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 6 of the source comparison for the ordering rationale. Because every adoption item is `skill-native` or reuses the already-built `re-full` extractor, there is no internal-build backlog ahead of the skill-native work; the three phases are a single track ordered by capability dependency (core MVP -> enhancements -> integration). One open item from the prior version (`WN-v31-1`, a v3.1.0 CI-verification warning) was reviewed during Step 0.6 ingest and deliberately left on v3.1.0's tracker as out of scope for this single-skill adoption.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/v3/v3.2/constitution.md - skipping check. Recommend running /constitution to establish project principles.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Core skill (solo-mode MVP) | `session-teach-back` SKILL.md with the Socratic loop, calibration opener, dated mastery checklist, drill-into-why, and hard completion gate; sources sessions by reusing `session-query`; registered in all three catalog registries; catalog passes `make validate` + `make lint` |
| 2 | Modes + interaction enhancements | teach-someone-else mode, eli5/eli14/intern depth levels, multiple-choice discipline, and an opt-in (off-by-default) checklist commit added to the same SKILL.md body |
| 3 | Integration + discoverability | bidirectional `[[session-teach-back]]` Related-Skills links across the `session-*` family, a `using-nexus-hub` mention, a CHANGELOG `[Unreleased]` entry, and a final green check |

---

## Phase 1: Core skill (solo-mode MVP)

**Goal**: A working `session-teach-back` skill that, given a session source, quizzes the human item by item against a persistent mastery checklist and refuses to finish until every item is confirmed.
**Prerequisites**: None.
**Stability Gate**: `make validate` and `make lint` both exit 0; the skill-security scanner reports 0 HIGH/CRITICAL on the new skill; the skill is present in all three registries and the registry counts are consistent.

### Sub-tasks

#### 1.1 -- Write the core SKILL.md

- [x] T001 Create the core skill at catalog/skills/workflow/session-teach-back/SKILL.md

**Objective**: Author the new skill body implementing the solo-mode Socratic loop (insight I1), the calibration opener (I9), the dated mastery checklist (I5), drill-into-why (I8), and the hard completion gate (I11), sourcing the session via the existing `session-query` extractor (I4) rather than inline `grep`.

**Prompt**:
> Create `catalog/skills/workflow/session-teach-back/SKILL.md` for the Nexus-Hub catalog. This skill adds a Socratic mastery-confirmation loop that quizzes the HUMAN operator on what a Claude Code session actually produced, confirming each concept item by item before finishing. Read `docs/v3/v3.2/comparisons/v3.2.0-comparison-teach.md` Sections 3, 5, 6, and 8 first -- they are the authoritative source for the mechanics, the security classification, and the adapt-not-adopt constraints.
>
> Required YAML frontmatter (per `AGENTS.md`): `name: session-teach-back`; a pushy `description` listing trigger phrases verbatim ("teach me what we built", "quiz me on this session", "teach-back", "did I understand X", "drill me on the session") AND a SKIP clause fencing off look-alikes (SKIP: generating a session record -> use `generate-session-history` / `session-history`; querying past sessions -> use `session-query`; task tracking -> use `dev-progress-tracker`); `summary_l0` (<=15 words, quoted); `overview_l1` (<=150 words, quoted).
>
> Required body sections in order: Title; "When to Use This Skill" (include explicit "When NOT to use"); "Instructions"; "Common Rationalizations" (table, each row a concrete failure mode -- e.g. "I will quiz all the concepts in one message" -> rebuttal that batching breaks the one-question-per-exchange retention mechanic); "Verification" (binary checklist of observable artifacts); "Related Skills" (link `[[session-query]]`, `[[session-history]]`, `[[dev-progress-tracker]]`).
>
> Instructions must specify: (1) Source resolution -- REUSE `session-query` to locate and digest the session (do NOT re-implement `grep` over `~/.claude/projects`; call out that the bundled `session-query` scripts `discover-sessions.{sh,ps1}` + `extract-session.{py,ps1}` are script-first, cross-platform, and zero-outbound). (2) A dated mastery checklist written to a catalog-convention path (use `docs/` or `.nexus/`, NOT the upstream `sessions/teaching/` path -- this is adaptation N2) with platform-neutral dating (NOT a hard-coded `TZ="America/New_York" date` -- also N2), YAML frontmatter (`mode`, `source`, `started`), semantic sections (The Problem / The Solution / Broader Context), `[ ]`/`[x]` checkboxes, and an `n/total confirmed` progress line at the top, with concrete-not-generic items tied to the real session. (3) The solo loop: re-read the checklist before each exchange; open by asking the user to restate their understanding then fill gaps (calibration); pick the next unconfirmed item; ask ONE targeted question; on a correct answer mark `[x]` immediately (never batch) and note inline progress; on a miss, explain and re-ask in a different form; drill into WHY before advancing; show progress every 3-4 exchanges. (4) Hard completion gate: never offer to wrap up until 100% of items are `[x]`.
>
> Constraints to bake in: one question per exchange (and explicitly note this is a teaching loop, NOT requirements intake -- it deliberately does not batch, which is the opposite of the general clarify-question batching rule, and both can coexist); keep the auto-commit of the checklist OUT of this core version (it arrives opt-in in Phase 2 per adaptation N1); do NOT add any slash command; do NOT ship a `scripts/` subdirectory (this is a prompt-only skill). Keep the body <=500 lines per the size norm. Follow `catalog/style-guides/markdown.md` (blank lines around lists/tables/headings, ASCII-only, 4-space nested indent, no hard-wrapping).

---

#### 1.2 -- Register the skill in the three catalog registries

- [x] T002 Register the skill in data/SKILL_INDEX.md, data/skills.json, and data/marketplace.json

**Objective**: Make the new skill discoverable by adding it to every catalog registry per the `AGENTS.md` "Register the skill" procedure.

**Prompt**:
> Register the new `session-teach-back` skill in the three Nexus-Hub catalog registries, following the exact procedure in `AGENTS.md` ("Register the skill"):
>
> 1. `data/SKILL_INDEX.md` -- add one table row: `| session-teach-back | Workflow | "<summary_l0 from the SKILL.md>" | catalog/skills/workflow/session-teach-back/SKILL.md |`.
> 2. `data/skills.json` -- add one entry to the `skills` array following the existing schema (name, title, description, long_description, summary_l0, overview_l1, version `1.0.0`, author, category `workflow`, language, tags, priority, based_on, tools_required, path, file, size, downloads `0`, status, security with default scores `structural: 100, integrity: 100, semantic: 95`). Copy the field shape from an adjacent `workflow` skill entry (e.g. `session-query` or `dev-progress-tracker`).
> 3. `data/marketplace.json` -- increment `skill_count` for the `workflow` category entry and `total_skills` in `statistics`.
>
> Do not hand-edit any other `data/` file. After editing, the next sub-task runs `make validate`.

---

#### 1.3 -- Testing and Stabilization

- [x] T003 Run and stabilize Phase 1 validators for catalog/skills/workflow/session-teach-back/SKILL.md

**Objective**: Confirm the new skill and registry edits leave the catalog green.

**Prompt**:
> Validate Phase 1. Run `make validate` (JSON catalog integrity + the skill-security scanner gate) and `make lint` (ShellCheck). The scanner must report 0 HIGH/CRITICAL on `catalog/skills/workflow/session-teach-back/SKILL.md` (it ships no scripts, so this is expected). Confirm the orphan-bundle audit is clean (the skill has no `scripts/`, `references/`, or `assets/` subdirs to orphan). Confirm `data/skills.json`, `data/SKILL_INDEX.md`, and `data/marketplace.json` agree on the new skill and that `marketplace.json` counts incremented consistently. If `make` is not on PATH (Windows dev host), invoke the underlying validators directly and note it. Fix any failure and re-run until all exit 0. Then run `/generate-session-history` to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] `make validate` and `make lint` exit 0 (or validators run directly, all green)
- [x] Skill-security scanner: 0 HIGH/CRITICAL on the new skill
- [x] Skill present and consistent across all three registries
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 2

---

## Phase 2: Modes + interaction enhancements

**Goal**: Extend the skill body with the teach-someone-else mode, depth levels, multiple-choice discipline, and an opt-in (off-by-default) checklist commit.
**Prerequisites**: Phase 1.
**Stability Gate**: `make validate` exits 0 and the scanner stays clean after each edit; the SKILL.md remains <=500 lines; auto-commit is documented as off by default and gated on user confirmation.

### Sub-tasks

#### 2.1 -- Add teach-someone-else mode and depth levels

- [x] T004 Add the teach-others mode and eli5/eli14/intern depth levels to catalog/skills/workflow/session-teach-back/SKILL.md

**Objective**: Implement insight I14 (reframe the same checklist as a guide for explaining to a named student) and I12 (adjustable explanation depth).

**Prompt**:
> Edit `catalog/skills/workflow/session-teach-back/SKILL.md` to add two capabilities described in `docs/v3/v3.2/comparisons/v3.2.0-comparison-teach.md` Section 3 (insights I14 and I12):
>
> 1. Teach-someone-else mode: when the user wants to teach a named student rather than self-quiz, reuse the same mastery checklist but reframe it as a teaching guide -- for each section, suggest explanation strategies and what questions to pose to the student, and track what the user has explicitly covered and confirmed the student understood. Add `student` and `mode` (solo | teaching) fields to the checklist frontmatter (these were defined in Phase 1's frontmatter spec). Trigger by phrase ("help me teach X to <name>", "teaching mode"), NOT by a `--student` CLI flag (Nexus-Hub skills trigger by phrase, not argv).
> 2. Depth levels: responses can be eli5, eli14, or intern-level on request, and stay concise (target under ~2000 characters per exchange).
>
> Keep the body <=500 lines; if it approaches the limit, move the teaching-mode walkthrough detail into `references/teaching-mode.md` and link to it from the SKILL.md (Tier-3 pattern) rather than inflating the body. Follow `catalog/style-guides/markdown.md`.

---

#### 2.2 -- Add multiple-choice discipline

- [x] T005 Add the multiple-choice questioning discipline to catalog/skills/workflow/session-teach-back/SKILL.md

**Objective**: Implement insight I13 (vary the correct-answer position; do not reveal the answer until after the user responds).

**Prompt**:
> Edit `catalog/skills/workflow/session-teach-back/SKILL.md` to add the multiple-choice discipline from `docs/v3/v3.2/comparisons/v3.2.0-comparison-teach.md` Section 3 (insight I13): when a quiz question is posed as multiple choice, vary the position of the correct answer across questions (do not always make it "C"), and never reveal which option is correct until after the user has responded. This sits inside the existing solo-loop instructions next to the "ask one targeted question (open-ended or multiple choice)" step. Keep the edit small and follow `catalog/style-guides/markdown.md`.

---

#### 2.3 -- Add opt-in (off-by-default) checklist commit

- [x] T006 Add an opt-in checklist commit step to catalog/skills/workflow/session-teach-back/SKILL.md

**Objective**: Adopt `/teach`'s checklist-commit idea as adaptation N1 -- offer to commit the mastery checklist, but never push unprompted and never on by default.

**Prompt**:
> Edit `catalog/skills/workflow/session-teach-back/SKILL.md` to add an OPT-IN checklist commit step, implementing adaptation N1 from `docs/v3/v3.2/comparisons/v3.2.0-comparison-teach.md` Section 8. The upstream `/teach` skill auto-commits and pushes the checklist with `data(teaching): add <slug>` by default; do NOT replicate that default. Instead: after the teach-back session completes, the skill MAY OFFER to commit the local checklist (suggested conventional message, e.g. `data(teaching): add <slug> mastery checklist`) and only commits/pushes after explicit user confirmation. State plainly that this respects the `git-guardrails` hook and the global "destructive/outward-facing git requires confirmation" rule, and that the default behavior is to write the checklist locally and stop. Add a "Common Rationalizations" row capturing "I'll just auto-push the checklist to save a step" -> rebuttal. Follow `catalog/style-guides/markdown.md`.

---

#### 2.4 -- Testing and Stabilization

- [x] T007 Run and stabilize Phase 2 validators for catalog/skills/workflow/session-teach-back/SKILL.md

**Objective**: Confirm the enhanced skill body still validates and stays within the size norm.

**Prompt**:
> Validate Phase 2. Run `make validate` and confirm the skill-security scanner stays at 0 HIGH/CRITICAL on `catalog/skills/workflow/session-teach-back/SKILL.md`. Confirm the SKILL.md body is <=500 lines (if a `references/teaching-mode.md` was added, confirm it is referenced from the SKILL.md so the orphan-bundle audit stays clean). Re-run `make lint`. If `data/skills.json` needs its `size` field refreshed for the grown skill, update it. Fix any failure and re-run until green. Then run `/generate-session-history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] `make validate` exits 0; scanner 0 HIGH/CRITICAL
- [x] SKILL.md <=500 lines; any `references/` file is referenced (no orphan)
- [x] Auto-commit documented as off by default and confirmation-gated
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 3

---

## Phase 3: Integration + discoverability

**Goal**: Wire the new skill into the catalog's cross-link graph and changelog so it is discoverable and the release is documented.
**Prerequisites**: Phases 1-2.
**Stability Gate**: bidirectional cross-links resolve to real skill names; `make validate` exits 0; CHANGELOG has an `[Unreleased]` entry.

### Sub-tasks

#### 3.1 -- Add bidirectional Related-Skills cross-links

- [x] T008 [P] Add `[[session-teach-back]]` back-links to catalog/skills/workflow/session-query/SKILL.md, catalog/skills/workflow/session-history/SKILL.md, and catalog/skills/workflow/dev-progress-tracker/SKILL.md

**Objective**: Complete the bidirectional cross-link graph (insight P2) so the `session-*` family points at the new skill and vice versa.

**Prompt**:
> Add a `[[session-teach-back]]` entry to the "Related Skills" section of each of these three skills, each with a one-sentence description of the relationship:
>
> - `catalog/skills/workflow/session-query/SKILL.md` -- "queries past sessions; `session-teach-back` reuses that extractor to source the material it quizzes you on".
> - `catalog/skills/workflow/session-history/SKILL.md` -- "writes the session record; `session-teach-back` quizzes you on what the session produced".
> - `catalog/skills/workflow/dev-progress-tracker/SKILL.md` -- "tracks task progress; `session-teach-back` uses the same checkbox-file pattern to track mastery".
>
> The forward links (from `session-teach-back` to these three) were already added in Phase 1's Related Skills section -- this sub-task only adds the back-links. Follow `catalog/style-guides/markdown.md`. Do not touch any other section of these files.

---

#### 3.2 -- Add using-nexus-hub mention and CHANGELOG entry

- [x] T009 [P] Mention the skill in catalog/skills/workflow/using-nexus-hub/SKILL.md and add a CHANGELOG.md [Unreleased] entry

**Objective**: Surface the new skill in the orientation skill and record the change in the changelog.

**Prompt**:
> Two small edits:
>
> 1. `catalog/skills/workflow/using-nexus-hub/SKILL.md` -- add a one-line mention of `session-teach-back` wherever the orientation skill enumerates session-lifecycle or workflow skills, so a new session can discover it. Match the existing list style.
> 2. `CHANGELOG.md` -- add an entry under `## [Unreleased]` -> `### Added`: a one-line description of the new `session-teach-back` workflow skill (Socratic mastery-confirmation loop for the human operator; skill-native, zero new code/dependency/outbound; reuses `session-query` for sourcing; auto-commit opt-in per N1). ASCII-only, no em-dashes, straight quotes, per the commit-message/markdown conventions.
>
> Follow `catalog/style-guides/markdown.md`. Do not bump any version number -- that is `/update version`'s job at release time.

---

#### 3.3 -- Testing and Stabilization

- [x] T010 Run the final validators and confirm catalog green for catalog/skills/workflow/session-teach-back/SKILL.md

**Objective**: Final green check across the whole adoption before the plan is considered done.

**Prompt**:
> Final validation. Run `make validate` and `make lint`; confirm both exit 0 and the skill-security scanner reports 0 HIGH/CRITICAL across the catalog. Verify every `[[...]]` link added in Phase 3 resolves to a real skill `name`. Verify no new slash command was created (the capability is skill-only) and no `scripts/<name>.py` installer artifact was added (so no `installer.sh` / `installer.ps1` edit is required). If `make` is unavailable on the dev host, run the validators directly and record it as a known gap for CI to confirm. Record any residual gap in `docs/v3/v3.2/known-gaps.md`. Then run `/generate-session-history` to document Phase 3 and the completed adoption.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution file was found, so there are no MUST principles to violate. This table is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | -- | -- |

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] `make validate` and `make lint` exit 0; scanner 0 HIGH/CRITICAL catalog-wide (validators run directly; `make`/`shellcheck` unavailable on host -- WN-v32-2, covered by CI; no shell surface so `make lint` is a no-op)
- [x] All `[[session-teach-back]]` cross-links resolve bidirectionally
- [x] No new slash command; no installer edit required
- [x] CHANGELOG `[Unreleased]` entry present
- [x] Session history generated; adoption complete
