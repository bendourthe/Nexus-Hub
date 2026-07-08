---
name: implement-phase
description: Implement one phase of a plan end-to-end - discover the plan and phase, review against the codebase, code subtask by subtask, lint, test with coverage, augment tests, run the troubleshooting loop and GO/NO-GO gate, then the full post-phase documentation and commit sequence. On a plan's final phase it also runs the mandatory architecture-refactor + known-gaps + CI/CD gate and the release-readiness workflow, handing off to /update release. This is the delegate behind /implement. Use whenever the user says "implement phase N", "build the next phase", "do phase 3 of the plan", "execute the plan", "continue implementing", or points at a plan file. SKIP - creating the plan itself (use /plan), or one-off edits with no plan to track.
summary_l0: "Implement one plan phase end-to-end with tests, gates, post-phase docs, commit, and final-phase release-readiness"
overview_l1: "The delegate behind /implement. It runs one plan phase end-to-end: Phase 0 resolves the plan and phase and detects the final phase from five signals; Phase 1 reviews the plan against the codebase; Phase 2 implements subtask by subtask in scope; Phases 3-7 lint, run tests with coverage, augment missing tests, loop on failures up to three times, and apply a four-part GO/NO-GO quality gate; Phase 8 runs the ten-step post-phase sequence (gitignore, test review, CI/CD readiness plus optimization, known-gaps append, docs-cleanup audit, devlog, docs, session history, commit message, and a required commit-and-push prompt). On the final phase it additionally runs the mandatory architecture-refactor plus known-gaps plus CI/CD-optimize gate and the release-readiness workflow, handing the version bump and tag off to /update release. The full ordered procedure lives in references/implement-phase-runbook.md. Trigger phrases: implement phase N, build the next phase, execute the plan, continue implementing."
---

# Implement Phase

Implement one phase of a plan end-to-end: discover the right plan and phase, review it against the codebase, write the code subtask by subtask, lint, test with coverage, troubleshoot failures, augment missing tests, pass a quality gate, and run the full post-phase documentation and commit sequence. When the target phase is the plan's final phase, also run the mandatory architecture-refactor plus known-gaps plus CI/CD gate and the release-readiness workflow. This is the delegate behind `/implement`.

The complete, ordered procedure is in [`references/implement-phase-runbook.md`](references/implement-phase-runbook.md) - read it when actually running a phase. This body is the overview, the gates, and the invariants.

## When to Use This Skill

- Implementing a specific phase of an existing plan ("implement phase 3", "build the next phase", "continue the plan").
- Executing a plan produced by `/plan` under `docs/v<MAJOR>/v<MAJOR>.<MINOR>/plans/` (or a legacy layout).
- Driving a phase all the way to a committed, documented, tested state - not just writing the code.

**Trigger phrases**: "implement phase N", "build the next phase", "do phase 3 of the plan", "execute the plan", "continue implementing".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Create or design the plan itself | `/plan` (`implementation-plan`) |
| Make a one-off edit with no plan to track | Just do the edit |
| Run the release commit/tag/push flow directly | `/update release` (this skill hands off to it on the final phase) |

## Workflow overview

The runbook defines ten stages; the load-bearing ones:

- **Phase 0 - Resolve and detect.** Resolve the plan and phase; set `is_final_phase` from the five signals (phase ordering, title heuristics, prior-phase completion, plan metadata, adjacent plans). Show a pre-flight summary and wait for confirmation.
- **Phases 1-2 - Review and implement.** Review the plan against the codebase, then implement subtask by subtask, in scope, logging `# DEVIATION:` markers.
- **Phases 3-7 - Lint, test, gate.** Lint/format; run tests with coverage; augment missing tests; troubleshoot failures (max 3 iterations, classified IMPL/TEST/ENV); apply the four-part GO/NO-GO gate (0 failures, >= 80% coverage, 0 lint errors, build succeeds).
- **Phase 8 - Post-phase sequence (every phase).** The ten steps 8.1-8.10 in strict order, ending in the REQUIRED commit-and-push prompt. Step 8.3 now includes a CI/CD optimization pass, not just a coverage/consistency check.
- **Phase 9 - Final phase only.** Run the mandatory refactor + known-gaps + CI/CD gate (9.0), resolve known gaps (9A), verify tests + CI/CD (9B), then hand 9C-9E off to `/update release`.

## Mandatory final-phase gate (v3.11.0)

When `is_final_phase` is true, before the release-readiness sub-phases, run the Phase 3 terminal-phase gate on the last phase - and run it **even if the plan predates v3.11.0** and has no explicit "Architecture Refactor, Known-Gaps Reconciliation, and CI/CD" phase (detect its absence and run the gate anyway): `[[project-refactor]]` (with the empty-dir / duplicate / orphan / structure-complexity detectors) plus `[[docs-layout-refactor]]` to clean the layout, `[[known-gaps-tracker]]` to reconcile gaps, and a CI/CD create/update/optimize pass. Every confirmation gate stays; never tag or push automatically - that is `/update release`'s job.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The user said this is the last phase, so I'll run the release workflow." | Never trust the claim alone. `is_final_phase` comes from five signals; a numerically-last phase with unchecked prior phases is treated as non-final. Detect, then confirm. |
| "Tests passed in Phase 4, I can skip the 8.2 re-run." | Phase 7's gate adjustments can drift the tree after Phase 4. The 8.2 re-run catches a green-then-red regression before the phase is declared done. |
| "This phase changed no CI, so I'll skip 8.3." | 8.3 is a no-op-safe step that also checks whether the workflow is optimized (path filters, concurrency, caching, gated matrix jobs). Invoke it every phase so CI drift and minute-bloat surface early. |
| "The plan has no final refactor phase, so there's nothing to clean up at the end." | Plans generated before v3.11.0 lack the mandatory final phase; the 9.0 gate runs the refactor + known-gaps + CI/CD work anyway on the last phase. Absence of the phase is not absence of the work. |
| "I'll create the release tag since everything passed." | The skill never tags or pushes automatically. The final phase hands off to `/update release`, which owns the version bump, changelog, tag, and push behind its own gates. |

## Verification

- [ ] Plan and phase resolved; `is_final_phase` set from the five signals and shown in the pre-flight summary.
- [ ] Code implemented subtask by subtask, in scope, with deviations logged.
- [ ] Lint clean; tests run with coverage; GO/NO-GO gate evaluated (0 failures, coverage threshold, 0 lint errors, build succeeds) or the user explicitly bypassed with the gap documented.
- [ ] Phase 8 ran all ten steps in order, ending in the commit-and-push prompt; known-gaps appended to the correct `## v<MAJOR>.<MINOR>.<PATCH>` subsection; session history written to `<version_dir>/development/history/`.
- [ ] On the final phase: the mandatory refactor + known-gaps + CI/CD gate (9.0) ran (even for a pre-v3.11.0 plan), and the version bump / tag / push was handed to `/update release` - no tag or push created automatically.

## Related Skills

- [[implementation-plan]] -- produces the plan this skill executes; its mandatory final phase (v3.11.0) is what the 9.0 gate runs.
- [[known-gaps-tracker]] -- the per-minor gap log this skill appends to (8.4) and reconciles on the final phase (9A).
- [[project-refactor]] -- the cleanliness engine (empty-dir/duplicate/orphan/structure) the final-phase gate invokes, alongside [[docs-layout-refactor]] for the docs tree.
- [[session-history]] -- writes the per-phase session-history file (8.8).
- [[code-commit-workflow]] -- the commit-message conventions the 8.9 step follows; `/update release` owns the final-phase commit/tag/push.

---

**Version**: 1.0.0
**Last Updated**: July 2026
