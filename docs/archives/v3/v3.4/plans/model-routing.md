# Plan - Platform-agnostic model routing

**Project**: Nexus-Hub
**Version**: v3.4.0
**Slug**: model-routing
**Plan Type**: Feature / Enhancement
**Created**: 2026-06-14
**Goal**: Ship a platform-agnostic model-routing capability - a `model-routing` skill and a `/route` command that detect the current agentic platform, dynamically enumerate its available models, assess a task's complexity, and recommend (then, with confirmation, apply) the cheapest model and reasoning effort that carries the work with zero quality loss - then wire that routing into the `/plan` and `/implement` loop so every plan phase runs on the right model automatically.

## Overview

This plan adds model routing to the Nexus-Hub loop. The premise is that most implementation work does not need the strongest model: a router that downshifts the easy majority of tasks to cheaper tiers - while never downshifting the hard minority - makes every session cheaper and faster with no degradation in output quality, and to the user it looks like the best model was used for everything. The capability ships in two halves. The standalone half (Phases 1-2) is a `model-routing` skill plus a `/route` command that a user invokes directly (`/route phase 1 of plan.md`, `/route "<task>"`): it detects the platform, enumerates models, scores the task, and emits a data-driven recommendation with reasoning and best-effort citations, then applies the chosen switch posture. The loop half (Phases 3-4) folds routing into `/plan` (assess each phase at planning time and annotate the plan with a recommended model and effort per phase) and `/implement` (re-confirm that recommendation at the start of each phase, since a stronger or cheaper model may have shipped between planning and implementation, then apply it).

Three design invariants hold across every phase and are non-negotiable. First, **no hardcoded model lists**: the router never assumes a fixed catalog (those go stale within weeks). It detects the platform, then enumerates live from that platform's own surface - `codex debug models` (JSON), `agy models`, the Anthropic `GET /v1/models` endpoint or the `/model` picker on Claude Code, the alias set on Gemini CLI - and caches the result for the session. Second, **the conservative quality guarantee**: the complexity rubric defaults to the strongest available tier whenever the assessment is uncertain or scores the task as high-complexity, high-context, or high-risk; routing only downshifts on a high-confidence reading that the task is genuinely simple. Routing saves money on the easy 70 percent and never gambles on the hard 30 percent. Third, **platform-agnostic by a capability abstraction, not a per-model special case**: each platform is described by a small routing profile (can-script-switch, enumerate command, switch command or keystroke, effort-knob shape, model-list source), mirroring the existing `scripts/lib/integrations/` registry pattern, so adding a platform is adding a profile, not rewriting the router.

The switch posture is **confirm, then auto-execute** (the user's chosen default). The router presents its recommendation with reasoning, asks the user to approve, and then acts according to what the platform mechanically allows, which research showed is a three-tier spectrum rather than uniform automation:

| Tier | Platforms | What the router does after approval |
|---|---|---|
| Scriptable | Codex CLI, Antigravity `agy`, Gemini CLI | Execute the switch directly (a `-c`/`-m`/`--profile` invocation, an `agy -m` flag, a config write) via a bundled `.sh`/`.ps1` helper |
| One user action | Claude Code | The main loop cannot switch its own model mid-session; the router emits the exact one-key `/model` and `/effort` instruction AND auto-routes any delegated subagent work to the chosen tier via the Task / Workflow `model` parameter (the built-in `opusplan` alias is native routing of this shape) |
| Manual only | Cursor, Copilot, OpenCode | No flag, env, config, or rule field pins a model; the router emits a recommendation plus a "select X in the model picker" instruction |

Delivery follows the AGENTS.md installer-aware contract. The skill is auto-distributed (a new skill folder is copied recursively by both installers) but must be registered in the three catalog registries; any bundled `.sh` helper needs a `.ps1` sibling and must be referenced from SKILL.md (orphan-bundle audit). The `/route` command is auto-copied and needs only a `total_commands` bump; its slash surface lands on Claude / Codex / Gemini / Cursor / Copilot per the v3.3.4 channels, body-only on OpenCode. The `/plan` and `/implement` integrations edit the command files and their retained skills (`generate-plan` / `implementation-plan`, `implement-phase`); the routing guidance written there MUST be platform-agnostic. This is explicitly **not** a `base-*.md` lockstep template change - routing is opt-in via `/route` and the plan/implement steps, not always-loaded instruction text.

This feature is policy-clean against the MCP Registry Policy: it introduces zero new outbound calls, dependencies, credentials, or third-party processors. Every enumeration and switch surface it uses belongs to the platform the user is already running (the agent's own CLI, the user's own Anthropic key or session). The optional `GET /v1/models` call is local-first and best-effort - it uses a key only if one is already present, and falls back to the `/model` picker otherwise. Best-effort citations (model docs, pricing pages) are fetched only when the harness already has web access; the router never hard-depends on the network.

## Constitution Check

*GATE: Must pass before Phase 1 work. Re-check after Phase 1 design.*

No constitution file found at `docs/v3/v3.4/constitution.md` - skipping check. Recommend running `/constitution` to establish project principles. This is informational, not blocking. As a proxy, this plan was checked against the AGENTS.md governing rules it must satisfy (MCP Registry Policy reverse-engineer-first and the Hard-No list, installer-aware distribution, three-registry skill registration, `.ps1` cross-platform parity, ASCII-only Markdown, pushy-description + binary-Verification authoring, the no-hardcoded-list lesson drawn from `multi-provider-ai`'s static matrix): all PASS - no rule is violated, since the feature is local, zero-outbound, and detection-driven rather than list-driven.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Routing skill foundation (skill-native) | A `model-routing` skill encoding platform detection, the per-platform routing-profile abstraction, the complexity-to-tier rubric, and the conservative strong-tier-default guarantee; registered in all 3 registries; validated and security-scanned |
| 2 | The `/route` command + switch helpers (skill-native) | A thin `/route` command that resolves a target (plan phase, free-text task, or current task), runs the assessment, and applies the confirm-then-auto-execute posture via bundled `.sh`/`.ps1` switch helpers; dry-run-verified per platform tier |
| 3 | `/plan` integration (planning-time routing) | `/plan` assesses every phase and annotates the plan (a recommended model + effort column in "Phases at a Glance" plus a per-phase field); platform-agnostic, graceful when routing is unavailable |
| 4 | `/implement` integration (per-phase re-confirmation) | `/implement` re-runs the assessment at the start of each phase, confirms or overrides the plan's recommendation, and applies the switch posture before the build step |

---

## Phase 1: Routing skill foundation (skill-native)

**Goal**: Add the `model-routing` skill - the brain of the feature - encoding how to detect the platform, enumerate its models dynamically, score a task, map the score to a model + effort with a conservative strong-tier default, and describe each platform's switch mechanics.
**Prerequisites**: None.
**Stability Gate**: `catalog/skills/ai-development/model-routing/SKILL.md` exists with valid YAML frontmatter; it is registered in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`; `make validate` passes (JSON integrity + orphan-bundle audit clean); 0 dangling wikilinks; and the skill-security scan returns an install-OK verdict.

### Sub-tasks

#### 1.1 - Design the routing model and platform-capability abstraction

**Objective**: Pin the skill's scope, the complexity rubric, and the platform routing-profile shape before writing prose, reusing what the catalog already has instead of duplicating it.

**Prompt**:
> In the Nexus-Hub repo, design (do not yet implement) a new `ai-development` skill named `model-routing`. Read these first to fix the boundary and reuse existing assets: `catalog/skills/ai-development/multi-provider-ai/SKILL.md` (has `Provider` / `ModelTier` enums and a model-ID matrix - note that its matrix is HARDCODED and the new skill must instead detect dynamically, but reuse the tier abstraction), `catalog/skills/ai-development/prompt-engineering/SKILL.md` (already has a task-complexity-to-tier routing table and a `select-model` pattern around its "Model routing" section - the new skill extends and operationalizes this, it does not re-invent it), `catalog/skills/ai-development/ai-billing-safeguards/SKILL.md` (budget caps the router must respect), and the `check-usage` skill behind `catalog/commands/usage.md` (consumption-time recommendations - `model-routing` is the planning/task-time counterpart, so cross-reference, do not collide). Produce a short design note covering: (1) a one-paragraph scope statement (what it does: detect platform, enumerate models live, score a task, recommend model+effort with citations, describe how to switch; what it explicitly does NOT do: it does not itself switch the Claude Code main loop, it does not maintain a hardcoded model list, it does not duplicate `check-usage`'s consumption reporting); (2) the complexity rubric - the input signals (task scope, structural complexity, context volume required, risk/blast-radius, whether it is mechanical vs. novel reasoning) and how they map to a tier + reasoning effort, with the rule that uncertainty or any high signal pins the STRONGEST available tier (the no-degradation guarantee); (3) the platform routing-profile schema (fields: `can_script_switch`, `enumerate_command`, `switch_mechanism`, `effort_knob`, `model_list_source`) populated for Claude Code, Codex, Antigravity `agy`, Gemini CLI, Cursor, Copilot, OpenCode, from the capability table in the parent plan's Overview; (4) whether thin deterministic Tier-3 helper scripts are warranted for platform detection and model enumeration (recommend yes - a `detect-platform` and an `enumerate-models` helper - deferred to sub-task 1.3). Output the note only; make no file edits. Constraint: zero new outbound calls, dependencies, or credentials.

---

#### 1.2 - Write SKILL.md (Tier 1 + Tier 2)

**Objective**: Author the skill body per the AGENTS.md SKILL.md contract and three-tier model.

**Prompt**:
> Create `catalog/skills/ai-development/model-routing/SKILL.md` using the design from 1.1. Follow the AGENTS.md SKILL.md contract exactly: required frontmatter (`name`, `description`, `summary_l0` <=15 words quoted, `overview_l1` <=150 words quoted). The `description` must be pushy and SKIP-claused, listing trigger phrases verbatim ("route this to the right model", "which model should I use", "pick the cheapest model that can do this", "is this an Opus task or a Sonnet task", "save tokens on this phase", "what reasoning effort for this") AND a SKIP clause ("SKIP: checking current usage against limits -> use /usage; setting hard spend caps for autonomous agents -> ai-billing-safeguards; choosing an API PROVIDER rather than a model tier -> multi-provider-ai"). Required body sections in order: title + intro; "When to Use This Skill" with an explicit "When NOT to use"; "Instructions" (numbered: detect the platform, enumerate available models live from that platform's surface, score the task on the rubric, map the score to a model + effort applying the strong-tier-default rule, assemble the recommendation with reasoning and best-effort citations, then describe the switch per the platform's tier in the spectrum); a "Platform routing profiles" subsection rendering the capability table (per platform: how to enumerate, how to switch, the effort knob, scriptable vs. one-action vs. manual); "Common Rationalizations" (>=3 rows, each a concrete failure mode - e.g. "this phase looks simple so Haiku is fine" rebutted by the blast-radius/uncertainty rule; "I'll just hardcode the current model names" rebutted by staleness; "auto-switching works everywhere" rebutted by the Claude-main-loop and Cursor constraints); "Verification" (binary, observable - the recommendation names a model that appears in the live-enumerated set, the reasoning cites at least the complexity signals, the switch instruction matches the detected platform's mechanism, uncertain/high-complexity tasks resolve to the strongest tier); "Related Skills" (bidirectional `[[wikilink]]` to `multi-provider-ai`, `prompt-engineering`, `ai-billing-safeguards`, `agent-orchestration-primitives`, and the `check-usage` skill). Keep the body <=500 lines. ASCII-only (hyphens, straight quotes, `...`); blank line before/after every list, table, code block, and heading; 4-space nested-list indent; each bullet a single continuous line. State explicitly in the body that the skill introduces no outbound call, dependency, or credential, and that the optional Anthropic `GET /v1/models` enumeration is best-effort and used only when a key is already present.

---

#### 1.3 - Add the Tier-3 detection and enumeration helpers (with `.ps1` parity)

**Objective**: Ship the deterministic, zero-outbound platform-detection and model-enumeration helpers the skill leans on, with cross-platform parity.

**Prompt**:
> Under `catalog/skills/ai-development/model-routing/scripts/`, add two stdlib-only, zero-outbound helpers, each with a `.sh` and a `.ps1` sibling per the AGENTS.md parity rule. (1) `detect-platform.{sh,ps1}`: detect which agentic platform is running from environment cues that are already present (e.g. `CLAUDECODE` / `CLAUDE_CODE_*` env vars for Claude Code, the presence of the `codex` / `agy` / `gemini` binaries on PATH and their config dirs `~/.codex` / `~/.gemini`, Cursor/Copilot markers), printing a single normalized platform id on stdout. (2) `enumerate-models.{sh,ps1}`: given a platform id, print the available models as JSON by calling that platform's OWN enumeration surface - `codex debug models` for Codex, `agy models` for Antigravity, the alias set for Gemini CLI, and for Claude Code an optional `curl https://api.anthropic.com/v1/models` only when `ANTHROPIC_API_KEY` is set (otherwise print a sentinel telling the caller to use the `/model` picker). No script may import a network module beyond the single optional documented Anthropic call, open any other connection, or require a new credential. Reference both helpers from SKILL.md (the orphan-bundle audit requires every bundled file to be referenced). Run ShellCheck on the `.sh` files.

---

#### 1.4 - Register the skill in all three catalog registries

**Objective**: Make the skill discoverable per AGENTS.md (a new skill MUST update the three registries).

**Prompt**:
> Register the new `model-routing` skill in the three catalog registries, modeled on an existing `ai-development` entry (e.g. `multi-provider-ai`). (1) `data/SKILL_INDEX.md`: add one row `| model-routing | ai-development | "<summary_l0>" | catalog/skills/ai-development/model-routing/SKILL.md |`. (2) `data/skills.json`: add one entry to the `skills` array following the existing schema (name, title, description, long_description, summary_l0, overview_l1, version, author, category=ai-development, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security with structural/integrity/semantic defaults 100/100/95). (3) `data/marketplace.json`: increment the `ai-development` category `skill_count` by 1 and increment `total_skills` in `statistics` by 1 - both relative to the CURRENT value at implementation time (do NOT hardcode a target number, because the v3.4.0 adoption plan also adds a skill and either may land first; mirror whatever the live count is and bump it by one), and update any other headline count-prose surface that tracks the catalog total (README, AGENTS.md, the `data/SKILL_INDEX.md` Total label, `data/marketplace.json` plugin description, `.claude-plugin/plugin.json` description). Do not hand-edit any other `data/` file. After editing, run `make validate` and confirm JSON integrity passes and `scripts/check_version_sync.py` (if it covers counts) is green.

---

#### 1.5 - Testing and Stabilization

**Objective**: Validate and security-scan the new skill; iterate until stable before Phase 2.

**Prompt**:
> Validate the new skill end to end. Run `make validate` (JSON catalog integrity + per-skill orphan-bundle audit - confirm no unreferenced files under the skill's `scripts/`), `make lint` (ShellCheck on the `.sh` helpers), and `make test` (pytest hook suite). Run the skill-security scan on the new skill and confirm an install-OK verdict. If `make` is not on PATH (the known v3.3.0 local-Windows gap WN-v33-1), invoke the underlying validators and the scanner directly and note that in the session history. Confirm: frontmatter parses as YAML, `summary_l0` and `overview_l1` are quoted strings, all `[[wikilink]]` cross-links resolve to real skills (0 dangling), and the pushy `description` either fits the length norm or is added to the validator allowlist per the pushy-description mandate (do NOT shorten it to pass). Manually dry-run the two helpers on this machine (Windows / PowerShell) and confirm `detect-platform.ps1` returns a sane platform id and `enumerate-models.ps1` either enumerates or prints the picker sentinel without error. Add a `## [Unreleased]` entry to `CHANGELOG.md` (note: skill-native, zero new outbound call / dependency / credential). Then run `/session` to document Phase 1.

---

### Phase 1 Exit Checklist

- [ ] All sub-tasks completed (helpers shipped with `.sh` + `.ps1` parity and referenced from SKILL.md)
- [ ] `make validate`, `make lint`, `make test` green (or direct-validator equivalents, per WN-v33-1)
- [ ] Skill registered in all three registries; catalog total bumped by 1 from the live value (not a hardcoded target)
- [ ] Skill-security scan returns install-OK; orphan-bundle audit clean; 0 dangling wikilinks
- [ ] CHANGELOG `[Unreleased]` entry added
- [ ] No known regressions; session history generated
- [ ] Ready to advance to Phase 2

---

## Phase 2: The `/route` command + switch helpers (skill-native)

**Goal**: Add a thin `/route` command that resolves what to assess, delegates to the `model-routing` skill, presents the recommendation with reasoning and citations, and applies the confirm-then-auto-execute posture using bundled per-platform switch helpers.
**Prerequisites**: Phase 1 (the skill the command dispatches to).
**Stability Gate**: `catalog/commands/route.md` exists and dispatches to `model-routing`; the switch helpers exist with `.sh`/`.ps1` parity and are referenced from the skill; a dry-run on at least the local platform shows a recommendation produced and the switch posture applied (executed where scriptable, instruction-only otherwise) with no error; `make lint` and the relevant tests are green; `data/marketplace.json` `total_commands` is bumped.

### Sub-tasks

#### 2.1 - Write the `/route` command (thin dispatcher)

**Objective**: Author `catalog/commands/route.md` as a thin scope-resolving dispatcher over the `model-routing` skill, matching the repo's command conventions.

**Prompt**:
> Create `catalog/commands/route.md` following the thin-dispatcher pattern used by `catalog/commands/plan.md` and `catalog/commands/implement.md` (read both first; commands need no frontmatter but use SKILL.md instruction conventions). The command resolves a TARGET from `$ARGUMENTS`: (a) `/route phase N of <plan-path>` or `/route <plan-path> phase-N` -> assess that specific plan phase's scope and sub-tasks; (b) `/route "<free-text task>"` -> assess that task; (c) `/route` (bare) -> assess the current in-flight task from conversation context. After resolving the target it delegates to the `model-routing` skill to detect the platform, enumerate models live, score the task, and produce a recommendation (model + reasoning effort + why, with best-effort citations). Then it applies the confirm-then-auto-execute posture: present the recommendation, ask the user to approve, and on approval act per the platform tier - execute the switch via the bundled helper on scriptable platforms (Codex / agy / Gemini CLI), print the exact `/model` + `/effort` keystroke on Claude Code (and offer to route delegated subagent work to the chosen tier), or print the picker instruction on Cursor / Copilot / OpenCode. Keep the dispatcher thin (heavy logic stays in the skill). Add a Notes section stating it is platform-agnostic and adds zero outbound calls. ASCII-only; follow the Markdown style guide.

---

#### 2.2 - Add the per-platform switch helpers (with `.ps1` parity)

**Objective**: Ship the deterministic switch-execution helpers for the scriptable platforms, with cross-platform parity, so "auto-execute" is real where the platform allows it.

**Prompt**:
> Under `catalog/skills/ai-development/model-routing/scripts/`, add `switch-model.{sh,ps1}`: given a platform id, a model id, and an optional effort level, perform the switch using that platform's documented non-interactive mechanism - for Codex, set the model and effort via a config override on the next invocation or write a profile (`-c model=... -c model_reasoning_effort=...` / `--profile`); for Antigravity `agy`, use the `-m` flag / config key; for Gemini CLI, set `--model` / `GEMINI_MODEL` / `settings.json model.name`; for Claude Code and the manual-only platforms, do NOT attempt a programmatic switch - print the exact user instruction (the `/model` and `/effort` keystrokes for Claude Code, the picker step for Cursor) and exit 0. The script must be idempotent, validate that the requested model is in the enumerated set before acting, refuse unknown platforms cleanly, and never edit a running session's state in a way the platform ignores. No new credential or outbound call. Reference the helper from SKILL.md. Run ShellCheck on the `.sh`.

---

#### 2.3 - Register the command surface

**Objective**: Bump the command count and confirm the slash surface per platform.

**Prompt**:
> Per AGENTS.md, a new command needs no skill-registry edit, but update `data/marketplace.json` `total_commands` (increment by 1 from the live value). Confirm the slash surface the new `/route` command gets per the v3.3.4 distribution channels and note it in the CHANGELOG entry: global slash surface on Claude (`commands/`), Codex (`prompts/`), Gemini (`workflows/`), Cursor (`~/.cursor/commands/`), and Copilot (VS Code `prompts/*.prompt.md`); project-only on Antigravity 2.0 (`.agents/workflows/`, seeded by `nexus-hub init`); body-only via the instruction file on OpenCode. Do not maintain any static command list - `/skills list` derives the cheatsheet at runtime.

---

#### 2.4 - Testing and Stabilization

**Objective**: Verify the command end to end across the switch-posture tiers; iterate until stable.

**Prompt**:
> Validate `/route` and the switch helpers. (1) On this machine, run `/route` against a sample task and against `phase 1 of docs/v3/v3.4/plans/model-routing.md`, and confirm: the platform is detected, models are enumerated (or the picker sentinel is returned), a recommendation with reasoning is produced, and an uncertain/high-complexity sample resolves to the strongest tier. (2) Exercise the switch posture on the locally available platform tier and confirm the correct behavior (execute vs. keystroke vs. picker instruction) with no error; for platforms not installed locally, assert the helper refuses cleanly with a clear message rather than guessing. (3) Run `make lint` and add or extend tests under `catalog/hooks/tests/` (or a dedicated test module) asserting the helpers validate the model against the enumerated set and that unknown platforms are refused. (4) Re-confirm WN-v33-1 (CI validate/scan green on the ubuntu runner; locally invoke validators directly if `make` is absent). Add a `## [Unreleased]` CHANGELOG entry for the `/route` command (note the slash surfaces from 2.3 and zero new outbound call / dependency / credential). Then run `/session` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] `/route` command created as a thin dispatcher to `model-routing`
- [x] Switch helpers shipped with `.sh` + `.ps1` parity, referenced from SKILL.md, model-validated, and clean-refusing on unknown platforms
- [x] `total_commands` bumped; slash-surface coverage noted in CHANGELOG
- [x] Dry-run shows recommendation + correct posture behavior per platform tier; strong-tier-default holds on uncertain input
- [x] `make lint` + tests green (or direct equivalents, per WN-v33-1)
- [x] No known regressions; session history generated
- [x] Ready to advance to Phase 3

---

## Phase 3: `/plan` integration (planning-time routing)

**Goal**: Make `/plan` assess every phase it generates and annotate the plan with a recommended model and reasoning effort per phase, platform-agnostically and with graceful degradation when routing is unavailable.
**Prerequisites**: Phase 1 (the routing skill). Independent of Phase 2 but sequenced after it so the standalone capability proves out first.
**Stability Gate**: A plan generated through `/plan` carries a recommended-model column in "Phases at a Glance" and a per-phase model/effort field; the step degrades silently when the routing skill or platform enumeration is unavailable; `make validate` and the planning-skill tests are green; AGENTS.md and CHANGELOG updated.

### Sub-tasks

#### 3.1 - Add a routing-assessment step to the plan workflow

**Objective**: Insert an optional, platform-agnostic model-routing assessment into `/plan` and its retained planning skill, at the point where phases are designed.

**Prompt**:
> Edit `catalog/commands/plan.md` and the retained planning skills (`catalog/skills/workflow/implementation-plan/SKILL.md` and the `generate-plan` skill it references) to add a model-routing assessment. In `plan.md`, add a short step (model it on the existing "Optional dynamic-workflow robustness (graceful degradation, REQUIRED)" section's tone): after the phase breakdown is designed and before the plan file is written, invoke the `[[model-routing]]` skill once per phase to score that phase's scope and recommend a model + reasoning effort, defaulting to the strongest tier on any uncertainty. The step is best-effort and degrades silently: if the routing skill or live model enumeration is unavailable, write a neutral "recommended model: assess at implementation time" placeholder rather than failing. Keep `plan.md` a thin dispatcher - the heavy logic stays in the skill. State that the assessment is platform-agnostic (it records tier intent like "strong reasoning tier, high effort" alongside the concretely-enumerated model name when available, so the recommendation survives a platform switch between planning and implementation). ASCII-only; follow the Markdown style guide.

---

#### 3.2 - Extend the plan template to carry per-phase model recommendations

**Objective**: Add the recommendation to the plan document structure so it is a durable artifact the implement step reads back.

**Prompt**:
> In `catalog/skills/workflow/implementation-plan/SKILL.md`, extend the plan template (the `## Phases at a Glance` table and the `## Phase N` header block). (1) Add a "Rec. model / effort" column to the "Phases at a Glance" table template. (2) Add a `**Recommended model**:` line to the per-phase header block template (alongside `**Goal**`, `**Prerequisites**`, `**Stability Gate**`), holding both the tier intent and the concretely-enumerated model+effort when available, plus a one-line rationale. Update the skill's Verification checklist to include "every phase carries a recommended model (or an explicit assess-at-implementation placeholder)". Keep the additions optional-friendly so existing plans without the column still validate. ASCII-only; blank lines around the table; do not hard-wrap.

---

#### 3.3 - Update platform-coverage docs and CHANGELOG

**Objective**: Document the new planning-time routing behavior.

**Prompt**:
> Update `AGENTS.md` (the section describing the `/plan` surface and the loop) to note that `/plan` now performs a best-effort, platform-agnostic model-routing assessment per phase and records it in the plan, degrading silently when unavailable. Add a `## [Unreleased]` CHANGELOG entry. ASCII-only. Confirm this is NOT a `base-*.md` lockstep change (it is command + skill behavior, not always-loaded instruction text) and state that in the CHANGELOG note.

---

#### 3.4 - Testing and Stabilization

**Objective**: Verify the planning integration and its graceful degradation; iterate until stable.

**Prompt**:
> Validate the `/plan` integration. (1) Generate a small throwaway plan through `/plan` and confirm each phase carries a recommended model + effort (or the assess-at-implementation placeholder), and that "Phases at a Glance" shows the new column. (2) Simulate routing-unavailable (no platform enumeration) and confirm the step degrades to the neutral placeholder without failing the plan generation. (3) Run `make validate` (confirm the template change does not break existing plan validation) and the planning-skill tests; re-confirm WN-v33-1. Fix any failure and re-run until green. Add/extend the CHANGELOG entry. Then run `/session` to document Phase 3.

---

### Phase 3 Exit Checklist

- [x] `/plan` runs a per-phase routing assessment; `plan.md` stays a thin dispatcher
- [x] Plan template carries the recommended-model column + per-phase field; existing plans still validate
- [x] Graceful degradation verified (neutral placeholder when routing unavailable)
- [x] AGENTS.md + CHANGELOG updated; confirmed not a base-template change
- [x] `make validate` + planning tests green (or direct equivalents)
- [x] No known regressions; session history generated
- [x] Ready to advance to Phase 4

---

## Phase 4: `/implement` integration (per-phase re-confirmation)

**Goal**: Make `/implement` re-run the routing assessment at the start of each phase - because a stronger or cheaper model may have shipped since planning - confirm or override the plan's recommendation, and apply the switch posture before the build step.
**Prerequisites**: Phase 1 (routing skill); Phase 3 (the plan now carries a recommendation to re-confirm). Final phase of this plan, so it triggers release readiness on completion.
**Stability Gate**: `/implement` performs a pre-build routing re-confirmation that reads the plan's recommendation, re-assesses against the currently-enumerated models, and applies the confirm-then-auto-execute posture; the step degrades gracefully and never blocks implementation; `make` checks and the `implement-phase` tests are green; AGENTS.md, the interactive guide (`nexus-hub-guide.html` loop section), and CHANGELOG are updated; release readiness run.

### Sub-tasks

#### 4.1 - Add a per-phase routing pre-flight to the implement workflow

**Objective**: Insert a re-confirmation step into `/implement` and its retained `implement-phase` skill, before subtask implementation begins.

**Prompt**:
> Edit `catalog/commands/implement.md` and the retained `implement-phase` skill to add a model-routing pre-flight at the start of each phase, before the subtask-by-subtask implementation step. The pre-flight: (1) reads the phase's `**Recommended model**` from the plan (written by Phase 3); (2) invokes `[[model-routing]]` to re-assess against the CURRENTLY enumerated models - this is the key reason for re-confirmation, since a plan built before a new model release should pick up the newer/cheaper option at implementation time; (3) if the re-assessment agrees with the plan, applies the confirm-then-auto-execute posture (execute on scriptable platforms, keystroke on Claude Code, picker instruction otherwise); if it disagrees (e.g. a newer model now dominates), surfaces the delta and asks the user which to use, defaulting to the stronger option. The step is best-effort and never blocks: if routing or enumeration is unavailable, proceed on the plan's recommendation (or the session's current model) with a one-line note. Keep `implement.md` a thin dispatcher; the logic lives in `implement-phase`. State platform-agnosticism explicitly. ASCII-only; follow the Markdown style guide.

---

#### 4.2 - Wire the troubleshooting-loop escalation (conditional upshift)

**Objective**: Let a phase that hits repeated test failures escalate to a stronger model, consistent with the no-degradation guarantee.

**Prompt**:
> In the `implement-phase` skill's troubleshooting loop, add a conditional model-escalation rule: if a phase's tests fail repeatedly (e.g. after N troubleshooting iterations on the same failure), the skill should recommend (and, per posture, with confirmation apply) an upshift to a stronger reasoning tier / higher effort before continuing, since persistent failure is a signal the task was under-tiered. This is an UPSHIFT only - never an automatic downshift mid-phase - to preserve the quality guarantee. Make it best-effort and platform-aware (on Claude Code it surfaces the `/model`+`/effort` keystroke; on scriptable platforms it can apply with confirmation). Document it in the skill body and its Verification. ASCII-only.

---

#### 4.3 - Update the loop documentation, the interactive guide, and CHANGELOG

**Objective**: Document the implement-time re-confirmation and escalation behavior AND reflect routing as an automated segment of the Nexus-Hub loop in the user-facing guide, now that the `/plan` + `/implement` integration is complete.

**Prompt**:
> Now that routing is wired into both `/plan` (Phase 3) and `/implement` (this phase), update the user-facing documentation so routing reads as an automated part of the Nexus-Hub loop. (1) `AGENTS.md`: in the `/plan`, `/implement`, and loop sections, describe the planning-time assessment, the per-phase re-confirmation, and the troubleshooting-loop upshift - all platform-agnostic and best-effort. (2) `guides/interactive-guide/nexus-hub-guide.html`: update the "THE GOLDEN PATH" / "The Nexus-Hub loop" section so the loop reflects that `/plan` and `/implement` now perform model routing (e.g. a routing note or sub-step on those two stages), and add the new `/route` command wherever the guide enumerates the command set; preserve the guide's existing structure and styling. (3) Any other user-facing surface that describes the loop or the command set (the README loop description; the commands cheatsheet style guide only if it hard-references behavior). (4) Add a `## [Unreleased]` CHANGELOG entry. Confirm and state that this is command + skill + docs behavior, not a `base-*.md` lockstep change. ASCII-only for Markdown (follow the Markdown style guide); the HTML guide follows its own existing conventions.

---

#### 4.4 - Testing and Stabilization

**Objective**: Verify the implement integration, its graceful degradation, and the escalation rule; iterate until stable; then run release readiness.

**Prompt**:
> Validate the `/implement` integration. (1) On a throwaway plan that carries Phase-3 recommendations, run `/implement` for a phase and confirm the pre-flight reads the recommendation, re-assesses against live models, and applies the correct posture; simulate a "newer model shipped since planning" case and confirm the delta is surfaced with the stronger-default. (2) Confirm routing-unavailable degrades to proceeding on the plan's recommendation with a note, never blocking. (3) Exercise the troubleshooting-loop upshift on a deliberately-failing sample and confirm it upshifts (with confirmation) and never auto-downshifts mid-phase. (4) Run `make validate`, `make lint`, `make test` (or direct equivalents per WN-v33-1) and the `implement-phase` tests; fix and re-run until green. Add the CHANGELOG entry. Run `/session` to document Phase 4. As this is the plan's final phase, `/implement` then triggers release readiness; route the version bump / changelog / tag / push through `/update release` per the implement-phase final-phase contract.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none - Constitution Check has no FAIL bullets) | | |

---

### Phase 4 Exit Checklist

- [x] `/implement` runs a per-phase routing re-confirmation before the build step; `implement.md` stays a thin dispatcher
- [x] Re-assessment picks up newer/cheaper models shipped since planning; disagreements surface with stronger-default
- [x] Troubleshooting-loop upshift implemented (upshift-only, with confirmation); never auto-downshifts mid-phase
- [x] Graceful degradation verified (never blocks implementation)
- [x] AGENTS.md, the interactive guide (`nexus-hub-guide.html` loop section), and CHANGELOG updated; the new `/route` command is listed in the guide; confirmed not a base-template change
- [x] `make` checks + `implement-phase` tests green (or direct equivalents)
- [x] No known regressions; session history generated
- [ ] Release readiness run via `/update release` (final phase)

---

## Out of Scope / Deferred (backlog)

The next `/plan` ingests these via the known-gaps file.

| ID | Item | Why deferred |
|---|---|---|
| R-1 | A model-cost / capability cache shared across sessions (persisted enumeration + pricing) | The session-scoped live enumeration in Phase 1 is sufficient for v3.4.0; a persisted cross-session cache is an optimization to add once routing is proven and only if enumeration latency is a real cost. |
| R-2 | Auto-detected budget-aware routing tied to `ai-billing-safeguards` hard caps (downshift automatically as a session approaches a spend cap) | Couples routing to the billing-safeguard runtime; worth doing after both are stable, as a dedicated integration. |
| R-3 | A `base-*.md` always-on routing nudge (surface a routing hint on every session start) | Deliberately excluded for v3.4.0 - routing stays opt-in via `/route` and the plan/implement steps to avoid always-loaded token cost and over-triggering; revisit only if users ask for ambient routing. |
| R-4 | Per-provider routing inside Cursor (recommend Anthropic vs. OpenAI vs. Google tier-for-tier) | Cursor is manual-only with no scriptable surface; cross-provider recommendation is feasible as advice but low-leverage until Cursor exposes a programmatic switch. |

## Carried-forward known gaps (from v3.3.0)

- **WN-v33-1** (Low): confirm CI `validate` and `scan` are green on the ubuntu runner; locally, `make` may not be on PATH, so invoke validators/scanner directly. Folded into 1.5, 2.4, 3.4, 4.4.
- **WN-v33-2** (Low): two benign pre-existing global-audit warnings (the `demo-capture` orphan `.pyc` is local-only/gitignored; `git-branching-workflow` has a 169-word `overview_l1` soft warning). No gate impact.
