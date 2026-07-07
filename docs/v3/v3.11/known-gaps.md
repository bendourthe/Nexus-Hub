# Known Gaps - v3.11

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-07-07

## v3.11.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 6 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

##### NI-1 - Phase 7.2: Codex delivery fix

- **Source phase**: Phase 7 - Cross-platform distribution robustness (sub-task 7.2)
- **Plan reference**: `docs/v3/v3.11/plans/v3.11.0-workflow-governance-refinements.md` (7.2)
- **Reason**: Session paused before the installer-mutating sub-tasks (user chose a fresh focused pass to avoid a half-applied two-language installer edit). 7.1 audit is complete and committed.
- **Suggested next step**: In both installers + `codex.py`, conform the custom-prompts delivery to Codex's current contract (verify D1 first), keep skills surfacing via the `AGENTS.md` SKILL_INDEX, and document/align the never-installed `agents`/`rules` config (C5) rather than adding dead copies. See `docs/v3/v3.11/platform-read-contracts.md`.

##### NI-2 - Phase 7.3: project-surface auto-seed + on-open hook (the reported Antigravity bug)

- **Source phase**: Phase 7 (sub-task 7.3)
- **Plan reference**: 7.3
- **Reason**: Deferred with the rest of the installer mutations.
- **Suggested next step**: When the installer / `nexus-hub upgrade` runs inside a git repo, also seed that repo's project surfaces (Antigravity `.agents/`, Cursor `.cursor/`, Claude stub) via `runner.py init` + a workspace install; install a fail-open, idempotent, opt-out (`NEXUS_HUB_NO_AUTOSEED=1`) on-open hook; make `nexus-hub init` prominent. User chose the "auto-seed + on-open hook" model.

##### NI-3 - Phase 7.4: post-install per-platform verification (doctor uplift)

- **Source phase**: Phase 7 (sub-task 7.4)
- **Plan reference**: 7.4
- **Reason**: Deferred with the installer mutations.
- **Suggested next step**: Extend `runner.py` with a `verify` that asserts the 7.1-contracted read-paths per detected platform and prints PASS / NEEDS-ACTION with the remediation command; wire both installers to run it at the end of every install. This is the guardrail that reports C1-C7.

##### NI-4 - Phase 7.5: cross-platform CI install-smoke

- **Source phase**: Phase 7 (sub-task 7.5)
- **Plan reference**: 7.5
- **Reason**: Deferred with the installer mutations.
- **Suggested next step**: Add an `install-smoke` job to `.github/workflows/ci.yml` (ubuntu/macos/windows) that installs into a throwaway HOME and asserts every platform's read-path is populated + correctly shaped; gate the macOS/Windows legs to merges/schedule.

##### NI-5 - Phase 8: full repo dogfood migration + v3.11.0 bump

- **Source phase**: Phase 8 - Nexus-Hub self-application
- **Plan reference**: Phase 8 (8.1-8.6)
- **Reason**: Terminal phase, not yet reached. The user explicitly required that the entire repo be migrated to the canonical docs-layout scheme at the end of the plan.
- **Suggested next step**: Migrate every `docs/v3.x.y/` (and the currently-untracked `docs/v3.11.0/`, incl. the stray `comparison-t3mp3st.md` / `plans/adoption-t3mp3st.md`) into `docs/v3/v3.x/` with link repair; normalize `docs/archive/`; run the upgraded `project-refactor` cleanup; optimize CI/CD; update registries + base-template parity; bump to v3.11.0 via `check_version_sync.py`; then `/update release`. The `/update refactor` whole-docs-tree migration (generalized to any repo in this session) is the mechanism.

##### NI-6 - Phase 7 secondary distribution defects (fix-all scope)

- **Source phase**: Phase 7 (7.1 audit findings; user chose "fix all")
- **Plan reference**: `docs/v3/v3.11/platform-read-contracts.md` (Defects C1-C7)
- **Reason**: Surfaced by the 7.1 audit beyond the plan's Codex+Antigravity scope; deferred with the installer mutations.
- **Suggested next step**: Fix C1/C2 (Gemini bash/PS parity + agents/rules mirror - switch `gemini` to a full registry mirror by dropping `--instruction-only` and remove the PS hardcoded copies); C3 (Antigravity 1.0 unreachable - retire the dead registration or wire it, a maintainer call); C6/C7 (Copilot - render the instruction body via the registry so it carries the SKILL_INDEX, and fix the stale spec). All in both installers in lockstep.

#### Deferred

##### DF-1 - Residual live-verification gaps (external platform contracts)

- **Source phase**: Phase 7 (7.1 audit, residual gaps D1-D7)
- **Plan reference**: `docs/v3/v3.11/platform-read-contracts.md` (Residual live-verification gaps)
- **Reason**: These contracts depend on the current external platform's behavior and cannot be confirmed from the repo alone.
- **Suggested next step**: Run a live probe per platform: Codex prompt read path + format (D1) and skills discovery (D2); Antigravity 2.0 root-vs-`.agents/` instruction file (D3), exact global subpath (D4), `subagents`/`rules` consumption (D5), `.agents` vs `.agent` (D6); Cursor/Copilot global slash surfaces (D7). Feed results back into 7.2-7.4.

#### Warnings

##### WN-1 - Extension-local compression eval not run in this environment

- **Source phase**: Phases 1-7 (verification)
- **Plan reference**: N/A (environment)
- **Reason**: `make` is unavailable on the Windows dev host, and the final `make validate` step (`cd extensions/nexus-context-compressor && python -m evals --check`) lives in an extension with its own environment; it is untouched by v3.11.0's changes but was not executed here.
- **Suggested next step**: Run the full `make validate` (including the compression accuracy-regression gate) in an environment with the extension deps before the v3.11.0 release (Phase 8 / `/update release`).

## Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| (none yet) | | | Phases 1-6 + 7.1 shipped clean; no in-version gaps opened by them. |
