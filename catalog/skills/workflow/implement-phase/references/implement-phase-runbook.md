# Implement-Phase Runbook (full workflow)

The complete, ordered procedure for the `implement-phase` skill. `SKILL.md` links here; the agent reads this on demand when actually running a phase. Reconstituted from the pre-v3.2.0 `/implement-phase` command and updated to v3.x reality: docs paths follow the `[[docs-layout-refactor]]` Version-directory resolution scheme (`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`), old flat commands are retargeted to their consolidated equivalents (`/update gitignore`, `/update docs`, `/update devlog`, `/session history`, `/commit`, `/test`), and the final-phase release work hands off to `/update release`.

## Phase 0: Resolve plan, version, and phase

1. **Parse the invocation.** First positional arg is a plan slug, a plan file path, or a version label; later args may be a phase and/or a driver mode. Disambiguate the first arg: contains `/` or ends in `.md` -> file path; matches `v?\d+\.\d+\.\d+` -> version; else -> slug. Phase accepted as a number (`3`), slug (`phase-3`), or quoted name. Driver mode is a later whole token only: `full` (alias `in-full`) or `phase-by-phase`. Do not treat a slug that contains "full" as a substring as a driver mode. An unknown later token prints usage and does not start a phase. Bare `/implement` stays one-phase.
2. **Search for plans**, deduping by absolute path:
    - Canonical: `docs/v*/v*/plans/*.md` (the two-level minor-grouped scheme).
    - Legacy: `docs/v*/plans/*.md` (flat) and `docs/versions/v*/v*/plans/*.md` (old three-level), plus the pre-rename `docs/**/implementation-plan.md`.
    - When a plan exists at both canonical and a legacy path, prefer canonical and surface: `Inconsistent layout: plan present at both canonical and legacy paths. Using canonical. Run /update refactor to migrate.`
3. **Plan selection.** File path -> resolve directly. Slug -> filter to `docs/**/plans/<slug>.md`; one match uses it, multiple asks which version. Version -> filter to that version. No arg + one plan -> use it. No arg + multiple -> list grouped by version, most-recent first. No plan -> report paths searched and suggest `/plan`.
4. **Parse the plan** to extract the phase list (numbers, names, completion status).
5. **Phase selection.** No phase specified -> show the phase list and ask. Target already complete -> warn and ask whether to re-implement.
6. **Final-phase detection** (`is_final_phase`) - use ALL five signals, never the user's claim alone:
    - **Phase ordering**: target is the numerically highest phase, or the last `## Phase N:` by document order.
    - **Title heuristics**: "Polish", "Final QA and Release", "Release Prep", "Wrap-up", or (v3.11.0+) "Architecture Refactor, Known-Gaps Reconciliation, and CI/CD".
    - **Prior-phase completion**: every prior phase shows `[x]` or has a session-history file under `<version_dir>/development/history/`.
    - **Plan metadata**: honor an explicit `Final-Phase: N` marker.
    - **Adjacent plans**: the plan is the only one under the active version dir.
    On conflict (numerically last but prior phases unchecked), set `is_final_phase = false` and say so.
7. **Pre-flight summary** - show plan, phase, status, prior-phases-complete, and final-phase (with a note that the release-readiness workflow runs after Phase 8 when final). Before requesting confirmation, follow the active instruction template's `Consequential Decisions` rule. Wait for confirmation before any code change.

## Phase 1: Pre-implementation review

Read the full plan and the target phase in detail (goals, acceptance criteria, subtasks, files, dependencies). Check prerequisites (marked complete + `git log` references). Scan the codebase for files the phase touches. Report the goal, subtask count, likely-affected files, and prerequisite/dependency status before implementing.

### Model-routing pre-flight

Before Phase 2 begins, run `[[model-routing]]` in implementation mode:

1. Read the target phase's `Recommended model tier`, `Recommended effort level`, and `Rationale` plus its current-provider map cell. Continue accepting historical `Recommended model` / `Rec. model / effort` fields.
2. Re-score the phase. When web access is available, refresh the four-provider candidate from official sources and validate/render it through `model-routing/scripts/model-map.{sh,ps1}`. Otherwise use the helper's validated dated fallback.
3. Enumerate the selected provider's live platform surface. If the mapped model is unavailable or the new score is higher, surface the delta and default to the same or stronger tier. Never silently downshift.
4. Present the recommendation and wait for approval. Then switch only through the platform's supported posture: scripted on Codex/Antigravity/Gemini CLI, one user action on Claude Code, picker-only on Cursor/Copilot/OpenCode. If refresh or enumeration is unavailable, state the fallback and continue on the plan tier or current session model.

During troubleshooting, repeated failures may trigger a confirmation-gated upshift only. Never downshift mid-phase.

## Phase 2: Implementation

Work subtask by subtask in plan order. After each subtask, confirm the code compiles/imports before moving on (do not accumulate broken subtasks). Log deviations inline with `# DEVIATION:` and keep a running list for Phase 8. Stay in scope: no refactors outside the phase boundary, no speculative features, no unrelated file changes. Compile/import-check the whole phase before linting.

## Phase 3: Lint and format

Detect language(s), run the linter + formatter (Python: `ruff check . --fix && ruff format .`; TS/JS: `eslint --fix` then `prettier --write`; Go: `gofmt -w` then `golangci-lint run`; mixed: each in turn). Auto-fix everything fixable and report. Resolve non-auto-fixable errors before testing; never suppress lint rules.

## Phase 4: Test execution and coverage

Detect the test runner and run the full suite with coverage (Python: `pytest --cov=src --cov-report=term-missing -q`; TS/JS: `vitest run --coverage`; Go: `go test -race -coverprofile=coverage.out ./...`). Capture passed/failed/skipped, line coverage, and which new/modified files are below 80%. Route: coverage >= 80% and 0 failures -> Phase 6 is a no-op; coverage < 80% or missing tests -> Phase 5; failures -> Phase 6.

## Phase 5: Test augmentation

Generate tests (via `/test`, i.e. the `unit-tests` and `test-cases` skills) for files added/modified in Phase 2. Enforce project standards (AAA, parametrize, fixtures in `conftest.py`/setup, no `sleep`). Re-run and re-capture coverage; add targeted tests for remaining uncovered paths (repeat once). Proceed to Phase 6 once tests are generated.

## Phase 6: Troubleshooting loop (max 3 iterations)

Read every failure (name, message, stack). Classify each `IMPL` / `TEST` / `ENV`. Apply targeted fixes (fix impl for IMPL; fix the test and document why for TEST; resolve and log for ENV). Re-run and check the failure count dropped. Stop early when green. After 3 iterations with failures remaining, stop and present the unresolved list with options: A. Skip failing tests and continue; B. Abort for manual investigation; C. Extend the loop N more iterations. Follow the active instruction template's `Consequential Decisions` rule before asking. Wait for the answer.

## Phase 7: Quality gate (GO / NO-GO)

Evaluate five gates: all tests passing (0 failures), line coverage >= 80%, 0 lint errors, build/compile succeeds, and the phase's own feature was exercised and observed through its primary real boundary with expected behavior matching observed behavior. Delegate what exercise and evidence count for the artifact type to `[[functional-verification]]`. Keep this fifth gate cheap and proportional: one representative phase-scoped smoke, not the whole-plan deep pass or another full suite. Documentation-only release evidence uses that skill's explicit no-runnable-feature path rather than a silent skip. All five pass -> run the post-phase sequence. Any failure REOPENS the phase: return gates 1-4 to the owning Phase 3-6 step; return a fifth-gate mismatch or blocked exercise to Phase 2, fix the implementation or required evidence, then rerun the proportional smoke and all of Phase 7. Bound this recovery by the Phase 6 three-iteration budget. Only when that retry budget is exhausted or a required input remains unavailable may the maintainer choose, after the active instruction template's `Consequential Decisions` walkthrough: A. Proceed with an explicit `QG` known gap owning the failed gate; B. Stop for manual resolution.

## Phase 8: Post-phase completion sequence (every phase)

Run every step in strict order at the end of EVERY phase (validation first, then documentation, then commit). Steps are no-ops when there is nothing to do, but each MUST be invoked. Wait for each to complete before the next.

- **8.1 `/update gitignore`** - ensure new artifacts/caches are ignored. Report `0 patterns added` when nothing is new.
- **8.2 Test review (post-phase pass)** - re-run the suite with Phase 4's command; confirm every file added/modified in Phase 2 has at least one test referencing it; if gaps surface, run `/test` once for the unreferenced files, then log remaining gaps as `MT` in 8.5 (do not loop).
- **8.3 CI impact record (per-phase, no remote run)** - detect the active CI system, then RECORD this phase's impact against `[[cicd-architect]]`: cross-check Phase 2 modifications against CI declarations (new script command, new runtime env var as a secret reference, new dependency picked up by install, new test path, new artifact) and state whether the existing pipeline already covers each. A no-op record ("no new commands, dependencies, env vars, test paths, or artifacts") is a valid outcome and must still be written.
    - **Do NOT run a per-phase optimization pass and do NOT change a pipeline file**, unless CI/CD is THIS phase's explicit deliverable. Per-phase pipeline authorship is what produces a different topology per phase and a pipeline nobody can run locally; the actual comparison, proposal, and migration happen once, in the terminal phase (9.0 duty 5), against the canonical contract.
    - Anything the record shows the pipeline does not cover becomes an input to that terminal reconciliation, and a `QG` entry in 8.5 if it is material. Never silently rewrite a CI config at any point.
- **8.4 Plan-delta note (always written)** - decide whether implementation showed this phase's plan to be **No delta**, **Wrong**, **Incomplete**, or based on a **False assumption**. Write exactly one primary disposition under `## Plan delta` in `<version_dir>/development/history/<phase-session-history>.md`, with the observed evidence and the consequence for every remaining phase. Create the current phase history file here if needed; step 8.9 completes it without removing or weakening this section. A non-blocking delta stays in session history and informs later work without plan or gap escalation. A blocking delta updates the plan before the driver continues or becomes a `DF` or `QG` known gap in 8.5 with Source phase, Plan reference, Reason, and Suggested next step. `No delta` is a considered, evidenced result and MUST still be written.
- **8.5 Known-gaps append** - via `[[known-gaps-tracker]]` (Append mode) into the correct `## v<MAJOR>.<MINOR>.<PATCH>` subsection of `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md`. Classify `# DEVIATION:` markers as NI/DF/BG; skipped failures as BG; coverage/untested-file gaps as MT; suppressed lint/warnings as WN; bypassed gates and unapproved CI gaps as QG. Include blocking plan deltas from 8.4. Every item carries Source phase, Plan reference, Reason, Suggested next step. Recompute the patch subsection's Summary; update Last updated; do NOT finalize.
- **8.6 Docs cleanup audit** - run `[[docs-layout-refactor]]` in `--mode audit` (report to `<version_dir>/docs-cleanup-report.md`; no files move). Propose cleanup of scratch docs THIS phase created only with explicit approval; default to leaving them.
- **8.7 `/update devlog`** - what was implemented, decisions, deviations, test results (8.2), CI/CD changes (8.3), known issues (reference the gap log rather than re-listing).
- **8.8 `/update docs`** - sync README, API docs, architecture docs, inline guides. No-op when nothing changed.
- **8.9 `/session history`** - complete the standalone session-history file in `<version_dir>/development/history/` (plan reference, subtasks, test results, CI/CD edits, deviations, next steps) while preserving the required `## Plan delta` section written in 8.4.
- **8.10 `/commit` (generate the message)** - structured, sectioned-bullet message scoped to the phase, including the known-gaps file, docs-cleanup report, session history, and every touched file. Sectioned bullets grouped by component; dedicated Tests / CI/CD / Known gaps sections; no hard-wrapping; single blank line between sections. Produces the message; does not auto-commit.
- **8.11 Commit prompt (REQUIRED, every phase)** - a NON-FINAL phase is commit-only in every mode. Push, pull request, and remote CI belong to the final phase (Phase 9), which owns the plan's single publication. Offering push here would bill a full pipeline run to validate work the plan itself says is incomplete, and a red check on incomplete work teaches the reader to ignore red checks. Behavior by mode:
    - **One-phase (default), non-final:** follow the active instruction template's `Consequential Decisions` rule, then always ask, as a numbered list with one plain-language consequence each: 1. Commit only (the work is saved locally; nothing leaves this machine); 2. Amend (loop to 8.10 to reword the commit message before saving); 3. Stop (nothing is saved; the changes stay uncommitted in the working tree). Never proceed past 8.11 without a definite answer. On commit, use a heredoc and report the SHA.
    - **One-phase, FINAL phase:** do not ask this question at all. Run Phase 9, whose 9F step owns the final commit, the approval gate, and the single push.
    - **`full` non-final:** auto-select commit-only. Still generate the commit message (8.10); still use a heredoc; still report the SHA. Do not push.
    - **`full` last phase:** run Phase 9 in full. After the evidence file is complete AND the integration result is green and merged, hand off to `/update release` (that command owns tag/push confirmation). Never tag or push the release from the driver.
    - **`phase-by-phase`, non-final:** replace the one-phase ask with this three-option menu and wait: (1) commit and continue; (2) commit and pause; (3) other. Cross-link `[[code-commit-workflow]]` for the commit itself.
    - **A user who explicitly asks to push a non-final phase** is making a deliberate exception, not hitting a menu option. State the cost in one line (a full pipeline run against knowingly incomplete work), then do what they ask. The rule removes the DEFAULT, not the user's authority.

## Driver loop (`full` / `phase-by-phase`)

Used only when the resolved mode is `full` (alias `in-full`) or `phase-by-phase`. One-phase invocations skip this section and run Phase 0-8 once.

1. Resolve the plan as in Phase 0. Start at the first incomplete phase even if the user named a later start. Preserve model-routing pre-flight per phase.
2. For each incomplete phase, run the existing Phase 0-8 sequence unchanged (review, implement, lint, test, quality gate, post-phase docs). Apply the 8.11 variant above.
3. **Stop the driver** (do not start the next phase) when a GO/NO-GO gate fails, the user pauses, or context is exhausted. On context exhaustion, write session history and a continuation prompt naming the next phase and the mode (`/implement <slug> full` or `phase-by-phase` from the next incomplete phase). Do not silently continue degraded.
4. After a successful last phase, require `<version_dir>/development/last-phase-evidence.md`, then hand off to `/update release`. Never tag or push the release from the driver.
5. If the user is mid-`full` and chooses to stop, leave a continuation line they can paste.

## Phase 9: Final-phase completion workflow (release-readiness)

During living-documentation reconciliation, run `technical-documentation`'s `references/handbook-refresh.md` on the actual final-phase candidate before the local completion/publication gate. Update both handbook views with approved settings and retain freshness, coverage, and browser evidence. The subsequent `/update release` handoff rechecks the integrated candidate before its version bump; it does not defer all handbook work until after publication. Existing CI/integration and release approval gates remain in force.

Runs only when `is_final_phase = true` AND Phase 8 completed cleanly. If `is_final_phase` is false because prior phases are unchecked, do not run Phase 9; say so and stop the release handoff.

Every last-phase duty is fail-closed. Announce the queued sub-phases. A duty is omitted only by writing a known-gap (`QG` or `DF`) with Source phase, Plan reference, Reason, and Suggested next step. If the user asks to skip a duty without that recorded gap, refuse. Every step is idempotent and prompts before it commits, archives, or tags.

### Last-phase evidence file (blocking)

Write `<version_dir>/development/last-phase-evidence.md` with one section per duty below. Each section quotes the proving command or scan. An empty finding is allowed only when the scan output is quoted. A missing file, a missing section, or an unresolved Goal-vs-codebase review or Tier 3 deep-pass finding without a recorded known-gap BLOCKS the 9C-9E `/update release` handoff. Completing every prior-phase checkbox is not evidence the Goal landed.

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

1. Run `[[project-refactor]]` (empty dirs, duplicates, non-version orphans, structure complexity) and `[[docs-layout-refactor]]` to clean the layout - propose-then-apply, with confirmation; repair references for anything that moves. Quote detector output under `## Architecture refactor`, including an empty finding.
2. Reconcile known gaps via `[[known-gaps-tracker]]` for this version AND every other `docs/**/known-gaps.md` whose Status is in-progress or whose Open Items remain. Glob both canonical and legacy layouts. If a file is unreachable, record the glob result and continue with what was found. This feeds 9A. Quote the disposition under `## Known-gaps reconciliation`.
3. Check living docs architecture (`docs/handbooks/` markdown + generated `html/` + atlas + technical companions, `docs/decisions/`, living `docs/README.md` / `DEVLOG.md` / `todos.md`). Self-gated: never invent `docs/testing/` or `docs/validation/`. Quote the check under `## Living docs architecture`.
4. Run `python scripts/check_release_preconditions.py --branches --repo-settings` and quote it under `## Git-tree hygiene`. Report only; never delete branches.
5. Run the TERMINAL PIPELINE RECONCILIATION via `[[cicd-architect]]` in existing-pipeline comparison mode, and run its six steps in order: DETECT the active provider (recording "none detected" rather than assuming one); COMPARE the existing pipeline field by field against the canonical contract (profiles, events, runner selection, the always-resolving aggregate required check, permissions, immutable action references, caching, concurrency, path scoping, artifact retention, structured reports, deployment boundaries, failure recovery); PROPOSE each difference with its cost, its risk, and the smallest change that closes it; obtain explicit APPROVAL per change, since silence is not approval; APPLY the approved changes and re-run the local gate; RECORD every declined or environment-only difference as a known gap with an owner and a next step. The comparison concludes PASS only when every required field has observable evidence - a green pipeline run is not evidence, because a pipeline that checks nothing is green for the wrong reason. This is the ONE place in the whole plan where pipeline files change, unless CI/CD was a named phase deliverable. If the repository ships more than one installer, run or add its declarative cross-installer parity checker as a HARD gate in the same pass as `[[platform-contract-verification]]`. Repositories with zero or one installer silently no-op. Quote the per-field result under `## CI/CD coverage`.
6. Invoke `[[functional-verification]]` and load its `references/deep-pass.md` runbook. Record the objective blast-radius verdict first; ambiguous evidence selects `run`, while a valid no-op still writes its diff evidence. Follow the selected deep-pass path in order and quote its final record under the literal `## Tier 3 deep pass` heading in `<version_dir>/development/last-phase-evidence.md`. This duty is fail-closed: an unresolved finding blocks publication unless disposition is recorded through the owning gate and gap skills, and the duty may be omitted only by recording a `QG` or `DF` known gap with Source phase, Plan reference, Reason, and Suggested next step. A reasoned no-op is completion of the duty, not an omission.
7. Independent Goal-vs-codebase review: after the deep pass reaches its terminal disposition, re-read the plan header Goal and Goals First / Definition of Done, then inspect the resulting codebase as if this agent had not implemented the phases. The `## Goal-vs-codebase review` section MUST list the plan Goal restated (fail closed and name the missing Goal if the plan has none), the code/docs artifacts that satisfy it, and any gap. A miss is a blocking finding or a new known-gap, not a pass.
8. Human/manual testing suggestions, last phase only. Quote them under `## Human/manual testing suggestions`.
9. Run the ADVISORY model-prompting-profile staleness check via `[[model-prompting-research]]`, the same step `/update release` performs as governance step 6. Invoke `python scripts/check_model_prompting_freshness.py --advisory` after enumerating the live roster. Do NOT duplicate its logic here: invoke the skill. It NEVER blocks the phase, never re-stamps a freshness marker, and degrades to a logged no-op offline.

Keep every confirmation gate; never tag or push automatically.

### 9A. Resolve known gaps and deferred work

Re-read `<version_dir>/known-gaps.md` `## Open Items`. Grep the codebase for `TODO`/`FIXME`/`XXX`/`HACK`/`# DEVIATION:` introduced this version; add unrecorded ones via `[[known-gaps-tracker]]`. Per-item triage: obsolete -> Resolved (superseded); small and in-scope -> fix inline under the Phase 3-7 gates, then Resolved; out of scope but real -> keep, with accurate Reason + Suggested next step for the next `/plan` ingest. Remove stale TODOs whose context is gone. If a release-blocker remains, follow the active instruction template's `Consequential Decisions` rule, then ask, as a numbered list with one plain-language consequence each: 1. Resolve before continuing (the release waits until the blocker is fixed); 2. Downgrade and continue (the release ships with the issue recorded as a known gap, so users meet it); 3. Cancel the workflow (nothing further runs; the phase work stays committed but unreleased).

### 9B. Complete LOCAL gate

Inspect the test surface (unit test per new/modified module; integration tests per new boundary; e2e per new user flow; declared test commands still run). Inspect the CI surface (build/test/lint jobs cover the new files; release/deploy still wired; new env vars/secrets declared without leaking values). Apply safe additions: generate missing tests via `/test` (stop after 3 passes, log remaining as MT); propose mechanical CI gaps for approval; never silently rewrite CI. Quote the suite under `## Full-suite testing and stabilization`.

This gate is LOCAL by construction. It runs before the branch is published, so it cannot depend on a remote result; anything that can only be proven remotely is a gap in the local gate, not a reason to publish early and find out.

### 9F. Publication and integration (the plan's single remote event)

Runs after 9.0, 9A, and 9B are complete and the evidence file has every required section. This is the ONLY point in the entire plan at which anything leaves the machine.

1. **Final commit.** Generate the message via 8.10 and create the final local phase commit. Stage only this plan's changes; verify the staged diff first.
2. **Approval gate.** Present the resolved branching model (via `[[git-branching-workflow]]`), the remote, the branch name, and the pull-request target. Follow the active instruction template's `Consequential Decisions` rule. Obtain EXPLICIT approval before the plan's first branch push. Silence is not approval.
3. **Push once.** Publish the branch. Report the result.
4. **Open the integration pull request** against the integration branch (not the protected release branch). Report the exact required checks expected, so the user can tell a missing check from a failing one.
5. **Wait for a terminal state** on every required check. This is the plan's first and only comprehensive remote validation, and it runs against the synthetic MERGE RESULT rather than the branch tip.
6. **On red, REOPEN this phase.** Classify the failure, reproduce it LOCALLY, apply the narrow fix, re-run the local gate, update known gaps and session history, then EITHER amend the final commit OR add ONE narrowly scoped stabilization commit - never both, and never a series - and push again with approval. `[[code-commit-workflow]]` owns which of the two fits. Never re-run a red check without a local reproduction: a re-run without one is a guess, and a check that cannot be reproduced locally is itself the finding (an environment difference, a missing local dependency, or an interpreter version floor).
7. **Merge only when every required check is green AND the user approves.**
8. **Verify the post-merge behavior.** Confirm the post-merge workflow performed only its intended smoke, publication, or provenance work and did NOT rerun the complete suite. A duplicate post-merge suite is a finding against the reconciliation in 9.0 duty 5.
9. Quote the required-check results and the merge SHA under `## Publication and integration`.

Never tag and never publish a release here; that is `/update release`.

### 9C-9E. Hand off to `/update release`

The documentation cleanup, the standard update checks, and the version bump / changelog / tag / push are owned by `/update release` in v3.x (it runs docs -> gitignore -> version via `scripts/check_version_sync.py` -> changelog -> devlog -> refactor, then cleans up, commits, tags, and pushes as one atomic flow, keeping its own confirmation gates). Do NOT re-implement the old inline `/update-*` sequence here and NEVER create a tag or push automatically.

**Hold the handoff** while `<version_dir>/development/last-phase-evidence.md` is missing, any required section is missing, a Goal-vs-codebase review or Tier 3 deep-pass finding is unresolved without a recorded known-gap, or 9F has not completed - that is, the branch has not been published, a required check is not green, or the merge to the integration branch has not landed. `/update release` starts only after the integration result is green and merged. Surface any other hold condition (unresolved release-blocker, tests failing / coverage below threshold without bypass, version-sync inconsistency, unapproved next-version choice) and stop before the release step if one is active.

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
