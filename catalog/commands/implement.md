---
description: Implement a whole plan end-to-end by default - one upfront approval round, then every phase, known gap, green integration, release, and cleanup, stopping only on a completion verdict, a named blocker, or the user's pause. One phase runs with an explicit `phase <N>` token. Use to "implement the plan", "execute the plan", "implement phase N", "build the next phase", "continue implementing", "pause the run". SKIP - creating the plan itself (use /plan), or one-off edits with no plan to track.
---

# /implement Command

Implement a plan end-to-end. By default `/implement` runs the whole plan: it asks every approval the run needs once, up front, then implements every phase (review, code, lint, test, troubleshoot, post-phase documentation and a local commit), publishes and integrates once, releases, and removes the plan's merged branches and worktree. It stops only when the completion checker reports a terminal verdict, on a named blocker outside the recorded approvals, or when the user pauses. One phase at a time is still available with an explicit token.

This is a thin dispatcher over the retained `implement-phase` skill. The full per-phase workflow (the nine post-phase steps, the troubleshooting loop, the quality gates) lives in that skill; this file resolves the plan and phase, then delegates.

## Argument resolution

`/implement` is argument-driven, not menu-driven - it infers what to do from the positional arguments:

- `/implement <plan>` - run the WHOLE plan (the full driver). `<plan>` is a slug, a plan file path, a plan name, or a `vX.Y.Z` version. Every incomplete phase runs in order with a local commit at each boundary; the fail-closed last phase publishes and integrates once, then the release and cleanup follow under the approvals recorded at the start.
- `/implement` (bare) - the same full driver on the next plan: the lowest `Status: queued` plan by semantic version whose queued predecessors are merged. The resolved plan is the first line of the upfront round; when two plans qualify or the order is unclear, ask.
- `/implement <plan> phase <N>` (also `phase-N` or `"Phase Name"`) - run exactly one phase, with the per-phase confirmation and commit prompt.
- `/implement <plan> next` - run one phase: the first not yet marked complete.
- `/implement <plan> phase-by-phase` - the full loop, but after each non-final phase wait with: (1) commit and continue; (2) commit and pause; (3) other. There is no push option: a non-final phase is commit-only.
- `/implement <plan> full` and `in-full` - accepted aliases for the default.
- `/implement pause` - pause the current run at the next safe point. User-only: the pause must come from the user's own prompt, is always honored, and the run resumes with `/implement <plan>`.

Mode tokens come after the plan, never first (except `pause`). Match whole tokens only - a slug that contains "full" or "phase" as a substring is not a mode. An unknown later token prints usage and does not start a phase. Preserve the per-phase model-routing pre-flight; Cursor, OpenCode, and Copilot have no scriptable model switch.

Pass every resolved value (plan path, phase identifier, driver mode, remaining args) through to the `implement-phase` skill unchanged. The driver loop lives in that skill; do not inline it here.

## Upfront round and completion (guarantee)

A full run asks once. Before the first phase, `/implement` presents one round (under the active template's `Consequential Decisions` rule) listing every approval the run will need as exact values: the resolved plan, push and merge, the release version with its tag and publication, the release pull requests and back-merge for that version, re-pushes after a locally reproduced fix (up to 3), generated release notes, refactor moves inside plan-touched folders, spend caps, the gap types the user allows to be deferred, and each "Ask first" surface the plan names. The answers are frozen in a run record outside the working tree by `check_plan_completion.py record create`. No approval recorded there is asked again. CI workflow, permission, and secret changes are never approvable in advance; they always stop the run as a named blocker.

What "done" means is owned by the completion contract (`implement-phase/references/completion-contract.md`) and decided by `scripts/check_plan_completion.py`; this command does not restate it. On platforms that support it, a turn-end gate and the `nexus-hub run-plan` runner keep the run going until the checker's verdict is terminal. Context pressure is handled by compaction and the runner, not by stopping.

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

## Queue re-assessment (guarantee)

Before writing code, at plan entry and at every phase entry, `/implement` re-validates the plan against the codebase as it stands now and the plans queued around it, through `[[plan-queue-assessment]]`. A plan written months earlier is not assumed still correct. The result is written into the phase session history as evidence for the existing `## Plan delta` disposition, including when nothing drifted, because an unwritten check is indistinguishable from a skipped one. The rule lives in that skill; this dispatcher states the guarantee.

## Worktree isolation and parallel plans (guarantee)

`/implement` isolates a plan in its own **worktree**, not merely its own branch, so a second plan can start in a separate session without switching the shared checkout underneath a running one. It then reports which queued plans are parallel-capable, with a copy-paste block for launching each in a new session. On the final phase, after the merge is green and merged, it retires the worktree: branch fully merged, tree clean, directory and branch deleted, `git worktree list` confirmed clear.

Mechanics belong to `[[using-git-worktrees]]`; ranking and overlap detection to `[[plan-queue-assessment]]`. This command owns neither, and the procedure lives in `implement-phase`. Where worktrees are unavailable, it falls back to a branch and says so.

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
- Before the final-phase local/publication gate, delegate living handbook refresh to `technical-documentation` and its `references/handbook-refresh.md`; `/update release` rechecks the integrated candidate before version changes.
- Never create a tag or push automatically; `/update release` keeps its own confirmation gates.

## Optional fan-out

For a phase that is itself a large fan-out task (the plan's prompt recommends dynamic-workflow execution), offer the at-scale path with confirmation and the scope-first token caution, falling back to single-agent execution when workflows are unavailable. See [[agent-orchestration-primitives]].

## Notes

- This command replaces `/implement-phase` (removed in v3.2.0).
- Keep this dispatcher thin. The end-to-end phase workflow, the upfront round, and the full / `phase-by-phase` loop live entirely in the `implement-phase` skill. The release itself runs through `/update release`, which consumes the recorded release approvals.
