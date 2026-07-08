# Session History - v3.11.0 Phase 7 (part 2): cross-platform distribution fixes

**Date**: 2026-07-08
**Plan**: `docs/v3/v3.11/plans/v3.11.0-workflow-governance-refinements.md`
**Phase**: 7 of 8 - Cross-platform distribution robustness (7.2-7.6 complete)
**Status**: Complete (stability gate PASS). Part 1 (7.1 audit) is in `2026-07-07_phase-7-part1-read-contract-audit.md`.

## Goal

After any install on Windows/macOS/Linux, every supported platform actually surfaces the catalog - verified against each platform's real read-path, not assumed. Fix the reported Codex/Antigravity bug and the adjacent surfacing defects the 7.1 audit found; add a post-install verification and cross-platform CI smoke so the bug class cannot silently recur.

## What changed (chunked, each validated + committed)

- **7.2 + C5 - Codex (commit 3d18564)**: documented in `codex.py` that Codex's live surfaces are `AGENTS.md` (SKILL_INDEX) + `~/.codex/prompts`; `agents`/`rules` are registry-parity declarations only, so `~/.codex/agents|rules` are intentionally not created (no dead dirs). Prompt read-path live probe tracked under DF-1.
- **C1/C2 - Gemini (commit 3d18564)**: switched both installers to a full registry mirror for `gemini` (dropped the instruction-only flag), so it renders `GEMINI.md` AND mirrors the catalog to `~/.gemini/{skills,workflows,agents,rules}` on every OS. Removed the PowerShell-only hardcoded copies - fixes the bash/PowerShell parity break and the never-delivered agents/rules; retired the dead Antigravity-1.0 `global_workflows` hardcode.
- **7.3 - auto-seed + on-open hook (commit 61a405f)**: `install_project_autoseed` (both installers) seeds the current repo's project surfaces (Antigravity `.agents/{workflows,skills,rules}`, Cursor, Claude stub) on a global install run from inside a git repo; ships an opt-in `nexus-hub-autoseed.{sh,ps1}` on-open hook (fail-open, idempotent, `NEXUS_HUB_NO_AUTOSEED=1` opt-out). Fixes the reported Antigravity bug. Respects the installer's no-auto-rc-edit policy (hook installed + enable line printed).
- **7.4 - post-install verify / doctor (commit 2ed4646)**: `runner.py verify` asserts each detected platform's real read-path and prints PASS / NEEDS-ACTION with a remediation hint (special-cases the Antigravity project-only `.agents/` surface). Wired into both installers; 4 unit tests. On the dev machine it correctly flagged the Antigravity project surface (-> `nexus-hub init`) and the stale pre-fix Gemini workflows.
- **7.5 - CI install-smoke + concurrency (commit 1959688)**: `install-smoke` job (ubuntu on PRs; +macOS/Windows on pushes) runs the registry install into a throwaway HOME, then `verify`, and asserts every platform read-path is populated + the auto-seed produces `.agents/workflows`. Added a workflow-level `concurrency` cancel-in-progress block (the largest CI-minute saver; Phase 8.4 optimization down-payment).
- **C6/C7/C3 (commit 2b545d5)**: Copilot workspace instruction now renders via the registry (`base-codex.md`) so it carries the `{{SKILL_INDEX}}` and is marker-merged (C6); `docs/specs/copilot.md` corrected re the global VS Code prompt-file slash surface (C7); `Antigravity10Integration` documented as deprecated + not installer-wired (C3).

## Verification

- Both installers: `bash -n scripts/installer.sh` OK; `installer.ps1` parses with 0 errors (checked after every chunk).
- Integration registry imports (15 keys); `codex.py` / `gemini.py` / `antigravity.py` / `copilot.py` load.
- `runner.py verify` functional on the dev machine: PASS for Claude/Codex/Cursor/OpenCode/Antigravity-global; NEEDS-ACTION for the Antigravity project `.agents/` (-> `nexus-hub init`) - the reported bug, now surfaced as an actionable line.
- Auto-seed functional smoke (short path): `runner.py init` seeds `.agents/{workflows,skills,rules}` + `.cursor/rules`.
- Install-smoke functional smoke (guarded, short path): registry install + verify assert all five global read-paths PASS, incl. Gemini `workflows:ok` (the C1/C2 fix).
- 4 verify unit tests pass (`tests/installer/test_verify_read_paths.py`); Phase 1 audit-docs tests still 13 pass.
- `validate_skills --bundles-only` / `--quality`, `validate_unicode_safety` (0 errors), `check_version_sync` (clean at 3.10.3), `validate_workflow_security`, ci.yml YAML parse: all clean.

## Notes and environment caveats

- The `/update refactor` whole-docs-tree generalization the user requested was made explicit this cycle (commit 4bde85e); Phase 8 performs the actual repo migration.
- Residual external-contract probes (DF-1) and the Windows MAX_PATH edge case (WN-2) are recorded in `known-gaps.md`; both are low-severity and the auto-seed is fail-open.
- `make` unavailable on the Windows dev host; gates run individually. The extension-local compression eval (WN-1) still needs a run in an env with the extension deps before release.

## Next steps

- Phase 8: full repo dogfood migration to the canonical docs-layout scheme + archive normalization + `project-refactor` cleanup + remaining CI optimization + registries + the v3.11.0 version bump, then `/update release`. Tracked as known-gaps NI-5.
