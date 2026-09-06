---
description: Implement one plan phase end-to-end - discover the plan, review, code, lint, test, troubleshoot, then run the post-phase docs and commit sequence. On a plan's final phase, automatically runs release readiness. Use to "implement phase N", "build the next phase", "do phase 3 of the plan", "execute the plan", "continue implementing". SKIP - creating the plan itself (use /plan), or one-off edits with no plan to track.
---

# /implement Command

Implement one phase of a plan end-to-end: discover the right plan and phase, review it against the codebase, write the code, lint, test, troubleshoot failures, augment missing tests, and run the full post-phase documentation and commit sequence when every quality gate passes. When the target phase is the final phase of the plan, `/implement` additionally runs the release-readiness workflow.

This is a thin dispatcher over the retained `implement-phase` skill. The full per-phase workflow (the nine post-phase steps, the troubleshooting loop, the quality gates) lives in that skill; this file resolves the plan and phase, then delegates.

## Argument resolution

`/implement` is argument-driven, not menu-driven - it infers what to do from the positional arguments:

- `/implement` (bare) - discover the plan (one plan = use it; multiple = ask which), then ask which phase, defaulting to the first incomplete phase.
- `/implement <slug>` - resolve to the plan at `docs/**/plans/<slug>.md`, then select the phase as above.
- `/implement <path/to/plan.md>` - use the plan at that path directly.
- `/implement <slug> phase-N` or `/implement <slug> "Phase Name"` - implement that specific phase.
- `/implement <slug> next` - implement the first phase not yet marked complete.
- A bare `vX.Y.Z` first argument selects the plan(s) under that version (legacy-compatible).
- `/implement <slug-or-path> full` (alias `in-full`) - implement every incomplete phase in order. Commit at each successful boundary (commit-only on non-final phases; no push). Run the fail-closed last phase, which publishes and integrates, then hand off to `/update release` with that command's confirmation gates once integration is green.
- `/implement <slug-or-path> phase-by-phase` - the same loop, but after each non-final phase wait with: (1) commit and continue; (2) commit and pause; (3) other. There is no push option: a non-final phase is commit-only.

Driver modes are a later positional token, never the first argument. Match whole tokens `full`, `in-full`, and `phase-by-phase` only - a slug that contains "full" as a substring is not a driver mode. An unknown later token prints usage and does not start a phase. Bare `/implement` and the one-phase forms above stay one-phase. Preserve the per-phase model-routing pre-flight; Cursor, OpenCode, and Copilot have no scriptable model switch.

Pass every resolved value (plan path, phase identifier, driver mode, remaining args) through to the `implement-phase` skill unchanged. The driver loop lives in that skill; do not inline it here.

## Delegation

Dispatch to the retained skill:

      (any invocation) -> implement-phase

The skill runs its full sequence: plan + phase resolution, pre-implementation review, subtask-by-subtask implementation, lint and format, test execution with coverage, test augmentation, the troubleshooting loop, the GO / NO-GO quality gate, and the post-phase completion sequence (gitignore, test review, CI-impact record, known-gaps update, docs cleanup audit, devlog, documentation, session history, commit message, and the commit prompt).

## Per-phase model-routing pre-flight (graceful degradation)

Before the subtask-by-subtask implementation step begins for a phase, `/implement` runs a best-effort model-routing pre-flight so the phase builds on the right capability tier. It re-confirms the generic recommendation `/plan` recorded at planning time, because the provider map or the selected provider's available models may have changed. The step never blocks implementation:

- **Read the plan's recommendation.** Read the target phase's `**Recommended model tier**`, `**Recommended effort level**`, and `**Rationale**` fields plus the matching two glance columns. Read `## Current model map` to resolve the concrete model for the user's selected provider. For historical plans, continue accepting the legacy `**Recommended model**` and `Rec. model / effort` fields.
- **Refresh and re-assess.** When web access is available, refresh the four-provider candidate from official sources, validate and render it through `model-routing/scripts/model-map.{sh,ps1}`, then invoke `[[model-routing]]` to re-score the phase and enumerate the selected provider's live platform surface. When offline, use the helper's validated dated fallback. This lets a plan written before a model release pick up the newer equivalent without changing its generic intent.
- **Apply the confirm-then-auto-execute posture on agreement.** If the re-assessment agrees with the plan, present the recommendation and, on approval, act per the platform tier - execute the switch on scriptable platforms (Codex, Antigravity `agy`, Gemini CLI), print the exact `/model` + `/effort` keystroke on Claude Code, or print the picker instruction on Cursor / Copilot / OpenCode.
- **Surface the delta on disagreement, defaulting up.** If the re-assessment disagrees (for example, the phase scores higher than planned or the mapped model is unavailable), surface the delta and ask which to use, defaulting to the same or stronger tier (the no-degradation guarantee).
- **Degrade visibly.** If map refresh, routing, or live enumeration is unavailable, proceed on the plan's generic tier/effort or the session's current model with a one-line note. Never silently substitute a lower tier.

This pre-flight is platform-agnostic. Public web research may refresh the map, but it requires no new credential or dependency; deterministic score/map validation and host enumeration/switch mechanics stay in `[[model-routing]]`. The retained `implement-phase` runbook executes the same pre-flight before its implementation stage. A phase that hits repeated test failures during the troubleshooting loop may upshift to a stronger tier or higher effort (upshift only, with confirmation, never an automatic mid-phase downshift); see the mid-task escalation rule in `[[model-routing]]`.

## Phase lifecycle (guarantee)

`/implement` enforces the same lifecycle `/plan` generates. Three guarantees, worth stating because they change what the reader should expect at a phase boundary:

- **A non-final phase finishes with a local commit and nothing else.** No push, no pull request, no remote CI, in every mode. Pushing per phase bills a full pipeline run to validate work the plan itself says is incomplete. A user who explicitly asks to push still gets it, after a one-line statement of the cost; what is removed is the default, not the authority.
- **A non-final phase records CI impact; it does not author a pipeline.** Step 8.3 states what this phase added that CI would need to know about and whether the pipeline already covers it. Pipeline files change mid-plan only when CI/CD is that phase's explicit deliverable.
- **The final phase owns everything remote.** It runs the terminal pipeline reconciliation via `[[cicd-architect]]`, completes the local gate, creates the final commit, obtains explicit approval, pushes ONCE, opens the integration pull request, waits for required checks against the merge result, reopens itself on red (reproducing locally before any re-push), and merges only on green.

The procedure lives in `implement-phase` and its runbook; this dispatcher states the guarantee.

## Final-phase release routing (v3.0.0 change)

The `implement-phase` skill auto-detects the final phase of a plan and runs a release-readiness workflow after the post-phase sequence. In v3.0.0 the consolidated release step is owned by `/update release`, so route the final-phase release work there instead of the old inline `update-*` sequence:

- Resolve known gaps and deferred work (skill sub-phase 9A) and verify tests + CI/CD readiness (9B) as before.
- For the documentation cleanup, standard update checks, and the version bump / changelog / tag / push (skill sub-phases 9C-9E), hand off to **`/update release`**, which runs docs + devlog + gitignore + version (via `scripts/check_version_sync.py`) + changelog + refactor, then cleans up, commits, tags, and pushes as one atomic flow.
- Hand off only after the integration pull request is green and merged. A non-green integration holds the release.
- Never create a tag or push automatically; `/update release` keeps its own confirmation gates.

## Optional fan-out

For a phase that is itself a large fan-out task (the plan's prompt recommends dynamic-workflow execution), offer the at-scale path with confirmation and the scope-first token caution, falling back to single-agent execution when workflows are unavailable. See [[agent-orchestration-primitives]].

## Notes

- This command replaces `/implement-phase` (removed in v3.2.0).
- Keep this dispatcher thin. The end-to-end phase workflow and the `full` / `phase-by-phase` loop live entirely in the `implement-phase` skill. Never tag or push a release from the driver.
