# Session History - v3.12.1 Phase 3: Antigravity adapter fix

**Date**: 2026-07-13
**Plan**: `docs/v3/v3.12/plans/v3.12.1-cross-platform-install-adapters.md`
**Phase**: 3 of 6 - Antigravity adapter fix
**Status**: Complete (stability gate PASS)

## Goal

Make a global install surface Nexus-Hub skills and slash commands in the Antigravity 2.0 IDE (via the correct `~/.gemini/config/` read-paths) and the `agy` CLI, with every command also available as a skill.

## What changed

### 3.1 - Corrected global read-paths + shared flattener (`scripts/lib/integrations/antigravity.py`)

- Rewrote `Antigravity20Integration.install_global` to write to the surfaces the platform actually reads, per `docs/policy/platform-read-contracts.md`: IDE skills -> `~/.gemini/config/skills/<name>/` (flattened), IDE slash commands -> `~/.gemini/config/global_workflows/<name>.md`, IDE rules -> `~/.gemini/GEMINI.md`; CLI catalog under `~/.gemini/antigravity-cli/`. Replaced the prior `~/.gemini/antigravity/` writes, which the IDE does not read.
- Replaced the identical-roots loop with explicit per-surface handling (IDE root `~/.gemini/config` with `global_workflows`; CLI root `~/.gemini/antigravity-cli` with `workflows`), and a new `_write_instruction_file(dst_path, ctx)` helper so the per-scope instruction filename is explicit (IDE rules = `GEMINI.md`, CLI + workspace = `AGENTS.md`), marker-merged and tracked as a shared file.
- Refactored the bespoke `_mirror_flattened_skills` / `_mirror_antigravity` into `_mirror_surface`, which calls the shared adapters (`flatten_skills`, `commands_to_skills`, `commands_to_slash`). Promoted `catalog_skill_names` into `_catalog_adapters.py` and switched both `codex.py` and `antigravity.py` to the one shared implementation (removing codex's private duplicate).

### 3.2 - Commands-as-skills + corrected installer warnings

- Antigravity now emits every command BOTH as a slash workflow (`global_workflows/` global, `.agents/workflows/` project) AND as a skill (`skills/<name>/SKILL.md`) via `commands_to_skills`, so `/name` and skill-invocation both work.
- `scripts/installer.sh` (~line 956) and `scripts/installer.ps1` (~line 1314): replaced the stale "slash commands appear only inside an OPEN project" warning with an accurate note (global skills -> `~/.gemini/config/skills`, slash -> `~/.gemini/config/global_workflows`, rules -> `~/.gemini/GEMINI.md`; CLI reads `~/.gemini/antigravity-cli`; `.agents/` still seeded by `nexus-hub init`). Antigravity is fully registry-routed, so the integration change alone fixed both installers; the warning text was the only installer edit.

### 3.3 - Tests (`tests/integrations/test_antigravity.py`)

- Replaced `test_antigravity_20_global_targets_both_ide_and_cli_roots` with `test_antigravity_20_global_targets_corrected_ide_and_cli_paths`: asserts `~/.gemini/config/skills`, `~/.gemini/config/global_workflows`, `~/.gemini/GEMINI.md`, and `~/.gemini/antigravity-cli/skills`, plus a regression guard that NO `~/.gemini/antigravity/` global write remains.
- Added `test_antigravity_20_commands_are_also_skills` (workspace `.agents/workflows/presentify.md` + `.agents/skills/presentify/SKILL.md`).
- Workspace tests (lay-files, flatten, hooks, commands-verbatim, idempotency) are unchanged and still green, since `.agents/` behavior was preserved.

## Verification

- `python -m pytest tests/integrations/test_antigravity.py tests/integrations/test_antigravity_commands.py tests/integrations/test_codex.py tests/integrations/test_catalog_adapters.py -q`: 28 passed.
- `python -m pytest tests/integrations/ -q` (full regression gate): **301 passed** (300 Phase-2 baseline + net 1 new antigravity test).
- Import smoke: `antigravity2` loads with `global_dir=~/.gemini/config`, `ide_commands_subdir=global_workflows`; `codex` still loads after the shared-helper refactor.
- `bash -n scripts/installer.sh`: OK. `installer.ps1` `Parser::ParseFile`: parses clean.
- `python scripts/validate_unicode_safety.py`: 0 errors.

## Notes / follow-ups

- `~/.gemini/GEMINI.md` is shared with the `gemini` IDE integration; marker-merge keeps one Nexus-Hub block (last writer wins on a combined install; both carry the SKILL_INDEX). Recorded for the Phase 6 known-gaps.
- Residual (Phase 6 known-gaps): the `agy` CLI global workflow dir and Antigravity global hooks path are best-effort (written under each surface root); confirm on a live `agy`.
- `runner.py verify` still checks the OLD antigravity/codex paths; corrected in Phase 5.2. `install-smoke` CI assertions updated in Phase 6.2.
- Next: Phase 4 (cross-platform sweep of the remaining integrations against the one-level-skill + dual-surface contract).
