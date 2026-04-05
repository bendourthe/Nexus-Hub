---
description: Generate a comprehensive v0.1.0 implementation plan through a guided discovery interview. Asks targeted questions about features, distribution, UI, platform, behavior, integrations, performance, and testing. Produces docs/v0.1.0/implementation-plan.md with phased sub-tasks and self-contained executable prompts.
---
# Generate Implementation Plan

Create a comprehensive `docs/v0.1.0/implementation-plan.md` through a structured
discovery interview, then generate a phased plan where every sub-task includes an
executable prompt that can be run in a future Claude Code session.

## How to Run This Command

This command can be run:
- At the end of `/setup-project` (Phase 9 invokes it automatically)
- Standalone at any time: `/generate-implementation-plan`
- When the user asks to "create a plan", "build a roadmap", or "generate an implementation plan"

---

## Step 1: Discovery Interview

Ask the following questions **one at a time**, waiting for the user's answer before
moving to the next question. Do not bundle multiple questions in a single message.

### Q1 — Core Purpose
Ask: "What is the core purpose of this application? What problem does it solve, and for whom?"

### Q2 — Key Features for v0.1.0
Ask: "What are the 5–10 key features or capabilities you want in v0.1.0? Bullet points are fine."

### Q3 — Installation and Distribution
Ask: "How should users install or access the final product?
(e.g., .exe / .dmg / .deb installer, pip / npm / cargo package, VS Code extension,
Docker container, web app, CLI from GitHub Releases, desktop GUI app)"

### Q4 — User Interface
Ask: "What kind of user interface does this need?
(e.g., command-line CLI, desktop GUI, web UI, IDE extension, TUI, or no UI — background service / API only)"

### Q5 — Platform Support
Ask: "Which platforms need to be supported?
(e.g., Windows only, macOS only, Linux only, all three, web / browser, mobile)"

### Q6 — Runtime Behavior
Ask: "How should the app behave at runtime?
(e.g., always-on daemon / service, on-demand CLI, event-driven, real-time streaming, scheduled jobs, interactive REPL)"

### Q7 — Integrations and External Dependencies
Ask: "What external services, APIs, models, or tools does it need to integrate with?
(e.g., LLM providers, local AI models, databases, cloud storage, auth providers, OS APIs)"

### Q8 — Performance and Resource Constraints
Ask: "Are there performance, scale, or hardware constraints?
(e.g., must run on 8 GB RAM, sub-200 ms response time, support N concurrent users, offline only — or none)"

### Q9 — Definition of Done for v0.1.0
Ask: "What does a successful v0.1.0 look like? What would you demo to prove it works end-to-end?"

### Q10 — Testing and Quality Expectations
Ask: "What level of testing do you want?
(e.g., unit tests only, CI/CD with integration and E2E tests, performance benchmarks, security audit, manual QA checklist)"

### Q11 — Additional Context (Optional)
Ask: "Anything else I should know — architectural preferences, reference projects, libraries to use or avoid, constraints? (Press Enter to skip)"

---

## Step 2: Research

After collecting all answers, identify any technical areas where the best approach is
unclear (packaging format, framework selection, local model integration, installer
toolchain, etc.). Run websearch queries to fill knowledge gaps before writing the plan.

---

## Step 3: Design the Phase Breakdown

Before writing the file, plan the phases:

1. **Phase 1 is always Foundation**: project scaffolding, toolchain, and a minimal
   working build that proves the distribution pipeline end-to-end.
2. **One concern per phase**: each phase delivers one coherent, independently testable
   capability.
3. **Installation early**: packaging/installer appears in the first third of the plan.
4. **UI and backend separated**: if there is a UI, it gets its own phase.
5. **Integration phase**: external APIs or local models get a dedicated phase with
   mocking strategies for earlier phases.
6. **Every feature appears**: every feature from Q2 must be covered by at least one sub-task.
7. **Phase count**: 4–8 phases for most v0.1.0 plans.

Show the user the proposed phases-at-a-glance table and ask for confirmation or changes
before writing the full plan.

---

## Step 4: Generate `docs/v0.1.0/implementation-plan.md`

Create the directory `docs/v0.1.0/` if it does not exist.

Write the plan using the structure below.

### File Format

```
# Implementation Plan — v0.1.0

**Project**: [Project Name]
**Version**: 0.1.0
**Created**: [Today's date]
**Goal**: [One-sentence definition of done from Q9]

## Overview

[2–3 paragraphs covering what is being built, how it will be distributed,
what the UI and runtime behavior look like, and what success looks like at v0.1.0.]

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1     | ...   | ...     |
...

---

## Phase N: [Phase Title]

**Goal**: [One sentence.]
**Prerequisites**: [Prior phases required, or "None".]
**Stability Gate**: [Observable condition proving the phase is complete and stable.]

### Sub-tasks

#### N.1 — [Sub-task Title]

**Objective**: [What this sub-task accomplishes.]

**Prompt**:
> [Complete, self-contained prompt the user can paste into a new Claude Code session.
> Includes: goal, specific files/dirs to create or modify, acceptance criteria,
> constraints. Must be actionable without reading the rest of this document.]

---

#### N.2 — [Sub-task Title]

**Objective**: [...]

**Prompt**:
> [Complete executable prompt.]

---

[... additional sub-tasks ...]

---

#### N.X — Testing and Stabilization

**Objective**: Generate and run all tests for this phase. Iterate until stable.

**Prompt**:
> Generate comprehensive tests for everything built in Phase N. Include [list relevant
> test types: unit, integration, E2E, performance benchmarks, CI configuration].
> Run the tests, fix all failures, and iterate until every test passes.
> Do not advance to Phase N+1 until this phase is fully verified.
> After all tests pass, run /generate-session-history to document Phase N.

---

### Phase N Exit Checklist

- [ ] All sub-tasks completed
- [ ] All tests passing
- [ ] No known regressions from prior phases
- [ ] Session history generated for this phase
- [ ] Ready to advance to Phase N+1
```

---

## Step 5: Confirm with the User

After writing the file, tell the user:
- Where the file was saved (`docs/v0.1.0/implementation-plan.md`)
- How many phases and sub-tasks were generated
- How to begin: open a new Claude Code session, open the plan, and paste the prompt
  from sub-task 1.1 to start Phase 1

---

## Guidelines

- Keep each sub-task prompt self-contained — a user should be able to copy it directly
  into a fresh session without needing additional context
- Use websearch freely for any technical areas that need research
- If the project already has `docs/v0.1.0/implementation-plan.md`, ask the user:
  **Regenerate** (overwrite) or **Append** (add phases) before proceeding
- Report progress to the user after the interview, after the phase design confirmation,
  and after writing the file
