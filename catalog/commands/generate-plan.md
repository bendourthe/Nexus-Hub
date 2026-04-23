---
description: Generate a comprehensive, phased plan through a guided discovery interview. Works for initial v0.1.0 builds, feature additions, enhancements, refactors, and any other multi-step workflow. Produces docs/<version>/plans/<slug>.md with phased sub-tasks and self-contained executable prompts.
---
# Generate Plan

Create a comprehensive, phased plan at `docs/<version>/plans/<slug>.md` through a structured discovery interview, then generate phased sub-tasks where every sub-task includes an executable prompt that can be run in a future Claude Code session.

This command works for initial v0.1.0 greenfield builds, feature additions, UX enhancements, refactors, bug-fix campaigns, and any other multi-step effort.

## How to Run This Command

- At the end of `/setup-project` (Phase 9 invokes it automatically for initial v0.1.0 plans)
- Standalone at any time: `/generate-plan`
- Former name `/generate-implementation-plan` still works as a deprecation alias
- When the user asks to "create a plan", "build a roadmap", "plan this refactor", or similar

---

## Step 0: Resolve Plan Type, Version, and Slug

Before the discovery interview, establish three things: what kind of plan this is, which version folder it belongs in, and what filename to use. Do not skip this step — it determines the output path.

### 0a. Plan Type

Ask: "What kind of plan are we building?

1. Initial project implementation (v0.1.0-style greenfield build)
2. Feature addition or enhancement
3. Refactor or technical-debt reduction
4. Other (describe in one sentence)"

The answer routes the Step 1 question set.

### 0b. Version Resolution

Determine the target version in this order:

1. Most recent git tag: `git tag --sort=-v:refname | head -n 1`
2. `CHANGELOG.md` most recent version heading (e.g. `## [0.9.7]`)
3. `package.json` `version`, `pyproject.toml`, `Cargo.toml`, or a root `VERSION` file
4. For plan type **1** (initial greenfield build) with no version found: default to `v0.1.0`
5. Otherwise ask the user explicitly; use `vUnknown` only on explicit user confirmation

Show the detected version and source, and ask:
> "Writing this plan under `docs/<version>/plans/`. Is that correct, or would you like a different version folder?"

Accept any `v`-prefixed or bare semver string. Normalize to the `v` prefix form (e.g. `0.2.0` → `v0.2.0`).

### 0c. One-Sentence Scope Statement

Before asking the full discovery questions, ask:
> "In one sentence, what is this plan about? (e.g. 'Enhance the UX of the settings panel', 'Integrate Stripe for subscription payments', 'Build the v0.1.0 CLI')"

This sentence will be used to derive the filename slug and also anchors the rest of the interview.

### 0d. Slug Derivation

From the one-sentence answer, derive a slug:

- Lowercase; hyphen-separated; sanitized to `[a-z0-9-]+`
- Keep noun phrases and key verbs; drop stopwords (`the`, `a`, `of`, `for`, `to`, `and`, `on`, `with`, etc.)
- Cap at ~5 words

Examples:

| One-sentence answer | Suggested slug |
|---|---|
| "Build the initial v0.1.0 of the dashboard app" | `v0.1.0-initial` |
| "Enhance the UX of the settings panel" | `settings-panel-ux` |
| "Integrate Stripe for subscription payments" | `stripe-subscription-integration` |
| "Refactor auth module to use JWT" | `auth-jwt-refactor` |
| "Fix the P0 bugs surfaced in the Q2 review" | `q2-review-bug-fixes` |

Show:
> "Suggested filename: `docs/<version>/plans/<slug>.md` — press Enter to accept, or type a new slug."

Rules:
- Reject empty or whitespace-only slugs and re-prompt
- Sanitize user overrides to `[a-z0-9-]+` (lowercase; spaces and underscores become hyphens; other characters are dropped)
- If `docs/<version>/plans/<slug>.md` already exists, propose `<slug>-2`, `<slug>-3`, ... or ask whether to overwrite
- Reserved slugs to reject: `index`, `readme`, `template`

---

## Step 1: Discovery Interview

Route on plan type from Step 0a. Ask questions **one at a time**, waiting for each answer before moving on. Do not batch multiple questions in a single message.

### Plan Type 1 — Initial Implementation

Use the full greenfield question set.

#### Q1 — Core Purpose
"What is the core purpose of this application? What problem does it solve, and for whom?"

#### Q2 — Key Features for this Release
"What are the 5–10 key features or capabilities you want in this release? (Bullet points are fine.)"

#### Q3 — Installation and Distribution
"How should users install or access the final product? (e.g., .exe / .dmg / .deb installer, pip / npm / cargo package, VS Code extension, Docker container, web app, CLI from GitHub Releases, desktop GUI app)"

#### Q4 — User Interface
"What kind of user interface does this need? (e.g., command-line CLI, desktop GUI, web UI, IDE extension, TUI, or no UI — background service / API only)"

#### Q5 — Platform Support
"Which platforms need to be supported? (e.g., Windows only, macOS only, Linux only, all three, web / browser, mobile)"

#### Q6 — Runtime Behavior
"How should the app behave at runtime? (e.g., always-on daemon / service, on-demand CLI, event-driven, real-time streaming, scheduled jobs, interactive REPL)"

#### Q7 — Integrations and External Dependencies
"What external services, APIs, models, or tools does it need to integrate with? (e.g., LLM providers, local AI models, databases, cloud storage, auth providers, OS APIs)"

#### Q8 — Performance and Resource Constraints
"Are there performance, scale, or hardware constraints? (e.g., must run on 8 GB RAM, sub-200 ms response time, support N concurrent users, offline only — or none)"

#### Q9 — Definition of Done
"What does successful delivery of this scope look like? What would you demo to prove it works end-to-end?"

#### Q10 — Testing and Quality Expectations
"What level of testing do you want? (e.g., unit tests only, CI/CD with integration and E2E tests, performance benchmarks, security audit, manual QA checklist)"

#### Q11 — Additional Context (Optional)
"Anything else I should know — architectural preferences, reference projects, libraries to use or avoid, constraints? (Press Enter to skip)"

### Plan Types 2, 3, 4 — Enhancement, Refactor, Other

Use the shorter, scope-focused question set.

#### Q1 — Goal
"What are we trying to accomplish with this plan? What problem are we solving, and for whom?"

#### Q2 — Scope In and Out
"What is explicitly in scope? What is explicitly out of scope? Be specific — this prevents drift during execution."

#### Q3 — Affected Areas
"Which modules, files, services, or user flows will this touch? List concrete paths if known."

#### Q4 — Constraints and Risks
"Any constraints or risks to keep in mind? (e.g., backwards compatibility, timelines, ownership, dependencies, open bugs blocking the work)"

#### Q5 — Definition of Done
"What does success look like? How will we know the plan has been fully executed — observable outcomes, acceptance tests, demo scenarios?"

#### Q6 — Testing Expectations
"What level of testing is needed? (e.g., unit, integration, manual QA, performance regression, security re-audit)"

#### Q7 — Additional Context (Optional)
"Anything else worth capturing — architectural preferences, prior art, things to avoid? (Press Enter to skip)"

---

## Step 2: Research (if needed)

After collecting answers, identify technical areas where the best approach is unclear (packaging format, framework selection, library choice, migration strategy, etc.). Run websearch queries to fill knowledge gaps before writing the plan.

---

## Step 3: Design the Phase Breakdown

Before writing the file, plan the phases:

1. **Phase 1 is the foundation**. For initial builds: scaffolding, toolchain, and a minimal working build that proves the distribution pipeline end-to-end. For enhancements/refactors: any setup, test harness, or scaffolding needed to safely execute subsequent phases.
2. **One concern per phase**: each phase delivers one coherent, independently testable capability.
3. **Installation / rollout early**: for initial builds, packaging appears in the first third. For enhancements, any feature-flagging or rollout mechanism appears early.
4. **UI and backend separated**: if there is a UI change, it gets its own phase.
5. **Integration phase**: external APIs or model integrations get a dedicated phase with mocking strategies for earlier phases.
6. **Every goal appears**: every feature or requirement from Step 1 must be covered by at least one sub-task.
7. **Phase count**: 4–8 phases for most plans; very small scopes may be 2–3; major refactors up to 10.

Show the user the proposed phases-at-a-glance table and ask for confirmation or changes before writing the full plan.

---

## Step 4: Generate the Plan File

Create the directory `docs/<version>/plans/` if it does not exist. Write the plan to `docs/<version>/plans/<slug>.md`.

### File Format

```
# Plan — [Plan Title]

**Project**: [Project Name]
**Version**: [version]
**Slug**: [slug]
**Plan Type**: [Initial Implementation / Feature / Refactor / Other]
**Created**: [Today's date]
**Goal**: [One-sentence definition of done from the discovery interview]

## Overview

[2–3 paragraphs covering what is being built or changed, how it will be delivered,
what the UI and runtime impact look like, and what success looks like.]

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
- Where the file was saved (`docs/<version>/plans/<slug>.md`)
- How many phases and sub-tasks were generated
- How to begin: run `/implement-phase <slug>` (or paste the prompt from sub-task 1.1 into a fresh Claude Code session)

---

## Guidelines

- Keep each sub-task prompt self-contained — a user should be able to copy it directly into a fresh session without needing additional context
- Use websearch freely for any technical areas that need research
- If `docs/<version>/plans/<slug>.md` already exists, ask the user: **Regenerate** (overwrite), **Append** (add phases), or **Rename** (pick a new slug) before proceeding
- Report progress to the user after the interview, after the phase design confirmation, and after writing the file
