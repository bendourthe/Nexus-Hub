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

## Optional per-phase model-routing assessment (graceful degradation)

After the phase breakdown is designed and before the plan file is written, `/plan` runs a best-effort model-routing assessment so each phase records the model and reasoning effort it should run on. This is opt-in by availability and never blocks plan generation:

- **Assess each phase once.** For every phase in the breakdown, invoke the `[[model-routing]]` skill to score that phase's scope and sub-tasks on its complexity rubric and recommend a model plus reasoning effort, defaulting to the strongest available tier on any uncertainty or high-risk signal (the no-degradation guarantee). The skill detects the platform and enumerates the live model set itself - `/plan` never hardcodes a model list.
- **Record platform-agnostic intent alongside the concrete name.** Write the recommendation as a tier intent ("strong reasoning tier, high effort") together with the concretely-enumerated model id and effort when enumeration succeeds, so the recommendation survives a platform switch between planning and implementation - `/implement` re-confirms it against the then-current models.
- **Degrade silently.** If the routing skill or live enumeration is unavailable (no platform surface, offline, manual-only platform), write the neutral placeholder `assess at implementation time` for that phase's recommendation rather than failing. The plan is still valid and complete without a concrete model name.
- This carries zero new outbound calls, dependencies, or credentials - the heavy logic stays in `[[model-routing]]`; `/plan` only invokes it per phase and records the result in the plan template (see the retained planning skill's "Phases at a Glance" column and per-phase `**Recommended model**` field).

## Mandatory final phase (planning scopes)

Every plan `generate-plan` / `implementation-plan` produces now ends with a mandatory final phase - "Architecture Refactor, Known-Gaps Reconciliation, and CI/CD" - and each phase's testing sub-task also creates/updates and optimizes CI/CD for that phase's changes. This is part of the plan contract, not a dispatcher responsibility: the template and the design rules live in the `[[implementation-plan]]` skill (its "Mandatory Final Phase" block and the "Terminal refactor phase" / "CI/CD per phase" design guidelines). This dispatcher only surfaces the guarantee; it does not duplicate the template.

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
