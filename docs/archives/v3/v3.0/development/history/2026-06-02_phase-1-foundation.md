# Session History -- v3.0.0 Phase 1: Foundation (version-sync guard + command scaffolding)

**Date**: 2026-06-02
**Plan**: [`docs/releases/v3/v3.0/plans/command-consolidation-skill-security.md`](../../plans/command-consolidation-skill-security.md)
**Phase**: 1 of 10 -- Foundation: version-sync guard + command scaffolding
**Outcome**: complete; all four sub-tasks (T001-T004) closed, all quality gates green.

## Goal

Close the v2.4.0-class CI version-drift failure systemically (installers were pinned at `2.3.0` while `plugin.json` had moved to `2.4.0`), and scaffold the command-consolidation architecture that Phases 3-5 depend on.

## Subtasks completed

1. **T001 -- Version-sync drift guard.** Created `scripts/check_version_sync.py` (stdlib-only, type-annotated) and `tests/validators/test_check_version_sync.py` (13 cases). The guard reads the canonical version from `.claude-plugin/plugin.json` and asserts six surfaces match it: `data/marketplace.json`, both installers, the latest `CHANGELOG.md` heading, and a new version marker in `README.md` / `AGENTS.md`.
2. **T002 -- Wiring + distribution.** Added the guard to the `make validate` target and the CI `validate` job, and registered it as an explicit-name copy step in both installers (`installer.sh` + `installer.ps1`), targeting `~/.nexus-hub/scripts/`.
3. **T003 -- Scope-mechanism style guide.** Created `catalog/style-guides/command-scope-mechanism.md` documenting the uniform interactive-scope-plus-optional-argument contract (design doc Section 4) and a copy-paste thin-command skeleton template for Phases 3-5.
4. **T004 -- Stabilization.** Ran the test suite and the emulated `make validate`; everything green.

## Key decisions

- **README/AGENTS version coverage via a hidden marker.** Those files carry many historical version references but no single canonical "current version" line, so scanning free prose would false-positive heavily. Chose to add an invisible, ASCII-only `<!-- nexus-hub-version: 2.4.0 -->` HTML comment to each, which the guard asserts and which gives `/update version` (Phase 4) a precise bump anchor. (Confirmed with the maintainer before implementing.)
- **Single cross-platform `.py` validator, no `.ps1` sibling.** Consistent with the five existing top-level `.py`-only validators (the NI-v24-1 convention the plan cites for T001).
- **Surface tolerance semantics.** Absent files are skipped (so the guard runs on partial trees and the pytest fixtures); present-but-version-less structured surfaces are findings; present-but-marker-less README/AGENTS are skipped; mismatched versions are drift findings.

## Test results

- `tests/validators/test_check_version_sync.py`: **13 passed**.
- Targeted regression suite (`tests/validators`, `tests/installer`, `catalog/hooks/tests/test_installer_smoke.py`, `test_platform_parity.py`): **228 passed / 0 failed**.
- In-process line coverage of `check_version_sync.py`: **93%** (uncovered lines are defensive error branches and the `__main__` guard).
- Emulated `make validate` (each validator invoked directly, since `make` is unavailable on the host): all steps green; the guard reported all six surfaces matched at `2.4.0`.

## CI/CD edits

- `.github/workflows/ci.yml`: added a "Validate version sync across all surfaces (v3.0.0 Phase 1)" step to the `validate` job. The new test file auto-discovers under the existing `pytest tests/validators -v` step. No new dependency (stdlib-only), no new secret.

## Deviations

- None. The plan's T001-T004 prompts were followed as written; the README/AGENTS marker is the implementation mechanism the T001 prompt's "README/AGENTS.md catalog-version prose" surface required.

## Troubleshooting / environment notes

- `make` and `shellcheck` are not installed on the Windows dev host. `make validate` was emulated by invoking each validator directly (all green). The ShellCheck pass on the new `installer.sh` copy block is deferred to the CI ubuntu job (WN-v30-1); the block reuses the exact `safe_copy ... true "..."` pattern of its 15 sibling blocks, so it is ShellCheck-clean by construction.
- The pre-existing PowerShell "unapproved verb" lint warnings (`Safe-Copy`, `Safe-Folder-Copy`, etc.) are unrelated to this change, which reuses the existing `Safe-Copy` cmdlet for consistency.

## Known gaps

See [`docs/releases/v3/v3.0/known-gaps.md`](../../known-gaps.md). One open item: WN-v30-1 (local lint verification partial; ShellCheck deferred to CI; low severity, covered by CI).

## Next steps

- **Phase 2 -- skill-native adoptions**: create `agent-orchestration-primitives` and `skill-security-scan` skills, enrich `multi-agent-coordinator`, and register the two new skills in all three data registries.
