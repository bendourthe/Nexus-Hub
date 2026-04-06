---
name: implementation-plan
description: >-
  Guide the user through a structured discovery interview to generate a comprehensive
  implementation plan (docs/v0.1.0/implementation-plan.md) for their project. Asks
  targeted questions about core functionality, key features, installation/distribution,
  UI/UX, platform support, app behavior, integrations, performance requirements,
  definition of done, and testing strategy. Then generates a phased plan where each
  phase contains sub-tasks with detailed executable prompts, ends with test generation
  and troubleshooting, and closes with a session-history entry. Use when starting a
  new project, when setup-project has just finished, or when a user asks to create an
  implementation plan, v0.1.0 plan, or roadmap for what they want to build.
summary_l0: "Generate a phased v0.1.0 implementation plan through guided discovery questions"
overview_l1: >-
  This skill conducts a structured discovery interview — asking one question at a
  time — to collect everything needed to write a comprehensive implementation plan.
  Topics covered: core purpose, key features, installation/distribution method, UI
  type, platform targets, runtime behavior, external integrations, performance
  constraints, definition of done for v0.1.0, and testing expectations. After the
  interview the skill produces docs/v0.1.0/implementation-plan.md structured into
  numbered phases, each containing numbered sub-tasks. Every sub-task includes a
  self-contained executable prompt so the user can hand the prompt directly to
  Claude Code to perform that sub-task in a future session. Each phase ends with a
  dedicated testing and troubleshooting sub-task and a generate-session-history call.
  Phases do not advance until the current phase is stable. Use websearch when
  research on libraries, toolchains, or distribution packaging is needed.
  Trigger phrases: implementation plan, v0.1.0 plan, build plan, project roadmap,
  what should I build first, create a plan, generate implementation plan, how do I
  build this, phased development plan.
---

# Implementation Plan

Guide the user through a structured discovery interview, then generate a comprehensive
`docs/v0.1.0/implementation-plan.md` broken into phased sub-tasks — each with an
executable prompt — so the full build can be completed session by session.

## When to Use This Skill

- Immediately after running `/setup-project` on a new project
- When the user asks to create a roadmap or implementation plan for what they want to build
- When starting v0.1.0 of any application and a structured build sequence is needed
- When the user provides a high-level vision but has not yet broken it down into steps

**Trigger phrases**: "implementation plan", "v0.1.0 plan", "build plan", "project roadmap",
"what should I build first", "create a plan", "generate implementation plan",
"how do I build this", "phased development plan", "plan for this project"

## What This Skill Does

### Phase A: Discovery Interview

Ask the questions below **one at a time**, waiting for each answer before continuing.
Do not batch multiple questions into one message.

#### Q1 — Core Purpose
> "What is the core purpose of this application? What problem does it solve, and for whom?"

#### Q2 — Key Features for v0.1.0
> "What are the 5–10 key features or capabilities you want in v0.1.0? (Bullet points are fine.)"

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

#### Q9 — Definition of Done for v0.1.0
> "What does a successful v0.1.0 look like? What would you demo to a user or stakeholder
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

### Phase C: Generate the Implementation Plan

Create `docs/v0.1.0/implementation-plan.md` following the structure below.

#### File Header

```markdown
# Implementation Plan — v0.1.0

**Project**: [Project Name]
**Version**: 0.1.0
**Created**: [Date]
**Goal**: [One-sentence definition of done from Q9]

## Overview

[2–3 paragraph summary covering: what is being built, how it will be distributed,
what the UI and runtime behavior look like, and what success looks like at v0.1.0.]

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | [Title] | [One-line outcome] |
| 2 | [Title] | [One-line outcome] |
| ... | ... | ... |
```

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

### Phase N Exit Checklist

- [ ] All sub-tasks completed
- [ ] All tests passing (unit, integration, and any phase-specific tests)
- [ ] No known regressions from prior phases
- [ ] Session history generated for this phase
- [ ] Ready to advance to Phase N+1
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
| Phase count | Target 4–8 phases for a v0.1.0 plan; very simple projects may have 3, complex ones up to 10 |

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

Create `docs/v0.1.0/` if it does not exist, then write `implementation-plan.md`
following the structure above.

### Step 5: Review and Confirm

Show the user the phases-at-a-glance table and ask:
- "Does this phase breakdown look right?"
- "Are there any features missing or phases you would reorder?"

Incorporate feedback, then write the final file.

---

## Quality Checklist

- [ ] All 11 discovery questions answered (Q11 may be skipped)
- [ ] Research performed for unfamiliar technical areas
- [ ] Every feature from Q2 appears in at least one sub-task
- [ ] Phase 1 establishes toolchain and produces a runnable build
- [ ] Installation/packaging step appears before the halfway point
- [ ] Every phase ends with a testing and stabilization sub-task
- [ ] Every sub-task has a complete, self-contained executable prompt
- [ ] Every phase has a stability gate and exit checklist
- [ ] File written to `docs/v0.1.0/implementation-plan.md`
- [ ] User confirmed the phase breakdown before final generation

## Related Skills

- `plan-before-code` - Lightweight planning for individual features within a phase
- `research-plan-implement` - Structured RPI workflow for a single complex feature
- `session-history` - Document each completed phase
- `test-driven-development` - Apply TDD within individual sub-tasks

---

**Version**: 1.0.0
**Last Updated**: April 2026
