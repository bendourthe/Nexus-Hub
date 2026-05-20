---
name: implementation-plan
description: >-
  Guide the user through a structured discovery interview to generate a comprehensive
  phased plan (docs/<version>/plans/<slug>.md) for their project. Works for initial
  v0.1.0 builds, feature additions, UX enhancements, refactors, and bug-fix campaigns.
  Asks targeted questions appropriate to the plan type, then generates a phased plan
  where each phase contains sub-tasks with detailed executable prompts, ends with test
  generation and troubleshooting, and closes with a session-history entry. Invoked via
  /generate-plan. Use when starting a new project, when setup-project has just finished,
  when /compare-project hands off a comparison report to operationalize, or when a user
  asks to create an implementation plan, v0.1.0 plan, enhancement plan, refactor plan,
  or roadmap.
summary_l0: "Generate a phased plan through guided discovery, saved to docs/<version>/plans/<slug>.md"
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
  After the interview the skill writes the plan to docs/<version>/plans/<slug>.md
  structured into numbered phases with numbered sub-tasks. Every sub-task includes a
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

Guide the user through a structured discovery interview, then generate a comprehensive plan at `docs/<version>/plans/<slug>.md` broken into phased sub-tasks — each with an executable prompt — so the full effort can be completed session by session. The command entry point is `/generate-plan`. When invoked with a comparison report path (`/generate-plan docs/<version>/comparison-<name>.md`), the command enters *From-comparison mode* (Step 0.5): it pre-seeds the interview from the report's Adoption Plan section, skipping questions the report already answers, and writes the plan to `docs/<version>/plans/adoption-<name>.md`.

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

### Phase C: Generate the Plan File

Resolve the target version (from git tags, CHANGELOG, or package manifests; default `v0.1.0` for fresh greenfield projects) and derive a slug from the one-sentence scope statement collected at the start of the interview (lowercase, hyphen-separated, ~5 words, sanitized to `[a-z0-9-]+`). Confirm both with the user before writing.

Create `docs/<version>/plans/` if it does not exist and write to `docs/<version>/plans/<slug>.md` following the structure below.

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

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | [Title] | [One-line outcome] |
| 2 | [Title] | [One-line outcome] |
| ... | ... | ... |
```

The `## Constitution Check` block is **required** in every generated plan. When `docs/<version>/constitution.md` exists, enumerate each MUST principle with PASS / FAIL / N/A and a one-sentence justification tied to the plan's scope. When the file does not exist, emit the informational note verbatim - the check is opt-in by design and does not block plan generation. See `[[project-constitution]]` for how principles are authored, amended, and propagated; failures here mean either the plan needs to change or the constitution itself needs an amendment (a `MAJOR` / `MINOR` / `PATCH` decision made through the constitution skill, not silently inside the plan).

#### Phase Structure

Each phase must follow this template exactly:

```markdown
---

## Phase N: [Phase Title]

**Goal**: [One sentence describing what this phase delivers.]
**Prerequisites**: [Phases that must be complete before starting, or "None".]
**Stability Gate**: [The observable condition that proves this phase is complete and stable.]

### Sub-tasks

#### N.1 — [Sub-task Title]

**Objective**: [What this sub-task accomplishes.]

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
> tests, E2E tests, performance benchmarks, CI/CD configuration, etc.]. Run the tests,
> fix any failures, and iterate until all tests pass and the implementation is stable.
> Do not proceed to Phase N+1 until this phase is fully tested and verified.
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
- What is the minimal foundation that makes everything else possible? (Phase 1)
- What can be built and tested independently? (each subsequent phase)
- What is the natural order given dependencies between components?
- Does every feature from Q2 appear somewhere?
- Where is the installation/packaging step?

### Step 4: Write the Plan

Create `docs/<version>/plans/` if it does not exist, then write `<slug>.md` inside it following the structure above. If the target file already exists, ask the user whether to **Regenerate** (overwrite), **Append** (add phases), or **Rename** (pick a new slug).

### Step 5: Review and Confirm

Show the user the phases-at-a-glance table and ask:
- "Does this phase breakdown look right?"
- "Are there any features missing or phases you would reorder?"

Incorporate feedback, then write the final file.

---

## Quality Checklist

- [ ] Plan type, version, and slug all resolved and confirmed with the user
- [ ] All discovery questions answered (optional "additional context" question may be skipped)
- [ ] Research performed for unfamiliar technical areas
- [ ] Every feature or goal from the interview appears in at least one sub-task
- [ ] Phase 1 establishes the foundation needed for subsequent phases (toolchain + runnable build for initial implementations; test harness or scaffolding for enhancements/refactors)
- [ ] For initial implementations: installation/packaging step appears before the halfway point
- [ ] Every phase ends with a testing and stabilization sub-task
- [ ] Every sub-task has a complete, self-contained executable prompt
- [ ] Every phase has a stability gate and exit checklist
- [ ] `## Constitution Check` section present between `## Overview` and `## Phases at a Glance` (with PASS / FAIL / N/A per MUST principle, or the informational note when no constitution file exists)
- [ ] `## Complexity Tracking` section present near the end of the file (empty table when no FAIL bullets; populated row per FAIL otherwise)
- [ ] File written to `docs/<version>/plans/<slug>.md`
- [ ] User confirmed the phase breakdown before final generation

## Related Skills

- `[[project-constitution]]` - authors and amends the constitution that the Constitution Check section enforces; FAIL verdicts here lead either to plan edits or to a constitution amendment via that skill
- `plan-before-code` - Lightweight planning for individual features within a phase
- `research-plan-implement` - Structured RPI workflow for a single complex feature
- `session-history` - Document each completed phase
- `test-driven-development` - Apply TDD within individual sub-tasks

---

**Version**: 1.2.0
**Last Updated**: April 2026
