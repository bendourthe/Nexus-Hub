---
description: Implement one phase of a plan end-to-end — from plan discovery and pre-implementation review through coding, linting, testing, troubleshooting, and the full post-phase documentation and commit sequence. Supports plans produced by /generate-plan under docs/<version>/plans/, plus legacy docs/<version>/implementation-plan.md files.
---

# Implement Phase Command

Implement one phase of a plan end-to-end. The command discovers the right plan and phase, implements the code, lints, tests, troubleshoots failures, augments missing tests, and runs the full post-phase documentation and commit sequence when everything passes.

Plans are expected at `docs/<version>/plans/<slug>.md` (produced by `/generate-plan`). Legacy plans at `docs/<version>/implementation-plan.md` are still discovered automatically for backwards compatibility.

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
    *   Primary location: `docs/**/plans/*.md` (the layout produced by `/generate-plan`).
    *   Legacy fallback: `docs/**/implementation-plan.md` (the pre-rename layout — still supported so old projects keep working).
    *   Also search `docs/development/` and the project root for both patterns.
    *   Dedupe by absolute path.

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

6.  **Pre-flight summary** — display before any code changes and wait for confirmation:

    ```
    Ready to implement:

    Plan:    docs/v0.2.0/plans/authentication.md
    Phase:   3 — Authentication
    Status:  Not started
    Prior phases complete: ✓ (phases 1–2)

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

Run each step in strict order. Wait for each to fully complete before starting the next.

1.  **`/update-gitignore`**
    *   Ensures any new build artifacts, cache directories, or generated files created during this phase are correctly ignored.

2.  **Update `docs/<version>/known-gaps.md`** (apply the `known-gaps-tracker` skill in Append mode)
    *   Locate or create `docs/<version>/known-gaps.md`. The version is the one that owns the active plan (`docs/<version>/plans/<slug>.md`).
    *   Walk the artifacts produced by Phases 2–7 and append every gap discovered during this phase, classified by category prefix:
        *   `# DEVIATION:` markers from Phase 2 → `NI` (skipped subtask), `DF` (intentionally deferred), or `BG` (deviation revealed a bug).
        *   Unresolved test failures from Phase 6 when the user picked option A "Skip failing tests" → `BG`.
        *   Coverage shortfalls from Phases 4 and 5 → `MT`.
        *   Suppressed lint rules or runtime warnings observed during Phase 3 → `WN`.
        *   Any gate the user bypassed with "Proceed anyway" in Phase 7 → `QG`.
    *   Each item must include all four fields: `Source phase`, `Plan reference`, `Reason`, `Suggested next step`.
    *   If this phase resolved any earlier open item from the same file, move it from `## Open Items` to the `## Resolved` table with `Resolved in: Phase N`.
    *   Recompute the `## Summary` table counts and update `Last updated`. **Do not finalize the file** — that happens at version bump in `/wrap-up-session` Phase 6.

3.  **`/update-devlog`**
    *   Documents: what was implemented, key decisions, deviations from the plan, test results, and any known issues.
    *   Reference `docs/<version>/known-gaps.md` for the structured gap list rather than re-listing items inline.

4.  **`/update-documentation`**
    *   Syncs README, API docs, architecture docs, and inline guides with the new code.

5.  **`/generate-session-history`**
    *   Produces a standalone session history file for this phase in `docs/<version>/development/history/`.
    *   Include: plan reference, subtasks completed, test results, deviations, and next steps.

6.  **`/generate-commit-message`**
    *   Generates a structured commit message scoped to this phase. Include `docs/<version>/known-gaps.md` in the file list so the gap log is committed alongside the phase work.
    *   The user reviews the message and commits manually — this command does **not** commit automatically.

---

## Completion Report

After the post-phase sequence, print a final summary:

```
Phase implementation complete:

Plan:           docs/v0.2.0/plans/authentication.md
Phase:          3 — Authentication
Subtasks done:  5/5
Tests:          42 passed, 0 failed (coverage: 84%)
Lint:           ✓ clean
Deviations:     1 (see devlog)
Known gaps:     2 added, 1 resolved (see docs/v0.2.0/known-gaps.md)
Files written:
  - docs/DEVLOG.md (updated)
  - docs/v0.2.0/known-gaps.md (updated)
  - docs/v0.2.0/development/history/2026-04_phase-3-authentication.md
Commit message: ready for your review

Next phase: 4 — API Endpoints
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
