# Session History - v3.12.1 Phase 1: Foundation (living contract doc + shared adapters)

**Date**: 2026-07-13
**Plan**: `docs/v3/v3.12/plans/v3.12.1-cross-platform-install-adapters.md`
**Phase**: 1 of 6 - Foundation: living contract doc + shared adapters
**Status**: Complete (stability gate PASS)

## Goal

Establish the durable, corrected source of truth for platform read-contracts, and the reusable catalog-to-platform adapter helpers that Phases 2-4 consume. No install behavior changes in this phase; foundation plus tests only.

## Context (why this release exists)

A comprehensive web-search re-verification against the platforms' current (2026) official docs confirmed the paths v3.11.0 Phase 7 had flagged as unverified. Both Codex and the Antigravity IDE discover skills exactly one level deep (`skills/<name>/SKILL.md`), but Nexus-Hub's catalog is two levels (`catalog/skills/<category>/<name>/`) and the installer copies it verbatim, so every skill is buried and none registers. Antigravity's real global read-paths are under `~/.gemini/config/` and `~/.gemini/GEMINI.md`, not `~/.gemini/antigravity/`. And commands reach Codex only through the now-deprecated prompts surface, while the new ChatGPT desktop app surfaces reusable actions as skills (`$name`). v3.11 built the verification scaffolding (a contract doc, `runner.py verify`, an `install-smoke` CI job) but encoded the same wrong paths, so `verify` passed while the apps still read nothing.

## What changed

### 1.1 - Living platform read-contracts doc (`docs/policy/platform-read-contracts.md`)

- Created the durable, sourced contract doc, superseding the version-scoped `docs/v3/v3.11/platform-read-contracts.md` snapshot (which remains as a point-in-time record).
- Corrected the Codex row: skills flattened one level at `~/.codex/skills/<name>/` AND `~/.agents/skills/<name>/` (`$name`), commands additionally emitted as skills, legacy prompts kept at `~/.codex/prompts/*.md` (`/prompts:name`), instruction `~/.codex/AGENTS.md` + repo root.
- Corrected the Antigravity 2.0 IDE row: global skills `~/.gemini/config/skills/<name>/`, global slash commands `~/.gemini/config/global_workflows/<name>.md`, global rules/instruction `~/.gemini/GEMINI.md`; `agy` CLI skills `~/.gemini/antigravity-cli/skills/<name>/`; project `.agents/`.
- Added a Sources section citing the 2026 official-doc URLs per corrected cell, a "How this doc is maintained" note (the three-layer verification story), a "Defects to resolve in this release" section for Phases 2-4, and a "Residual live-verification gaps" list.

### 1.2 - Shared catalog-to-platform adapters (`scripts/lib/integrations/_catalog_adapters.py`)

- `flatten_skills(ctx, key, src, dst)`: copies `catalog/skills/<category>/<name>/` to `<dst>/<name>/`, dropping the category level (generalizes the Antigravity `_mirror_flattened_skills` for reuse in Phase 3 and Codex in Phase 2).
- `commands_to_skills(ctx, key, src, dst, existing_skill_names)`: synthesizes `<dst>/<name>/SKILL.md` from each command's frontmatter `description` (with a "Run the /<name> command." lead-in) plus its body; frontmatter carries only `name` + `description` (the required-and-sufficient set for Codex and Antigravity); skips a command whose name collides with a real catalog skill.
- `commands_to_slash(ctx, key, src, dst, style)`: emits flat slash-command `.md` files (`verbatim` for Claude/Antigravity workflows; `codex_prompts` for the legacy Codex top-level prompts surface).
- All three return `list[FileAction]`, honor `ctx.dry_run` / `ctx.overwrite`, track written paths in the manifest for clean teardown, and follow the derived-artifact sync-on-difference semantics of `_command_surface.mirror_command_surface`. Stdlib-only, no outbound calls.

### 1.3 - Adapter unit tests (`tests/integrations/test_catalog_adapters.py`)

- 10 tests over fixture catalogs: category-drop on flatten, bundled-subdir preservation, missing-source not-found, dry-run-writes-nothing, SKILL.md synthesis (name + slash lead-in + source description + body), name-collision skip, quoted-YAML description, verbatim byte-identity, codex_prompts top-level (no nesting), unknown-style ValueError, and idempotency.

## Verification

- `python -m pytest tests/integrations/test_catalog_adapters.py -q`: 10 passed.
- `python -m pytest tests/integrations/ -q`: 296 passed (full suite; no regression from the new module).
- `python scripts/validate_unicode_safety.py`: 0 errors (the 1050 warnings are pre-existing curly quotes in legacy templates; none in the new files).
- `python scripts/validate_no_personal_paths.py`: clean.
- `python scripts/scan_supply_chain_iocs.py`, `validate_workflow_security.py`: clean.
- `python scripts/validate_skills.py --bundles-only`: PASS (0 errors, 2 pre-existing warnings).
- `python scripts/check_version_sync.py`: clean at 3.11.3 (project version not bumped - that is the release step, Phase 6 handoff to `/update release`).
- `make validate` / `make lint` / `make test` could not be run as `make` targets on this machine (git-bash has no `make`); the constituent validators were run directly instead.

## Notes / follow-ups

- The adapters are intentionally not wired into any integration yet; Phase 2 (Codex) and Phase 3 (Antigravity) do that, and Phase 4 sweeps the remaining platforms.
- Residual live-verification gaps (desktop-app `~/.codex/skills` vs `~/.agents/skills` preference, `agy` CLI global workflow path, Antigravity global hooks path) are recorded in the contract doc and will be reconciled into `docs/v3/v3.12/known-gaps.md` in Phase 6.
