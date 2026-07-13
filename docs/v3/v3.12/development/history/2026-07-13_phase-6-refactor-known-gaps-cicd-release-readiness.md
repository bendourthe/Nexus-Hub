# Session History - v3.12.1 Phase 6: Refactor, known-gaps, CI/CD, release readiness

**Date**: 2026-07-13
**Plan**: `docs/v3/v3.12/plans/v3.12.1-cross-platform-install-adapters.md`
**Phase**: 6 of 6 (terminal) - Architecture refactor, known-gaps reconciliation, CI/CD, and release readiness
**Status**: Complete (stability gate PASS); release handoff pending user confirmation

## Goal

Clean up and finalize the release: confirm no stray artifacts, reconcile known gaps, update the CI install-smoke assertions to the corrected paths, run full validation plus a real end-to-end install proof, and prepare the release surfaces (deferring the version bump/tag/push to `/update release` under user confirmation).

## What changed

### 6.1 - Architecture refactor + known-gaps reconciliation

- Refactor check: every new artifact is referenced and correctly placed (`_catalog_adapters.py` used by base/codex/antigravity; `verify_platform_contracts.py` in `make validate`; the `platform-contract-verification` skill referenced from `update.md` + registered; `docs/policy/platform-read-contracts.md` linked from the AGENTS.md distribution table; the `docs/v3/v3.12/` tree populated). No empty/orphan/duplicate artifacts introduced.
- `docs/v3/v3.12/known-gaps.md` (new): recorded 6 DF items (all Low) mapping 1:1 to the contract doc's residual live-verification gaps (Codex skills alias, agy CLI workflow dir, Antigravity global hooks, OpenCode canonical global dir, Gemini IDE skill-dir, Antigravity project instruction), plus 1 WN (the catalog-wide pushy-description vs 250-char full-validator tension). Notes record the intended native-skill injection and the load-bearing `~/.agents/skills` shared location.

### 6.2 - CI/CD

- `.github/workflows/ci.yml` install-smoke: updated the bash and PowerShell read-path assertions to the corrected labels/paths ("Codex / ChatGPT -- skills:ok", "Antigravity 2.0 IDE (global) -- skills:ok"). Existing cost gating (ubuntu on PRs, +macOS/Windows on pushes) and concurrency controls unchanged.

### 6.3 - Docs + release readiness

- `CHANGELOG.md`: added the `## [Unreleased]` entry (Fixed / Added / Changed) summarizing the cross-platform adapter fixes and the three-layer verification gate; catalog now **266 skills**.
- `AGENTS.md`: updated the skill count to 266, rewrote the distribution-table skills row (flattened one-level + command-skills across all SKILL.md platforms) and commands row (Antigravity global slash surface), corrected the stale "Antigravity slash commands are project-only" caveat, and pointed to `docs/policy/platform-read-contracts.md` as the living contract.

## Verification

- **End-to-end install proof** (isolated temp HOME with `USERPROFILE` redirected): a global install of codex/antigravity2/claude produced all corrected read-paths -- `~/.codex/skills/presentify/SKILL.md`, `~/.agents/skills/presentify/SKILL.md`, `~/.codex/prompts/presentify.md`, `~/.gemini/config/skills/presentify/SKILL.md`, `~/.gemini/config/global_workflows/presentify.md`, `~/.gemini/GEMINI.md`, `~/.gemini/antigravity-cli/skills/presentify/SKILL.md`, `~/.claude/skills/presentify/SKILL.md` -- with NO category-dir leak. `nexus-hub verify` reports PASS for Claude, Codex / ChatGPT, Gemini IDE, Antigravity IDE (global), Antigravity CLI, Cursor, and OpenCode.
- `python scripts/verify_platform_contracts.py`: OK (7 platforms).
- `make validate` constituents: JSON integrity OK; unicode-safety 0 errors (new v3.12 docs + the CHANGELOG Unreleased entry are ASCII-clean; the flagged warnings are pre-existing em-dashes in old CHANGELOG entries); version-sync clean at 3.11.3 (bump is the release step's job); `verify_platform_contracts.py` OK.
- Tests: verify-read-paths + contract-checker + adapters 18 passed; the full `tests/integrations/` suite remains 309 passed (unchanged - Phase 6 touched only CI YAML + docs, no integration code).

## Environment note (non-blocking)

The first end-to-end install attempt used only `HOME=<temp>`, but on the Windows/Git-Bash dev host Python's `Path.home()` resolves `USERPROFILE`, so that run installed the correct v3.12 catalog into the developer's REAL home directory (idempotent, re-runnable, and revertible by re-installing from `main`). The isolation was fixed by also setting `USERPROFILE`, and the reported proof above is from the isolated run. Flagged to the user.

## Release readiness (handoff, NOT executed)

All six phases are complete and green. The plan's terminal phase hands off to `/update release` for the version bump (3.11.3 -> 3.12.0), changelog finalization, the docs count reconciliation across README/CHANGELOG, the Phase 5.3 platform-contract re-verification governance step, commit, tag, push, and GitHub Release. Per the repo's confirmation gates and the user's instruction, the version bump / tag / push are NOT performed automatically; they await explicit user confirmation. The branch `feat/cross-platform-install-adapters` (6 commits) is also not yet pushed.
