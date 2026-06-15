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

Pass every resolved value (plan path, phase identifier, remaining args) through to the `implement-phase` skill unchanged.

## Delegation

Dispatch to the retained skill:

      (any invocation) -> implement-phase

The skill runs its full sequence: plan + phase resolution, pre-implementation review, subtask-by-subtask implementation, lint and format, test execution with coverage, test augmentation, the troubleshooting loop, the GO / NO-GO quality gate, and the post-phase completion sequence (gitignore, test review, CI/CD check, known-gaps update, docs cleanup audit, devlog, documentation, session history, commit message, and the commit-and-push prompt).

## Per-phase model-routing pre-flight (graceful degradation)

Before the subtask-by-subtask implementation step begins for a phase, `/implement` runs a best-effort model-routing pre-flight so the phase builds on the right model. It re-confirms the recommendation `/plan` recorded at planning time, because a stronger or cheaper model may have shipped since the plan was written. The step is opt-in by availability and never blocks implementation:

- **Read the plan's recommendation.** Read the target phase's `**Recommended model**` field (written by `/plan`'s planning-time routing assessment) and its "Rec. model / effort" entry, capturing both the platform-agnostic tier intent and any concretely-enumerated model id + effort.
- **Re-assess against the currently-enumerated models.** Invoke the `[[model-routing]]` skill to detect the platform, enumerate the live model set, and re-score the phase. This is the whole reason for re-confirmation: a plan built before a new model release should pick up the newer or cheaper option at implementation time. The skill never hardcodes a model list.
- **Apply the confirm-then-auto-execute posture on agreement.** If the re-assessment agrees with the plan, present the recommendation and, on approval, act per the platform tier - execute the switch on scriptable platforms (Codex, Antigravity `agy`, Gemini CLI), print the exact `/model` + `/effort` keystroke on Claude Code, or print the picker instruction on Cursor / Copilot / OpenCode.
- **Surface the delta on disagreement, defaulting up.** If the re-assessment disagrees (e.g. a newer model now dominates, or the phase scores higher than planned), surface the delta and ask which to use, defaulting to the stronger option (the no-degradation guarantee).
- **Degrade silently.** If the routing skill or live enumeration is unavailable (no platform surface, offline, or a manual-only platform), proceed on the plan's recommendation - or the session's current model - with a one-line note, never blocking the build.

This pre-flight is platform-agnostic and carries zero new outbound calls, dependencies, or credentials - the heavy logic lives in `[[model-routing]]`; this file stays a thin dispatcher that invokes it once per phase. A phase that hits repeated test failures during the troubleshooting loop may upshift to a stronger tier or higher effort (upshift only, with confirmation, never an automatic mid-phase downshift); see the mid-task escalation rule in `[[model-routing]]`.

## Final-phase release routing (v3.0.0 change)

The `implement-phase` skill auto-detects the final phase of a plan and runs a release-readiness workflow after the post-phase sequence. In v3.0.0 the consolidated release step is owned by `/update release`, so route the final-phase release work there instead of the old inline `update-*` sequence:

- Resolve known gaps and deferred work (skill sub-phase 9A) and verify tests + CI/CD readiness (9B) as before.
- For the documentation cleanup, standard update checks, and the version bump / changelog / tag / push (skill sub-phases 9C-9E), hand off to **`/update release`**, which runs docs + devlog + gitignore + version (via `scripts/check_version_sync.py`) + changelog + refactor, then cleans up, commits, tags, and pushes as one atomic flow.
- Never create a tag or push automatically; `/update release` keeps its own confirmation gates.

## Optional fan-out

For a phase that is itself a large fan-out task (the plan's prompt recommends dynamic-workflow execution), offer the at-scale path with confirmation and the scope-first token caution, falling back to single-agent execution when workflows are unavailable. See [[agent-orchestration-primitives]].

## Notes

- This command replaces `/implement-phase` (removed in v3.2.0).
- Keep this dispatcher thin. The end-to-end phase workflow lives entirely in the `implement-phase` skill.
