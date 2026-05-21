---
description: Generate a comprehensive, phased plan through a guided discovery interview. Works for initial v0.1.0 builds, feature additions, enhancements, refactors, and any other multi-step workflow. Produces docs/<version>/plans/<slug>.md with phased sub-tasks and self-contained executable prompts.
---
# Generate Plan

Create a comprehensive, phased plan at `docs/<version>/plans/<slug>.md` through a structured discovery interview, then generate phased sub-tasks where every sub-task includes an executable prompt that can be run in a future Claude Code session.

This command works for initial v0.1.0 greenfield builds, feature additions, UX enhancements, refactors, bug-fix campaigns, and any other multi-step effort.

## How to Run This Command

- At the end of `/setup-project` (Phase 9 invokes it automatically for initial v0.1.0 plans)
- Standalone at any time: `/generate-plan`
- **From a comparison report**: `/generate-plan <path/to/comparison-*.md>` triggers *From-comparison mode* (Step 0.5) and pre-seeds the interview from the report's Adoption Plan section. Also reached automatically when `/compare-project` chains into this command.
- When the user asks to "create a plan", "build a roadmap", "plan this refactor", or similar

**Constitution-aware generation**: every plan written by this command includes a `## Constitution Check` section (between `## Overview` and `## Phases at a Glance`) and a `## Complexity Tracking` section near the end of the file. When a constitution file is found at `docs/<version>/constitution.md` (or `CONSTITUTION.md` at the repo root), the Constitution Check section enumerates each MUST principle with a PASS / FAIL / N/A verdict and a one-sentence justification. When no constitution file is found, the section emits an informational note recommending `/constitution` without blocking plan generation. Both behaviors are non-blocking by design - the constitution itself is opt-in, and a project that has not adopted one still gets a usable plan. See `[[project-constitution]]` for how the constitution is authored and amended.

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

## Step 0.5: From-Comparison Mode

**Trigger**: the command was invoked with a single positional argument whose path matches `**/comparison-*.md` (for example `/generate-plan docs/v0.9.7/comparison-shannon.md`). This mode is also reached when `/compare-project` Step 8 chains into `/generate-plan` and hands off the comparison path plus a scope filter.

**If the trigger is not met, skip this step entirely and proceed to Step 1.**

When triggered, this step overrides Step 0 defaults and short-circuits redundant parts of Step 1.

### 0.5a. Read and parse the comparison report

Read the comparison file at the supplied path. Parse the Adoption Plan section (Section 10 for repo/local reports; Section 5 for article reports) into a flat list of adoption items, each tagged with its tier (P0 / P1 / P2 / P3) and carrying its `What | Source | Target | Effort | Dependencies | Risk` columns.

If the file cannot be found or no adoption items can be parsed, fall back to the standard flow and announce the fallback:
> "Could not parse adoption items from `<path>` — proceeding with the standard discovery interview."

### 0.5b. Resolve the scope-tier filter

If the caller (e.g. `/compare-project` Step 8) handed off an explicit scope filter (`p0p1`, `p0p1p2`, or `all`), use it directly.

Otherwise, ask inline:
> "Which adoption scope should this plan cover?
> 1. P0 + P1 only (Critical + High)
> 2. P0 + P1 + P2 (through Medium)
> 3. All items (P0 + P1 + P2 + P3)"

Filter the parsed adoption items according to the selected tier. Items below the cutoff become the plan's *"explicitly out of scope"* section.

### 0.5c. Inherit version; derive slug and plan type

- **Version**: inherit from the comparison file's path (`docs/<version>/comparison-*.md`). Do not re-resolve from git tags — the comparison file is authoritative for the scope it represents, and its version may lag behind the current project version.
- **Slug (default)**: `adoption-<name>`, where `<name>` is the trailing segment of the comparison filename (e.g. `comparison-shannon.md` -> `adoption-shannon`).
- **Plan type (default)**: `2 — Feature/Enhancement` (adoption items are additive, neither greenfield nor pure refactor).

Confirm all three in a single consolidated question:
> "Proposed output: `docs/<version>/plans/adoption-<name>.md` as a Feature/Enhancement plan. Press Enter to accept, or reply with any override (different version, slug, or plan type)."

### 0.5d. Abbreviated discovery interview

Skip the interview questions already answered by the comparison report. Specifically, do **not** re-ask:

- **Q1 Goal** — derive as: *"Adopt `<scope-filter>` items from `<comparison-name>`"*
- **Q2 Scope In/Out** — in-scope items are the filtered Adoption Plan rows; out-of-scope items are the rows below the filter cutoff. State both explicitly in the generated plan.
- **Q3 Affected Areas** — derive from the `Target` column across the filtered items.
- **Q4 Constraints/Risks (partial)** — seed from the `Risk` column; still ask for any *additional* constraints not captured in the report.

Still ask (the report does not answer these):

- **Q5 Definition of Done** — observable success criteria for the adoption as a whole.
- **Q6 Testing Expectations** — what level of testing the adoption requires.
- **Additional constraints / timeline** — any deadline, ownership, or environmental constraint the report did not capture.

### 0.5e. Phase design seeded from adoption items

When the plan advances to Step 3 (*Design the Phase Breakdown*), group the filtered adoption items into phases by dependency order: P0 items and items with no `Dependencies` entry go to Phase 1; items that depend on earlier items - or sit in lower tiers - fill subsequent phases. Each adoption item (or tightly coupled cluster of items) becomes one sub-task whose *Objective* and *Prompt* draw directly from the report's `What`, `Source`, `Target`, `Effort`, and `Risk` columns.

### 0.5f. Reverse-engineer-first ordering (when flag is set)

`/compare-project` always passes `reverse-engineer-first=true` when chaining into this command (see the MCP Registry Policy in `AGENTS.md`). Manual invocations may also pass the flag. When set, Step 0.5e's dependency-ordered phase grouping is overlaid with the ordering from the comparison report's Section 9.4 (repo/local) or Section 6 (article) Security and Reverse-Engineering Assessment:

1. **Phase 1 contains `skill-native` items only** - zero-code skill replacements that ship immediately. These must come first because they close capability gaps without any code change.
2. **Phases 2-N contain `re-full` / `re-partial` items** - internal MCP or skill builds. Group by dependency and by target package (e.g. one phase per new package under `extensions/`). These are the largest phases and often include scaffolding sub-tasks (package layout, pyproject.toml, tests skeleton).
3. **Phases after the RE builds contain `vendor-intrinsic` items** - adoptions that introduce a trusted vendor wrapper. Each must carry the justification inline: `(a)` vendor is the intrinsic data destination, `(b)` cannot be reverse-engineered locally, `(c)` extremely worth it. Cite the MCP Registry Policy by name.
4. **`drop-outright` items DO NOT appear in the plan** - they go to an out-of-scope appendix titled **"Items explicitly NOT adopted (security / policy reasons)"** following the N-item convention (N1, N2, ...). Each entry cites the policy grounds for rejection.

The generated plan's Overview section must state: *"Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 / Section 6 of the source comparison for the ordering rationale."*

When the flag is NOT set (manual invocation with `/generate-plan <path>` not originating from `/compare-project`), ask the user:
> "This comparison report includes a Section 9 Security and Risk Assessment. Should the generated plan sequence phases in reverse-engineer-first order (recommended, matches the MCP Registry Policy default), or by P-tier only (legacy behavior)?"

Default to RE-first if the user declines to answer.

After completing Step 0.5, resume the standard flow at Step 0.6 (*Prior-Version Known-Gaps Ingest*).

---

## Step 0.6: Prior-Version Known-Gaps Ingest

**Always run this step**, regardless of whether Step 0.5 (From-comparison mode) executed. The goal is to surface any unfinished work, deferred items, bugs, warnings, or coverage gaps recorded by `/implement-phase` and `/wrap-up-session` during the previous version, so they are pulled forward into the new plan instead of being silently dropped.

This step applies the `known-gaps-tracker` skill in **Ingest mode**.

### 0.6a. Resolve the prior version

Determine the immediately previous semver from the version selected in Step 0b. Examples:

| New version | Prior version |
|---|---|
| `v0.2.0` | `v0.1.0` |
| `v1.1.0` | `v1.0.0` |
| `v0.1.1` | `v0.1.0` |

If the version selected in Step 0b is the project's **first** version (no prior tag and no prior `docs/v*` directory), skip directly to Step 1 — there is nothing to ingest.

### 0.6b. Build the candidate file list

Search for all of these files and aggregate the ones that exist:

1. `docs/<prior-version>/known-gaps.md` — always include if it exists, regardless of `Status`.
2. `docs/v*/known-gaps.md` for **any** older version where the file's `Status:` line is still `in-progress` — these are gaps that have lingered across more than one version and must not be dropped.

Skip any file whose `Status:` is `finalized` *and* that is not the immediately prior version.

### 0.6c. Parse and merge

Parse every candidate file. Merge their `## Open Items` sections into a single in-memory list, tagging each item with its originating version (e.g., `[v0.1.0:NI-2]`). Preserve the four fields per item: `Source phase`, `Plan reference`, `Reason`, `Suggested next step`.

If the merged list is empty, announce *"No open items found in prior known-gaps files; proceeding to the discovery interview."* and skip to Step 1.

### 0.6d. Present and ask

If the merged list is non-empty, show the user a compact summary grouped by originating version:

```
Found N open items from prior versions:

From v0.1.0 (finalized):
  [NI-2] Settings panel keyboard shortcuts not wired (Phase 4)
  [BG-1] Token refresh race condition (Phase 6)

From v0.0.5 (still in-progress):
  [MT-3] tests/integration/payment_flow.py below 60% coverage

How should I treat these in the new plan?
  A. Ingest all open items as scope (recommended)
  B. Pick a subset to ingest
  C. Skip - I will handle them outside this plan
```

Wait for the user's answer before continuing.

### 0.6e. Seed the discovery interview

Selected items become **inputs** to the rest of the plan-generation flow:

- **Q2 (Scope)**: pre-fill the in-scope list with the ingested items (the user can still edit).
- **Q3 (Affected Areas)**: union the `Plan reference` paths and any module names mentioned in `Reason` fields with whatever the user adds.
- **Step 3 (Phase Breakdown)**: each ingested item (or tightly-coupled cluster of items) becomes one sub-task. Tag the sub-task title with the prefix `[from <prior-version> known-gaps: <ID>]`. The sub-task `Prompt` block must restate the original `Reason` and `Suggested next step` so the executable prompt is self-contained.
- **Plan Overview**: state explicitly *"This plan ingests N item(s) carried forward from prior known-gaps files: see sub-tasks tagged `[from … known-gaps: …]`."*

### 0.6f. Update source files after writing the plan

After Step 4 successfully writes the new plan file, edit each ingested item in its source `known-gaps.md`:

- Move it from `## Open Items` to the `## Resolved` table.
- Set `Resolved in: transferred to <new-version> plan`.
- Recompute the Summary table counts in the source file.

The ingested items are *not yet fixed* — they have only been transferred to a different tracking surface (the new plan). Resolution happens later when the relevant sub-task is implemented and `/implement-phase` records it as resolved in the new version's own `known-gaps.md`.

After completing Step 0.6, proceed to Step 1 (or, if Step 0.5 ran, to Step 2 with the abbreviated discovery applied).

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

### Phase organization for user-story-driven plans

When the plan is feature-driven (plan type 2) AND a sibling `spec.md` exists with user stories authored against `catalog/templates/spec-template.md` (P1 / P2 / P3 priorities, FR-### / SC-### IDs), organize phases by user story so each user-story phase ships an independently testable MVP increment. Use the following fixed shape:

| Phase | Title | Story labels on tasks? | Purpose |
|-------|-------|-----------------------|---------|
| Phase 1 | **Setup** | No | Project initialization, scaffolding, toolchain, distribution pipeline smoke. Blocking prerequisites for every user story. |
| Phase 2 | **Foundational** | No | Cross-cutting building blocks shared by all user stories (database schema, auth middleware, base service layer, shared test harness). |
| Phase 3 | **User Story 1 (P1)** | `[US1]` on every task | First independently testable increment. Implementing only this phase delivers a viable MVP. |
| Phase 4 | **User Story 2 (P2)** | `[US2]` on every task | Second priority story. Builds on Phases 1-2 but does not block US1. |
| Phase N-1 | **User Story K (P3)** | `[USK]` on every task | Lowest-priority story. Subsequent priorities follow this same template. |
| Phase N | **Polish & Cross-Cutting Concerns** | No | Performance tuning, documentation polish, accessibility passes, observability, follow-up cleanups deferred during US phases. |

Within each user-story phase, sequence sub-tasks `Tests (if requested) -> Models -> Services -> Endpoints -> Integration` so the phase produces a vertical slice in dependency order. Cross-link the phase title back to the spec by appending `(implements <FR-IDs>, <SC-IDs>)` to the phase header when the user-story IDs map to specific Functional Requirements / Success Criteria.

When the plan is plan type 1 (initial greenfield), 3 (refactor), or 4 (other) - or feature-driven but **no** spec with user stories exists - skip the user-story phase shape and fall back to the 7 general rules above. The strict task-line format in Step 4 still applies in both cases; only the `[US#]` label is conditional on having user stories.

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

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[List each MUST principle from docs/<version>/constitution.md and state PASS / FAIL / N/A
per principle, with a one-sentence justification. If constitution.md does not exist, state
"No constitution file found at docs/<version>/constitution.md - skipping check. Recommend
running /constitution to establish project principles." - this is informational, not blocking.]

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

- [ ] T### [P?] [US?] [Description with exact file path, e.g. src/services/user_service.py]

**Objective**: [What this sub-task accomplishes.]

**Prompt**:
> [Complete, self-contained prompt the user can paste into a new Claude Code session.
> Includes: goal, specific files/dirs to create or modify, acceptance criteria,
> constraints. Must be actionable without reading the rest of this document.]

---

#### N.2 — [Sub-task Title]

- [ ] T### [P?] [US?] [Description with exact file path]

**Objective**: [...]

**Prompt**:
> [Complete executable prompt.]

---

[... additional sub-tasks ...]

---

#### N.X — Testing and Stabilization

- [ ] T### Run and stabilize Phase N tests

**Objective**: Generate and run all tests for this phase. Iterate until stable.

**Prompt**:
> Generate comprehensive tests for everything built in Phase N. Include [list relevant
> test types: unit, integration, E2E, performance benchmarks, CI configuration].
> Run the tests, fix all failures, and iterate until every test passes.
> Do not advance to Phase N+1 until this phase is fully verified.
> After all tests pass, run /generate-session-history to document Phase N.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |

---

### Phase N Exit Checklist

- [ ] All sub-tasks completed
- [ ] All tests passing
- [ ] No known regressions from prior phases
- [ ] Session history generated for this phase
- [ ] Ready to advance to Phase N+1
```

### Task line format (required for every sub-task)

Every sub-task MUST begin with a single Markdown checkbox line immediately after the `#### N.M — [Sub-task Title]` heading and before the `**Objective**:` line. This line is the summary line for downstream tooling (the strict-format grep validator in Step 5, `/analyze-spec` coverage matrix, `/tasks-to-issues` conversion); the existing executable `**Prompt**:` block underneath remains the actionable detail and is never replaced by the summary line.

Task line components (in left-to-right order):

1. **Checkbox**: ALWAYS start with `- [ ]` (an unchecked Markdown checkbox followed by exactly one space).
2. **Task ID**: Sequential `T001`, `T002`, ..., counted across the entire plan in execution order (not reset per phase). Pad to at least three digits; four digits (`T1234`) are allowed once a plan exceeds 999 tasks. IDs MUST be globally unique within a single plan file.
3. **`[P]` parallel marker**: Include ONLY when the task is safely parallelizable - it touches different files than every other task lacking a dependency on it and depends on no incomplete task. Omit otherwise. The marker is exactly `[P]` (capital P, square brackets, single space on either side).
4. **`[US#]` story label**: REQUIRED for every task whose containing phase is a User-Story phase from the Step 3 organization table. Format is `[US1]`, `[US2]`, `[US3]`, ... mapping to the corresponding `### User Story N` heading in the sibling `spec.md` (priority order from the spec template: US1 = P1, US2 = P2, ...). Setup, Foundational, and Polish phases MUST omit the story label. When both `[P]` and `[US#]` apply, `[P]` precedes `[US#]`.
5. **Description**: Clear imperative action followed by the exact file path the task creates or modifies. Use forward slashes for path separators (`src/models/user.py`, not `src\models\user.py`) for cross-platform consistency. When a task touches multiple files, name the primary file in the description and list the rest in the underlying executable prompt.

#### Examples

Correct - Setup phase task (no story label):

```
- [ ] T001 Create project structure per implementation plan
```

Correct - Foundational phase task with parallel marker (no story label):

```
- [ ] T005 [P] Implement authentication middleware in src/middleware/auth.py
```

Correct - User Story 1 phase task with both parallel marker and story label:

```
- [ ] T012 [P] [US1] Create User model in src/models/user.py
```

Correct - User Story 1 phase task with story label but no parallel marker (depends on T012):

```
- [ ] T014 [US1] Implement UserService in src/services/user_service.py
```

Correct - Polish phase task (no story label):

```
- [ ] T042 Add release notes section to CHANGELOG.md
```

#### Anti-patterns

These all fail Step 5 format validation:

- `[ ] T001 ...` - missing the leading `- ` hyphen-space
- `- [ ] 001 ...` - missing the `T` prefix on the task ID
- `- [ ] T01 ...` - task ID under three digits
- `- [ ] T001 [US1] Create User model` (Setup phase) - story label on a non-user-story phase
- `- [ ] T012 Create User model in src/models/user.py` (User Story 1 phase) - missing required `[US1]` label
- `- [ ] T012 [US1] [P] Create User model in src/models/user.py` - marker order reversed (`[P]` must precede `[US#]`)
- `- [ ] T012 [US1] Create User model` - missing exact file path in description

### Constitution Check + Complexity Tracking (required sections)

Every generated plan MUST include both sections shown in the file-format template above:

1. **Constitution Check** - inserted between `## Overview` and `## Phases at a Glance`. Resolution rules:
    - Look for a constitution file in this order: `docs/<version>/constitution.md`, then `CONSTITUTION.md` at the repo root.
    - **If found**: parse the file's `## Principles` section; for each principle marked MUST (or stated as a MUST clause in its `**Statement**:` line), emit one bullet `- **<Principle ID> <Title>**: PASS | FAIL | N/A - <one-sentence justification tied to the plan's scope>`. `N/A` is correct when the principle does not apply to the plan's scope (e.g., a UX-only principle on a backend-only refactor); `FAIL` requires a corresponding row in the Complexity Tracking table.
    - **If not found**: emit the informational note verbatim - `No constitution file found at docs/<version>/constitution.md - skipping check. Recommend running /constitution to establish project principles.` - and do not block plan generation.
    - The check is opt-in by design; the gate's purpose is to surface principle alignment, not to halt planning when a project has not yet ratified principles.
    - The header line `*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*` is required verbatim so downstream tooling (`/analyze-spec`, code review) can locate the gate.

2. **Complexity Tracking** - inserted near the end of the file, between the last phase's `## Phase N: Testing and Stabilization` block (or the final phase content) and that phase's `### Phase N Exit Checklist`. Resolution rules:
    - When every Constitution Check bullet is PASS or N/A, leave the table empty (keep the header, the blockquote rationale, and the column headers; the example row may be removed). Future amendments can populate it without reshaping the section.
    - When any Constitution Check bullet is FAIL, every failing principle MUST have a corresponding row that states the violation, why it is needed, and why the simpler alternative was rejected.

Treat both sections as part of the plan's contract with `[[project-constitution]]` and `/analyze-spec` - they are not optional adornment.

### Spec-quality-checklist companion (feature-level plans only)

When the plan being generated is **plan type 2** (feature addition or enhancement) AND a `spec.md` exists in the same directory as the plan output (`docs/<version>/plans/` for the default layout, or `specs/<NNN>-<slug>/` for the opt-in layout from Phase 7 of the adoption-spec-kit plan), write a companion checklist alongside the plan:

1. Resolve the target directory:
    - Default layout: `docs/<version>/plans/<slug>/checklists/requirements.md` (a `<slug>` subdirectory under `plans/` is acceptable when the plan needs a directory companion).
    - `specs/<NNN>-<slug>/` layout: `specs/<NNN>-<slug>/checklists/requirements.md`.
2. Copy the contents of `catalog/templates/spec-quality-checklist.md` (installed at `~/.nexus-hub/templates/spec-quality-checklist.md`) into the resolved path. Replace `[FEATURE NAME]` with the plan title, `[DATE]` with today's UTC date, and `[Link to spec.md]` with a relative link to the sibling `spec.md`.
3. If a checklist file already exists at the target path, do not overwrite. Announce: `Spec-quality-checklist already exists at <path> - leaving in place. Re-run /clarify-spec or edit the checklist directly to refresh.`
4. Tell the user the checklist was written and recommend the next step:
    - If unchecked items remain after the user reviews: run `/clarify-spec` to resolve them.
    - If all items pass: run `/analyze-spec` to verify cross-artifact coverage, then `/implement-phase <slug> phase-1`.

Skip the checklist companion entirely for plan types 1 (initial greenfield build), 3 (refactor), and 4 (other) - the checklist's value is feature-spec quality validation, and those plan types do not produce a feature spec. The Constitution Check section above is still emitted for all plan types.

---

## Step 5: Confirm with the User

After writing the file, run the **Task Format Validation** pass below before reporting to the user. If the pass surfaces any violations, fix them in-place (re-numbering, adding missing labels, normalizing marker order) and re-run the validator. Do not announce the plan to the user until the validator reports zero violations.

### Task Format Validation

Read the freshly written plan file and identify every task line. A task line is any line that starts with `- [ ]` followed by a `T###` token; the closing-checklist lines (Phase N Exit Checklist) and template placeholders do not count.

For each task line, verify the regex `^- \[ \] T[0-9]{3,}( \[P\])?( \[US[0-9]+\])? .+$` matches. Additionally verify:

- Task IDs are sequential starting at `T001` with no gaps and no duplicates across the entire plan.
- Story labels appear **only** on tasks inside User-Story phases as defined by the Step 3 organization table. Tasks inside Setup, Foundational, and Polish phases MUST NOT carry a `[US#]` label.
- Every task inside a User-Story phase carries the matching `[US#]` label (US1 for Phase 3 in the canonical shape, US2 for Phase 4, ...).
- When both markers appear on the same task, `[P]` precedes `[US#]`.
- Every description contains at least one path-like token (heuristic: a substring matching `[\w./-]+\.[\w]+` or referencing a known directory such as `src/`, `tests/`, `docs/`, `catalog/`). Tasks that legitimately have no file (e.g., "Run `/generate-session-history` to document Phase N") are allowed when they sit in the Testing and Stabilization sub-task.

Emit a one-line summary back to your working context: `Task format validation: <N> tasks total, <M> with [P] marker, <K> mapped to user stories. ALL tasks match the required format.` When violations are detected instead, list each violating line with its line number and the specific rule it broke, then fix in-place and re-run. Hard cap at three repair iterations; if violations persist after three iterations, surface the remaining offenders to the user and ask whether to relax a specific rule.

### Report to the user

After validation passes, tell the user:
- Where the file was saved (`docs/<version>/plans/<slug>.md`)
- How many phases and sub-tasks were generated
- Task format counts from the validation summary above (total tasks, parallelizable tasks, user-story-mapped tasks)
- How to begin: run `/implement-phase <slug>` (or paste the prompt from sub-task 1.1 into a fresh Claude Code session)

---

## Guidelines

- Keep each sub-task prompt self-contained — a user should be able to copy it directly into a fresh session without needing additional context
- Use websearch freely for any technical areas that need research
- If `docs/<version>/plans/<slug>.md` already exists, ask the user: **Regenerate** (overwrite), **Append** (add phases), or **Rename** (pick a new slug) before proceeding
- Report progress to the user after the interview, after the phase design confirmation, and after writing the file
