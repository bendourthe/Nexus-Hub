# Implement-Phase Runbook

Summary: the ordered implementation, verification, publication and release procedure for an approved plan or minor.
Read this when: running a phase, continuing a full run, or coordinating minor members.
Covers: scope resolution, the canonical authorization handoff, focused checks, final validation, integration and cleanup.

The complete, ordered procedure for the `implement-phase` skill. `SKILL.md` links here; the agent reads this on demand when actually running a phase. Reconstituted from the pre-v3.2.0 `/implement-phase` command and updated to v3.x reality: docs paths follow the `[[docs-layout-refactor]]` Version-directory resolution scheme (`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`), old flat commands are retargeted to their consolidated equivalents (`/update gitignore`, `/update docs`, `/update devlog`, `/session history`, `/commit`, `/test`), and the final-phase release work hands off to `/update release`.

## Phase 0: Resolve plan, version, and phase

1. **Parse the invocation.** First positional arg is a plan slug, a plan file path, or a version label; later args may be a phase and/or a driver mode. Disambiguate the first arg: contains `/` or ends in `.md` -> file path; matches `v?\d+\.\d+\.\d+` -> version; matches `v\d+\.\d+` exactly -> minor scope; else -> slug. A minor scope runs every member plan that `python ~/.nexus-hub/scripts/check_plan_completion.py members vX.Y` prints, each through the minor coordinator below under one minor record, with compatible implementation concurrent and publication in version order; the membership rule, the per-plan-record refusal, and the resume rule live in the completion contract. A malformed minor token (`v0.5.x`, `v0`), a per-plan mode token after a minor, or an empty minor (`No queued plans in vX.Y`) prints usage or that line and starts nothing. Phase accepted as a number (`3`), slug (`phase-3`), or quoted name. Mode resolution: `/implement <plan>` and bare `/implement` run the FULL driver (the default since v4.13.2); `phase <N>`, `phase-N`, a quoted phase name, or `next` runs ONE phase; `phase-by-phase` is opt-in; `full` and `in-full` are aliases for the default; `/implement pause` pauses the current run. Mode tokens are later whole tokens only - do not treat a slug that contains "full" or "phase" as a substring as a mode. An unknown later token prints usage and does not start a phase.
2. **Search for plans**, deduping by absolute path:
    - Canonical: `docs/v*/v*/plans/*.md` (the two-level minor-grouped scheme).
    - Legacy: `docs/v*/plans/*.md` (flat) and `docs/versions/v*/v*/plans/*.md` (old three-level), plus the pre-rename `docs/**/implementation-plan.md`.
    - When a plan exists at both canonical and a legacy path, prefer canonical and surface: `Inconsistent layout: plan present at both canonical and legacy paths. Using canonical. Run /update refactor to migrate.`
3. **Plan selection.** File path -> resolve directly. Slug -> filter to `docs/**/plans/<slug>.md`; one match uses it, multiple asks which version. Version -> filter to that version. No arg -> the lowest `Status: queued` plan by semantic version whose queued predecessors are merged; show it as the first line of the upfront round, and ask when two plans qualify or the order is ambiguous. No plan -> report paths searched and suggest `/plan`.
4. **Parse the plan** to extract the phase list (numbers, names, completion status).
5. **Phase selection.** Full mode selects the first phase still needing implementation or focused verification without another question. A one-phase invocation with no phase identifier shows the list and asks once. For `next`, apply the deferred-final-validation rule from Phase 4 when only comprehensive tests remain pending, keeping those task IDs unchecked. Re-implementing a completed phase changes the requested work and needs an explicit decision.
6. **Final-phase detection** (`is_final_phase`) - use ALL five signals, never the user's claim alone:
    - **Phase ordering**: target is the numerically highest phase, or the last `## Phase N:` by document order.
    - **Title heuristics**: "Polish", "Final QA and Release", "Release Prep", "Wrap-up", or (v3.11.0+) "Architecture Refactor, Known-Gaps Reconciliation, and CI/CD".
    - **Prior-phase completion**: every prior phase shows `[x]` or has a session-history file under `<version_dir>/development/history/`.
    - **Plan metadata**: honor an explicit `Final-Phase: N` marker.
    - **Adjacent plans**: the plan is the only one under the active version dir.
    Prior unchecked tasks that consist only of recorded deferred final validation do not create a conflict when the phase history and local commit prove implementation and focused checks are complete. Keep those tasks unchecked until the final evidence exists. On any other conflict (numerically last but prior phases unchecked), set `is_final_phase = false` and say so.
7. **Pre-flight summary** - show plan, phase, status, prior-phases-complete, and final-phase (with a note that the release-readiness workflow runs after Phase 8 when final). In one-phase mode, follow the active instruction template's `Consequential Decisions` rule and wait for confirmation before any code change. In full mode the upfront round (Phase 0a) replaces this confirmation for every phase of the run.

### Phase 0a: Upfront approval round (full mode)

A full run asks once. Before the first phase:

1. **Inspect the existing run first.** Show open blockers and pause state. Apply the completion contract's "Authorization policy" before requesting any new consent. Continue automatically only when native verification covers the exact action; a real failed check, edit conflict or tampered record remains unresolved. When a manual decision is needed, use the contract's "Manual decisions" procedure, keeping the same pending question for unchanged conditions. Resume never silently clears a technical blocker.
2. **Describe the initial scope once.** List the resolved plan or frozen minor members, repository and branches, releases, cleanup, spend caps, exclusions and the bounded corrections the run requires. Explain the concrete results in plain language. The completion contract owns which classes, bounds and explicitly named CI/security paths can be authorized; do not infer blanket permission or repeat unconditional prohibitions from older templates. Include the required carry, archive and closing-pull-request classes for the resolved run.
3. **Render and capture the genuine initial decision.** Write the exact approval specification to `<file>` and the outcomes and parallel-plan display data to `<summary>` using [`approval-page.md`](approval-page.md). Run `python ~/.nexus-hub/scripts/check_plan_completion.py record render <plan> --session <id> --approvals <file> --summary <summary> --question --platform <row>`. Use the contract's manual decision procedure and native capture path; never synthesize a user reply, trusted mode event or approval code. Run `record create <plan> --session <id> --approvals <file>` only after genuine capture and require `RECORDED`. Report any refusal reason honestly. A platform without a verified capture path cannot record unattended authority.

    For a minor scope, pass `--minor vX.Y` in place of `<plan>`. In a later session, use the native resume procedure from the completion contract, preserving the frozen scope and original limits; a different session does not inherit authority merely by reading the record.

4. **Show the native decision display.** The approval-page reference owns wording and layout; the completion contract owns the decision and capture rules. A supported host question tool may show Approve and Decline, but a click counts as a recorded answer only through a verified native receipt path. Otherwise request the native short reply as an actual user message. The host goal is advisory; the checker decides done.

From here on, every approval point in this runbook, the final-phase template and delegated skills follows the completion contract's "Authorization policy". Reuse verified in-scope authority without repeated consent, retain native provenance, and obtain a concise manual decision for an uncovered action. Record technical blockers once with current evidence; repeated observations do not create duplicate blockers or new questions.

### Phase 0b: Isolate the plan in its own worktree

A plan runs in a dedicated **worktree**, not merely a branch in the shared checkout. A branch alone serializes work: a second plan cannot start without switching the one checkout, and a switch underneath a running session silently changes the files it is editing.

1. **Detect existing isolation first** and create the worktree through `[[using-git-worktrees]]`, which owns the mechanics (native tool before raw `git worktree`, setup detection, clean-baseline check). Do not re-derive that procedure here.
2. **Name both consistently**: branch `feat/<version>-<slug>`, worktree directory `<repo-parent>/<repo-name>-<version>-<slug>`. A predictable directory is what lets the release step find and remove it later.
3. **Already inside a worktree for this plan** -> continue in it; never nest a second one.
4. **Worktrees unavailable** (no `git worktree`, or the user declines) -> fall back to a branch in the current checkout, say so in one line, and note that parallel plans are unavailable this session.

Record the worktree path in the phase evidence file. The release step reads it to verify teardown, and a path recorded nowhere is a directory nobody removes.

### Phase 0c: Assess and dispatch parallel plans

Delegate compatibility to [[plan-queue-assessment]] and write its assessment, including named unknowns. A single-plan invocation reports compatible queued plans without starting plans outside its approval. A minor invocation automatically dispatches eligible approved members through the minor coordinator below. A launch suggestion alone is not dispatch evidence: record the actual returned agent handle, branch, linked worktree, base, signed claims and status. State the assessment's overlap basis as named paths and prerequisites, or their verified absence. If no plans qualify, explicitly report "no eligible parallel plans" with the named conflicts, missing prerequisites or unknowns; never omit the assessment. If the assessment owner is unavailable, mark compatibility not covered and execute serially; never reconstruct its ranking rules from memory or infer safety from task paths alone.

## Phase 1: Pre-implementation review

Read the full plan and the target phase in detail (goals, acceptance criteria, subtasks, files, dependencies). Check prerequisites using task results, phase histories and `git log` references. A generic prior-phase prerequisite is satisfied by completed implementation, a passing focused gate and its local commit when the only unchecked tasks are recorded in `## Deferred final validation` with original task IDs and a final-gate destination. A specifically required earlier test result, safety proof or recorded acceptance criterion remains blocking. Scan the codebase for files the phase touches. Report the goal, subtask count, likely-affected files, and prerequisite/dependency status before implementing.

### Queue re-assessment (plan entry and every phase entry)

A plan was written against the codebase as it stood then. It executes against the codebase as it stands now, after the plans queued around it have moved. Re-validate that before writing code, not after.

Run `[[plan-queue-assessment]]` against this plan and the enumerated queue. Do NOT restate its rules; it owns them. Two scopes:

- **Plan entry**, once, when the first phase of a plan begins: assess the whole plan's assumptions and touched-file surface.
- **Phase entry**, every phase: assess this phase's stated prerequisites and target files.

Keep it cheap and proportional. It reads the plan and the queue inventory; it does not re-run the suite.

Write the result into the phase session history as evidence for the existing `## Plan delta` section (step 8.4). **This step supplies evidence to that disposition; it does not introduce a second vocabulary.** A finding requiring a plan edit is blocking and follows 8.4's existing escalation path. **A finding of no drift is written explicitly** - an unwritten check is indistinguishable from a skipped one, which is the exact pattern that turns four added assessment steps into ritual rather than evidence.

### Model-routing pre-flight

Before Phase 2 begins, run `[[model-routing]]` in implementation mode:

1. Read the target phase's `Recommended model tier`, `Recommended effort level`, and `Rationale` plus its current-provider map cell. Continue accepting historical `Recommended model` / `Rec. model / effort` fields.
2. Re-score the phase. When web access is available, refresh the four-provider candidate from official sources and validate/render it through `model-routing/scripts/model-map.{sh,ps1}`. Otherwise use the helper's validated dated fallback.
3. Enumerate the selected provider's live platform surface. If the mapped model is unavailable or the new score is higher, surface the delta and default to the same or stronger tier. Never silently downshift.
4. Present the recommendation and apply the completion contract's authorization policy. In full mode, a supported in-scope switch within approved spend and exclusions proceeds without another consent question; uncovered upshifts require a manual decision. Then switch only through the platform's supported posture: scripted on Codex/Antigravity/Gemini CLI, one user action on Claude Code, picker-only on Cursor/Copilot/OpenCode. If refresh or enumeration is unavailable, state the fallback and continue on the plan tier or current session model.

During troubleshooting, repeated failures may trigger an upshift under the same authorization and spend limits. Never downshift mid-phase.

## Phase 2: Implementation

Work subtask by subtask in plan order. After each subtask, confirm the code compiles/imports before moving on (do not accumulate broken subtasks). Log deviations inline with `# DEVIATION:` and keep a running list for Phase 8. Stay in scope: no refactors outside the phase boundary, no speculative features, no unrelated file changes. Compile/import-check the whole phase before linting.

## Phase 3: Lint and format

Detect the changed languages and run the repository linter and formatter on the touched files or smallest supported package scope. Avoid repository-wide auto-fixes. Resolve errors in scope before testing; never suppress lint rules.

## Phase 4: Test execution and coverage

Run focused tests covering the files and behavior changed in Phase 2, plus the repository's cheap fast checks (for Nexus-Hub: `python scripts/ci/run.py --profile fast`). Select tests through [[cicd-integration]], which owns selection and evidence invalidation. Capture the command, source scope, environment, terminal exit and passed/failed/skipped counts. Fix failures in that scope before continuing.

**Complete implementation before comprehensive validation.** The full suite, project coverage collection and its threshold, coverage-driven augmentation, broad platform validation, E2E sweeps, performance benchmarks and whole-plan deep passes wait until all implementation tasks are complete in the final phase. Run a specific expensive check earlier only when it is the phase's explicit deliverable or a named risk requires that check before dependent work; record the command and reason. This exception does not authorize a whole-suite run by default.

If the blast radius is uncertain, inspect the affected dependencies and run the smallest relevant subsystem checks. Record the uncertain integration coverage for the final phase rather than defaulting to the full suite. A known failure or an unverified safety-critical prerequisite blocks dependent work; deferred comprehensive testing is not permission to ignore either.

For existing plans, carry generic comprehensive commands from intermediate phases into the `## Deferred final validation` inventory owned by [[cicd-integration]]. Record original task IDs and keep those tasks unchecked until their final evidence exists. A phase with completed implementation, passing focused checks and a local commit can advance with only these recorded validation obligations pending; report that distinction explicitly. This does not permit advancing past a failed prerequisite or a required earlier acceptance check.

## Phase 5: Test augmentation

Write tests for genuinely NEW behavior this phase introduced that no existing test reaches, and enforce project standards (AAA, parametrize, fixtures in `conftest.py`/setup, no `sleep`). Then proceed to Phase 6.

**Coverage-driven augmentation to the 80% threshold is a final-phase duty (9B), not a per-phase one.** Chasing a coverage number against a half-built interface produces tests that a later phase rewrites or deletes, so the work is paid twice and the second payment is a merge conflict against the agent's own output. A phase-scoped test proving the new behavior is durable; a test written only to move a percentage is not. Record what was left for 9B rather than expanding this step.

## Phase 6: Troubleshooting loop (max 3 iterations)

Read every failure (name, message, stack). Classify each `IMPL` / `TEST` / `ENV`. Apply targeted fixes (fix impl for IMPL; fix the test and document why for TEST; resolve and log for ENV). Re-run and check the failure count dropped. Stop early when green. After 3 iterations with failures remaining, stop and present the unresolved list with options: A. Skip failing tests and continue; B. Abort for manual investigation; C. Extend the loop N more iterations; D. Escalate by failure class as Step 7 of `[[model-routing]]` routes it (confirm first, upshift only). Follow the active instruction template's `Consequential Decisions` rule before asking. Wait for the answer.

## Phase 7: Quality gate (GO / NO-GO)

Evaluate five gates: all tests passing in this phase's blast-radius scope (0 failures), coverage not regressed on the files Phase 2 touched when an existing cheap measurement is available (do not start coverage collection here; the >= 80% project threshold is asserted once, in 9B), 0 lint errors, build/compile succeeds, and the phase's own feature was exercised and observed through its primary real boundary with expected behavior matching observed behavior. Delegate what exercise and evidence count for the artifact type to `[[functional-verification]]`. Keep this fifth gate cheap and proportional: one representative phase-scoped smoke, not the whole-plan deep pass or another full suite. Documentation-only release evidence uses that skill's explicit no-runnable-feature path rather than a silent skip. All five pass -> run the post-phase sequence. Any failure REOPENS the phase: return gates 1-4 to the owning Phase 3-6 step; return a fifth-gate mismatch or blocked exercise to Phase 2, fix the implementation or required evidence, then rerun the proportional smoke and all of Phase 7. Bound this recovery by the Phase 6 three-iteration budget. Only when that retry budget is exhausted or a required input remains unavailable may the maintainer choose, after the active instruction template's `Consequential Decisions` walkthrough: A. Proceed with an explicit `QG` known gap owning the failed gate; B. Stop for manual resolution.

**Verification behaviors.** Read the phase's verification effort: the optional `**Recommended verification effort**` plan field, or the pre-flight re-score when it is higher; an absent field equals the phase's effort, and no edge-case-density field is read from the plan. When the verification effort is above the phase's effort, request the applicable behaviors from [`verification-behaviors.md`](verification-behaviors.md) inside the phase's blast radius and quote each result as evidence; a missing result is a NO-GO. Otherwise the behaviors are advisory: request those that apply inside the blast radius, and record a missing result in the phase history instead of failing the gate. Keep this step cheap and proportional: it never widens the test scope beyond the blast radius and never re-runs gate 5's exercise.

## Phase 8: Post-phase completion sequence (every phase)

Run every step in strict order at the end of EVERY phase (validation first, then documentation, then commit). Steps are no-ops when there is nothing to do, but each MUST be invoked. Wait for each to complete before the next.

- **8.1 `/update gitignore`** - ensure new artifacts/caches are ignored. Report `0 patterns added` when nothing is new.
- **8.2 Test review (post-phase pass)** - Reuse Phase 4-7 results when their tested source, dependencies, configuration and environment are unchanged; record the receipt instead of rerunning the command. If a correction changed those inputs, rerun only the affected checks selected through [[cicd-integration]]. Confirm new behavior has appropriate tests or recorded boundary evidence; documentation-only artifacts need no artificial test per file. Log remaining test gaps as `MT` in 8.5 without an augmentation loop.
- **8.3 CI impact record (per-phase, no remote run)** - detect the active CI system, then RECORD this phase's impact against `[[cicd-architect]]`: cross-check Phase 2 modifications against CI declarations (new script command, new runtime env var as a secret reference, new dependency picked up by install, new test path, new artifact) and state whether the existing pipeline already covers each. A no-op record ("no new commands, dependencies, env vars, test paths, or artifacts") is a valid outcome and must still be written.
    - **Do NOT run a per-phase optimization pass and do NOT change a pipeline file**, unless CI/CD is THIS phase's explicit deliverable. Per-phase pipeline authorship is what produces a different topology per phase and a pipeline nobody can run locally; the actual comparison, proposal, and migration happen once, in the terminal phase (9.0 duty 5), against the canonical contract.
    - Anything the record shows the pipeline does not cover becomes an input to that terminal reconciliation, and a `QG` entry in 8.5 if it is material. Never silently rewrite a CI config at any point.
- **8.4 Plan-delta note (always written)** - decide whether implementation showed this phase's plan to be **No delta**, **Wrong**, **Incomplete**, or based on a **False assumption**. Write exactly one primary disposition under `## Plan delta` in `<version_dir>/development/history/<phase-session-history>.md`, with the observed evidence and the consequence for every remaining phase. Create the current phase history file here if needed; step 8.9 completes it without removing or weakening this section. A non-blocking delta stays in session history and informs later work without plan or gap escalation. A blocking delta updates the plan before the driver continues or becomes a `DF` or `QG` known gap in 8.5 with Source phase, Plan reference, Reason, and Suggested next step. `No delta` is a considered, evidenced result and MUST still be written.
- **8.5 Known-gaps append** - via `[[known-gaps-tracker]]` (Append mode) into the correct `## v<MAJOR>.<MINOR>.<PATCH>` subsection of `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md`. Classify `# DEVIATION:` markers as NI/DF/BG; skipped failures as BG; coverage/untested-file gaps as MT; suppressed lint/warnings as WN; bypassed gates and unapproved CI gaps as QG. Include blocking plan deltas from 8.4. Every item carries Source phase, Plan reference, Reason, Suggested next step. Recompute the patch subsection's Summary; update Last updated; do NOT finalize.
- **8.6 Docs cleanup audit** - run `[[docs-layout-refactor]]` in `--mode audit` (report to `<version_dir>/docs-cleanup-report.md`; no files move). Apply scratch-document cleanup only under matching authority through the completion contract; otherwise report the proposal and leave the files.
- **8.7 `/update devlog`** - what was implemented, decisions, deviations, test results (8.2), CI/CD changes (8.3), known issues (reference the gap log rather than re-listing).
- **8.8 `/update docs`** - sync README, API docs, architecture docs, inline guides. No-op when nothing changed.
- **8.9 `/session history`** - complete the standalone session-history file in `<version_dir>/development/history/` (plan reference, subtasks, test results, CI/CD edits, deviations, next steps) while preserving the required `## Plan delta` section written in 8.4.
- **8.10 `/commit` (generate the message)** - structured, sectioned-bullet message scoped to the phase, including the known-gaps file, docs-cleanup report, session history, and every touched file. Sectioned bullets grouped by component; dedicated Tests / CI/CD / Known gaps sections; no hard-wrapping; single blank line between sections. Produces the message; does not auto-commit.
- **8.11 Commit prompt (REQUIRED, every phase)** - a NON-FINAL phase is commit-only in every mode. Push, pull request, and remote CI belong to the final phase (Phase 9), which owns the plan's single publication. Offering push here would bill a full pipeline run to validate work the plan itself says is incomplete, and a red check on incomplete work teaches the reader to ignore red checks. Behavior by mode:
    - **One-phase (`phase <N>` or `next`), non-final:** follow the active instruction template's `Consequential Decisions` rule, then always ask, as a numbered list with one plain-language consequence each: 1. Commit only (the work is saved locally; nothing leaves this machine); 2. Amend (loop to 8.10 to reword the commit message before saving); 3. Stop (nothing is saved; the changes stay uncommitted in the working tree). Never proceed past 8.11 without a definite answer. On commit, use a heredoc and report the SHA.
    - **One-phase, FINAL phase:** do not ask this question at all. Run Phase 9, whose 9F step owns the final commit, the approval gate, and the single push.
    - **`full` non-final:** auto-select commit-only. Still generate the commit message (8.10); still use a heredoc; still report the SHA. Do not push. Replace the per-phase closing summary with ONE progress line (phase, commit SHA, checker score); the full Completed / Verified / Open / Next report runs once, when the checker reports `PLAN COMPLETE`, because a per-phase summary reads as "done" and is where full runs used to stop.
    - **`full` last phase:** run Phase 9 in full. After the evidence file is complete AND the integration result is green and merged, hand off to `/update release` (that command owns tag/push confirmation). Never tag or push the release from the driver.
    - **`phase-by-phase`, non-final:** replace the one-phase ask with this three-option menu and wait: (1) commit and continue; (2) commit and pause; (3) other. Cross-link `[[code-commit-workflow]]` for the commit itself.
    - **A user who explicitly asks to push a non-final phase** is making a deliberate exception, not hitting a menu option. State the cost in one line (a full pipeline run against knowingly incomplete work), then do what they ask. The rule removes the DEFAULT, not the user's authority.

## Driver loop (`full` / `phase-by-phase`)

Used only when the resolved mode is `full` (alias `in-full`) or `phase-by-phase`. One-phase invocations skip this section and run Phase 0-8 once.

A parent-bound minor worker follows the local phase sequence only: shared Phase 8 updates are proposals for the coordinator, not permission to write shared ledgers or trackers. It uses `check-member` through the coordinator instead of a standalone plan record and returns its local handoff at implementation-ready or `READY_FOR_COORDINATOR`. The minor coordinator below owns final comprehensive validation, publication and release; the standalone driver steps 3-4 do not authorize a worker to perform them.

1. Resolve the plan as in Phase 0. Start at the first incomplete phase even if the user named a later start. When an earlier phase has only recorded deferred final validation pending and its implementation, focused gate and local commit are evidenced, continue with the next implementation phase without marking the deferred tasks complete. Preserve model-routing pre-flight per phase.
2. For each incomplete phase, run the existing Phase 0-8 sequence unchanged (review, implement, lint, test, quality gate, post-phase docs). Apply the 8.11 variant above.
3. **Stop the driver only on a terminal verdict** from `python ~/.nexus-hub/scripts/check_plan_completion.py check` (the completion contract owns what each verdict means): a named blocker, the user's pause, or completion. A failed GO/NO-GO gate that the Phase 6 budget cannot recover becomes a blocker in the closed list, not a silent stop. Context pressure is handled by compaction, and a session that ends anyway is resumed by the turn-end gate or the `nexus-hub run-plan` runner from the run record; write session history before any compaction so nothing is lost.
4. After a successful last phase, require `<version_dir>/development/<version>-last-phase-evidence.md`, run integration, then `/update release` under the recorded release approvals, then cleanup. The run is over when the checker prints `PLAN COMPLETE`.
5. If the user is mid-`full` and chooses to stop, leave a continuation line they can paste.

## Minor driver (`/implement vX.Y`)

Used only for a minor scope. A single coordinator owns the approved minor record and drives every member through implementation, then ordered publication and release. `CK` below is `python ~/.nexus-hub/scripts/check_plan_completion.py`. Native admission rules and verdicts belong to the completion contract; queue compatibility belongs to [[plan-queue-assessment]].

Before the first worker reservation, install the matching check_plan_completion.py and completion_minor.py together and verify that turn-end gates and the runner resolve those updated helpers. Existing records without implementation claims retain their signature behavior. The first reservation adds signed controller binding; an older checker cannot verify that extended record, so do not mix helper revisions or downgrade readers after admission. Use the supported delivery path with edit preservation; never alter a record to make an older reader accept it.

### Implementation admission and automatic workers

1. **Assess the frozen queue.** Read the approved members and the live source, then obtain complete dependency/read/write claims from [[plan-queue-assessment]]. Preserve frozen plan prose with a release-scoped assessment sidecar. Do not treat release order as a dependency. Unknown or conflicting claims stay serial; a real implementation prerequisite must already be merged into the proposed worker base.
2. **Bound capacity once.** Detect the active harness's actual agent start, message and wait tools and available slots. Reserve capacity for the coordinator; admit no more workers than available slots and the remaining aggregate spend budget allow. Share the run's review and stabilization limits; never multiply caps per worker. If agent tools or worktrees are unavailable, state the reason and use serial implementation under the same ordered publication gate. Do not add a worker process engine or assume Dynamic Workflows exists.
3. **Create and admit an eligible worker.** Through [[using-git-worktrees]], create its approved branch and linked worktree from the assessed integration commit, or reattach to its exact registered identity on resume. Write a claims JSON file with `depends_on`, `read_paths` and `write_paths`. From the controller run `CK record member-implement-start --minor vX.Y --member vX.Y.Z --session <parent-id> --repo <controller> --worktree <worker-root> --head <base-sha> --claims <claims.json>`. Proceed only on native admission; never modify or re-sign a record by hand.
4. **Dispatch a whole-plan slice.** Invoke the actual harness agent tool with the admitted root/branch/base, parent minor/session/controller, plan and assessment paths, exclusive claims, prerequisites, testing cadence and a precise return contract through [[multi-agent-coordinator]]. Say the worker is not alone and must preserve others' edits. Include: `Do not write to persistent agent memory. You are a spawned subagent; only the parent session may record memory.` Do not invoke standalone `/implement` in a child or ask it to create approvals. Only the coordinator mutates signed state.
5. **Implement and observe.** Each worker implements its whole plan with focused checks, plan-specific history and one local commit per phase. It proposes shared metadata deltas separately: known-gaps ledgers, CHANGELOG, version/release metadata and docs/todos are coordinator-only. At each checkpoint the coordinator invokes `CK check-member --minor vX.Y --member vX.Y.Z --session <parent-id> --repo <controller>` for a read-only projection bound to the parent approval. Record actual terminal proof, not a worker's success assertion.
6. **Refill available slots.** Recheck merged dependencies, active claims, live worker state and remaining budget whenever capacity opens. Start another eligible member immediately without waiting for unrelated releases. Failed, interrupted and implementation-ready workers retain claims until native verified-merge retirement; a stopped handle does not free ownership. Resume the same addressable worker and registered worktree rather than creating duplicate writers. A genuine run blocker or pause stops new dispatch and reaches all workers at a safe checkpoint.
7. **Wait locally when ready.** A worker with pending real coordinator-owned implementation tasks returns `READY_FOR_COORDINATOR`, naming original task IDs and proposed changes; those tasks stay unchecked, are not generic validation deferrals, and the plan is not yet fully implemented. Otherwise it returns implementation-ready with commit IDs, changed paths, focused proof, plan-specific evidence, pending comprehensive validation and proposed coordinator deltas. It does not push, open a pull request, merge, tag or release. The coordinator continues other eligible implementation while this member waits for its publication turn.

### Ordered publication admission

1. **Select the lowest unreleased member.** Native `member-start` decides predecessor readiness through the completion contract. A predecessor's pending cleanup alone does not block publication; every other predecessor predicate must pass. The coordinator completes missing release/back-merge work under that member's recorded approval. A later ready worker remains local while this gate is closed.
2. **Refresh the base.** Fetch `origin` and tags, confirm the live target contains the prior release/back-merge, then refresh only this worker's unpublished commits onto that integration tip. Preserve its phase histories and resolve scoped conflicts; do not reset another checkout. Reassess any expanded claims before writing outside the admitted surface.
3. **Record publication admission.** From the controller run `CK record member-start --minor vX.Y --member vX.Y.Z --session <parent-id> --repo <controller> --head <refreshed-integration-sha> [--coordinator-claims <coordinator-claims.json>]`. The optional JSON is `{"write_paths": ["<exact-relative-file>"]}` and names only coordinator changes traced to the frozen plan or standard release duties. Native admission signs those exact paths and rejects conflicts with other active workers. This records the publication base, not permission to skip final checks. Refusals remain native evidence; fix their cause without changing signed state manually.
4. **Finish and validate the complete plan.** After publication admission the coordinator applies the signed proposed metadata and source deltas sequentially, tests them and completes their original task IDs. If a worker requested coordinator work before finishing its local phases, satisfy those tasks and resume that same worker for every remaining phase. Do not treat publication admission or READY_FOR_COORDINATOR as completed implementation or permission to push. All implementation tasks, including real coordinator-owned work, must be complete before comprehensive validation. Audit changed paths against the union of worker writes and signed coordinator paths. Run Phase 9's comprehensive local gate on the refreshed final tree, reusing only unchanged evidence through [[cicd-integration]]. A failed or uncertain affected check holds publication. Keep deferred comprehensive tasks unchecked until their passing final evidence exists.
5. **Publish and release in order.** Run 9F once: final commit, approval scope check, first branch push, hosted required checks, and green merge. Reproduce failures locally before a bounded stabilization push. Hand off `/update release` only after current green merged integration. Verify its tag, main ancestry and back-merge before admitting the next publication. Cleanup remains required for final `MINOR COMPLETE` but does not serialize independent implementation.
6. **Preserve completion evidence.** After independently verified merge and integration ancestry, parent-bound projections read canonical merged plan/evidence through the controller, so approved removal of the worker does not erase proof. Before merge, a missing or mismatched registered worktree is cannot-verify. Keep the controller active and retain its signed evidence through final minor close; do not rehome or reseal it by copying state.

A blocker in any member stops the whole minor run: record it with `CK record block --minor vX.Y --member vX.Y.Z --category <category> --evidence <text>` and report it. Retain every worker's claims and local work for the approved continuation.

### Minor close (after the last member's release)

Run once, after the last member is `PLAN COMPLETE` and its back-merge is on `origin/develop`. Record every step's command and output in `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/development/vX.Y-minor-close-evidence.md`, which moves with the archive.

1. **There is always a close.** Every minor record carries `archive-minor`, `minor-close-pr`, and `cleanup-merged` (the checker refuses a minor spec without them), and the archive travels in the closing pull request, so steps 2 to 10 always run. When the `gap-migration` list is empty, the close carries only the archive.
2. **Cut the closing branch** from the post-release `origin/develop`: `git fetch origin` then `git switch -c chore/close-vX.Y origin/develop`.
3. **Migrate** each frozen unfixable gap: `python ~/.nexus-hub/scripts/minor_close.py migrate --minor vX.Y --id <id> --reason <reason> --evidence <text>` (Migrate mode of `[[known-gaps-tracker]]`). Fix every fixable gap instead of migrating it.
4. **Archive** (the record always carries `archive-minor`): `python ~/.nexus-hub/scripts/minor_close.py archive --minor vX.Y --apply` ("Archive a closed minor" in `[[docs-layout-refactor]]`). It commits once on the closing branch.
5. **Local fast gate**: the project's fast profile (Nexus-Hub: `python scripts/ci/run.py --profile fast`) must pass.
6. **Push once and open one pull request** to develop under `minor-close-pr`: `git push -u origin chore/close-vX.Y`, then `gh pr create --base develop --head chore/close-vX.Y`.
7. **Wait for the required checks.** A red required check: reproduce it locally, fix it narrowly on the closing branch, and re-push under the completion contract's scoped repair authority and verification budget; never re-run it blindly. When develop moved since the branch was cut, merge `origin/develop` into the closing branch (never rebase) and re-run step 5 before the re-push.
8. **Merge** the pull request under `minor-close-pr` once its required checks pass.
9. **Back-merge** `main` into `develop` when `main` has commits develop lacks (`git merge-base --is-ancestor origin/main origin/develop` fails), under `minor-close-pr`.
10. **Final cleanup pass**: `python ~/.nexus-hub/scripts/cleanup_merged.py --apply --receipt --minor vX.Y --session <id>`, after the last merge (the closing pull request, or the last member's when step 1 skipped the close), under the recorded `cleanup-merged` approval.
11. **Verdict**: `CK check-minor vX.Y`. The run is over only when it prints `MINOR COMPLETE vX.Y <head> <nonce>`; an `INCOMPLETE` line names the next unmet id.

## Phase 9: Final-phase completion workflow (release-readiness)

For a Nexus-Hub candidate, the read-only `python scripts/check_release_preconditions.py --handbooks` must pass before publication. A full inventory and final content/rendered evidence are required; known gaps cannot waive a failed document.

During living-documentation reconciliation, run `technical-documentation`'s `references/handbook-refresh.md` on the actual final-phase candidate before the local completion/publication gate. Update both handbook views with approved settings and retain freshness, coverage, and browser evidence. The subsequent `/update release` handoff rechecks the integrated candidate before its version bump; it does not defer all handbook work until after publication. Existing CI/integration and release approval gates remain in force.

Runs only when `is_final_phase = true` AND Phase 8 completed cleanly. If `is_final_phase` is false because prior phases are unchecked, do not run Phase 9; say so and stop the release handoff.

Every last-phase duty is fail-closed. Announce the queued sub-phases. A duty is omitted only by writing a known-gap (`QG` or `DF`) with Source phase, Plan reference, Reason, and Suggested next step. If the user asks to skip a duty without that recorded gap, refuse. Every step is idempotent and verifies its authority through the completion contract before committing, archiving or tagging; covered actions do not prompt again.

### Last-phase evidence file (blocking)

Write `<version_dir>/development/<version>-last-phase-evidence.md` with one section per duty below. The version prefix matters because several patch plans share one minor directory; the checker accepts the unprefixed legacy name only when it names the plan file. Each section quotes the proving command or scan. An empty finding is allowed only when the scan output is quoted. A missing file, a missing section, or an unresolved Goal-vs-codebase review or Tier 3 deep-pass finding without a recorded known-gap BLOCKS the 9C-9E `/update release` handoff. Completing every prior-phase checkbox is not evidence the Goal landed.

Required sections:

1. Architecture refactor
2. Known-gaps reconciliation
3. Living docs architecture
4. Git-tree hygiene
5. CI/CD coverage
6. Tier 3 deep pass
7. Goal-vs-codebase review
8. Human/manual testing suggestions
9. Full-suite testing and stabilization
10. Publication and integration

### 9.0 Mandatory refactor + known-gaps + CI/CD gate (v3.11.0, fail-closed)

Before the release-readiness sub-phases, run the last-phase duties on the plan's last phase - **even when the plan was generated before v3.11.0 and has no explicit "Architecture Refactor, Known-Gaps Reconciliation, and CI/CD" phase** (detect its absence and run the gate anyway):

1. Run `[[project-refactor]]` (empty dirs, duplicates, non-version orphans, structure complexity) and `[[docs-layout-refactor]]` to clean the layout - propose-then-apply, with confirmation (explicit, or the `refactor-moves` approval recorded in the run record for moves inside plan-touched folders); repair references for anything that moves. Quote detector output under `## Architecture refactor`, including an empty finding.
2. Reconcile known gaps via `[[known-gaps-tracker]]` for this version AND every other `docs/**/known-gaps.md` whose Status is in-progress or whose Open Items remain. Glob both canonical and legacy layouts. If a file is unreachable, record the glob result and continue with what was found. This feeds 9A. Quote the disposition under `## Known-gaps reconciliation`.
3. Check living docs architecture (`docs/handbooks/` mapped sources/outputs in legacy or topic layouts + code-grounded overview + technical companions, `docs/decisions/`, living `docs/README.md` / `DEVLOG.md` / `todos.md`). Self-gated: never invent `docs/testing/` or `docs/validation/`. Quote the check under `## Living docs architecture`.
4. Run `python ~/.nexus-hub/scripts/check_release_preconditions.py --branches --repo-settings` and quote it under `## Git-tree hygiene`. Report branch hygiene; removal happens only through `cleanup_merged.py --apply` under a recorded approval.
5. Run the TERMINAL PIPELINE RECONCILIATION via `[[cicd-architect]]`: DETECT the provider, COMPARE the pipeline with its canonical contract, PROPOSE each difference with its cost and risk, verify AUTHORITY through the completion contract, APPLY only covered or manually approved changes, run affected checks through [[cicd-integration]], and RECORD declined or environment-only differences as known gaps. Trusted full access permits continuation only for explicitly scoped changes and paths; explicit exclusions remain binding. Keep the comparison's required per-field evidence, including profiles, events, runner selection, required aggregate check, permissions, immutable action references, caching, concurrency, path scoping, retention, reports, deployment boundaries and recovery. Comprehensive validation waits for 9B after implementation is complete. This is the plan's terminal pipeline reconciliation unless CI/CD is an earlier phase's stated deliverable. If multiple installers ship, their declarative parity check remains a hard gate with `[[platform-contract-verification]]`. Quote results under `## CI/CD coverage`.
6. Invoke `[[functional-verification]]` and load its `references/deep-pass.md` runbook. Record the objective blast-radius verdict first; ambiguous evidence selects `run`, while a valid no-op still writes its diff evidence. Follow the selected deep-pass path in order and quote its final record under the literal `## Tier 3 deep pass` heading in `<version_dir>/development/<version>-last-phase-evidence.md`. This duty is fail-closed: an unresolved finding blocks publication unless disposition is recorded through the owning gate and gap skills, and the duty may be omitted only by recording a `QG` or `DF` known gap with Source phase, Plan reference, Reason, and Suggested next step. A reasoned no-op is completion of the duty, not an omission.
7. Independent Goal-vs-codebase review: after the deep pass reaches its terminal disposition, re-read the plan header Goal and Goals First / Definition of Done, then inspect the resulting codebase as if this agent had not implemented the phases. The `## Goal-vs-codebase review` section MUST list the plan Goal restated (fail closed and name the missing Goal if the plan has none), the code/docs artifacts that satisfy it, and any gap. A miss is a blocking finding or a new known-gap, not a pass.
8. Human/manual testing suggestions, last phase only. Quote them under `## Human/manual testing suggestions`.
9. Run the ADVISORY model-prompting-profile staleness check via `[[model-prompting-research]]`, the same step `/update release` performs as governance step 6. Invoke `python scripts/check_model_prompting_freshness.py --advisory` after enumerating the live roster. Do NOT duplicate its logic here: invoke the skill. It NEVER blocks the phase, never re-stamps a freshness marker, and degrades to a logged no-op offline.

Keep every correctness gate and verify action authority through the completion contract; a matching recorded authorization replaces repeated consent.

### 9A. Resolve known gaps and deferred work

Re-read `<version_dir>/known-gaps.md` `## Open Items`. Grep the codebase for `TODO`/`FIXME`/`XXX`/`HACK`/`# DEVIATION:` introduced this version; add unrecorded ones via `[[known-gaps-tracker]]`. Per-item triage: obsolete -> Resolved (superseded); small and in-scope -> fix inline under the Phase 3-7 gates, then Resolved; out of scope but real -> keep, with accurate Reason + Suggested next step for the next `/plan` ingest. Remove stale TODOs whose context is gone. If a release-blocker remains, follow the active instruction template's `Consequential Decisions` rule, then ask, as a numbered list with one plain-language consequence each: 1. Resolve before continuing (the release waits until the blocker is fixed); 2. Downgrade and continue (the release ships with the issue recorded as a known gap, so users meet it); 3. Cancel the workflow (nothing further runs; the phase work stays committed but unreleased).

### 9B. Complete LOCAL gate

Confirm all implementation tasks, including final-phase refactors and known-gap fixes, are complete before starting longer validation. Collect every phase's `## Deferred final validation` inventory, run all remaining obligations, and mark their original task IDs complete only after the required results exist. Inspect the test surface (unit test per new/modified module; integration tests per new boundary; e2e per new user flow; declared test commands still run). Inspect the CI surface (build/test/lint jobs cover the new files; release/deploy still wired; new env vars/secrets declared without leaking values). Apply safe additions: generate missing tests via `/test` (stop after 3 passes, log remaining as MT); explain mechanical CI gaps and apply only changes authorized through the completion contract. Quote the suite under `## Full-suite testing and stabilization`.

**This is where the whole-suite obligations that non-final phases scoped away come due, and they are not optional here.** Phases 3-7 ran a blast-radius scope; this gate is the first and only point at which the plan's complete test surface is asserted. Run, in order: the FULL suite with coverage against the repository's canonical gate (for Nexus-Hub: `python scripts/ci/run.py --profile full`, never a hand-transcribed step list); enforcement of the project coverage threshold (>= 80%) with augmentation up to the 3-pass limit; and the cross-phase integration tests that no single phase's scope could have covered, because they exercise boundaries between phases. Inventory the canonical profile command coverage before execution: integration tests and coverage already included in the full profile must not be run again as duplicate suites. Run only missing obligations separately. Broad platform validation belongs to the integration matrix; run local platform checks only for a specific affected boundary or when the plan or a recorded acceptance criterion requires local platform proof. A phase-scoped green from Phase 7 is not evidence for the complete gate. Quote the full-suite command and its result; a scoped run recorded here does not satisfy this gate. For corrections after this complete run, apply the evidence-reuse and invalidation rules in [[cicd-integration]] rather than automatically restarting all profiles.

This gate is LOCAL by construction. It runs before the branch is published, so it cannot depend on a remote result; anything that can only be proven remotely is a gap in the local gate, not a reason to publish early and find out.

### 9F. Publication and integration (the plan's single remote event)

Runs after 9.0, 9A, and 9B are complete and the evidence file has every required section. This is the ONLY point in the entire plan at which anything leaves the machine.

1. **Final commit.** Generate the message via 8.10 and create the final local phase commit. Stage only this plan's changes; verify the staged diff first.
2. **Authorization check.** Present the resolved branching model, remote, branch and pull-request target. Verify publication authority through the completion contract immediately before the first push. Keep native provenance for a covered action; request a manual decision only when the native check finds it uncovered. A table of claimed approvals in the agent's reply confers no authority.

    **Measure the scope against the REMOTE integration branch, never the local one.** Run `git fetch` first, then state BOTH a commit count and a file count from `git log --oneline origin/<base>..HEAD` and `git diff --stat origin/<base>..HEAD`. A branch cut from a local integration branch that is ahead of its remote carries those extra commits into the pull request, and `git diff <base>..HEAD` cannot see them: it compares against the local branch, which already contains them. This is the ordinary case, not an edge case, because local integration branches accumulate unpushed work.

    When the remote count exceeds this plan's own commits, say so BEFORE asking for approval, list the extra commits, and give the command that isolates this plan's work (`git diff <branch-point>..HEAD`). Then check whether they can be unbundled: if the integration branch requires a pull request, they cannot, and the honest move is disclosure in the pull-request description rather than silence. Approval obtained against an understated scope is not approval for what actually merges.
3. **Push once.** Immediately before `git push origin <branch>`, run `python ~/.nexus-hub/scripts/check_plan_completion.py check <plan>` and require `approval.remote met` when a run record exists; the overall verdict can still be `INCOMPLETE` for work that follows the push. If the predicate is not met, record `approval-not-covered` with `--approval-class push-merge` and stop. Without a record, require `git remote get-url --push --all origin` to return exactly one URL matching the destination and repository the user explicitly approved; ask again on any difference. Do not replace `origin` with an alternate URL or override its push URL in the push command. Publish the branch and report the result.
4. **Open the integration pull request** against the integration branch (not the protected release branch). Report the exact required checks expected, so the user can tell a missing check from a failing one.
5. **Wait for a terminal state** on every required check. This is the plan's first and only comprehensive remote validation, and it runs against the synthetic MERGE RESULT rather than the branch tip.
6. **On red, REOPEN this phase.** Classify the failure, reproduce it LOCALLY, apply the narrow fix, revalidate affected checks and retain valid unaffected evidence through [[cicd-integration]], update known gaps and session history, then EITHER amend the final commit OR add ONE narrowly scoped stabilization commit - never both, and never a series - and push again under the contract's verified repair authority. A signed scoped correction policy can cover further repair consent on its exact paths; it does not expand the troubleshooting-iteration or spend budget. Do not re-ask merely because another covered repair is needed. Repeat step 3's push-remote check immediately before the re-push. `[[code-commit-workflow]]` owns which of the two fits. Never re-run a red check without a local reproduction: a re-run without one is a guess, and a check that cannot be reproduced locally is itself the finding (an environment difference, a missing local dependency, or an interpreter version floor).
7. **Merge only when every required check is green and native verification covers the merge.** Use the matching recorded `push-merge` authority for the verified current result; request a manual decision through the completion contract only when scope is uncovered.
8. **Verify the post-merge behavior.** Confirm the post-merge workflow performed only its intended smoke, publication, or provenance work and did NOT rerun the complete suite. A duplicate post-merge suite is a finding against the reconciliation in 9.0 duty 5.
9. Quote the required-check results and the merge SHA under `## Publication and integration`.
10. **Retire the worktree.** Only after the merge is confirmed green and merged:
    1. Verify the branch is **fully merged** into the integration branch: `git branch --merged <base>` lists it, and `git log <base>..<branch>` is empty. An unmerged commit here means work is about to be deleted.
    2. Verify the worktree has **no uncommitted or untracked work**: `git -C <worktree> status --porcelain` is empty. A non-empty result stops the teardown and is reported, never force-removed.
    3. Remove the worktree and delete its directory through `[[using-git-worktrees]]`, which owns the mechanics.
    4. Delete the local branch once its worktree is gone.
    5. Run `git worktree prune`, then confirm `git worktree list` no longer shows the path and the directory is absent from disk.
    6. Quote all of it under `## Worktree teardown` in the evidence file.

    A plan that ships without this leaves a full checkout behind. After ten plans that is ten stale copies of the repository, each pinning objects and each capable of being edited by mistake. The teardown is the step that keeps parallel worktrees a temporary cost rather than a permanent one.

    **Never remove a worktree before the merge is green and merged**, and never with `--force` to get past a dirty tree. Both convert an unfinished branch into deleted work.

Never tag and never publish a release here; that is `/update release`.

### 9A2. Record the gaps this run leaves open

After 9A's triage, and before the final commit, record every item still open in this plan's `## v<version>` section: `python ~/.nexus-hub/scripts/minor_close.py carry --plan <plan> --session <id>` (`--dry-run` first). It moves each item into the next patch's section under the next free id, with a `**Carried from**` line naming its version and old id, or, when this is the last plan of its minor, migrates every open item of the minor to the next minor's `.0` section. The ledger change then travels in the plan's own pull request. What counts as recorded is owned by the completion contract's "Single-plan carry and archive" section.

### 9C-9E. Hand off to `/update release`

The documentation cleanup, the standard update checks, and the version bump / changelog / tag / push are owned by `/update release` in v3.x (it runs docs -> gitignore -> version via `scripts/check_version_sync.py` -> changelog -> devlog -> refactor, then cleans up, commits, tags, and pushes as one atomic flow with the completion contract's authorization policy). Do not re-implement the old inline `/update-*` sequence or bypass the required release checks.

**Hold the handoff** while `<version_dir>/development/<version>-last-phase-evidence.md` is missing, any required section is missing, a Goal-vs-codebase review or Tier 3 deep-pass finding is unresolved without a recorded known-gap, or 9F has not completed - that is, the branch has not been published, a required check is not green, or the merge to the integration branch has not landed. `/update release` starts only after the integration result is green and merged. Surface any other hold condition (unresolved release-blocker, tests failing / coverage below threshold without bypass, version-sync inconsistency, unapproved next-version choice) and stop before the release step if one is active.

### 9G. Archive the minor after its last plan

Only when this plan is the last unshipped plan of its minor (the completion check then reports the minor's archive as unmet), after `/update release` and the cleanup of this plan's branch and worktree: finalize the minor's known-gaps header, create `chore/close-vX.Y` from the integration branch, run `python ~/.nexus-hub/scripts/minor_close.py archive --minor vX.Y --plan <plan> --session <id>` (a dry run), then again with `--apply`. It archives the tree, removes every folder left empty under `docs/releases/`, and re-points the run record at the archived plan. Push the branch and merge its closing pull request under the recorded `minor-close-pr` approval, then run the completion check on the archived plan path; the archive counts only once that merge lands.

## Completion report

The report follows the Completed / Verified / Open / Next shape from `catalog/style-guides/agent-communication.md` (skill: `[[agent-communication]]`). The old field list maps into it; nothing is dropped, it is grouped so the reader can act on it.

- **Completed**: the plan, the phase, the subtasks done, and the files written, in plain language.
- **Verified**: the test results, the lint result, coverage, the proportional functional smoke, and the Plan-delta disposition. On the final phase, the Release readiness block nests here, summarizing 9.0 including the Tier 3 deep pass, 9A, 9B, and the `/update release` handoff outcome.
- **Open**: deviations, the known-gaps delta, and any active hold condition. Write "nothing outstanding" when empty; never omit the part.
- **Next**: the commit action taken and the next phase, or that the plan is complete.

Add one plain-language line for a reader who does not know the codebase. Cap the report at about 15 lines, excluding the Open list, which is the only part allowed to grow.

**Turns that end with work still running** (a suite executing, a background task pending) follow the contract's waiting-state rule instead: the first line is a status banner naming what is running, that no action is needed, and that results will follow; the rest is capped at about 8 lines; every finding is deferred to the completion report that follows.

Worked example of a non-final phase report:

> **Completed**: Phase 3 of `v4.0.0-agent-communication-overhaul` is done. All 12 instruction templates now carry the communication contract, and the parity checker treats it as a locked section.
>
> **Verified**: 21 new tests pass, the full suite is green, and every budgeted file is still under its word ceiling (tightest: base-codex at 13 words of headroom).
>
> **Open**: The parity checker covers 5 of the 12 templates by design, so drift in the other 7 is caught by the new aggregate test rather than by the release gate. Recorded as a known gap.
>
> **Next**: Committed as `494411c7`. Phase 4 upgrades the report templates in the workflow commands.
>
> In plain terms: every AI assistant this repo supports will now describe its work the same way, and a check stops that wording from drifting apart.

## Iterative refinement

The whole workflow is iterative: after a pass, check completeness and correctness, refine, and loop up to 3 times (or the user-specified count) until the phase is stable.
