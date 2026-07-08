# Known Gaps - v3.11

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-07-08

## v3.11.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 1 | 5 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

##### NI-5 - Phase 8: full repo dogfood migration + v3.11.0 bump

- **Source phase**: Phase 8 - Nexus-Hub self-application
- **Plan reference**: `docs/v3/v3.11/plans/v3.11.0-workflow-governance-refinements.md` (Phase 8, 8.1-8.6)
- **Reason**: Terminal phase, not yet reached. The user explicitly required that the entire repo be migrated to the canonical docs-layout scheme at the end of the plan.
- **Suggested next step**: Migrate every `docs/v3.x.y/` (and the currently-untracked `docs/v3.11.0/`, incl. the stray `comparison-t3mp3st.md` / `plans/adoption-t3mp3st.md`) into `docs/v3/v3.x/` with link repair; normalize `docs/archive/`; run the upgraded `project-refactor` cleanup; apply the CI optimizations already partly landed in 7.5 (concurrency) to the remaining jobs (path filters, caching, gated matrix); update registries + base-template parity; bump to v3.11.0 via `check_version_sync.py`; then `/update release`. The `/update refactor` whole-docs-tree migration (generalized to any repo this cycle) is the mechanism.

#### Deferred

##### DF-1 - Residual live-verification gaps (external platform contracts)

- **Source phase**: Phase 7 (7.1 audit, residual gaps D1-D7)
- **Plan reference**: `docs/v3/v3.11/platform-read-contracts.md` (Residual live-verification gaps)
- **Reason**: These contracts depend on the current external platform's behavior and cannot be confirmed from the repo alone. The 7.4 `verify` and 7.5 CI smoke now REPORT/CATCH the resulting surfacing gaps, but the underlying external contracts still want a live probe.
- **Suggested next step**: Live-probe per platform: Codex prompt read path + format (D1) and skills discovery (D2); Antigravity 2.0 root-vs-`.agents/` instruction file (D3), exact global subpath (D4), `subagents`/`rules` consumption (D5), `.agents` vs `.agent` (D6); Cursor/Copilot global slash surfaces (D7); and whether `nexus-hub init` (the launcher) passes the `init` subcommand through (the on-open hook calls it fail-open). Feed results back into codex.py / antigravity.py.

#### Warnings

##### WN-1 - Extension-local compression eval not run in this environment

- **Source phase**: Phases 1-7 (verification)
- **Plan reference**: N/A (environment)
- **Reason**: `make` is unavailable on the Windows dev host, and the final `make validate` step (`cd extensions/nexus-context-compressor && python -m evals --check`) lives in an extension with its own environment; it is untouched by v3.11.0 but was not executed here.
- **Suggested next step**: Run the full `make validate` (including the compression accuracy-regression gate) in an environment with the extension deps before the v3.11.0 release (Phase 8 / `/update release`).

##### WN-2 - Windows MAX_PATH risk when seeding Antigravity `.agents/skills/` into a deep target

- **Source phase**: Phase 7 (7.3 auto-seed / 7.4 verify smoke)
- **Plan reference**: 7.3
- **Reason**: The Antigravity `.agents/skills/<name>/references/examples/...` flattened copy can exceed the Windows 260-char MAX_PATH when the target repo lives at a very deep path (observed with the OneDrive + deep-temp scratch dir during the 7.3 smoke; `shutil.copytree` raised WinError 3). A normal-depth repo is well under the limit.
- **Suggested next step**: Consider enabling Windows long-path support in the copytree (prefix `\\?\`) or shortening the deepest bundled skill paths; low severity - most repos are far under 260 chars, and the auto-seed is fail-open.

## Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| NI-1 | Phase 7.2 Codex delivery fix | Phase 7.2 (commit 3d18564) | codex.py documents that Codex surfaces via AGENTS.md SKILL_INDEX + prompts; agents/rules intentionally not created (no dead dirs). Prompt read-path live probe remains under DF-1. |
| NI-2 | Phase 7.3 project auto-seed + on-open hook (the reported bug) | Phase 7.3 (commit 61a405f) | Global install from inside a repo seeds .agents/{workflows,skills,rules} + Cursor + Claude stub; opt-in on-open hook shipped; smoke-verified. |
| NI-3 | Phase 7.4 post-install doctor/verify | Phase 7.4 (commit 2ed4646) | `runner.py verify` reports PASS / NEEDS-ACTION per platform; wired into both installers; 4 unit tests. Caught the Antigravity project-surface gap on the dev machine. |
| NI-4 | Phase 7.5 cross-platform CI install-smoke | Phase 7.5 (commit 1959688) | `install-smoke` job (ubuntu + gated macOS/Windows) asserts read-paths + auto-seed; workflow concurrency added. |
| NI-6 | Phase 7 secondary distribution defects (C1/C2/C3/C6/C7) | Phase 7 (commits 3d18564, 2b545d5) | Gemini full-mirror parity (C1/C2); Codex config alignment (C5); Copilot SKILL_INDEX via registry (C6) + spec fix (C7); Antigravity 1.0 deprecation documented (C3). |
