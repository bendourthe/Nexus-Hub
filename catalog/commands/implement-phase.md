---
description: Implement one phase of a plan end-to-end — from plan discovery and pre-implementation review through coding, linting, testing, troubleshooting, and the full post-phase documentation and commit sequence. When the final phase of a plan completes, also runs an automatic release-readiness workflow (resolve known gaps, verify tests + CI/CD, refactor docs / project, run update-* checks, prepare the version bump and release). Supports plans produced by /generate-plan under docs/versions/<vMAJOR>/<vSEMVER>/plans/ (canonical) and docs/<vSEMVER>/plans/ (legacy), plus older docs/<version>/implementation-plan.md files.
---

# Implement Phase Command

Implement one phase of a plan end-to-end. The command discovers the right plan and phase, implements the code, lints, tests, troubleshoots failures, augments missing tests, and runs the full post-phase documentation and commit sequence when everything passes.

When the phase being implemented is the **final phase** of the plan (detected automatically — never relies solely on the user saying "this is the last one"), the command additionally runs Phase 9, an automatic release-readiness workflow: it resolves outstanding known gaps, verifies test and CI/CD coverage, runs the docs and project refactor commands, applies the standard `/update-*` checks, and prepares the version bump, tag, and release.

Plans are expected at `<version_dir>/plans/<slug>.md`. `<version_dir>` resolves to the canonical `docs/versions/<vMAJOR>/<vSEMVER>/` when present, falling back to legacy `docs/<vSEMVER>/` when the project has not yet migrated. Legacy plans at `<version_dir>/implementation-plan.md` are still discovered automatically for backwards compatibility.

## Invocation

```
/implement-phase                                       # interactive — prompts for plan and phase
/implement-phase <slug>                                # resolve to docs/**/plans/<slug>.md
/implement-phase <path/to/plan.md>                     # direct file path
/implement-phase <slug> phase-3                        # slug + phase number
/implement-phase <slug> "Authentication"               # slug + phase name
/implement-phase v0.2.0                                # version only (picks the single plan under that version, or prompts)
/implement-phase v0.2.0 phase-3                        # legacy-compatible form
/implement-phase v0.2.0 "Authentication"               # legacy-compatible form
```

---

## Phase 0: Resolve Plan, Version, and Phase

1.  **Parse the invocation** for optional positional arguments. The first positional argument is **either** a plan slug, a plan file path, or a version label; the second (if present) is the phase. Disambiguate as follows:
    *   If the first argument contains a `/` or ends in `.md` → treat as a file path.
    *   Else if it matches `v?\d+\.\d+\.\d+` → treat as a version label.
    *   Else → treat as a plan slug.
    *   Accept phase as a number (`3`), a slug (`phase-3`), or a quoted name (`"User Authentication"`).

2.  **Search for plans**:
    *   Canonical location: `docs/versions/v*/v*/plans/*.md` (the layout produced by `/generate-plan` after Step 0b.5 path resolution).
    *   Legacy flat layout: `docs/v*/plans/*.md` (still supported for projects that have not migrated).
    *   Legacy filename: `docs/**/implementation-plan.md` (the pre-rename layout — still supported so old projects keep working).
    *   Also search `docs/development/` and the project root for both patterns.
    *   Dedupe by absolute path. When a plan exists at both canonical and legacy paths (a transitional state), prefer the canonical path and surface a notice: `Inconsistent layout: plan present at both canonical and legacy paths. Using canonical. Run /refactor-docs --canonicalize-layout to migrate.`

3.  **Plan selection**:
    *   If a **file path** was given: resolve it directly; error if the file does not exist.
    *   If a **slug** was given: filter matches to `docs/**/plans/<slug>.md`. If a single match remains, use it. If multiple (different versions), ask which version.
    *   If a **version** was given (or derived from a slug that matched one version): filter to plans under that version. If one plan, use it. If multiple, ask which slug.
    *   If **no argument** was given and one plan total is found: use it automatically and confirm in chat.
    *   If **no argument** was given and multiple plans are found: list them grouped by version, most-recent first:

        ```
        Found multiple plans:

        docs/v0.2.0/plans/
          1. authentication.md
          2. payment-integration.md
        docs/v0.1.0/plans/
          3. v0.1.0-initial.md
        docs/v0.1.0/implementation-plan.md          (legacy)

        Which plan should I work from?
        ```

    *   If **no plan found anywhere**: report the paths searched and suggest running `/generate-plan` first.

4.  **Parse the selected plan** to extract the phase list (numbers, names, and completion status).

5.  **Phase selection**:
    *   If **no phase was specified**: display the phase list and ask which to work on:

        ```
        Phases in this plan:
        1. [✓] Environment Setup
        2. [✓] Database Schema
        3. [ ] Authentication — (target)
        4. [ ] API Endpoints
        5. [ ] Frontend Integration

        Which phase should I implement?
        ```

    *   If **the specified phase is already marked complete**: warn the user and ask:

        ```
        Phase 3 (Authentication) appears to be already marked complete in the plan.
        Re-implement anyway? (Y = yes, N = pick a different phase)
        ```

6.  **Final-phase detection** — examine the parsed phase list to determine whether the **target phase is the final phase of the plan**. Use ALL of the following signals; do not rely on the user's claim alone.

    *   **Phase ordering**: the target phase is the numerically highest phase in the plan, or the last `## Phase N: ...` heading by document order.
    *   **Phase title heuristics**: titles such as "Polish & Cross-Cutting Concerns", "Final QA and Release", "Release Prep", "Polish", or "Wrap-up" reinforce final-phase detection.
    *   **Completion status of prior phases**: every prior phase shows `[✓]` in the parsed phase list OR has a corresponding session-history file under `<version_dir>/development/history/`.
    *   **Plan metadata**: if the plan front matter or Overview contains a `Final-Phase: N` marker, honor it explicitly.
    *   **Adjacent plans**: the plan slug indicates the only plan under the active version directory (e.g., `v0.1.0/plans/v0.1.0-initial.md` with no sibling plans), suggesting this plan owns the entire version.

    Set the boolean `is_final_phase` based on the combined signals. If signals conflict (e.g., target phase is numerically last but several prior phases are unchecked), set `is_final_phase = false` and surface a one-line notice: `Final-phase detection: target phase is numerically last, but N prior phases are not marked complete. Treating as non-final.`

    The `is_final_phase` flag determines whether Phase 9 (the Final-Phase Completion Workflow) runs after Phase 8. Detection happens here in Phase 0 so the pre-flight summary can show it; the workflow itself executes only after Phase 8 completes successfully.

7.  **Pre-flight summary** — display before any code changes and wait for confirmation:

    ```
    Ready to implement:

    Plan:    docs/versions/v0/v0.2.0/plans/authentication.md
    Phase:   3 — Authentication
    Status:  Not started
    Prior phases complete: ✓ (phases 1–2)
    Final phase:           no   (3 of 5)

    Shall I proceed?
    ```

    When `is_final_phase = true`, the summary instead shows:

    ```
    Ready to implement:

    Plan:    docs/versions/v0/v0.2.0/plans/v0.2.0-initial.md
    Phase:   5 — Polish & Cross-Cutting Concerns
    Status:  Not started
    Prior phases complete: ✓ (phases 1–4)
    Final phase:           yes  (5 of 5)
    Release-readiness workflow will run automatically after Phase 8.

    Shall I proceed?
    ```

---

## Phase 1: Pre-Implementation Review

1.  **Read the full plan** to understand overall architecture and how the target phase fits.

2.  **Read the target phase in detail** — extract:
    *   Goals and acceptance criteria
    *   Subtasks and their order
    *   Files to create or modify (if listed)
    *   Dependencies on prior phases

3.  **Check prerequisites** — for each phase the target depends on:
    *   Confirm it is marked complete in the plan.
    *   Search git log for commits referencing it (`git log --oneline --all | grep -i "<phase name>"`).
    *   If a prerequisite appears incomplete, warn the user with specifics and ask whether to continue.

4.  **Scan the codebase** for files the phase will touch — grep for module names, class names, and identifiers mentioned in the phase description.

5.  **Report before implementation begins**:

    ```
    Pre-implementation review:

    Phase goal:         [goal from plan]
    Subtasks:           N subtasks
    Files likely affected:
      - src/auth/handler.py
      - tests/unit/test_auth.py
      - ...
    Prerequisite check: ✓ phases 1–2 complete
    Dependency warnings: none
    ```

---

## Phase 2: Implementation

1.  **Work subtask by subtask** in the order specified by the plan.

2.  **Incremental verification** — after each subtask, confirm the code compiles or imports cleanly before moving to the next one. Do not accumulate multiple broken subtasks.

3.  **Log deviations** — if the plan cannot be followed exactly, note each deviation inline with a `# DEVIATION:` comment and keep a running list to report in Phase 8. Common reasons: plan references a file that does not exist, a dependency API has changed, or a subtask is already implemented.

4.  **Stay in scope** — do not refactor code outside the phase boundary, do not add speculative features or error handling for hypothetical scenarios, and do not change unrelated files.

5.  **Compile/import check** — once all subtasks are done, verify the project builds or imports without errors before proceeding to linting.

---

## Phase 3: Lint and Format

1.  **Detect the project's language(s)** from file extensions, `package.json`, `pyproject.toml`, `go.mod`, `tsconfig.json`, `.eslintrc`, and similar config files.

2.  **Run the appropriate linter and formatter**:

    | Language | Commands |
    |---|---|
    | Python | `ruff check . --fix && ruff format .` |
    | TypeScript / JS | `eslint --fix .` then `prettier --write .` |
    | Go | `gofmt -w .` then `golangci-lint run` |
    | Mixed | Run each language's tools in turn |
    | No config found | Report which tools were tried and ask the user how to lint |

3.  **Auto-fix everything fixable** — apply auto-fixes without prompting. Report a summary of what was fixed.

4.  **Manual issues** — for lint errors that cannot be auto-fixed, resolve them before proceeding. Do not skip or suppress lint rules. Do not proceed to testing with lint errors outstanding.

---

## Phase 4: Test Execution and Coverage Analysis

1.  **Detect the test runner** from `package.json` scripts, `pyproject.toml`, `Makefile`, or `go.mod`.

2.  **Run the full test suite** with coverage enabled:

    | Language | Command |
    |---|---|
    | Python | `pytest --cov=src --cov-report=term-missing -q` |
    | TypeScript / JS | `vitest run --coverage` or `jest --coverage` |
    | Go | `go test -race -coverprofile=coverage.out ./...` |

3.  **Capture and report**:
    *   Total: passed / failed / skipped
    *   Line coverage percentage
    *   Which new or modified files have coverage below 80%

4.  **Routing**:
    *   Coverage >= 80% **and** 0 failures → skip to Phase 6 (Troubleshooting Loop is a no-op).
    *   Coverage < 80% **or** tests missing for newly implemented code → proceed to Phase 5.
    *   Failures present → proceed to Phase 6.

---

## Phase 5: Test Augmentation

1.  **Invoke `/generate-unit-tests`** targeting the files added or modified during Phase 2.
    *   For integration-level behavior (APIs, database calls, service interactions) also invoke `/generate-tests`.

2.  **Ensure generated tests follow project standards**:
    *   AAA pattern (Arrange, Act, Assert)
    *   Parametrize for data-driven cases
    *   Fixtures in `conftest.py` / `vitest.setup.ts` — not inline
    *   No `sleep` / fixed delays in tests

3.  **Re-run the test suite** after adding new tests. Re-capture coverage.

4.  **If coverage is still below 80%**: identify the remaining uncovered paths and generate additional targeted tests for them. Repeat once more if needed.

5.  **Proceed to Phase 6** once tests are generated (whether or not all pass — failures are handled there).

---

## Phase 6: Troubleshooting Loop (max 3 iterations)

Repeat the following loop up to **3 times** total:

1.  **Read every failure** — collect test name, failure message, and full stack trace.

2.  **Classify each failure**:
    *   `IMPL` — bug in the implementation code
    *   `TEST` — the test itself is incorrect (wrong expectation, bad mock, stale fixture)
    *   `ENV` — environment or dependency issue (missing package, wrong Python/Node version)

3.  **Apply targeted fixes**:
    *   `IMPL` failures → fix the implementation; do not change the test unless the test was wrong.
    *   `TEST` failures → fix the test; document why the original expectation was wrong.
    *   `ENV` failures → resolve the environment issue; document the fix in the deviation log.

4.  **Re-run the test suite** and check whether the failure count decreased.

5.  **Stop early** if all tests pass before reaching 3 iterations.

**After 3 iterations with remaining failures** — stop the loop and report:

```
Unresolved failures after 3 iterations:

1. test_auth_token_expiry
   Error:    AssertionError: expected 401, got 200
   Attempts: [list of fixes tried]
   Assessment: likely requires a mock for the JWT expiry clock

2. ...

How would you like to proceed?
A. Skip failing tests and continue to the quality gate
B. Abort — I will investigate manually
C. Extend the loop (specify how many more iterations)
```

Wait for the user's answer before continuing.

---

## Phase 7: Quality Gate (GO / NO-GO)

Evaluate all four gates before running the post-phase sequence:

| Gate | Threshold | Status | Action if failed |
|---|---|---|---|
| All tests passing | 0 failures | ✓ / ✗ | Re-enter troubleshooting loop or escalate |
| Line coverage | >= 80% | ✓ / ✗ | Re-enter test augmentation |
| Lint errors | 0 errors | ✓ / ✗ | Fix before proceeding |
| Build / compile | Succeeds | ✓ / ✗ | Fix before proceeding |

**If all gates pass**: print `Phase complete — running post-phase sequence.` and continue.

**If any gate fails after retries**: ask the user:

```
The following quality gates did not pass:
- [gate]: [current value] (threshold: [required value])

Would you like to:
A. Proceed anyway (document the gap in the devlog)
B. Stop here — I will resolve this manually
```

---

## Phase 8: Post-Phase Completion Sequence

Run **every** step below in strict order at the end of **every** phase — not just the final one. The order is deliberate: validation steps run first so failures surface before any documentation work, then documentation steps run, then the commit step closes the phase. Do not skip steps based on perceived irrelevance ("nothing to update", "no tests changed") — the steps are designed to be no-ops when there is nothing to do, but they MUST be invoked so the user gets a consistent end-of-phase signal every time.

Wait for each step to fully complete before starting the next.

### 8.1. `/update-gitignore`

Ensures any new build artifacts, cache directories, or generated files created during this phase are correctly ignored. Report `0 patterns added` when there is nothing new — do not skip the call.

### 8.2. Test review (post-phase pass)

Even if Phase 4-6 finished green, perform a short consistency check before declaring the phase done. This catches drift between what Phase 4 ran and what the codebase looks like after Phase 7's quality-gate adjustments:

1. **Re-run the test suite once** with the same command Phase 4 used. Report `<N> passed, <M> failed, coverage <X>%`.
2. **Confirm new code is exercised**: every file added or modified during Phase 2 should have at least one test file that imports / references it. List any unreferenced new files.
3. **If gaps surface here** (new file with no tests, or failures that were green in Phase 4 but red now): invoke `/generate-unit-tests` for the unreferenced files, then re-run the suite. Stop after one augmentation pass — log remaining gaps as `MT` entries in step 8.4 below; do not loop.

Report:

```
Sub-step 8.2 complete.
  Tests:               N passed, M failed (coverage: X%)
  New files w/o tests: K (added as MT entries to known-gaps.md)
```

### 8.3. CI/CD readiness check (per-phase)

A lightweight CI/CD pass that catches per-phase configuration drift. (The deeper sweep happens in Phase 9B for the final phase.)

1. **Detect the active CI system** from `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `azure-pipelines.yml`, `.circleci/config.yml`. If none is present, report `CI/CD: not configured for this project` and continue.
2. **Cross-check Phase 2 modifications against CI declarations**:
    *   If Phase 2 added a new top-level script command (e.g., new entry in `package.json` `scripts`, new pytest module, new Make target), confirm the CI build/test job runs the equivalent.
    *   If Phase 2 added a new environment variable used at runtime, confirm it is declared in the CI workflow (as a secret reference; never the value itself).
    *   If Phase 2 added a new package dependency, confirm the install step in CI picks it up (lockfile changes committed, install command unchanged).
3. **Never silently rewrite CI/CD configs**. When a gap is detected, propose the diff inline; apply only with explicit user approval. Unapproved CI gaps become `QG` entries in step 8.4.

Report:

```
Sub-step 8.3 complete.
  CI system:        GitHub Actions
  Workflows touched: 0
  Proposed edits:    N (applied: M, deferred: K)
```

### 8.4. Update `<version_dir>/known-gaps.md` (known-gaps-tracker skill, Append mode)

*   Locate or create `<version_dir>/known-gaps.md`. The version is the one that owns the active plan (`<version_dir>/plans/<slug>.md`).
*   Walk the artifacts produced by Phases 2–7 plus sub-steps 8.2 and 8.3 above. Append every gap discovered during this phase, classified by category prefix:
    *   `# DEVIATION:` markers from Phase 2 → `NI` (skipped subtask), `DF` (intentionally deferred), or `BG` (deviation revealed a bug).
    *   Unresolved test failures from Phase 6 when the user picked option A "Skip failing tests" → `BG`.
    *   Coverage shortfalls from Phases 4 and 5, and new files without tests from sub-step 8.2 → `MT`.
    *   Suppressed lint rules or runtime warnings observed during Phase 3 → `WN`.
    *   Any gate the user bypassed with "Proceed anyway" in Phase 7, including unapproved CI gaps from sub-step 8.3 → `QG`.
*   Each item must include all four fields: `Source phase`, `Plan reference`, `Reason`, `Suggested next step`.
*   If this phase resolved any earlier open item from the same file, move it from `## Open Items` to the `## Resolved` table with `Resolved in: Phase N`.
*   Recompute the `## Summary` table counts and update `Last updated`. **Do not finalize the file** — that happens at version bump in `/wrap-up-session` Phase 6.

### 8.5. Docs cleanup audit (`/refactor-docs --mode audit`)

Run `/refactor-docs` in audit-only mode — the report writes to `<next_version_dir>/docs-cleanup-report.md` and **no files move**.

The audit pass catches stale docs artifacts that the active phase may have left behind (orphan comparison reports, abandoned session-history drafts, superseded plans). The report surfaces them for the next session or the final-phase workflow to apply.

If the audit finds Cat 1 (delete) or Cat 2 (archive) candidates whose origin is THIS phase (e.g., a temporary scratch doc the agent created and abandoned), propose them inline and ask whether to clean up now. Default to leaving them in place — the audit-only report is the canonical surface.

Report:

```
Sub-step 8.5 complete.
  Docs cleanup report: <next_version_dir>/docs-cleanup-report.md
  Cat 1: N   Cat 2: N   Cat 3: N   Cat 4: N
  Cleaned up this phase: M files (only if user explicitly approved)
```

### 8.6. `/update-devlog`

Documents what was implemented, key decisions, deviations from the plan, test results from sub-step 8.2, CI/CD changes from sub-step 8.3, and any known issues. Reference `<version_dir>/known-gaps.md` for the structured gap list rather than re-listing items inline.

### 8.7. `/update-documentation`

Syncs README, API docs, architecture docs, and inline guides with the new code. Run regardless of whether the phase felt "documentation-affecting" — the command is a no-op when nothing changes.

### 8.8. `/generate-session-history`

Produces a standalone session history file for this phase in `<version_dir>/development/history/`. Include: plan reference, subtasks completed, test results (from 8.2), CI/CD edits (from 8.3), deviations, and next steps.

### 8.9. `/generate-commit-message`

Generates a structured commit message scoped to this phase. Include `<version_dir>/known-gaps.md`, the docs cleanup report from 8.5, any session-history files written in 8.8, and every other file touched during the phase in the staged file list.

*   **Sectioned-bullet structure (CRITICAL)**: a phase commit always touches multiple components, so the body MUST use **labeled sections with bullets**, NOT multiple flowing paragraphs. After the subject line and a 1-2 sentence intro paragraph, organize the body as named sections with headers ending in a colon, each followed by contiguous bullets (no blank lines between bullets within a section). Group bullets by component / module / theme (e.g., `Reporting package (`src/reporting/`):`, `Packaging and paths:`, `Desktop UI:`). Always treat **Tests** (test counts, coverage), **CI/CD** (workflow edits or N/A), and **Known gaps** (referencing `<version_dir>/known-gaps.md`) as their own dedicated final sections.
*   **No hard-wrapping (CRITICAL)**: every paragraph and every bullet point in the commit body and footer MUST be written as a single continuous line in the source, regardless of length. Do NOT insert line breaks at any column width (50, 72, 80, 100, etc.). The 72-char "convention" from older git tooling docs is obsolete - modern Git, GitHub, GitLab, and `git log` all soft-wrap on display. The subject line's 50-char cap is the only exception (a hard limit, not a wrap).
*   **Whitespace**: exactly one blank line between sections; never two or more. Within a section, bullets are contiguous.

The command produces the message in your working context. It does **not** commit automatically — step 8.10 is the explicit prompt that asks for permission.

### 8.10. Commit and push prompt (REQUIRED — run on every phase)

After the commit message is generated, **always** ask the user whether to commit and push. This step is non-negotiable: a phase is not done until the user has had the explicit choice. Skipping this step is the source of the inconsistency the previous version of Phase 8 produced; every phase ends here.

Show the user:

```
Phase N is ready to commit.

Files staged (M):
  - src/...
  - tests/...
  - docs/...

Commit message preview:
  <subject line>

  <first paragraph of body>
  ...

How should I proceed?
  1. Commit only (review staged files, run `git commit`; do NOT push)
  2. Commit and push (run `git commit` then `git push` against the current branch's upstream)
  3. Stage another file / amend the message (loop back to 8.9)
  4. Stop — I will handle the commit manually
```

Wait for the user's answer. Then:

*   **Option 1 (Commit only)**: run `git status` to confirm staged content, run `git commit` with the prepared message via heredoc, then report the new commit SHA. Do NOT push.
*   **Option 2 (Commit and push)**: same as Option 1, then run `git push` against the upstream of the current branch. Report the push result (commits ahead/behind, any branch protection warning). If no upstream is configured, ask whether to set it (`git push -u origin <branch>`) before pushing.
*   **Option 3 (Amend)**: accept additional files or message edits from the user, regenerate via /generate-commit-message if needed, then loop back to this prompt.
*   **Option 4 (Stop)**: leave staging as-is and exit. Report the prepared commit message verbatim so the user can use it.

**Never proceed past 8.10 without a definite answer.** A pre-flight that runs Phase 8 but skips the prompt is broken; surface the issue and re-prompt.

Final report after option 1 or 2:

```
Sub-step 8.10 complete.
  Action:        committed and pushed (or: committed only)
  Commit SHA:    abc1234
  Push target:   origin/main (3 commits ahead before push; 0 after)
```

---

---

## Phase 9: Final-Phase Completion Workflow (release-readiness)

**Runs only when `is_final_phase = true` was set in Phase 0 step 6 AND Phase 8 completed without errors.** Skip this entire phase otherwise — the regular Completion Report follows immediately.

The purpose of this phase is to leave the repository in a clean, documented, tested, versioned, and releasable state at the end of a plan. Every step below is safe to rerun and idempotent: if work was already done in a prior partial run, the step should detect that and short-circuit rather than redo.

Run sub-phases A through E in strict order. Wait for each to fully complete before starting the next.

Announce at the start:

```
Final phase detected (5 of 5). Running release-readiness workflow.

Sub-phases queued:
  A. Resolve known gaps and deferred work
  B. Verify tests and CI/CD readiness
  C. Run documentation and layout cleanup
  D. Run standard /update-* checks
  E. Prepare version bump, tag, and release

This workflow is non-destructive: every step prompts before it commits, archives,
or tags. Reply "skip A" / "skip B" / etc. to bypass any sub-phase.
```

Wait for confirmation or skip directives before continuing.

### 9A. Resolve Known Gaps and Deferred Work

Goal: every gap, TODO, deferred task, follow-up item, and incomplete implementation note that was recorded during the plan is either resolved or explicitly captured for the next plan.

1. **Re-read the gap log**: open `<version_dir>/known-gaps.md`. Re-read the `## Open Items` section.
2. **Scan for in-code markers**: grep the codebase for `TODO`, `FIXME`, `XXX`, `HACK`, and `# DEVIATION:` markers introduced during this version. Cross-reference against the gap log; add any unrecorded markers as new gap entries (apply the `known-gaps-tracker` skill in Append mode).
3. **Per-item triage** — for each open item:
    *   **Still applies?** If the item was rendered obsolete by other work this version, move it to `## Resolved` with `Resolved in: superseded by Phase N work`.
    *   **In scope to resolve now?** If the fix is small, contained, and within the spirit of the plan's final phase, fix it inline. Use the same lint/test gates Phase 3-7 enforce. Move the entry to `## Resolved` with `Resolved in: Phase N (final-phase sweep)`.
    *   **Out of scope but still real?** Leave it in `## Open Items`. Ensure the `Reason` and `Suggested next step` fields are accurate so the next version's `/generate-plan` Step 0.6 can ingest it cleanly.
4. **Remove stale TODOs**: TODOs whose original context no longer exists (the referenced file was deleted, the bug was fixed, the deferred feature shipped) are removed from the source code with a brief commit-message note.
5. **Final report**:

    ```
    Sub-phase 9A complete.
      Gaps resolved this sub-phase:  N
      Gaps removed (stale):          N
      Open items carried forward:    N  (see <version_dir>/known-gaps.md)
    ```

If any open item is a blocker for the release (severity `BG`, marked `release-blocker`, or explicitly tagged as such), surface it now and ask the user whether to:

```
A. Resolve it before continuing (block 9B-9E)
B. Downgrade severity and continue (you take responsibility for the release containing this gap)
C. Cancel the final-phase workflow (resume after the blocker is fixed)
```

### 9B. Verify Tests and CI/CD Readiness

Goal: appropriate test coverage and CI/CD updates accompany the implementation.

1. **Inspect test surface**:
    *   For each module/file added or modified during the plan, confirm there is at least one unit test that exercises its main path.
    *   Confirm integration tests exist for any new service boundary (API endpoint, database call, message handler, external service integration).
    *   Confirm end-to-end tests exist for any new user-facing flow.
    *   Read existing test scripts/commands declared in `package.json`, `pyproject.toml`, `Makefile`, `go.mod` — every command listed should still execute cleanly.

2. **Inspect CI/CD surface** (detect the active CI system from `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `azure-pipelines.yml`, `.circleci/config.yml`):
    *   Verify the build job runs the project's build command.
    *   Verify the test job runs the same suite Phase 4 ran locally.
    *   Verify lint/typecheck jobs (if the project uses them) cover the files this plan added.
    *   Verify release/deploy workflows are still wired to the project's current entry points.
    *   Check whether new environment variables or secrets introduced this version are declared in the CI config (without leaking values).

3. **Apply safe additions**:
    *   When tests are missing for new code, invoke `/generate-unit-tests` and (for integration paths) `/generate-tests`, then re-run the suite per Phase 4-6 protocols. Stop after 3 augmentation passes; surface remaining gaps as `MT` entries in the gap log.
    *   When the CI config has a clear, mechanical gap (a new lint command not yet declared, a new test path not yet referenced), propose the diff to the user. Apply only after explicit approval.
    *   Never silently rewrite CI/CD configs.

4. **Final report**:

    ```
    Sub-phase 9B complete.
      Test files added:              N
      Test count delta:              +M
      Coverage:                      X% (was Y%)
      CI/CD edits proposed:          N  (applied: M, deferred: K)
    ```

### 9C. Run Documentation and Layout Cleanup

Goal: docs and project artifacts are organized; outdated content is archived.

1. **`/refactor-docs --mode audit`**: run in audit-only mode against `docs/`. The report lands at `<next_version_dir>/docs-cleanup-report.md`. Surface the Cat 1 / 2 / 3 / 4 summary.
2. **If the audit finds Cat 2 candidates from prior versions** (i.e., the project has older `docs/v*/` or `docs/versions/v*/v*/` directories whose contents should be archived): offer the user the choice to run `/refactor-docs --apply --canonicalize-layout` (and optionally `--auto-archive-older-versions`) now. Default to **NO** — the user must explicitly approve the layout change. The audit report alone fulfills sub-phase 9C even when no apply step runs.
3. **`/refactor-project`**: run in propose-only mode against the project artifacts outside `docs/`. When the final-phase workflow coincides with a major-version boundary (`active_major > prior_major`), also pass `--archive-prior-versions` so prior-major release notes, deploy checklists, and version-scoped CI workflows are surfaced for archival.
4. **Apply only on explicit approval**. Both refactor commands have confirmation gates; never auto-apply layout changes during the final-phase workflow.
5. **Final report**:

    ```
    Sub-phase 9C complete.
      Docs audit report:              <next_version_dir>/docs-cleanup-report.md
        Cat 1: N   Cat 2: N   Cat 3: N   Cat 4: N
      Project refactor plan:          <inline summary>
        Move: N   Archive: M   Manual review: K
      Applied changes:                <0 unless user opted in>
    ```

### 9D. Run Standard `/update-*` Checks

Goal: the project's standard update commands all complete cleanly before the release.

Detect the project type, language, package manager, and CI system. Then run the relevant subset of:

| Command | When to run |
|---|---|
| `/update-gitignore` | always (new build artifacts may have appeared) |
| `/update-documentation` | always (sync README, API docs, architecture docs, inline comments) |
| `/update-config` | when the project has `.claude/settings.json`, `settings.local.json`, or other tool configs that may need a refresh |
| `/update-scripts` | when the project has `scripts/` and the final phase added new helpers (run only if the command exists; otherwise mark as N/A) |
| `/update-ci` | when CI was edited during 9B (run only if the command exists; otherwise mark as N/A) |
| `/update-package-metadata` | when the project has a `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` whose metadata needs a refresh |
| `/update-release-notes` | always (prepare the next CHANGELOG / RELEASE_NOTES entry) |

For each command that does not exist as a slash command in the repo, perform the equivalent inline (update the relevant files directly with the same conventions). Always report which were run vs. skipped.

Each `/update-*` step is itself a propose-then-confirm flow. Honor each step's existing confirmation gate. Never bypass an `--apply` requirement.

Final report:

```
Sub-phase 9D complete.
  Commands run:    /update-gitignore, /update-documentation, /update-release-notes
  Commands N/A:    /update-scripts (no scripts/ dir), /update-ci (no CI changes)
  Files modified:  N (across M files)
```

### 9E. Prepare Version Bump, Tag, and Release

Goal: prepare (not necessarily execute) the version bump, tag, and release.

1. **Determine the next version**:
    *   Read the active version from Phase 0.
    *   Inspect the plan's scope: feature additions imply MINOR; bug-fix-only plans imply PATCH; breaking changes (declared in plan Overview or detected via API surface diff) imply MAJOR.
    *   For initial v0.x.0 plans, follow the plan's own version declaration (default `v0.1.0` for greenfield).
    *   Surface the proposed next version and the rationale. Ask the user to confirm or override.

2. **Sweep version references**: find every place the current version appears across the repo. Typical surfaces:
    *   `package.json` `version` field
    *   `pyproject.toml` `[project].version`, `[tool.poetry].version`
    *   `Cargo.toml` `[package].version`
    *   `go.mod` (rarely versioned in-file, usually via tags)
    *   `VERSION` file
    *   `CHANGELOG.md`, `RELEASE_NOTES.md`
    *   UI footer/about strings, splash screens, telemetry headers
    *   Docs (README badges, install instructions, version notes in `<version_dir>/`)
    *   `<version_dir>` itself (the directory name is version-scoped)
    *   Config files: `.env.example`, `config/*.toml`, `settings/*.yml`
    *   Installer scripts, distribution metadata (`setup.py`, `npm publish` flags)

3. **Propose the consolidated diff** to the user. Show every file that would change and the substring transform. Wait for explicit approval.

4. **Apply approved version bumps** with the standard copy + verify protocol used elsewhere in the codebase (read, replace, write, re-read to confirm).

5. **Prepare the release artifact**:
    *   Run `/update-release-notes` to draft the new CHANGELOG entry / release notes summary.
    *   Append a short "Highlights" section drawn from the plan's phase titles and any sub-phase 9A resolved items.
    *   Reference the gap log carryover so the release notes mention what slips to the next version.

6. **Prepare the git tag**:
    *   Propose the tag name `v<next-version>` and the annotated tag message (typically the release notes' short summary).
    *   **Never create the tag automatically**. Always present the exact `git tag` command for the user to run after they review the commit. If the workflow supports it and the user explicitly authorizes it ("yes, create the tag"), then run the tag command and report the SHA.

7. **Final report**:

    ```
    Sub-phase 9E complete.
      Next version:        v0.3.0 (was v0.2.0; rationale: feature additions, no breaking changes)
      Files updated:       N (package.json, pyproject.toml, CHANGELOG.md, README.md, ...)
      Release notes:       drafted in <next_version_dir>/RELEASE_NOTES.md
      Git tag:             prepared as v0.3.0 (annotated; not yet created)
      Carryover gaps:      N items remain open in <version_dir>/known-gaps.md
                           (will be ingested by /generate-plan for the next version)
    ```

8. **Hold conditions** — refuse to create the tag or open the release if any of these are true; surface the blocker and stop:

    *   Sub-phase 9A reported unresolved release-blocker gaps.
    *   Sub-phase 9B left tests failing or coverage below 80% without explicit user bypass.
    *   Sub-phase 9D's `/update-*` checks reported a failure that was not waived.
    *   The version-bump diff produced an inconsistency (different version strings in different files post-apply).
    *   The user has not explicitly approved the next-version choice.

### Phase 9 completion criteria

The Final-Phase Completion Workflow is **complete** when:

- All five sub-phases finished or were explicitly skipped by the user.
- No hold condition is active.
- The repository is in a clean, releasable state with the prepared (but not necessarily executed) version bump and tag.

After completion, proceed to the Completion Report below. The report includes a final "Release readiness" block summarizing 9A-9E.

---

## Completion Report

After the post-phase sequence, print a final summary. When the regular sequence finished and the phase was non-final, use the short form:

```
Phase implementation complete:

Plan:           docs/versions/v0/v0.2.0/plans/authentication.md
Phase:          3 — Authentication
Subtasks done:  5/5
Tests:          42 passed, 0 failed (coverage: 84%)
Lint:           ✓ clean
Deviations:     1 (see devlog)
Known gaps:     2 added, 1 resolved (see docs/versions/v0/v0.2.0/known-gaps.md)
Files written:
  - docs/DEVLOG.md (updated)
  - docs/versions/v0/v0.2.0/known-gaps.md (updated)
  - docs/versions/v0/v0.2.0/development/history/2026-04_phase-3-authentication.md
Commit message: ready for your review
Commit action:  committed and pushed (origin/main: 1 commit pushed)

Next phase: 4 — API Endpoints
```

When the phase was the final one and Phase 9 ran, extend the summary with a release-readiness block:

```
Phase implementation complete (final phase):

Plan:           docs/versions/v0/v0.2.0/plans/v0.2.0-initial.md
Phase:          5 — Polish & Cross-Cutting Concerns  (FINAL)
Subtasks done:  4/4
Tests:          212 passed, 0 failed (coverage: 86%)
Lint:           ✓ clean

Release readiness (Phase 9):
  9A  Known gaps:       3 resolved, 0 release-blockers, 2 carried forward
  9B  CI/CD:            tests + lint + build wired; 2 CI edits applied
  9C  Refactor audits:  docs (Cat 2: 4), project (Move: 1, Archive: 0)
  9D  /update-* checks: gitignore, documentation, release-notes (all OK)
  9E  Version bump:     v0.3.0 prepared; tag drafted (not created)
                         release notes drafted in docs/versions/v0/v0.3.0/RELEASE_NOTES.md

Hold conditions:    none active
Commit action:      committed and pushed (origin/main)
Ready to release:   yes — review commit, then run the proposed tag command
```

---

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Is it complete?
    *   Are there any obvious errors?
    *   Does it meet the user's requirements?
2.  **Refine**:
    *   Fix any issues found.
    *   Add missing components.
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.
