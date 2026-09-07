# Known Gaps - v4.8

**Project**: Nexus-Hub
**Status**: open; seeded when the agentic-setup work landed on develop after the v4.7.0 release
**Last updated**: 2026-09-06

## Carried in from the v3.14 agentic-setup adoption

That branch shipped its own v3.14 ledger, written 2026-07-13 while the release was still held. It is
superseded: v3.14.0 released on 2026-07-16 and develop's v3.14 ledger has been maintained through
v3.14.6. Rather than merge a stale ledger over a released one, its still-open items are carried here,
where the work is actually landing. WN-2 (stale marketplace skill-count prose) is dropped as resolved:
the counts were recomputed from the merged catalog in this landing and now sum to 336.

### Warnings (WN)

#### WN-1 - New pushy skill descriptions exceed the 250-char full-mode length check

- **Source phase**: Phase 1 (1.1, 1.2), Phase 2 (2.1)
- **Plan reference**: `docs/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md` sub-tasks 1.1-1.2, 2.1
- **Reason**: `false-confidence-test-audit`, `commit-sweep`, and `lint-repair-loop` carry pushy descriptions (verbatim trigger phrases plus a SKIP clause) well over 250 characters, so `validate_skills.py` FULL mode would flag them. This is the known catalog-wide pushy-description-vs-250-char tension (the WN-v3121 family); `make validate` does not run full mode and is clean. Intentional per the AGENTS.md description-style rule (combat under-triggering).
- **Suggested next step**: None required. Track with the catalog-wide description-length decision; do not shorten at the cost of trigger coverage.

#### WN-3 - Bash hook tests cannot run on the Windows dev host

- **Source phase**: Phase 2 (2.3)
- **Plan reference**: sub-task 2.3
- **Reason**: `pytest catalog/hooks/tests/test_lint_autofix.py` fails locally because `shutil.which("bash")` resolves to the Windows `system32\bash.EXE` (WSL), which cannot read a Windows-path `.sh` (exit 127). This is the WN-1 environment family from v3.12. The hook's six behaviors were instead verified end-to-end through Git Bash (opt-in gate, fail-open, non-commit no-op, disabled-env opt-out, skip-unstaged, and format + re-stage with ruff on PATH), ShellCheck is clean, the `.ps1` AST parses, and the test collects cleanly (7 tests).
- **Suggested next step**: None required. CI (ubuntu) is the authoritative gate for the bash hook suites; `pip install pytest ruff` was added to the CI tests job this phase so the ruff-gated formatting cases also run there (ubuntu-latest ships jq).

### Missing tests / coverage gaps (MT)

#### MT-1 - capture_screenshot.py is not unit-tested

- **Source phase**: Phase 4 (4.2)
- **Plan reference**: `docs/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md` sub-task 4.2
- **Reason**: `capture_screenshot.py` drives a headless Chromium-family browser, which is not reliably present in CI or on the dev host, so it is documented and degrades gracefully (exit 3 with an install hint) rather than unit-tested. The perceptual-diff core (`perceptual_diff.py`) IS fully tested (7 cases, Pillow-gated), and `Pillow` was added to the CI tests job so those run.
- **Suggested next step**: Add a browser-gated smoke test in a CI job that installs a headless browser, or exercise it in the Phase 7 end-of-shift orchestrator's visual-regression step when a browser is available.
