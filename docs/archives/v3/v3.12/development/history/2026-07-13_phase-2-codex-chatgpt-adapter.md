# Session History - v3.12.1 Phase 2: Codex / ChatGPT desktop adapter

**Date**: 2026-07-13
**Plan**: `docs/v3/v3.12/plans/v3.12.1-cross-platform-install-adapters.md`
**Phase**: 2 of 6 - Codex / ChatGPT desktop adapter
**Status**: Complete (stability gate PASS)

## Goal

Make a global or workspace install surface every Nexus-Hub skill and command in the new ChatGPT desktop app (Chat + Work + Codex) and the Codex CLI: skills flattened and discoverable, every command available as `$name` (skill) and as `/prompts:name` (legacy prompt).

## What changed

### 2.1 - Codex integration owns its adapter mirror (`scripts/lib/integrations/codex.py`)

- Rewrote `CodexIntegration` to override `install_global` / `install_workspace` with a `_mirror_codex` helper (the same ownership pattern as `Antigravity20Integration`), instead of inheriting the generic verbatim `SkillsIntegration._mirror_catalog`.
- Global scope now writes: flattened skills into BOTH `~/.codex/skills/<name>/` and `~/.agents/skills/<name>/` (`flatten_skills`); one skill per catalog command into both roots (`commands_to_skills`, so `$presentify` / `$implement` / etc. resolve); legacy top-level prompts into `~/.codex/prompts/<name>.md` (`commands_to_slash` style `codex_prompts`, for `/prompts:name`); and the marker-merged `~/.codex/AGENTS.md` instruction with the `{{SKILL_INDEX}}` block.
- Workspace scope writes the project equivalents: `.codex/skills` + `.agents/skills` (flattened + command-skills), `.codex/prompts`, and a repo-root `AGENTS.md`.
- Added `_catalog_skill_names` so a command whose name collides with a real catalog skill is skipped (no collisions today, but guarded). Dropped the inert `agents_subdir` / `rules_subdir` config keys (Codex has no discovery for them; the generic mirror they fed is no longer used), avoiding dead-dir creation.

### 2.2 - Replaced the raw verbatim-copy Codex blocks in both installers

- `scripts/installer.sh` (global block ~line 921, workspace block ~line 1321) and `scripts/installer.ps1` (global ~line 1284, workspace ~line 1651): removed the `safe_folder_copy` / `Safe-Folder-Copy` of `catalog/skills` -> `.codex/skills` and `catalog/commands` -> `.codex/prompts`, and dropped the `--instruction-only` / `-InstructionOnly` flag. Each is now a single full registry call (`invoke_registry_platform ... codex ... ""` / `Invoke-RegistryPlatform ... -IntegrationKey "codex"`), so the rewritten integration performs the full adapter mirror. This is the exact pattern v3.11 already used for the Gemini IDE block, and it removes the flattening bug at its source.
- Kept the installers byte-equivalent in behavior (lockstep); both parse clean (`bash -n`, PowerShell `Parser::ParseFile`).

### 2.3 - Tests

- Added `tests/integrations/test_codex.py` (5 tests): workspace flatten into both skill roots (no category dirs, >=50 skills, SKILL.md present), commands-as-skills + top-level legacy prompts, repo-root AGENTS.md, global dry-run targets `~/.codex/{skills,prompts,AGENTS.md}` + `~/.agents/skills`, and idempotency.
- Updated `tests/integrations/test_parity_with_legacy_installer.py`: removed the now-obsolete `("codex", "catalog/skills", ".codex/skills")` byte-identical row (codex skills are intentionally flattened now, asserted in `test_codex.py`); kept the `.codex/prompts` verbatim-parity row (prompts stay a flat verbatim copy).

## Verification

- `python -m pytest tests/integrations/test_codex.py tests/integrations/test_catalog_adapters.py -q`: 15 passed.
- Targeted affected suite (parity, install_workspace, base_writeresult, markdown_integration, contract, registry, codex): 169 passed.
- `python -m pytest tests/integrations/ -q` (full regression gate): **300 passed** (296 Phase-1 baseline + 5 new codex tests - 1 removed obsolete parity row).
- `bash -n scripts/installer.sh`: OK. PowerShell `Parser::ParseFile` on `scripts/installer.ps1`: parses clean.
- `python scripts/validate_unicode_safety.py`: 0 errors (new/changed files add no non-ASCII).
- Codex integration import smoke: loads, `skills_subdir=skills`.

## Notes / follow-ups

- Codex has no bare custom-slash surface, so `/presentify` literal is not achievable there; the command surfaces as `$presentify` (skill) and `/prompts:presentify` (legacy). Bare `/name` remains available on Claude, Cursor, and (Phase 3) Antigravity.
- `runner.py verify`'s expected-path table still reflects the OLD codex paths; it is corrected in Phase 5.2. The `install-smoke` CI assertions are updated in Phase 6.2.
- Next: Phase 3 (Antigravity global read-path correction to `~/.gemini/config/...`).
