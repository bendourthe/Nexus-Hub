# Implement-Phase Runbook (full workflow)

The complete, ordered procedure for the `implement-phase` skill. `SKILL.md` links here; the agent reads this on demand when actually running a phase. Reconstituted from the pre-v3.2.0 `/implement-phase` command and updated to v3.x reality: docs paths follow the `[[docs-layout-refactor]]` Version-directory resolution scheme (`docs/v<MAJOR>/v<MAJOR>.<MINOR>/`), old flat commands are retargeted to their consolidated equivalents (`/update gitignore`, `/update docs`, `/update devlog`, `/session history`, `/commit`, `/test`), and the final-phase release work hands off to `/update release`.

## Phase 0: Resolve plan, version, and phase

1. **Parse the invocation.** First positional arg is a plan slug, a plan file path, or a version label; the second (optional) is the phase. Disambiguate: contains `/` or ends in `.md` -> file path; matches `v?\d+\.\d+\.\d+` -> version; else -> slug. Phase accepted as a number (`3`), slug (`phase-3`), or quoted name.
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
7. **Pre-flight summary** - show plan, phase, status, prior-phases-complete, and final-phase (with a note that the release-readiness workflow runs after Phase 8 when final). Wait for confirmation before any code change.

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

Read every failure (name, message, stack). Classify each `IMPL` / `TEST` / `ENV`. Apply targeted fixes (fix impl for IMPL; fix the test and document why for TEST; resolve and log for ENV). Re-run and check the failure count dropped. Stop early when green. After 3 iterations with failures remaining, stop and present the unresolved list with options: A. Skip failing tests and continue; B. Abort for manual investigation; C. Extend the loop N more iterations. Wait for the answer.

## Phase 7: Quality gate (GO / NO-GO)

Evaluate four gates: all tests passing (0 failures), line coverage >= 80%, 0 lint errors, build/compile succeeds. All pass -> run the post-phase sequence. Any fail after retries -> ask the user: A. Proceed anyway (document the gap); B. Stop for manual resolution.

## Phase 8: Post-phase completion sequence (every phase)

Run every step in strict order at the end of EVERY phase (validation first, then documentation, then commit). Steps are no-ops when there is nothing to do, but each MUST be invoked. Wait for each to complete before the next.

- **8.1 `/update gitignore`** - ensure new artifacts/caches are ignored. Report `0 patterns added` when nothing is new.
- **8.2 Test review (post-phase pass)** - re-run the suite with Phase 4's command; confirm every file added/modified in Phase 2 has at least one test referencing it; if gaps surface, run `/test` once for the unreferenced files, then log remaining gaps as `MT` in 8.4 (do not loop).
- **8.3 CI/CD readiness + optimization (per-phase)** - detect the active CI system. Cross-check Phase 2 modifications against CI declarations (new script command, new runtime env var as a secret reference, new dependency picked up by install). AND run an optimization pass: confirm the workflow uses path filters, `concurrency` cancel-in-progress, dependency caching, and gates expensive-OS/matrix jobs to merges/schedule - propose the diff for any missing optimization. Never silently rewrite CI configs; propose diffs inline, apply only on approval; unapproved gaps become `QG` entries in 8.4.
- **8.4 Known-gaps append** - via `[[known-gaps-tracker]]` (Append mode) into the correct `## v<MAJOR>.<MINOR>.<PATCH>` subsection of `docs/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md`. Classify `# DEVIATION:` markers as NI/DF/BG; skipped failures as BG; coverage/untested-file gaps as MT; suppressed lint/warnings as WN; bypassed gates and unapproved CI gaps as QG. Every item carries Source phase, Plan reference, Reason, Suggested next step. Recompute the patch subsection's Summary; update Last updated; do NOT finalize.
- **8.5 Docs cleanup audit** - run `[[docs-layout-refactor]]` in `--mode audit` (report to `<version_dir>/docs-cleanup-report.md`; no files move). Propose cleanup of scratch docs THIS phase created only with explicit approval; default to leaving them.
- **8.6 `/update devlog`** - what was implemented, decisions, deviations, test results (8.2), CI/CD changes (8.3), known issues (reference the gap log rather than re-listing).
- **8.7 `/update docs`** - sync README, API docs, architecture docs, inline guides. No-op when nothing changed.
- **8.8 `/session history`** - standalone session-history file in `<version_dir>/development/history/` (plan reference, subtasks, test results, CI/CD edits, deviations, next steps).
- **8.9 `/commit` (generate the message)** - structured, sectioned-bullet message scoped to the phase, including the known-gaps file, docs-cleanup report, session history, and every touched file. Sectioned bullets grouped by component; dedicated Tests / CI/CD / Known gaps sections; no hard-wrapping; single blank line between sections. Produces the message; does not auto-commit.
- **8.10 Commit-and-push prompt (REQUIRED, every phase)** - always ask: 1. Commit only; 2. Commit and push; 3. Amend (loop to 8.9); 4. Stop. Never proceed past 8.10 without a definite answer. On commit, use a heredoc, report the SHA (and push result for option 2).

## Phase 9: Final-phase completion workflow (release-readiness)

Runs only when `is_final_phase = true` AND Phase 8 completed cleanly. Every step is idempotent and prompts before it commits/archives/tags. Announce the queued sub-phases and accept `skip <X>` directives.

### 9.0 Mandatory refactor + known-gaps + CI/CD gate (v3.11.0)

Before the release-readiness sub-phases, run the Phase 3 terminal-phase gate on the plan's last phase - **even when the plan was generated before v3.11.0 and has no explicit "Architecture Refactor, Known-Gaps Reconciliation, and CI/CD" phase** (detect its absence and run the gate anyway):

1. Run `[[project-refactor]]` (with the v3.11.0 detectors: empty dirs, duplicates, non-version orphans, structure complexity) and `[[docs-layout-refactor]]` to clean the layout - propose-then-apply, with confirmation; repair references for anything that moves.
2. Reconcile the version's known gaps via `[[known-gaps-tracker]]` (this feeds 9A).
3. Create or update the CI/CD pipeline so it covers every change in the plan, and optimize it to reduce action minutes (path filters, concurrency cancel-in-progress, caching, gating expensive-OS/matrix jobs) while keeping comprehensive testing.
4. Run the ADVISORY model-prompting-profile staleness check via `[[model-prompting-research]]`, the same step `/update release` performs as governance step 5. Do NOT duplicate its logic here: invoke the skill. It self-gates (real work only in a repo shipping the profile layer plus `[[model-routing]]`, a silent no-op elsewhere), enumerates the live roster, runs `check_model_prompting_freshness.py --advisory`, and on drift prints a one-line note plus an offer to run `/tune-prompting`. It NEVER blocks the phase, never re-stamps a freshness marker, and degrades to a logged no-op offline. This is the deliberate opposite of the platform read-contract check, which DOES hard-gate a release; see `/update release` governance step 5 for why prompting freshness must stay decoupled from the release clock.

Keep every confirmation gate; never tag or push automatically.

### 9A. Resolve known gaps and deferred work

Re-read `<version_dir>/known-gaps.md` `## Open Items`. Grep the codebase for `TODO`/`FIXME`/`XXX`/`HACK`/`# DEVIATION:` introduced this version; add unrecorded ones via `[[known-gaps-tracker]]`. Per-item triage: obsolete -> Resolved (superseded); small and in-scope -> fix inline under the Phase 3-7 gates, then Resolved; out of scope but real -> keep, with accurate Reason + Suggested next step for the next `/plan` ingest. Remove stale TODOs whose context is gone. If a release-blocker remains, ask: A. Resolve before continuing; B. Downgrade and continue; C. Cancel the workflow.

### 9B. Verify tests and CI/CD readiness

Inspect the test surface (unit test per new/modified module; integration tests per new boundary; e2e per new user flow; declared test commands still run). Inspect the CI surface (build/test/lint jobs cover the new files; release/deploy still wired; new env vars/secrets declared without leaking values). Apply safe additions: generate missing tests via `/test` (stop after 3 passes, log remaining as MT); propose mechanical CI gaps for approval; never silently rewrite CI.

### 9C-9E. Hand off to `/update release`

The documentation cleanup, the standard update checks, and the version bump / changelog / tag / push are owned by `/update release` in v3.x (it runs docs -> devlog -> gitignore -> version via `scripts/check_version_sync.py` -> changelog -> refactor, then cleans up, commits, tags, and pushes as one atomic flow, keeping its own confirmation gates). Do NOT re-implement the old inline `/update-*` sequence here and NEVER create a tag or push automatically - hand off to `/update release` and let it drive its gates. Surface any hold condition (unresolved release-blocker, tests failing / coverage below threshold without bypass, version-sync inconsistency, unapproved next-version choice) and stop before the release step if one is active.

## Completion report

Non-final phase: short form (plan, phase, subtasks done, tests, lint, deviations, known-gaps delta, files written, commit action, next phase). Final phase: extend with a "Release readiness" block summarizing 9.0 / 9A / 9B and the `/update release` handoff outcome, plus any active hold conditions.

## Iterative refinement

The whole workflow is iterative: after a pass, check completeness and correctness, refine, and loop up to 3 times (or the user-specified count) until the phase is stable.
