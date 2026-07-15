# Known Gaps - v3.15

**Project**: Nexus-Hub
**Status**: in development (Phase 4 of 8 complete)
**Last updated**: 2026-07-13 (Phase 4: visual-regression-testing skill + perceptual-diff / capture scripts)

## v3.15.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 3 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Warnings

##### WN-1 - New pushy skill descriptions exceed the 250-char full-mode length check

- **Source phase**: Phase 1 (1.1, 1.2), Phase 2 (2.1)
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.0-agentic-setup-adoption.md` sub-tasks 1.1-1.2, 2.1
- **Reason**: `false-confidence-test-audit`, `commit-sweep`, and `lint-repair-loop` carry pushy descriptions (verbatim trigger phrases plus a SKIP clause) well over 250 characters, so `validate_skills.py` FULL mode would flag them. This is the known catalog-wide pushy-description-vs-250-char tension (the WN-v3121 family); `make validate` does not run full mode and is clean. Intentional per the AGENTS.md description-style rule (combat under-triggering).
- **Suggested next step**: None required. Track with the catalog-wide description-length decision; do not shorten at the cost of trigger coverage.

##### WN-2 - Catalog skill-count prose in marketplace.json is stale

- **Source phase**: Phase 1 (1.3)
- **Plan reference**: sub-task 1.3
- **Reason**: `data/marketplace.json` `plugin.description` prose still reads "265 curated skills" while the true count is now 269 (`skills.json` and the `SKILL_INDEX.md` total are both current). The prose count was already stale before this version and bundles the command and hook counts plus the version, which are reconciled together at release.
- **Suggested next step**: `/update release` reconciles the marketplace `plugin.description` counts (skills / commands / hooks) and the version bump atomically; no mid-version action is needed.

##### WN-3 - Bash hook tests cannot run on the Windows dev host

- **Source phase**: Phase 2 (2.3)
- **Plan reference**: sub-task 2.3
- **Reason**: `pytest catalog/hooks/tests/test_lint_autofix.py` fails locally because `shutil.which("bash")` resolves to the Windows `system32\bash.EXE` (WSL), which cannot read a Windows-path `.sh` (exit 127). This is the WN-1 environment family from v3.12. The hook's six behaviors were instead verified end-to-end through Git Bash (opt-in gate, fail-open, non-commit no-op, disabled-env opt-out, skip-unstaged, and format + re-stage with ruff on PATH), ShellCheck is clean, the `.ps1` AST parses, and the test collects cleanly (7 tests).
- **Suggested next step**: None required. CI (ubuntu) is the authoritative gate for the bash hook suites; `pip install pytest ruff` was added to the CI tests job this phase so the ruff-gated formatting cases also run there (ubuntu-latest ships jq).

#### Missing tests / coverage gaps

##### MT-1 - capture_screenshot.py is not unit-tested

- **Source phase**: Phase 4 (4.2)
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.0-agentic-setup-adoption.md` sub-task 4.2
- **Reason**: `capture_screenshot.py` drives a headless Chromium-family browser, which is not reliably present in CI or on the dev host, so it is documented and degrades gracefully (exit 3 with an install hint) rather than unit-tested. The perceptual-diff core (`perceptual_diff.py`) IS fully tested (7 cases, Pillow-gated), and `Pillow` was added to the CI tests job so those run.
- **Suggested next step**: Add a browser-gated smoke test in a CI job that installs a headless browser, or exercise it in the Phase 7 end-of-shift orchestrator's visual-regression step when a browser is available.

### Notes

- Phase 1 and Phase 2 added Markdown skills. Skills have no pytest surface by design (they are validated structurally by `validate_skills.py`, not unit-tested), so the absence of unit tests is not an MT gap. The Phase 2 `lint-autofix` hook DOES have a test (`test_lint_autofix.py`).
- Phase 2's `lint-autofix` hook is registered but OPT-IN (inert unless `NEXUS_ENABLE_LINT_AUTOFIX=1`), a deliberate deviation from the plan's "opt-out" wording because the hook mutates files; it is placed after `git-guardrails` so a blocked commit is not autofixed, and it never touches a file with unstaged changes. The LLM-judgment repair half is the `lint-repair-loop` skill, run on the session model (no external repair vendor, per the MCP Registry Policy hard-no on generation-as-service).
- The plan was renumbered from v3.13.0 to v3.15.0 during Phase 1: v3.13.0 is the committed presentify-universal-ingestion version and an untracked v3.14.0-codex-lb-adoption draft already exists.
