# Plan -- Loop Engineering Adoption (skill-native loop library + connective layer)

**Project**: Nexus-Hub
**Version**: v3.3.0
**Slug**: adoption-loop-engineering
**Plan Type**: Feature / Enhancement (catalog content; additive)
**Created**: 2026-06-09
**Source**: [docs/releases/v3/v3.2/comparisons/v3.2.0-comparison-loop-engineering.md](../../v3.2/comparisons/v3.2.0-comparison-loop-engineering.md) (Section 7 Adoption Plan)
**Goal**: Ship a skill-native loop-engineering layer -- a loop-definition schema, a seeded local loop library, the five-pieces-to-primitive mapping, goal-based-stop guidance, a scheduled-triage recipe, and named loop anti-patterns -- so operators can compose Nexus-Hub's existing primitives into named, goal-terminated loops, with zero new outbound call, dependency, or credential.

## Goals-First (target problem, persona, definition of done)

- **Target problem**: Nexus-Hub already owns every loop-engineering primitive (worktrees, skills, sub-agents, plugins/connectors, an external-memory layer) and has deliberately delegated the loop *driver* (`/loop`, `/goal`) to the host harness. What it lacks is the *connective layer and the registry*: nothing composes those primitives into the named, goal-terminated, continuous loops the practice is built from, and -- unlike skills, commands, agents, and hooks -- there is no loop registry. Operators re-derive loop structure ad hoc.
- **Persona**: Nexus-Hub catalog consumers -- AI coding agents and their operators -- running iterative agentic workflows across Claude Code / Codex / Cursor and the other installer-targeted platforms.
- **Definition of done (observable)**: a new `loop-engineering` workflow skill exists and is registered in all three catalog registries; it ships a loop-definition schema, a seeded loop library (`references/loop-library.md`), the five-pieces mapping, a goal-based-stop + independent-evaluator section, a scheduled-triage recipe, and named loop anti-patterns; `agent-orchestration-primitives` and `verification-before-completion` are enriched and bidirectionally cross-linked; `make validate` (bundles + quality), the orphan-bundle audit, and the `nexus-skill-scanner` gate all pass; a `## [Unreleased]` CHANGELOG entry is added; and a demonstration shows an operator assembling one library loop end-to-end. Zero new outbound call, dependency, credential, or third-party processor is introduced (verified against the MCP Registry Policy).

## Overview

This plan operationalizes the Section 7 adoption plan of the loop-engineering comparison report. The report's central finding is that the work is overwhelmingly *connective*, not *net-new*: Addy Osmani's five pieces and the loops-gallery archetypes map onto primitives Nexus-Hub already ships, so the build is catalog content (Markdown) that composes owned parts and is executed by the host's `/loop` + `/goal`. The single net-new artifact type is a **loop registry** -- a catalog of named loop *definitions*, each declaring a goal, an iteration cap, a between-runs check command, an exit condition, a maturity flag, and a graceful-degradation note.

Every adoption candidate is `skill-native` (the cheapest reverse-engineering bucket): there are no `re-partial`, `vendor-intrinsic`, or outbound-call items, so the reverse-engineer-first ordering collapses to plain value/effort sequencing within one bucket. The gallery's hosted form (install counts, a remote website) is reverse-engineered into the local pattern only and never adopted as a service dependency; per the Reverse-Engineering Attribution Rule, the shipped artifact uses the generic name "loop library" and does not name the external gallery.

The plan is four phases: Phase 1 establishes the foundation (the skill, the schema, the seeded library, and registry registration -- everything else references it); Phase 2 makes loops safe to terminate (goal-based stop + independent evaluator); Phase 3 rounds out the framework (scheduled-triage recipe + named anti-patterns); Phase 4 is catalog integration, validation, and release readiness. The plan deliberately does **not** ship a Dynamic-Workflow `.js` template for loops: Dynamic Workflows are one-shot fan-outs, whereas a loop is continuous and host-driven, so the loop library references `/loop` + `/goal`, not the workflow runtime.

## Constitution Check

*GATE: Must pass before Phase 1 research. Re-check after Phase 1 design.*

No constitution file found at `docs/v3/v3.3/constitution.md` (only the template at `catalog/templates/constitution-template.md` and the `/constitution` command exist) - skipping check. Recommend running `/constitution` to establish project principles. This is informational, not blocking.

For grounding, the plan was checked against the project's *de facto* governing rules in `AGENTS.md` and `CLAUDE.md`, all of which it satisfies:

- **Reverse-engineer-first / MCP Registry Policy**: every item is `skill-native`; no outbound call, dependency, or credential. PASS.
- **Reverse-Engineering Attribution Rule**: shipped artifact uses generic naming, no gallery attribution. PASS.
- **Skill registration rule**: the new skill is registered in `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` (Phase 1 / Phase 4). PASS.
- **Pushy-description mandate**: the new skill carries a pushy, SKIP-claused description; the known `validate_skills.py` default-mode length conflict (WN-v32-1) is handled via the allowlist in Phase 4, not by shortening. PASS.
- **No static command list / no new command**: this plan ships skills and skill enrichments only; no `/loop` or `/goal` command (rejected by prior decision). PASS.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Foundation: loop-engineering skill + schema + seeded library | New skill with a loop-definition schema and a seeded local loop library, registered in all three registries |
| 2 | Goal-based stopping + independent-evaluator pattern | `agent-orchestration-primitives` and `verification-before-completion` teach falsifiable, checker-evaluated exit conditions |
| 3 | Scheduled-triage recipe + named loop anti-patterns | The article's full triage-to-ship loop expressed with owned primitives; cognitive-surrender / comprehension-debt named with mitigations |
| 4 | Catalog integration, validation, and release readiness | Registries consistent, allowlist updated, validate / scan / orphan-bundle audit green, CHANGELOG entry added |

---

## Phase 1: Foundation -- loop-engineering skill + schema + seeded library

**Goal**: Create the `loop-engineering` workflow skill carrying a loop-definition schema and a seeded local loop library, and register it in all three catalog registries.
**Prerequisites**: None.
**Stability Gate**: The skill body, its `references/loop-library.md`, and its `references/loop-schema.md` exist and conform to the SKILL.md size norm and three-tier model; every bundled file is referenced from SKILL.md (orphan-bundle audit clean); the skill is present in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` with the machine-readable counts mutually consistent; `make validate` (bundles + quality) passes (allowlist handling deferred to Phase 4 if the default-mode length warning blocks local review).

### Sub-tasks

#### 1.1 -- Author the loop-engineering skill body

**Objective**: Write `catalog/skills/workflow/loop-engineering/SKILL.md` -- the connective-layer skill that names Addy Osmani's five pieces plus the memory layer and maps each to the Nexus-Hub primitive that already provides it, then teaches how to assemble a named, goal-terminated loop from owned parts.

**Prompt**:
> Create `catalog/skills/workflow/loop-engineering/SKILL.md` following the Nexus-Hub SKILL.md contract in `AGENTS.md` (required frontmatter: `name`, `description`, `summary_l0`, `overview_l1`; required body sections in order: title + intro, When to Use This Skill with explicit "When NOT to use", Instructions, Common Rationalizations table, Verification binary checklist, Related Skills). Requirements:
> - `name: loop-engineering`; `summary_l0` <= 15 words; `overview_l1` <= 150 words.
> - `description`: pushy and SKIP-claused per the AGENTS.md "combat undertriggering" rule. Lead with the action, list verbatim trigger phrases ("run this in a loop", "loop until tests pass", "set up an agentic loop", "iterate until green", "build a loop that ships PRs", "what loop should I use"), then a SKIP clause fencing off look-alikes ("SKIP: a one-shot task with no iteration; choosing between single-agent / subagents / workflows -- use agent-orchestration-primitives; the host /loop or /goal command mechanics themselves").
> - Body: (a) name the five pieces (automations, worktrees, skills, plugins/connectors, sub-agents) + the external-memory layer, each mapped to the owning Nexus-Hub primitive with a file-path citation (`using-git-worktrees`, the 250-skill catalog, `catalog/agents/` + `adversarial-verifier` + `agent-orchestration-primitives`, `mcp-builder` + the MCP registry, `dev-progress-tracker` / `known-gaps-tracker` / `filesystem-context-patterns`); (b) state explicitly that the loop *driver* (`/loop`, `/goal`) is a host-platform command this skill references and never reimplements (cite `agent-orchestration-primitives` Step 8 and the CHANGELOG v3.1.0 decision); (c) an "Assemble a loop" procedure that points at the loop-definition schema (sub-task 1.2) and the seeded library (sub-task 1.3); (d) the orchestration-tax / human-review-bandwidth caution, cross-linking `agent-orchestration-primitives` and `ai-billing-safeguards`.
> - Keep the body <= 500 lines (size norm); push the schema and the library to `references/` files (sub-tasks 1.2, 1.3) and link to them rather than inlining.
> - Common Rationalizations must cite concrete failure modes (e.g. "I'll just loop without an exit condition" -> unbounded token burn; "the maker can grade its own exit" -> failure-mode 2 from agent-orchestration-primitives). Verification items must be binary and observable.
> - Related Skills: bidirectional cross-links to `agent-orchestration-primitives`, `using-git-worktrees`, `adversarial-verifier`, `verification-before-completion`, `dev-progress-tracker`, `known-gaps-tracker`, `ai-billing-safeguards`.
> Do not name the external loops gallery anywhere in the file (Reverse-Engineering Attribution Rule). Acceptance: the file exists, frontmatter is YAML-parseable, all four required body sections are present and ordered, and every primitive claim cites a real catalog path.

---

#### 1.2 -- Define the loop-definition schema

**Objective**: Write `catalog/skills/workflow/loop-engineering/references/loop-schema.md` -- the reusable, declarable structure every loop definition follows, reverse-engineered from the gallery's canonical shape.

**Prompt**:
> Create `catalog/skills/workflow/loop-engineering/references/loop-schema.md`. It defines the fields every loop definition in the library must declare, as a self-contained reference the agent can read cold:
> - `name` -- kebab-case identifier.
> - `goal` -- the falsifiable end state in one sentence.
> - `iteration_cap` -- a hard maximum number of iterations (the unbounded-loop guard).
> - `check_command` -- the exact shell command run between iterations to measure progress (e.g. `npm test`, `gh pr checks`, `make validate`).
> - `exit_condition` -- the observable, command-derived condition that ends the loop (e.g. "check_command exits 0", "coverage >= threshold and tests pass", "no unchecked items remain in spec.md"). Must be evaluated by a checker, not asserted by the maker (cross-link Phase 2).
> - `driver` -- which host command runs it (`/loop` for interval/continuous, `/goal` for a hard completion requirement), with the graceful-degradation note (fall back to manual re-invocation when the host lacks the command).
> - `maturity` -- `experimental` | `hardened` (the local, service-free analog of the gallery's hardened flag; no install counts).
> - `agents` -- which platforms the loop is known to run on.
> - `tags` -- discovery tags.
> Include one fully worked example and a short "anti-patterns" note (no `iteration_cap` -> unbounded burn; a vibe-based `exit_condition` instead of a command; the maker self-certifying the exit). Reference this file from SKILL.md (sub-task 1.1) so it is not an orphan bundle. Acceptance: the schema file exists, every field is documented with a purpose and an example, and SKILL.md links to it.

---

#### 1.3 -- Seed the loop library

**Objective**: Write `catalog/skills/workflow/loop-engineering/references/loop-library.md` -- the registry of named loop definitions, seeded with the archetypes that have no current packaged Nexus-Hub equivalent plus mapped examples that point at existing surfaces.

**Prompt**:
> Create `catalog/skills/workflow/loop-engineering/references/loop-library.md` as a catalog of loop definitions, each conforming to `references/loop-schema.md` (sub-task 1.2). Seed it with:
> - Three archetypes that have no current packaged Nexus-Hub equivalent, authored in full: **ship-pr-until-green** (`check_command: gh pr checks`, exit: all checks pass, cap 10, driver `/loop`), **build-until-green** (`check_command: <project build>`, exit: build exits 0, cap 10), **e2e-until-green** (`check_command: <project e2e>`, exit: suite exits 0, cap 10). Use placeholders for project-specific commands and say so.
> - Two "mapped example" definitions that explicitly point at existing Nexus-Hub surfaces rather than duplicating them: **coverage-until-threshold** (note: prefer the `/test` command, which already runs this loop -- `catalog/commands/test.md`), and **pr-self-review** (note: prefer `/review changes` + `multi-agent-code-review`). These show operators when a loop is already a first-class command.
> - A short header explaining the library is local and service-free (no install counts, no remote fetch), how to add a new loop, and the maturity convention.
> Mark the three archetypes `experimental` (they ship unproven) and the two mapped examples as pointers. Do not name the external gallery. Reference this file from SKILL.md. Acceptance: the library file exists, every entry conforms to the schema, the three archetypes are complete, the two mapped examples cite the existing command/skill they defer to, and SKILL.md links to it.

---

#### 1.4 -- Register the skill in all three catalog registries

**Objective**: Make the new skill discoverable by registering it per the AGENTS.md skill-registration rule.

**Prompt**:
> Register `loop-engineering` in the three catalog registries exactly as `AGENTS.md` "Register the skill" prescribes:
> - `data/SKILL_INDEX.md`: add one table row `| loop-engineering | Workflow | "<summary_l0>" | catalog/skills/workflow/loop-engineering/SKILL.md |`.
> - `data/skills.json`: add one entry to the `skills` array following the existing schema (name, title, description, long_description, summary_l0, overview_l1, version, author, category=workflow, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security with the default 100/100/95 scores).
> - `data/marketplace.json`: increment the Workflow category `skill_count` and the `statistics.total_skills`.
> Update the machine-readable counts so `skills.json` and `marketplace.json` agree on the new total. Do NOT hand-reconcile headline-total prose surfaces (README, AGENTS.md, plugin description, the SKILL_INDEX Total label) -- per prior-version item WN-v32-3, that reconciliation is the develop->main release bump's job via `/update version`. Run `make validate` (or invoke `scripts/validate_skills.py --bundles-only` and `--quality` directly if `make` is unavailable on the host) and confirm JSON integrity. Acceptance: all three registries list the skill, the machine-readable totals match, and `make validate` (bundles + quality) passes.

---

#### 1.5 -- Testing and Stabilization

**Objective**: Generate and run all checks for Phase 1. Iterate until the phase is stable before advancing to Phase 2.

**Prompt**:
> Verify everything built in Phase 1: (1) frontmatter of `loop-engineering/SKILL.md` is YAML-parseable and carries all four required Tier-1 fields; (2) all four required body sections are present and ordered; (3) `references/loop-schema.md` and `references/loop-library.md` exist, conform, and are both referenced from SKILL.md (run the orphan-bundle audit: `scripts/validate_skills.py` bundle check, or confirm each bundled file's basename appears in SKILL.md); (4) the three registries are consistent and `make validate` bundles + quality pass; (5) no body exceeds the 500-line size norm. Fix any failure and re-check. Note explicitly if the bare-default `validate_skills.py` reports a description-length warning -- that is the known WN-v32-1 pushy-description conflict, resolved by the allowlist in Phase 4, not by shortening the description here. After all checks pass, run `/session history` to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] `loop-engineering/SKILL.md` + `references/loop-schema.md` + `references/loop-library.md` exist and conform
- [x] Orphan-bundle audit clean (every bundled file referenced from SKILL.md)
- [x] Skill registered in all three registries; machine-readable totals consistent
- [x] `make validate` (bundles + quality) passes
- [x] No known regressions
- [x] Session history generated for Phase 1
- [x] Ready to advance to Phase 2

---

## Phase 2: Goal-based stopping + independent-evaluator pattern

**Goal**: Teach, as reusable methodology, that a loop's exit condition must be a falsifiable command evaluated by a checker that did not produce the work -- enriching the two skills that own verification and orchestration rather than adding a new skill.
**Prerequisites**: Phase 1 (the loop schema references this pattern).
**Stability Gate**: `agent-orchestration-primitives` and `verification-before-completion` each carry an explicit goal-based-stop + independent-evaluator section, are bidirectionally cross-linked with `loop-engineering`, and still pass `make validate`; no new skill was created (catalog count unchanged by this phase).

### Sub-tasks

#### 2.1 -- Enrich agent-orchestration-primitives with goal-based stopping

**Objective**: Extend the skill's existing Step 8 (which already names `/loop` and `/goal`) with the independent-evaluator rule for loop termination.

**Prompt**:
> Edit `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md`. In or adjacent to Step 8 ("Pair workflows with the platform's continuous-operation commands"), add a focused subsection on goal-based stopping for loops: (1) a loop's exit condition must be a falsifiable command (the schema's `check_command` + `exit_condition`), not a subjective judgement; (2) the exit must be evaluated by a checker that did not produce the work -- reuse the existing failure-mode-2 framing ("verifiers declare victory without verifying") and point at `adversarial-verifier`; (3) cross-link the new `loop-engineering` skill as the home for assembling such loops. Keep the addition tight (the skill is already near its size budget); push nothing to a new file. Do not duplicate the loop schema -- reference it. Acceptance: the subsection exists, cites the independent-evaluator rule, and cross-links `loop-engineering` and `adversarial-verifier`.

---

#### 2.2 -- Enrich verification-before-completion with loop-exit evidence

**Objective**: Connect the "fresh evidence before any completion claim" rule to loop exit conditions.

**Prompt**:
> Edit `catalog/skills/workflow/verification-before-completion/SKILL.md` to state that a loop's exit condition is a completion claim and therefore requires the same fresh, observable evidence the skill already mandates (the `check_command` output, not the agent's reassurance). Add a one-line cross-link to `loop-engineering` (loop assembly) and `agent-orchestration-primitives` (the independent-evaluator rule). Keep the edit minimal and within the size norm. Acceptance: the skill explicitly treats a loop exit as a completion claim requiring evidence, and cross-links both skills.

---

#### 2.3 -- Backlink from loop-engineering

**Objective**: Make the cross-links bidirectional.

**Prompt**:
> In `catalog/skills/workflow/loop-engineering/SKILL.md`, ensure the Related Skills section and the schema's `exit_condition` discussion link to `agent-orchestration-primitives` (goal-based stop + independent evaluator) and `verification-before-completion` (exit = completion claim requiring evidence). Confirm the links resolve to real skill names. Acceptance: bidirectional cross-links exist between all three skills.

---

#### 2.4 -- Testing and Stabilization

**Objective**: Generate and run all checks for Phase 2. Iterate until stable.

**Prompt**:
> Verify: (1) both enriched skills still have valid frontmatter and pass `make validate` bundles + quality; (2) neither edit pushed a body past the 800-line hard cap; (3) all cross-links between `loop-engineering`, `agent-orchestration-primitives`, and `verification-before-completion` are bidirectional and name real skills; (4) no new skill was created, so `data/skills.json` count is unchanged from Phase 1. Fix and re-check. After all checks pass, run `/session history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] Goal-based-stop + independent-evaluator section present in `agent-orchestration-primitives`
- [x] `verification-before-completion` treats a loop exit as an evidence-bearing completion claim
- [x] Bidirectional cross-links among the three skills
- [x] `make validate` passes; catalog count unchanged by this phase
- [x] Session history generated for Phase 2
- [x] Ready to advance to Phase 3

---

## Phase 3: Scheduled-triage recipe + named loop anti-patterns

**Goal**: Express the article's full automation-to-ship loop with owned primitives, and name the loop's human-cost anti-patterns with mitigations.
**Prerequisites**: Phase 1 (the recipe lives in the loop-engineering skill); Phase 2 (the recipe's fix-loop uses goal-based stopping).
**Stability Gate**: `loop-engineering` carries a scheduled-triage recipe section composing host `/loop` + `/schedule` with the owned memory-layer primitives; `verification-before-completion` (or the loop-engineering skill) names "cognitive surrender" and "comprehension debt" as risks with mitigations cross-linking `session-teach-back`; `make validate` passes.

### Sub-tasks

#### 3.1 -- Add the scheduled-triage recipe

**Objective**: Document the article's A8 loop (automation -> triage -> state file -> worktree per finding -> maker + checker sub-agents -> connectors -> human inbox) using only owned primitives.

**Prompt**:
> Add a "Scheduled-triage recipe" section to `catalog/skills/workflow/loop-engineering/SKILL.md` (or a `references/scheduled-triage-recipe.md` if the body would exceed the 500-line norm -- if you create the reference file, link it from SKILL.md so it is not an orphan). The recipe composes only owned/host primitives: host `/loop` (interval) or `/schedule` for the cadence; a triage step that reads CI failures / open issues / recent commits; writing findings to the memory layer (`docs/todos.md` via `dev-progress-tracker`, or `known-gaps`); spawning an isolated `git worktree` per viable finding (`using-git-worktrees`); a maker sub-agent drafting the fix and an independent checker sub-agent reviewing it (`adversarial-verifier`, Phase 2 exit rule); host connectors (MCP) opening the PR / updating the ticket; and routing unhandleable items to a human inbox. State the scope-first token caution and cross-link `ai-billing-safeguards`. Make clear this is a recipe to adapt, not a runnable script, and that it introduces no new outbound call or dependency. Acceptance: the recipe section exists, every step names the owned primitive it uses with a citation, and it carries the token caution.

---

#### 3.2 -- Name the loop anti-patterns

**Objective**: Capture cognitive surrender and comprehension debt as named risks with concrete mitigations.

**Prompt**:
> In `catalog/skills/workflow/verification-before-completion/SKILL.md` (the natural home, since these are verification-adjacent risks), add a short "Loop anti-patterns" note naming: (1) **cognitive surrender** -- the operator stops forming opinions on loop output because automation is comfortable; mitigation: keep verification a human responsibility, cross-link the independent-evaluator rule; (2) **comprehension debt** -- the gap between shipped code and operator understanding widens each cycle; mitigation: cross-link `session-teach-back` (the Socratic mastery-confirmation loop already in the catalog) as the explicit countermeasure. Add a reciprocal cross-link from `loop-engineering`'s "When NOT to use" / risks discussion. Keep edits within the size norm. Acceptance: both anti-patterns are named with mitigations, and `session-teach-back` is cross-linked as the comprehension-debt countermeasure.

---

#### 3.3 -- Testing and Stabilization

**Objective**: Generate and run all checks for Phase 3. Iterate until stable.

**Prompt**:
> Verify: (1) the scheduled-triage recipe cites an owned/host primitive for every step and introduces no outbound call/dependency (re-confirm against the MCP Registry Policy); (2) if a `references/scheduled-triage-recipe.md` was created, it is referenced from SKILL.md (orphan-bundle audit clean); (3) the two anti-patterns are named with mitigations and `session-teach-back` is cross-linked; (4) `make validate` bundles + quality pass; (5) no body exceeds the size norm. Fix and re-check. After all checks pass, run `/session history` to document Phase 3.

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] Scheduled-triage recipe present, every step citing an owned primitive, with the token caution
- [x] Cognitive-surrender and comprehension-debt named with mitigations; `session-teach-back` cross-linked
- [x] Orphan-bundle audit clean (recipe added inline; no new reference file)
- [x] `make validate` passes; no new outbound call/dependency introduced
- [x] Session history generated for Phase 3
- [x] Ready to advance to Phase 4

---

## Phase 4: Catalog integration, validation, and release readiness

**Goal**: Bring the new skill fully into the catalog's quality and security gates, handle the known pushy-description warning, and stage the changelog -- leaving release-time count reconciliation and the version tag to `/update version`.
**Prerequisites**: Phases 1-3.
**Stability Gate**: `make validate`, `make lint` (if any shell surface was added -- none expected), the orphan-bundle audit, and the `nexus-skill-scanner` gate all pass for the new skill; the new skill is in `scripts/validate_skills.allowlist.json` so its pushy description does not error in default mode; a `## [Unreleased]` CHANGELOG entry describes the loop-engineering layer; an end-to-end demonstration assembles one library loop.

### Sub-tasks

#### 4.1 -- Handle the pushy-description allowlist (WN-v32-1)

**Objective**: Prevent the known default-mode description-length error from regressing CI ergonomics, without shortening the mandated pushy description.

**Prompt**:
> Add `catalog/skills/workflow/loop-engineering/SKILL.md` to `scripts/validate_skills.allowlist.json`, mirroring the existing entries for `session-teach-back`, `session-query`, `skill-security-scan`, and `agent-orchestration-primitives` (all pushy-description skills). Confirm that `make validate` (which runs `validate_skills.py --bundles-only` and `--quality`) is green and that the strict `--allow-existing` path demotes the >250-char description to a warning for this file. Do NOT shorten the description -- the length is intentional per the AGENTS.md pushy-description mandate and the Phase 1 / T1.1 requirement. Reference prior-version item WN-v32-1. Acceptance: the skill is in the allowlist, `make validate` is green, and the description is unchanged.

---

#### 4.2 -- Run the skill-security scan

**Objective**: Confirm the new skill clears the `nexus-skill-scanner` gate.

**Prompt**:
> Run the `nexus-skill-scanner` (`make scan`, or invoke the scanner directly if `make` is unavailable) against `catalog/skills/workflow/loop-engineering/`. The skill is pure Markdown with no bundled scripts, so it must score LOW with zero HIGH/CRITICAL findings. Because the recipe text mentions shell `check_command`s (e.g. `gh pr checks`, `npm test`), confirm these are documentation examples in fenced blocks, not executable payloads, and that they do not trip a false positive. If any finding appears, adjudicate it with the `skill-security-scan` skill. Acceptance: the scanner reports no HIGH/CRITICAL findings for the new skill.

---

#### 4.3 -- Cross-link and consistency audit

**Objective**: Confirm the loop-engineering family is coherently linked and the registries are consistent.

**Prompt**:
> Audit cross-links and consistency: (1) every `[[skill-name]]` link added in Phases 1-3 resolves to a real catalog skill; (2) cross-links are bidirectional among `loop-engineering`, `agent-orchestration-primitives`, `verification-before-completion`, and `session-teach-back`; (3) `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` agree on the post-Phase-1 skill total; (4) the new skill's `references/` files are all referenced (final orphan-bundle audit). Fix any dangling link or count drift in the machine-readable registries only. Acceptance: no dangling cross-links, bidirectional family links, machine-readable totals consistent, orphan-bundle audit clean.

---

#### 4.4 -- Stage the CHANGELOG entry

**Objective**: Record the work under `## [Unreleased]` for the eventual release bump.

**Prompt**:
> Add an entry under `## [Unreleased]` -> `### Added` in `CHANGELOG.md` describing the loop-engineering layer: the new `loop-engineering` workflow skill (loop-definition schema + seeded local loop library + five-pieces-to-primitive mapping + scheduled-triage recipe), the goal-based-stop / independent-evaluator enrichments to `agent-orchestration-primitives` and `verification-before-completion`, and the named loop anti-patterns cross-linking `session-teach-back`. State that it is skill-native (zero new outbound call, dependency, credential, or third-party processor), that the loop driver remains the host `/loop` + `/goal` (no catalog command added), and that the gallery pattern was reverse-engineered into a local registry per the Reverse-Engineering Attribution Rule. Follow the Markdown style guide (ASCII-only, blank lines around lists). Do NOT bump the version number or reconcile headline counts here -- that is the develop->main release bump's job via `/update version` (per WN-v32-3). Acceptance: a single accurate `[Unreleased] / Added` entry exists, version unbumped.

---

#### 4.5 -- End-to-end demonstration and stabilization

**Objective**: Prove an operator can assemble and run one library loop, and run the full Phase 4 gate.

**Prompt**:
> Demonstrate the deliverable end-to-end: pick one seeded loop (e.g. ship-pr-until-green), and walk through assembling it from the schema + library + host `/loop`, showing the goal, iteration cap, check command, and checker-evaluated exit condition (do not actually open PRs -- the demonstration is the assembled, runnable loop definition with its real check command for this repo, e.g. `make validate` as the check). Then run the full Phase 4 gate: `make validate` (bundles + quality), `make scan`, the orphan-bundle audit, and `make lint` only if a shell surface was added (none expected). Confirm all green. If `make` is unavailable on the host, invoke each validator and the scanner directly and note that local verification was partial (WN-style), to be confirmed on CI. After all checks pass, run `/session history` to document Phase 4, then report release readiness: this plan's scope is a MINOR bump to v3.3.0, applied at the develop->main release via `/update version` (which also reconciles all headline count-prose surfaces).

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | - | All Constitution Check items PASS or N/A; every item is skill-native with no new dependency, outbound call, or command. |

---

### Phase 4 Exit Checklist

- [x] All sub-tasks completed
- [x] New skill in `scripts/validate_skills.allowlist.json`; description unchanged; `make validate` green
- [x] `nexus-skill-scanner` reports no HIGH/CRITICAL findings for the new skill
- [x] All cross-links resolve and are bidirectional; machine-readable registry totals consistent
- [x] `## [Unreleased]` CHANGELOG entry added; version NOT bumped (release-bump's job)
- [x] End-to-end demonstration assembles one library loop with a checker-evaluated exit
- [x] Orphan-bundle audit clean; `make lint` run only if a shell surface was added (none expected)
- [x] Session history generated for Phase 4
- [x] Plan complete; ready for develop->main release via `/update version` (MINOR -> v3.3.0)
