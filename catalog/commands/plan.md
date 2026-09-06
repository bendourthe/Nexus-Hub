---
description: Define goals and produce a robust, phased plan. Use to plan a build, feature, enhancement, refactor, or any multi-step effort; to fix a goal and definition-of-done before decomposing; to bootstrap docs/todos.md; or to fan a plan's tasks out to GitHub issues. Trigger phrases - "make a plan", "plan this feature", "build a roadmap", "plan this refactor", "what are the goals", "define the goal", "create todos", "file issues from the plan", "plan from this comparison". SKIP - implementing a phase that already has a plan (use /implement), or one-off task lists with no phasing.
---

# /plan Command

Define the goal and produce a robust, phased plan. `/plan` is the merge point of three lineages - phased planning (`generate-plan`), goal-setting (`product-strategy` + plan-mode goals), and at-scale orchestration (dynamic workflows) - so it is robust by default and workflow-accelerated when available. It works for greenfield builds, feature additions, enhancements, refactors, bug-fix campaigns, and any other multi-step effort.

This is a thin dispatcher over the retained planning skills, following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). Heavy logic stays in the skills; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `goals`, `new`, `feature`, `refactor`, `from-comparison`, `todos`, `issues`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- `/plan goals <one-liner>` accepts an inline goal (Codex `/plan <inline>` style): return a crisp goal statement + definition-of-done, no full plan.
- `/plan from-comparison <path>` or a bare `*.md` comparison-report path routes to `from-comparison` and pre-seeds from the report's Adoption Plan. The generated plan is written into the SAME version directory as its seeding comparison, driven by the comparison's `Adoption target: vX.Y.Z` field (not a freshly-resolved in-flight version), so a comparison and the plan it seeds always live together; the `[[implementation-plan]]` skill owns the resolution and its legacy-comparison fallback.
- Otherwise, present this menu and wait for a selection:

      What scope?
        1. feature        (recommended) - plan a feature or enhancement on an existing project
        2. goals          - fix the target problem, persona, and definition-of-done only
        3. new            - greenfield v0.1.0 build (full discovery interview)
        4. refactor       - plan a refactor or cleanup campaign
        5. from-comparison - seed a plan from a /compare adoption report (RE-first ordering)
        6. todos          - bootstrap docs/todos.md as a living progress tracker
        7. issues         - fan a plan's / tasks.md task lines out to GitHub issues

      Reply with a number or a scope name.

## Goals-first step (every planning scope)

Before decomposition, every scope except `todos` and `issues` runs a goals-first step seeded from the `product-strategy` STRATEGY anchor: fix the target problem, the persona, and an observable definition-of-done. A detailed plan for the wrong objective is the most common planning failure, and this step prevents it. The `goals` scope runs only this step and stops; `/plan goals <one-liner>` does it inline.

## Optional dynamic-workflow robustness (graceful degradation, REQUIRED)

When dynamic workflows are available in the harness, `/plan` can use them as a quality mechanism, not just for speed. This path is always opt-in and never assumed present:

- **Detect availability** first. Dynamic workflows are a plan-gated research-preview feature (Pro / Max / Team / Enterprise, Claude Code v2.1.154+, toggleable in `/config`). If they are off or unavailable, fall back to single-agent planning silently and continue - never hard-depend on them.
- **Multi-angle drafting** (offer for large or high-stakes plans): draft the plan from several independent angles (MVP-first, risk-first, architecture-first), have independent agents adversarially weigh them, and synthesize the strongest.
- **Parallel research at scale**: fan research out across sources and subsystems concurrently, keeping intermediates off the planning context and returning only the converged grounding.
- **Workflow-aware phase prompts**: when a generated phase is a large fan-out task (audit every endpoint, migrate N files, generate tests for every unit), write that phase's executable prompt to recommend dynamic-workflow execution and cross-link `[[agent-orchestration-primitives]]`.
- Always present the workflow path with the scope-first token caution: calibrate on a small slice before fanning out across the whole surface. This carries zero new outbound calls, dependencies, or credentials - dynamic workflows are an Anthropic-runtime feature, so this is command behavior plus skill-native guidance.

## Per-phase tier assessment and current model map

After the phase breakdown is designed and before the plan file is written, `/plan` records generic capability intent for each phase and builds a portable provider lookup:

- **Assess each phase once.** Invoke `[[model-routing]]` for every phase and map the complexity rubric to `frontier`, `strong`, `standard`, or `fast`, plus `low`, `medium`, `high`, or `max` effort. Any uncertainty or high-risk signal defaults to `frontier` with high/max effort (the no-degradation guarantee).
- **Keep phase rows generic.** Write only `Recommended model tier` and `Recommended effort level` in the glance table. Repeat them in separate per-phase fields with a one-line `Rationale`. Concrete provider model ids never become authoritative phase recommendations.
- **Refresh every provider on every invocation.** Use web search and official documentation to populate a candidate map with the current Anthropic, OpenAI, Google, and Cursor model for each tier. Validate and render that candidate through `model-routing/scripts/model-map.{sh,ps1}` before writing `## Current model map`. Host-platform enumeration may validate the current picker, but it MUST NOT limit the plan to the host provider.
- **Cite and date the map.** A fresh plan records `**Model map status**: fresh as of YYYY-MM-DD; sources cited below.` and at least one official URL per provider under `### Model map sources`.
- **Degrade visibly.** When web access is unavailable, run the helper's `fallback` command, which validates and renders the dated bundled `last-known-model-map.json` snapshot as `offline fallback; stale as of YYYY-MM-DD.`. If that snapshot is absent or invalid, run `unavailable`, fill every map cell with `assess at implementation time`, and mark the map unavailable. The plan remains valid, but never hides staleness.

Web search uses public documentation and adds no new credential or dependency. The retained planning skill owns the exact table and fallback grammar; `[[model-routing]]` owns scoring plus map validation/rendering; `/implement` re-confirms the generic tier and effort against a refreshed map and the selected provider's live platform surface.

## Mandatory final phase (planning scopes)

Every plan ends with a fail-closed last phase - "Architecture Refactor, Known-Gaps Reconciliation, and CI/CD" - that includes independent Goal-vs-codebase review, a last-phase evidence file, and the living handbook architecture check. Automated tests still end every phase; human/manual testing suggestions wait until that last phase. New plans are written to the current version dir. This is part of the plan contract, not a dispatcher responsibility: the template and the duties live in the `[[implementation-plan]]` skill. This dispatcher only surfaces the guarantee; it does not duplicate the template.

## Plan lifecycle (guarantee)

Every generated plan carries the same lifecycle, and it is worth stating up front because it changes what the reader should expect while the plan runs:

- **Every phase verifies locally and ends with one local commit.** Lint, tests, coverage, documentation, session history, then a single commit scoped to that phase.
- **No non-final phase pushes.** A non-final phase does not push, does not open a pull request, and does not start remote CI. Running the pipeline once per phase bills for validating work the author already knows is incomplete, and a red check on incomplete work teaches the reader to ignore red checks.
- **CI impact is recorded per phase; the pipeline is reconciled once.** Each phase names what it added that CI would need to know about (a command, a dependency, an environment variable, a test path, an artifact) and whether the pipeline already covers it. Pipeline files change mid-plan only when CI/CD is that phase's explicit deliverable.
- **The final phase owns the terminal reconciliation.** It compares the repository's existing pipeline against the canonical contract via `[[cicd-architect]]`, proposes each difference with its cost, applies what the user approves, and records what the user declines as a known gap.
- **The final phase owns publication.** One branch push, with explicit approval, then the integration pull request, which is the plan's first remote validation and runs against the merge result. A red required check reopens the final phase.
- **Release work waits for green integration.** `/update release` starts only after the integration result is green and merged.

The full templates, prompts, and exit checklists that enforce this live in `[[implementation-plan]]`; the pipeline half lives in `[[cicd-architect]]`. This dispatcher states the guarantee and stops there.

## Unicode hygiene of the written plan (guarantee)

Every plan file this command writes is sanitized before it is presented: the retained skill's Step 4 closing pass runs `python scripts/validate_unicode_safety.py --strict --fix --root . --path <plan-file>` on the just-written file (and again on the final file when Step 5 rewrites it), so invisible characters and non-ASCII punctuation never reach a plan the user reads. The pass is scoped to that one file, never the repository, and a non-zero exit after the fix blocks presenting the plan. This dispatcher only surfaces the guarantee; the rules live in the `[[implementation-plan]]` skill.

## Presenting the finished plan

Present the plan the way `catalog/style-guides/agent-communication.md` requires: lead with a plain-language summary (what the plan builds, how many phases, and which single phase carries the most risk) BEFORE the phases-at-a-glance table, then link the plan file rather than restating its contents in chat. The detail already lives in the file; a chat message that repeats it makes the reader choose between two copies. Skill: `[[agent-communication]]`.

## Delegation

Dispatch the resolved scope to the retained skill(s):

      goals            -> product-strategy (goal + DoD), no full plan
      new              -> generate-plan (greenfield discovery interview)
      feature          -> generate-plan (feature/enhancement interview) + implementation-plan
      refactor         -> generate-plan (refactor interview)
      from-comparison  -> generate-plan (from-comparison mode, RE-first ordering)
      todos            -> generate-todos (bootstrap docs/todos.md)
      issues           -> tasks-to-issues (fan tasks.md -> GitHub issues via gh)

For the planning scopes, `generate-plan` preserves everything it always did: the guided discovery interview, prior-version known-gaps ingest, knowledge-base + strategy grounding, the Constitution Check + Complexity Tracking gates, and the strict `T###` task-line file-format contract. Pass any remaining arguments through unchanged.

## Notes

- This command replaces `/generate-plan`, `/generate-todos`, and `/tasks-to-issues` (removed in v3.2.0).
- Keep this dispatcher thin. The discovery interviews, the comparison ingest, and the issue-creation logic all live in the retained skills.
