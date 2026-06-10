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
