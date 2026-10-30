---
name: implement-phase
description: Implement a plan end-to-end, the whole plan by default (one upfront approval round, then every phase to a checker-decided finish) or one phase on request - discover the plan and phase, review against the codebase, code subtask by subtask, lint, test with coverage, augment tests, run the troubleshooting loop and GO/NO-GO gate, then the full post-phase documentation and commit sequence. On a plan's final phase it also runs the mandatory architecture-refactor + known-gaps + CI/CD gate and the release-readiness workflow, handing off to /update release. This is the delegate behind /implement. Use whenever the user says "implement phase N", "build the next phase", "do phase 3 of the plan", "execute the plan", "continue implementing", or points at a plan file. SKIP - creating the plan itself (use /plan), or one-off edits with no plan to track. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/.
summary_l0: "Implement one release-plan phase with tests, evidence, documentation, and commit gates"
overview_l1: "The delegate behind /implement. Full is the default: one upfront approval round, then every phase to a checker-decided finish. Each phase runs end-to-end: resolve the phase and final-phase signals; review the plan against the codebase; implement each subtask in scope; lint, run the phase's blast-radius tests, troubleshoot, and apply a five-part GO/NO-GO gate including a proportional real-boundary smoke. The full suite, the coverage threshold, and cross-phase integration tests are asserted once, in the final phase. Phase 8 runs eleven ordered steps, records CI impact without editing pipelines, always writes the Plan delta, maintains gaps and release evidence, and ends every non-final phase commit-only. Phase 9 runs only on the final phase: reconcile architecture, gaps, and CI/CD; execute the Tier 3 deep pass; independently review the resulting tree against the plan Goal; pass the full local gate; then publish once under recorded authority and green integration checks. The ordered procedure lives in references/implement-phase-runbook.md. Triggers: implement the plan, implement phase N, continue implementing, pause the run."
---

# Implement Phase

Implement one phase of a plan end-to-end: discover the right plan and phase, review it against the codebase, write the code subtask by subtask, lint, run focused tests during implementation and full validation with coverage after all implementation tasks are complete, troubleshoot failures, augment missing tests, pass a quality gate, and run the full post-phase documentation and commit sequence. When the target phase is the plan's final phase, also run the mandatory architecture-refactor plus known-gaps plus CI/CD gate and the release-readiness workflow. This is the delegate behind `/implement`.

The complete, ordered procedure is in [`references/implement-phase-runbook.md`](references/implement-phase-runbook.md) - read it when actually running a phase. This body is the overview, the gates, and the invariants.

What "done" means for a full run, and when an action may proceed automatically or needs a manual decision, is owned by [`references/completion-contract.md`](references/completion-contract.md). The installed checker (`python ~/.nexus-hub/scripts/check_plan_completion.py`) decides verdicts and verifies recorded authority. This skill delegates predicates, authorization scope, trusted permission evidence and genuine answer capture to that contract.

The upfront approval page's words, sections, question layout and compatibility lines live in [`references/approval-page.md`](references/approval-page.md); the page is printed by `record render ... --page`.

The verification behaviors the GO/NO-GO gate can request, each routed to the skill that owns it, live in [`references/verification-behaviors.md`](references/verification-behaviors.md).

## When to Use This Skill

- Implementing a specific phase of an existing plan ("implement phase 3", "build the next phase", "continue the plan").
- Executing a plan produced by `/plan` under `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/plans/` (or a legacy layout).
- Driving a phase all the way to a committed, documented, tested state - not just writing the code.
- Driving every incomplete phase of a plan in one session (`/implement <slug> full` or `phase-by-phase`).

**Trigger phrases**: "implement phase N", "build the next phase", "do phase 3 of the plan", "execute the plan", "continue implementing", "implement full", "implement in-full", "phase-by-phase".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Create or design the plan itself | `/plan` (`implementation-plan`) |
| Make a one-off edit with no plan to track | Just do the edit |
| Run the release commit/tag/push flow directly | `/update release` (this skill hands off to it on the final phase) |

## Workflow overview

The runbook defines ten stages; the load-bearing ones:

- **Phase 0 - Resolve and detect.** Resolve the plan and mode (full by default; one phase only with `phase <N>` or `next`; a minor token `vX.Y` resolves to that minor's member plans, implemented concurrently when compatible and released in version order under one approval, per the runbook's Phase 0 and the completion contract); set `is_final_phase` from the five signals (phase ordering, title heuristics, prior-phase completion, plan metadata, adjacent plans). One-phase mode shows a pre-flight summary and waits; full mode runs the upfront approval round (Phase 0a) once and records it.
- **Phases 1-2 - Review and implement.** Review the plan against the codebase, then implement subtask by subtask, in scope, logging `# DEVIATION:` markers.
- **Phases 3-7 - Lint, test, gate.** Lint/format; run the tests in THIS phase's blast radius (the files Phase 2 touched, plus the repo's fast gate) rather than the whole suite; write tests for genuinely new behavior; troubleshoot failures (max 3 iterations, classified IMPL/TEST/ENV); apply the five-part GO/NO-GO gate (0 failures in scope, no coverage regression on touched files when an existing cheap measurement is available, with new coverage collection deferred to the final phase, 0 lint errors, build succeeds, and the phase's feature matches expected behavior through a cheap real-boundary smoke delegated to `[[functional-verification]]`).
- **Phase 8 - Post-phase sequence (every phase).** The eleven steps 8.1-8.11 run in strict order. 8.3 RECORDS this phase's CI impact against `[[cicd-architect]]` and does NOT author or optimize a pipeline file unless CI/CD is this phase's explicit deliverable. 8.4 always writes `## Plan delta` in the current phase's session history and escalates only a blocking Wrong, Incomplete, or False assumption disposition. 8.11 is COMMIT-ONLY on every non-final phase in every mode: one-phase asks Commit / Amend / Stop, `full` auto-commits, and `phase-by-phase` uses a three-option menu. Push, pull request, and remote CI belong to the final phase alone.
- **Phase 9 - Final phase only.** Run the fail-closed last-phase duties, including duty 5's terminal pipeline reconciliation through `[[cicd-architect]]`, the Tier 3 whole-plan deep pass through `[[functional-verification]]`, and then an independent Goal-vs-codebase review of the resulting tree; write `<version_dir>/development/<version>-last-phase-evidence.md` with its own `## Tier 3 deep pass` section; resolve known gaps (9A); complete the LOCAL gate (9B); then run 9F: the final commit, recorded-authorization check, plan's single branch push, integration pull request, required-check wait, and merge. The approval gate measures scope against the REMOTE integration branch (`git fetch`, then `origin/<base>..HEAD`), stating a commit count as well as a file count, because a branch cut from a local branch ahead of its remote carries those extra commits into the pull request and a local-only diff cannot see them. A red check REOPENS the phase and is reproduced locally before any re-push. Hand 9C-9E off to `/update release` only when the evidence file is complete, the deep pass and Goal-vs-codebase review have no unresolved miss without a recorded gap, AND the integration result is green and merged.
- **Driver loop** - the default (`full`, aliases `in-full`, bare `/implement <plan>`) and `phase-by-phase`. Iterate incomplete phases with the Phase 0-8 sequence, one progress line per phase instead of a closing summary. Stop only on a terminal verdict from the completion checker: a named blocker, the user's pause, or `PLAN COMPLETE`. Context pressure is handled by compaction and the runner, not by stopping. After the last phase, integration, `/update release` under the recorded approvals, and cleanup follow. See the runbook. Cross-link `[[code-commit-workflow]]` for phase-boundary commits.

## Worktree isolation and parallel plans (v4.12.1)

Three guarantees, stated here because they change what a reader should expect at the start and end of a plan. The procedure lives in the runbook.

- **A plan runs in its own worktree, not just its own branch.** A branch alone serializes work: a second plan cannot start without switching the single checkout, and switching underneath a running session changes the files it is editing. Mechanics belong to `[[using-git-worktrees]]`; this skill owns only when a worktree is created and how it is named, so the release step can find it. Where worktrees are unavailable, fall back to a branch, say so in one line, and note that parallel plans are off for that session.
- **Phase 0 automatically dispatches eligible whole plans in a minor run.** [[plan-queue-assessment]] owns compatibility; this skill owns the bounded coordinator loop, native admission, harness-tool dispatch and implementation-ready wait state in the runbook. Workers use the parent minor approval, never standalone `/implement`. If agent tools, verified claims or worktrees are unavailable, report the limitation and run serially.
- **The final phase reconciles worktree retirement after green merged integration.** Apply the completion contract and cleanup executor, and quote the removal or exact KEEP decision under `## Worktree teardown`. The active-controller and active-worker exception in the completion contract permits deferred cleanup during a minor run; final minor completion still requires its cleanup evidence. Never override KEEP or force-remove a dirty worktree.

## Mandatory final-phase gate (v3.11.0)

When `is_final_phase` is true, before the release-readiness sub-phases, run the fail-closed last-phase duties - even if the plan predates v3.11.0 and has no explicit "Architecture Refactor, Known-Gaps Reconciliation, and CI/CD" phase (detect its absence and run the gate anyway). Each duty writes a section of `<version_dir>/development/<version>-last-phase-evidence.md` quoting the proving command or scan: architecture refactor via `[[project-refactor]]` and `[[docs-layout-refactor]]`; known-gaps reconciliation for this version and every other still-open `docs/**/known-gaps.md`; living docs architecture; git-tree hygiene via `python ~/.nexus-hub/scripts/check_release_preconditions.py --branches --repo-settings` (report only); CI/CD coverage plus installer parity; the Tier 3 `[[functional-verification]]` deep pass; independent Goal-vs-codebase review of the resulting tree; last-phase-only human testing suggestions; full-suite testing. If the repository ships more than one installer, run the declarative parity checker in the same pass as `[[platform-contract-verification]]`; zero or one installer is a silent no-op. A duty is omitted only by recording a known-gap (`QG` or `DF`) with Source phase, Plan reference, Reason, and Suggested next step. The `/update release` handoff is blocked while the evidence file is missing or a deep-pass or Goal-review finding is unresolved without a recorded gap. Keep the five-signal `is_final_phase` detection; `/update release` verifies tag and publication authority through the completion contract.

## Progress reporting

Read [references/progress-reporting.md](references/progress-reporting.md) at run start or resume. It owns the periodic and on-demand report, including scope, task percentages, observed worker counts, elapsed time, dependencies, remaining-time ranges and efficiency review. `/update status` enters that reference in read-only mode and never starts this skill's implementation driver.

## Close every phase with the progress table

A phase boundary ends with a table, before the closing summary, so a reader can
see where a multi-session plan actually stands without opening the plan file:

```bash
python ~/.nexus-hub/scripts/plan_status.py --plan <plan-file>
```

It prints the plan name, the target version, and every phase with its status and
task counts. Emit the table whenever a message closes work on a plan, not only
at the final phase - the point is that progress is visible continuously rather
than reconstructed at the end.

For the consolidated report, use these generated counts as the source and follow the reporting reference for additional observed fields; emit one table rather than duplicate reports.

The script derives everything from the plan's own headings and checkboxes, so
the table cannot disagree with the file. Do not hand-write it: a hand-written
table is a second source of truth that drifts on the first missed tick.

## Parallel implementation ownership

The minor driver implements independent whole plans concurrently and publishes them sequentially. Workers own only admitted paths and their local phase commits; the coordinator owns shared ledgers, CHANGELOG, version/release metadata, trackers, signed state mutations and every publication. A ready worker waits locally until native publication admission succeeds; refresh its unpublished commits onto the current integration base, resolve scoped conflicts, and complete affected final validation before its first push. [[cicd-integration]] owns evidence invalidation and reuse. The completion contract owns both admissions and parent-bound member projections; the runbook owns their execution order.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The user said this is the last phase, so I'll run the release workflow." | Never trust the claim alone. `is_final_phase` comes from five signals; a numerically-last phase with unchecked prior phases is treated as non-final. Detect, then confirm. |
| "The tests pass, so the feature works" | Tests can stay green while the real boundary or rendered layout is broken. That exact inference let a broken layout through four green gates; the fifth gate must exercise the phase's feature through its real boundary and compare expected with observed behavior via `[[functional-verification]]`. |
| "Earlier results cover every later edit." | Reuse the receipt only when tested source, dependencies, configuration and environment are unchanged. After corrections, rerun affected checks through [[cicd-integration]]; an unchanged tree needs no automatic second run. |
| "The phase is green, so the plan is tested." | Phases 3-7 run a blast-radius scope by design. The full suite, the >= 80% threshold, and the cross-phase integration tests are asserted once, in 9B. A scoped green is evidence about one phase, never about the plan. |
| "I should run the whole suite each phase to be safe." | That buys a verdict the final phase must re-establish anyway, at two full runs per phase, while generating coverage tests against interfaces later phases still change. Scope the phase; assert the whole in 9B. |
| "Nothing contradicted the plan, so there is no Plan delta to write." | No delta is an explicit Tier 2 disposition, not an omitted section. Every phase history records the evidence and the consequence for remaining phases; only a blocking delta escalates. |
| "Every phase smoke passed, so the final deep pass is redundant." | Phase smokes prove each phase's narrow boundary at that moment. Tier 3 checks the completed tree, cross-phase interactions, every planned feature, adversarial behavior, and plan sufficiency; invoke its objective run-or-no-op decision and write the evidence section. |
| "This phase changed no CI, so I'll skip 8.3." | 8.3 is a no-op-safe step that also checks whether the workflow is optimized (path filters, concurrency, caching, gated matrix jobs). Invoke it every phase so CI drift and minute-bloat surface early. |
| "The plan has no final refactor phase, so there's nothing to clean up at the end." | Plans generated before v3.11.0 lack the mandatory final phase; the 9.0 gate still writes `<version_dir>/development/<version>-last-phase-evidence.md`. Absence of the heading is not absence of the work. |
| "The heading existed so the work was done." | A last-phase title without the evidence file is incomplete. Each duty must quote a proving command or scan. |
| "Tests passed so the Goal landed." | Green tests are not a Goal-vs-codebase review. Re-read the plan Goal and inspect the artifacts; a miss blocks `/update release` unless a known-gap records it. |
| "Skip this last-phase duty; it will be a no-op." | There is no skip license on Phase 9. Omit a duty only by writing a `QG` or `DF` known-gap with Source phase, Plan reference, Reason, and Suggested next step, or refuse. |
| "This phase is done, so I'll write the full summary and stop." | In full mode a phase boundary is a progress line, not an ending. The run ends only when the checker reports a terminal verdict; a per-phase summary that reads as "done" is exactly where full runs used to stall. |
| "Full access approves any CI, permission or secret change." | The completion contract authorizes only explicitly scoped actions and paths under genuine approval plus trusted mode evidence. Unknown mode, excluded actions and changed scope still require a manual decision; checks and edit preservation still apply. |
| "Green tests alone let me create a release tag." | `/update release` owns the version bump, changelog, tag and push. It checks recorded authority through the completion contract as well as all required release evidence. |
| "full should also push each phase so CI stays green." | Every non-final phase is commit-only in every mode, `full` included. Pushing per phase bills a full pipeline run to validate work the plan itself says is incomplete, and seven red checks on incomplete work teach the reader to ignore red checks. The driver never tags or pushes a release. |
| "The user can just pick the push option if they want it." | There is no push option on a non-final phase; 8.11 offers Commit / Amend / Stop. A user who explicitly ASKS to push still gets it, after a one-line statement of the cost. The rule removes the default, not the user's authority. |
| "I will update the CI workflow now while I am in this file anyway." | A phase changes pipeline files only when the pipeline is that phase's explicit deliverable. Per-phase pipeline authorship is what produces a different topology per phase and a pipeline nobody can run locally; 8.3 records the impact and 9.0 duty 5 reconciles it once. |

## Handbook gate handoff

The final phase invokes `[[technical-documentation]]` through `references/handbook-refresh.md` on the actual candidate before local completion and feature publication. The final-phase template must name recursive source/output inventory, code-claim review, reproducible checks and final rendered evidence. `/update release` rechecks the merged candidate before version mutation and rechecks affected outputs afterward. Failed required evidence blocks either handoff; unchanged dependency hashes reuse existing output. The runbook owns execution order.

## Verification

- [ ] Plan and phase resolved; `is_final_phase` set from the five signals and shown in the pre-flight summary.
- [ ] The plan runs in its own worktree, created through `[[using-git-worktrees]]`, with its path recorded in the phase evidence; or a branch fallback was stated explicitly.
- [ ] Phase 0 recorded the queue assessment and, for a minor run, actual worker handles, exclusive signed claims, worktree/base identity and status; eligible plans dispatched when capacity opened, or a named serial fallback was recorded.
- [ ] On the final phase, worktree retirement followed the completion contract after green merged integration: verified removal and worktree-list proof, or the exact executor KEEP and permitted minor-controller/worker deferral, were quoted under `## Worktree teardown`; final minor cleanup remains required.
- [ ] Code implemented subtask by subtask, in scope, with deviations logged.
- [ ] Lint clean; this phase's blast-radius tests ran; the five-part GO/NO-GO gate evaluated 0 failures in scope, no coverage regression on touched files when an existing cheap measurement is available, with new coverage collection deferred to the final phase, 0 lint errors, a successful build, and a cheap proportional real-boundary functional smoke whose expected and observed behavior matched through `[[functional-verification]]`, or the bypass was documented as a gap.
- [ ] Phase 8 ran all eleven steps in order; 8.3 recorded CI impact without changing a pipeline file; 8.4 wrote exactly one `## Plan delta` disposition with evidence and the consequence for remaining phases in `<version_dir>/development/history/<phase-session-history>.md`; only a blocking delta updated the plan or became a `DF` or `QG` gap; every non-final phase ended commit-only with no push in every mode; known gaps and session history are current.
- [ ] On the final phase: `<version_dir>/development/<version>-last-phase-evidence.md` exists with one quoted section per duty, including `## Goal-vs-codebase review`, `## Tier 3 deep pass`, and `## Publication and integration`; the deep-pass duty invoked `[[functional-verification]]` and its `references/deep-pass.md`, or a recorded `QG` or `DF` gap names the omission; duty 5 reconciled CI/CD with observable evidence per field or recorded the difference as a known gap; 9F pushed once under verified recorded authority and merged only on green required checks; a missing file, an unresolved Goal or deep-pass miss without a recorded gap, or a non-green integration blocked `/update release`; tag and release actions passed through `/update release` with matching authority.
- [ ] Driver modes, when used, iterated incomplete phases without dropping gates; a failed quality gate stopped the loop; one-phase invocations were unchanged.

## Related Skills

- [[implementation-plan]] -- produces the plan this skill executes; its mandatory final phase (v3.11.0) is what the 9.0 gate runs.
- [[known-gaps-tracker]] -- the per-minor gap log this skill appends to (8.5) and reconciles on the final phase (9A).
- [[project-refactor]] -- the cleanliness engine (empty-dir/duplicate/orphan/structure) the final-phase gate invokes, alongside [[docs-layout-refactor]] for the docs tree.
- [[platform-contract-verification]] -- verifies host discovery in the same final-phase pass where cross-installer parity verifies delivery.
- [[session-history]] -- completes the per-phase session-history file (8.9) while preserving the Plan-delta section written in 8.4.
- [[functional-verification]] -- owns the proportional Phase 7 exercise procedure and the Phase 9 whole-plan `references/deep-pass.md` runbook; this skill owns when those procedures gate the lifecycle.
- [[code-commit-workflow]] -- the commit-message conventions the 8.10 step follows, and the plan-context mode that makes a phase boundary the commit unit; `/update release` owns the release commit/tag/push.
- [[cicd-architect]] -- the canonical lifecycle this skill executes; 8.3 records against it and 9.0 duty 5 runs its existing-pipeline comparison.

---

**Version**: 1.0.0
**Last Updated**: July 2026
