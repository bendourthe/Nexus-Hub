---
name: implementation-plan
description: >-
  Guide the user through a structured discovery interview to generate a comprehensive
  phased plan (docs/v<MAJOR>/v<MAJOR>.<MINOR>/plans/v<MAJOR>.<MINOR>.<PATCH>-<slug>.md) for their project. Works
  for initial v0.1.0 builds, feature additions, UX enhancements, refactors, and bug-fix campaigns.
  Asks targeted questions appropriate to the plan type, then generates a phased plan
  where each phase contains sub-tasks with detailed executable prompts, ends with test
  generation and troubleshooting, and closes with a session-history entry. Invoked via
  /generate-plan. Use when starting a new project, when setup-project has just finished,
  when /compare-project hands off a comparison report to operationalize, or when a user
  asks to create an implementation plan, v0.1.0 plan, enhancement plan, refactor plan,
  or roadmap.
summary_l0: "Generate a phased plan through guided discovery, saved to docs/v<MAJOR>/v<MAJOR>.<MINOR>/plans/v<MAJOR>.<MINOR>.<PATCH>-<slug>.md"
overview_l1: >-
  This skill conducts a structured discovery interview — asking one question at a
  time — to collect everything needed to write a comprehensive phased plan. The first
  step establishes plan type (initial implementation, feature/enhancement, refactor,
  other), target version, and an auto-suggested filename slug derived from a
  one-sentence scope statement. For initial implementation plans the interview covers
  core purpose, key features, installation/distribution, UI type, platform targets,
  runtime behavior, integrations, performance, definition of done, and testing. For
  enhancements/refactors the interview uses a shorter scope-focused question set:
  goal, in/out scope, affected areas, constraints, definition of done, and testing.
  After the interview the skill writes the plan to docs/v<MAJOR>/v<MAJOR>.<MINOR>/plans/v<MAJOR>.<MINOR>.<PATCH>-<slug>.md
  (the legacy flat layout docs/<vSEMVER>/plans/<slug>.md is honored when already present;
  see the docs-layout-refactor Version-directory resolution for the path-resolution algorithm) structured into numbered
  phases with numbered sub-tasks. Every sub-task includes a
  self-contained executable prompt that can be handed directly to Claude Code in a
  future session. Each phase ends with a dedicated testing and troubleshooting
  sub-task and a generate-session-history call. Phases do not advance until the
  current phase is stable. Use websearch when research on libraries, toolchains, or
  distribution packaging is needed.
  Trigger phrases: implementation plan, v0.1.0 plan, build plan, project roadmap,
  enhancement plan, refactor plan, what should I build first, create a plan,
  generate plan, generate implementation plan, how do I build this, phased
  development plan.
---

# Implementation Plan

Guide the user through a structured discovery interview, then generate a comprehensive plan at `<version_dir>/plans/<slug>.md` broken into phased sub-tasks — each with an executable prompt — so the full effort can be completed session by session.

`<version_dir>` is resolved per the `[[docs-layout-refactor]]` skill's Version-directory resolution algorithm. The canonical layout is `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` (e.g., `docs/v3/v3.11/`), with patch releases sharing their minor dir; legacy projects using the flat `docs/<vSEMVER>/` or the old three-level `docs/versions/<vMAJOR>/<vSEMVER>/` layout are auto-detected and respected to avoid mid-version path churn. Use `/update refactor` to migrate a legacy project to the canonical layout.

The command entry point is `/generate-plan`. When invoked with a comparison report path (`/generate-plan <version_dir>/comparisons/v<MAJOR>.<MINOR>.<PATCH>-comparison-<name>.md`; glob `<version_dir>/comparisons/*-comparison-<name>.md` to find it), the command enters *From-comparison mode* (Step 0.5): it pre-seeds the interview from the report's Adoption Plan section, skipping questions the report already answers, and writes the plan **co-located with the seeding comparison**.

In From-comparison mode the plan's target version and `version_dir` are NOT resolved fresh from git tags / CHANGELOG. They come from the comparison report's `Adoption target: vX.Y.Z` header field (written by the `[[cross-project-comparison]]` Step 6.5 "Resolve Adoption Target") - the release that will ADOPT the comparison. The plan is written to `<adoption_version_dir>/plans/vX.Y.Z-adoption-<name>.md`, where `<adoption_version_dir>` is the version directory for that adoption target, so the plan always lives in the same version tree as the comparison that seeded it. The generated plan's header carries `**Seeded from**: <path to the comparison>` (in that same tree) and its `**Version**:` and `**Filename**:` fields match the adoption target. **Graceful degradation**: if the comparison has no `Adoption target:` field (a legacy comparison authored before this convention), fall back to the normal version resolution (Phase C / Step 4) and emit a one-line note recommending the comparison be given an `Adoption target:` field so it and the plan it seeds stay co-located.

## When to Use This Skill

- Immediately after running `/setup-project` on a new project (for the initial v0.1.0 plan)
- When `/compare-project` hands off a comparison report whose Adoption Plan should be operationalized (Step 0.5 *From-comparison mode* pre-seeds the interview)
- When the user asks to create a roadmap or implementation plan for what they want to build
- When planning a feature addition, UX enhancement, refactor, or bug-fix campaign
- When the user provides a high-level vision but has not yet broken it down into steps

**Trigger phrases**: "implementation plan", "v0.1.0 plan", "build plan", "project roadmap",
"what should I build first", "create a plan", "generate plan", "generate implementation plan",
"enhancement plan", "refactor plan", "how do I build this", "phased development plan", "plan for this project"

## What This Skill Does

### Phase A: Discovery Interview

Before the main interview, determine the **plan type**: Initial Implementation (v0.1.0-style greenfield build), Feature/Enhancement, Refactor, or Other. Then also collect a one-sentence scope statement that anchors both the interview and the filename slug.

The question set below is the full **Initial Implementation** interview. For Feature/Enhancement/Refactor/Other plans, use the shorter scope-focused question set documented in [`/generate-plan`](../../../commands/generate-plan.md) Step 1 (Goal, Scope In/Out, Affected Areas, Constraints, Definition of Done, Testing, Additional Context).

Ask the questions below **one at a time**, waiting for each answer before continuing. Do not batch multiple questions into one message.

#### Q1 — Core Purpose
> "What is the core purpose of this application? What problem does it solve, and for whom?"

#### Q2 — Key Features for this Release
> "What are the 5–10 key features or capabilities you want in this release? (Bullet points are fine.)"

#### Q3 — Installation and Distribution
> "How should users install or access the final product?
> Examples: .exe / .dmg / .deb installer, pip / npm / cargo package, VS Code extension,
> Docker container, web app (hosted), CLI downloaded from GitHub Releases, desktop app."

#### Q4 — User Interface
> "What kind of user interface does this need?
> Examples: command-line (CLI), desktop GUI (Electron, Tkinter, WPF, SwiftUI),
> web UI (React, Vue, Svelte), IDE extension (VS Code, JetBrains),
> no UI (background service or API only), TUI (terminal UI)."

#### Q5 — Platform Support
> "Which platforms need to be supported?
> Examples: Windows only, macOS only, Linux only, cross-platform (all three),
> web (any browser), mobile (iOS / Android)."

#### Q6 — Runtime Behavior
> "How should the app behave at runtime?
> Examples: always-on background service / daemon, on-demand CLI invocation,
> event-driven (reacts to file changes, webhooks, etc.), real-time streaming responses,
> scheduled jobs, interactive REPL."

#### Q7 — Integrations and External Dependencies
> "What external services, APIs, models, or tools does it need to integrate with?
> Examples: specific LLM providers or local models, databases, cloud storage,
> authentication providers, VS Code extension APIs, OS-level APIs."

#### Q8 — Performance and Resource Constraints
> "Are there any performance, scale, or hardware constraints to keep in mind?
> Examples: must run on low-end hardware (8 GB RAM), sub-200 ms response times,
> handle N concurrent users, bundle size under X MB, offline-only."

#### Q9 — Definition of Done
> "What does successful delivery of this scope look like? What would you demo to a user or stakeholder
> to show it works end-to-end?"

#### Q10 — Testing and Quality Expectations
> "What level of testing and quality assurance do you want?
> Examples: unit tests only, full CI/CD pipeline with integration and E2E tests,
> performance benchmarks, manual QA checklist, security audit."

#### Q11 — Additional Context (Optional)
> "Anything else I should know — architectural preferences, constraints, prior art,
> reference projects, or things to avoid? (Press Enter to skip.)"

---

### Phase B: Research (if needed)

After the interview, if any aspect of the build (packaging format, framework choice,
local model integration, installer toolchain, etc.) is unfamiliar or uncertain,
use websearch to research the best approach before writing the plan.

Research areas to consider:
- Installer/packaging toolchain for the chosen distribution method and platform
- Recommended project structure for the chosen UI framework and language
- How to integrate specific LLMs or local models
- CI/CD pipeline setup for the target platform
- Testing frameworks best suited to the chosen language/framework

---

### Phase B.5: Knowledge-Base Grounding (before designing phases)

Before designing the phase breakdown, ground the plan in what the project already knows. This is the read half of the compound loop - solved problems and product framing captured earlier become inputs to the new plan instead of being re-derived.

1. **Search the solved-problem store**: if `docs/solutions/` exists, search it (by category, component, and the problem's symptom tokens) for prior solutions relevant to this plan's scope. A matching entry can change the phase breakdown: reuse the documented resolution, avoid a known dead end, or fold the recurrence-recognition note into a test. Cite any entry you lean on in the relevant sub-task's `Prompt`. The store is written by [[solution-knowledge-base]] and audited by [[solution-refresh]].
2. **Read the strategy anchor**: if `STRATEGY.md` (or `docs/<version>/strategy.md`) exists, read it and check that this plan's scope serves the stated Target Problem and Persona and moves at least one Key Metric. If the plan serves no stated persona or metric, surface that tension - either narrow the plan or amend the strategy via [[product-strategy]]; do not plan around it silently.

When neither file exists, note that and proceed - grounding is best-effort, not a blocker.

---

### Phase C: Generate the Plan File

Resolve the target version (from git tags, CHANGELOG, or package manifests; default `v0.1.0` for fresh greenfield projects), then resolve `<version_dir>` per the `[[docs-layout-refactor]]` Version-directory resolution algorithm (canonical `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` for new content, patch releases sharing their minor dir; legacy `docs/<vSEMVER>/` or `docs/versions/<vMAJOR>/<vSEMVER>/` preserved when already present). Derive a slug from the one-sentence scope statement collected at the start of the interview (lowercase, hyphen-separated, ~5 words, sanitized to `[a-z0-9-]+`); the plan file is then named with a release prefix - `v<MAJOR>.<MINOR>.<PATCH>-<slug>.md` - so multiple patch releases sharing one minor dir never collide. Confirm both with the user before writing.

**From-comparison mode overrides the version resolution above.** When the plan is seeded from a comparison report (Step 0.5), do NOT resolve the target version fresh from git tags / CHANGELOG. Read the comparison's `Adoption target: vX.Y.Z` field and use it for both the target version and `<version_dir>`, so the plan co-locates with the comparison, and name the file `vX.Y.Z-adoption-<name>.md`. Only fall back to the fresh resolution above when the comparison lacks the field (a legacy comparison), emitting the one-line note described in From-comparison mode. Either way, still confirm the resolved target with the user before writing.

Create `<version_dir>/plans/` if it does not exist and write to `<version_dir>/plans/v<MAJOR>.<MINOR>.<PATCH>-<slug>.md` following the structure below.

#### File Header

```markdown
# Plan — [Plan Title]

**Project**: [Project Name]
**Version**: [version, e.g. v0.1.0]
**Slug**: [slug]
**Plan Type**: [Initial Implementation / Feature / Refactor / Other]
**Created**: [Date]
**Goal**: [One-sentence definition of done from the discovery interview]

## Overview

[2–3 paragraph summary covering: what is being built or changed, how it will be
delivered, what the UI and runtime impact look like, and what success looks like
for this scope.]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[List each MUST principle from docs/<version>/constitution.md and state PASS / FAIL / N/A
per principle, with a one-sentence justification. If constitution.md does not exist, state
"No constitution file found at docs/<version>/constitution.md - skipping check. Recommend
running /constitution to establish project principles." - this is informational, not blocking.]

## Current model map

**Model map status**: [Use exactly one status from Step 3.5: "fresh as of YYYY-MM-DD; sources cited below.", "offline fallback; stale as of YYYY-MM-DD.", or "unavailable; assess at implementation time."]

| Tier | Anthropic | OpenAI | Google | Cursor |
|------|-----------|--------|--------|--------|
| frontier | [current model id or fallback] | [current model id or fallback] | [current model id or fallback] | [current model id or fallback] |
| strong | [current model id or fallback] | [current model id or fallback] | [current model id or fallback] | [current model id or fallback] |
| standard | [current model id or fallback] | [current model id or fallback] | [current model id or fallback] | [current model id or fallback] |
| fast | [current model id or fallback] | [current model id or fallback] | [current model id or fallback] | [current model id or fallback] |

### Model map sources

- Anthropic: [official model catalog or release-notes URL]
- OpenAI: [official model catalog or release-notes URL]
- Google: [official model catalog or release-notes URL]
- Cursor: [official available-models or models-and-pricing URL]

## Phases at a Glance

| Phase | Title | Outcome | Recommended model tier | Recommended effort level |
|-------|-------|---------|------------------------|--------------------------|
| 1 | [Title] | [One-line outcome] | [frontier / strong / standard / fast] | [low / medium / high / max] |
| 2 | [Title] | [One-line outcome] | [frontier / strong / standard / fast] | [low / medium / high / max] |
| ... | ... | ... | ... | ... |
```

The two recommendation columns are populated by Step 3.5 and contain generic intent only. Concrete model ids belong in `## Current model map`, never in the phase rows. Historical plans generated before this contract remain valid inputs to `/implement`; new plans MUST use the two columns and the four-provider map.

The `## Constitution Check` block is **required** in every generated plan. When `docs/<version>/constitution.md` exists, enumerate each MUST principle with PASS / FAIL / N/A and a one-sentence justification tied to the plan's scope. When the file does not exist, emit the informational note verbatim - the check is opt-in by design and does not block plan generation. See `[[project-constitution]]` for how principles are authored, amended, and propagated; failures here mean either the plan needs to change or the constitution itself needs an amendment (a `MAJOR` / `MINOR` / `PATCH` decision made through the constitution skill, not silently inside the plan).

#### Phase Structure

Each phase must follow this template exactly:

```markdown
---

## Phase N: [Phase Title]

**Goal**: [One sentence describing what this phase delivers.]
**Prerequisites**: [Phases that must be complete before starting, or "None".]
**Stability Gate**: [The observable condition that proves this phase is complete and stable.]
**Recommended model tier**: [frontier / strong / standard / fast]
**Recommended effort level**: [low / medium / high / max]
**Rationale**: [One sentence tying the tier and effort to the phase's complexity signals. Do not name a concrete provider model here.]

### Sub-tasks

#### N.1 — [Sub-task Title]

**Objective**: [What this sub-task accomplishes.]

**Failure modes** *(required when this sub-task introduces or changes a component)*: [What the component does when its inputs are malformed or absent, when a dependency it calls is unreachable or slow, and when two of its operations conflict.]

**Build class** *(state only where a reader could not otherwise tell)*: [load-bearing, or scaffolding naming what replaces it and when.]

**Prompt**:
> [A complete, self-contained prompt the user can paste directly into a new Claude Code
> session to perform this sub-task. Include: the goal, specific files or directories to
> create or modify, acceptance criteria, and any constraints. The prompt must be
> actionable without needing the rest of this document.]

---

#### N.2 — [Sub-task Title]

**Objective**: [What this sub-task accomplishes.]

**Prompt**:
> [Complete executable prompt.]

---

[... additional sub-tasks ...]

---

#### N.X — Testing and Stabilization

**Objective**: Generate and run all tests for this phase. Iterate until the phase is
stable before advancing to Phase N+1.

**Prompt**:
> Generate comprehensive tests for everything built in Phase N. This should include:
> [list the specific kinds of tests appropriate for this phase: unit tests, integration
> tests, E2E tests, performance benchmarks, etc.]. Run the tests, fix any failures, and
> iterate until all tests pass and the implementation is stable. Then create or update the
> CI/CD pipeline to cover this phase's changes and optimize it to reduce CI action minutes
> (path filters, concurrency cancel-in-progress, dependency caching, gating expensive-OS or
> matrix jobs to merges/schedule) while keeping comprehensive coverage - keep the language
> platform-agnostic, with GitHub Actions as the primary example. Do not proceed to Phase
> N+1 until this phase is fully tested and verified.
> After all tests pass, run `/generate-session-history` to document Phase N.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |

---

### Phase N Exit Checklist

- [ ] All sub-tasks completed
- [ ] All tests passing (unit, integration, and any phase-specific tests)
- [ ] No known regressions from prior phases
- [ ] Session history generated for this phase
- [ ] Ready to advance to Phase N+1
```

The `## Complexity Tracking` block sits near the end of the file, between the last phase's content and that phase's `### Phase N Exit Checklist`. Leave the row blank (keep only the header, blockquote, and column titles) when every Constitution Check bullet is PASS or N/A. Populate one row per FAIL principle, stating the violation, why it is needed, and why the simpler alternative was rejected. Treat the section as part of the plan's contract with `[[project-constitution]]` and `/analyze-spec`.

#### Mandatory Final Phase (every plan)

Every generated plan MUST end with a final phase dedicated to architecture refactor, known-gaps reconciliation, and CI/CD - even a small plan (there it may be a light, near-no-op pass, but it is never omitted). This is a REFACTOR / known-gaps / CI phase, NOT a deferred-testing phase: per-phase testing still stands (see the "Testing continuous" guideline below and the testing rationalization). Emit it verbatim as the last `## Phase N`:

```markdown
## Phase N: Architecture Refactor, Known-Gaps Reconciliation, and CI/CD

**Goal**: Leave the project well-organized, its known gaps reconciled, and its CI/CD complete and optimized.
**Prerequisites**: All prior phases.
**Stability Gate**: The layout is clean (no deprecated/obsolete files, empty dirs, redundant files/dirs, or overcomplicated structure left un-triaged); the version's known gaps are reconciled; CI/CD covers every change and is optimized; project validation/tests pass.
**Recommended model tier**: frontier
**Recommended effort level**: max
**Rationale**: Repo-wide refactor, reference repair, known-gap reconciliation, and release gating carry high context volume and blast radius.

### Sub-tasks

#### N.1 - Architecture refactor
**Objective**: Refactor toward a well-organized, intuitive layout.
**Prompt**:
> Identify deprecated/obsolete files, empty directories, redundant files/dirs, and overcomplicated structure, then refactor toward a clean, intuitive layout via [[project-refactor]] and [[docs-layout-refactor]] (propose-then-apply, with confirmation; repair every reference for anything that moves).

#### N.2 - Known-gaps reconciliation
**Objective**: Reconcile the version's open gaps.
**Prompt**:
> Reconcile this version's known gaps via [[known-gaps-tracker]]: resolve, defer, or transfer each open item, and finalize the per-minor known-gaps file for the version.

#### N.3 - CI/CD create/update/optimize
**Objective**: CI/CD covers all changes and is optimized.
**Prompt**:
> Create or update the CI/CD pipeline so it covers every change in this plan, then optimize it to reduce action minutes (path filters, concurrency cancel-in-progress, dependency caching, gating expensive-OS or matrix jobs to merges/schedule) while keeping comprehensive testing. Keep it platform-agnostic; GitHub Actions is the primary example.

#### N.4 - Testing and Stabilization
**Objective**: Prove the refactor preserved behavior and CI/CD is green.
**Prompt**:
> Run the full validation/test suite, confirm the refactor changed no behavior, confirm CI/CD passes and the action-minute reduction is real, and iterate until clean. Generate a session-history entry for this phase.
```

#### Phase Design Guidelines

Apply these rules when deciding how many phases to create and how to split them:

| Guideline | Detail |
|-----------|--------|
| Foundation first | Phase 1 is always project scaffolding, toolchain setup, and a "hello world" build that proves the distribution pipeline works end to end |
| One concern per phase | Each phase should deliver one coherent, independently testable capability |
| No orphaned features | Every feature mentioned in Q2 must appear in at least one sub-task |
| Installation early | If the project has a non-trivial installer or packaging step, include a phase for it in the first third of the plan so packaging issues are caught early |
| UI and backend separated | If there is a UI, give it its own phase rather than mixing it with business logic |
| Integration phase | If external APIs or local models are involved, create a dedicated integration phase with clear mocking/stubbing strategies for early phases |
| Testing continuous | Every phase ends with a testing sub-task — not a single final QA phase |
| Phase count | Target 4–8 phases for most plans; very small scopes may have 2–3; major refactors up to 10 |
| Terminal refactor phase | Every plan ends with a mandatory final phase that reviews architecture and refactors toward a clean, intuitive layout, reconciles the version's known gaps, and creates/updates/optimizes CI/CD - even small plans (a light near-no-op pass, but never omitted). Distinct from per-phase testing, which still applies to every phase. |
| CI/CD per phase | Every phase's testing sub-task also creates or updates the CI/CD pipeline for that phase's changes and optimizes it (path filters, concurrency cancellation, caching, gating expensive jobs) to keep action minutes low while coverage stays comprehensive |

---

## Instructions

### Step 1: Run the Discovery Interview

Ask Q1 through Q11 one at a time. Record all answers internally before generating the plan.

### Step 2: Assess Research Needs

Based on the answers, identify any technical areas that need research. Run websearch
queries as needed. Summarize findings in a brief "Research Notes" block at the top of
your working context (not written to the file).

### Step 3: Design the Phase Breakdown

Before writing the file, outline the phases mentally:
- Did Phase B.5 grounding surface a prior `docs/solutions/` entry or a strategy constraint that changes the breakdown? Fold it in before designing.
- What is the minimal foundation that makes everything else possible? (Phase 1)
- What can be built and tested independently? (each subsequent phase)
- What is the natural order given dependencies between components?
- Does every feature from Q2 appear somewhere?
- Where is the installation/packaging step?

### Step 3.5: Assess Each Phase's Tier and Refresh the Model Map

Once the phase breakdown is fixed and before writing the file, score every phase to generic capability intent and build the plan's cross-provider lookup:

- **Score each phase.** Invoke `[[model-routing]]` once per phase and map the rubric to `frontier`, `strong`, `standard`, or `fast`, plus `low`, `medium`, `high`, or `max` effort. Any uncertainty or high-risk signal defaults to `frontier` with `high` or `max` effort. Record the generic values in the two glance columns and the three per-phase fields.
- **Refresh all providers.** On every full `/plan` invocation, use web search and official provider documentation to populate `## Current model map` for Anthropic, OpenAI, Google, and Cursor. Host-platform enumeration may confirm the current host's picker, but it MUST NOT limit the plan to one provider or become the authoritative plan recommendation.
- **Cite the roster.** Emit `**Model map status**: fresh as of YYYY-MM-DD; sources cited below.` and include at least one official URL per provider under `### Model map sources`.
- **Degrade visibly, never silently.** If web search or official docs are unavailable, use the dated bundled snapshot and emit `**Model map status**: offline fallback; stale as of YYYY-MM-DD.`. If no verified snapshot exists, fill all 16 cells with `assess at implementation time` and emit `**Model map status**: unavailable; assess at implementation time.`. Plan generation never blocks, but staleness is explicit.

Web search is the only added network activity and uses public documentation without a new credential or dependency. The exact document contract is defined in `docs/v3/v3.15/development/cross-provider-routing-contract.md`. `/implement` re-confirms the phase tier and effort against a refreshed map and the selected provider's live platform surface before implementation.

### Step 3.6: Name Each Sub-task's Failure Modes and Build Class

Two per-sub-task fields close gaps that otherwise surface only during review.

**Failure modes are mandatory for every component the plan introduces or changes.** For each such component, state what happens in three specific situations: its inputs are malformed or absent, a dependency it calls is unreachable or slow, and two of its operations conflict. Three named situations rather than a general instruction to handle errors, because "handle errors well" is satisfiable by any behavior including a silent swallow.

This composes with the spec instead of duplicating it. `catalog/templates/spec-template.md`'s `### Edge Cases` prompts name the user-visible edge case ("what happens when an upstream dependency is unreachable?"); this field names the handling ("retry twice with backoff, then serve cache with a staleness banner"). Error handling has no mandatory home in the spec by design, because a spec that pinned retry policy would fail `spec-quality-checklist.md`'s implementation-detail checks. The plan is where it belongs. Do NOT close this gap by pushing error handling, data models, interfaces, or schemas back into the spec template.

A sub-task that only edits prose, moves a file, or runs a tool introduces no component and carries no failure-mode line.

**Build class separates disposable code from the code that proves the design.** Where a sub-task deliberately produces something provisional (a stub, a hardcoded fixture, a shortcut taken to reach a checkpoint), label it `scaffolding` and say what replaces it and when. Where it produces the part that actually demonstrates the approach works, label it `load-bearing`. A reviewer should never have to guess whether a hardcoded value is a shortcut awaiting replacement or the intended implementation, and that distinction is usually unrecoverable from the diff alone.

Keep this to one line. It is a label, not a section: state the class only where a reader could not otherwise tell, and skip it where the answer is obvious.

The build-class convention is adopted on its own merits rather than on precedent. It was proposed on the strength of an example specification said to demonstrate it, and that document turned out to carry no code blocks and no such labeling, so the cited evidence does not support the claim. The idea survives its evidence failing, because the review problem it names is real and observable.

### Step 4: Write the Plan

Create `<version_dir>/plans/` if it does not exist (where `<version_dir>` is the path resolved earlier - canonically `docs/v<MAJOR>/v<MAJOR>.<MINOR>/`, with legacy `docs/<vSEMVER>/` or `docs/versions/<vMAJOR>/<vSEMVER>/` honored when already present), then write the release-prefixed `v<MAJOR>.<MINOR>.<PATCH>-<slug>.md` inside it following the structure above. If the target file already exists, follow the active instruction template's `Consequential Decisions` rule before asking the user whether to **Regenerate** (overwrite), **Append** (add phases), or **Rename** (pick a new slug).

### Step 5: Review and Confirm

Follow the active instruction template's `Consequential Decisions` rule before asking for approval of the phase breakdown.

Show the user the phases-at-a-glance table and ask:
- "Does this phase breakdown look right?"
- "Are there any features missing or phases you would reorder?"

Incorporate feedback, then write the final file.

---

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The user already knows what they want, I can skip the discovery questions" | Skipping discovery produces a plan built on the agent's assumptions; the unasked question is exactly the requirement that gets missed and forces a rewrite mid-implementation. |
| "I will add the install and packaging step at the end" | Deferring packaging to the end means the build is unrunnable for the whole middle of the plan; the install step must land before the halfway point so each phase produces something executable. |
| "A phase does not need its own testing sub-task if I test at the end" | Batching all testing into a final phase hides which phase introduced a defect; every phase must end with a testing and stabilization sub-task so failures are localized. |
| "Error handling is an implementation detail, I will let the implementer decide" | Then nobody decided. "Handle errors" is satisfiable by any behavior including a silent swallow, and the spec deliberately holds only the user-visible edge case, not the handling. If the plan does not name what happens on malformed input, an unreachable dependency, and conflicting operations, that choice gets made mid-implementation by whoever hits it first, under time pressure, without review. |
| "The stub is obviously temporary, labelling it is busywork" | It is obvious to you today and invisible in the diff tomorrow. An unlabelled hardcoded value reads identically whether it is a shortcut awaiting replacement or the intended implementation, so the reviewer has to guess, and the guess that ships is the one that treats scaffolding as finished. One word per sub-task removes the guess. |

## Verification

- [ ] Plan type, version, and slug all resolved and confirmed with the user
- [ ] All discovery questions answered (optional "additional context" question may be skipped)
- [ ] Research performed for unfamiliar technical areas
- [ ] Every feature or goal from the interview appears in at least one sub-task
- [ ] Phase 1 establishes the foundation needed for subsequent phases (toolchain + runnable build for initial implementations; test harness or scaffolding for enhancements/refactors)
- [ ] For initial implementations: installation/packaging step appears before the halfway point
- [ ] Every phase ends with a testing and stabilization sub-task (which also creates/updates and optimizes CI/CD for that phase's changes)
- [ ] The plan's last phase is the mandatory "Architecture Refactor, Known-Gaps Reconciliation, and CI/CD" phase (sub-tasks: N.1 architecture refactor, N.2 known-gaps reconciliation, N.3 CI/CD create/update/optimize, N.4 testing and stabilization)
- [ ] Every sub-task has a complete, self-contained executable prompt
- [ ] Every sub-task that introduces or changes a component states its failure modes across all three situations (malformed or absent input, unreachable or slow dependency, conflicting operations), and no error-handling, data-model, interface, or schema detail was pushed back into the spec to achieve it
- [ ] Sub-tasks producing provisional work carry a one-line `scaffolding` build class naming what replaces it and when; `load-bearing` is stated wherever a reader could not otherwise tell
- [ ] Every phase has a stability gate and exit checklist
- [ ] `## Current model map` is present with four tiers, Anthropic / OpenAI / Google / Cursor columns, a dated status, and source URLs (or one exact offline fallback marker)
- [ ] Every phase carries an allowed generic model tier and effort in both the glance table and its separate per-phase fields; concrete model ids appear only in the Current model map
- [ ] `## Constitution Check` section present between `## Overview` and `## Phases at a Glance` (with PASS / FAIL / N/A per MUST principle, or the informational note when no constitution file exists)
- [ ] `## Complexity Tracking` section present near the end of the file (empty table when no FAIL bullets; populated row per FAIL otherwise)
- [ ] File written to the resolved `<version_dir>/plans/v<MAJOR>.<MINOR>.<PATCH>-<slug>.md` (canonical `docs/v<MAJOR>/v<MAJOR>.<MINOR>/plans/v<MAJOR>.<MINOR>.<PATCH>-<slug>.md` or legacy `docs/<vSEMVER>/plans/<slug>.md`)
- [ ] For From-comparison mode: the plan's target version, `<version_dir>`, `**Version**`, `**Filename**`, and `**Seeded from**` all derive from the comparison's `Adoption target:` field so the plan is co-located with its comparison; for a legacy comparison lacking the field, the fallback resolution ran and the one-line note was emitted
- [ ] User confirmed the phase breakdown before final generation

## Related Skills

- `[[project-constitution]]` - authors and amends the constitution that the Constitution Check section enforces; FAIL verdicts here lead either to plan edits or to a constitution amendment via that skill
- `[[solution-knowledge-base]]` - writes the `docs/solutions/` store that Phase B.5 grounding reads; closes the capture -> plan half of the compound loop
- `[[product-strategy]]` - authors the `STRATEGY.md` anchor that Phase B.5 grounding checks the plan against (problem / persona / metrics)
- `[[model-routing]]` - scores each phase to generic tier and effort, refreshes the four-provider Current model map for `/plan`, and preserves host-native enumeration for direct `/route` switching
- `plan-before-code` - Lightweight planning for individual features within a phase
- `research-plan-implement` - Structured RPI workflow for a single complex feature
- `session-history` - Document each completed phase
- `test-driven-development` - Apply TDD within individual sub-tasks

---

**Version**: 1.6.0
**Last Updated**: August 2026
