# Session History - v3.12.1 Phase 4: Cross-platform sweep

**Date**: 2026-07-13
**Plan**: `docs/v3/v3.12/plans/v3.12.1-cross-platform-install-adapters.md`
**Phase**: 4 of 6 - Cross-platform sweep
**Status**: Complete (stability gate PASS)

## Goal

Audit every remaining skills-folder platform against the one-level-skill + dual-command-surface contract, fix confirmed breakages, and reconcile the contract doc.

## Key finding (scope decision)

Web verification against current (2026) official docs confirmed that Claude Code, Gemini CLI, and OpenCode all discover skills ONE LEVEL DEEP (`skills/<name>/SKILL.md`, the SKILL.md open standard), exactly like Codex and Antigravity. Nexus-Hub shipped NESTED `<category>/<name>/` skills to all of them via the generic verbatim mirror, so native skill folders were broken on Claude/Gemini/OpenCode too (skills still reached the agent via the `{{SKILL_INDEX}}` in each instruction file, and commands worked; what was missing was native `$name`/skill-picker invocation). The approved plan had said "leave Claude/Cursor alone" (based on the user's note that they work, which was true for commands). Given the confirmed defect and the user's "work across all agentic platforms" goal, the user chose to extend the flatten + command-skills fix to ALL skills-folder platforms.

Sources: Claude Code skills <https://code.claude.com/docs/en/skills>; OpenCode skills <https://opencode.ai/docs/skills/>; Gemini CLI skills <https://geminicli.com/docs/cli/skills/>.

## What changed

### 4.1 - Flatten skills + command-skills across the generic-mirror platforms

- `scripts/lib/integrations/base.py`: taught `SkillsIntegration._mirror_catalog` to flatten the skills subdir and add a skill per command when the platform declares `flatten_skills_layout: True`, otherwise keep the verbatim (nested) tree copy. Uses a local import of the shared adapters (`flatten_skills`, `commands_to_skills`, `catalog_skill_names`) to avoid the base <-> _catalog_adapters import cycle. Commands/agents/rules/hooks stay verbatim tree copies.
- Set `flatten_skills_layout: True` on `claude`, `gemini`, `gemini-cli`, `opencode`, `nexus-ai`. Each now flattens `catalog/skills/<category>/<name>/` to `<skills-dir>/<name>/` and emits every command as `<skills-dir>/<name>/SKILL.md`. Codex and Antigravity already do this via their own overrides (Phases 2-3); Cursor has no skills surface and is unaffected.
- Reinforcing property: Claude, Gemini CLI, and OpenCode cross-read each other's skill dirs (`~/.claude/skills`, `~/.agents/skills`), so flattening them is mutually reinforcing on a full install.

### 4.2 - Contract-doc reconciliation + sweep tests

- `docs/policy/platform-read-contracts.md`: updated the skills cells for claude, gemini, gemini-cli, opencode, nexus-ai to "flattened `<dir>/<name>/` (+ command-skills)"; added the cross-read alias notes; added the Phase 4 source URLs; added residual gaps #5 (OpenCode canonical global dir `~/.config/opencode/skills` vs `~/.opencode/skills`, mitigated by the `~/.claude/skills` + `~/.agents/skills` aliases) and #6 (Gemini IDE / Code Assist skill-dir confirmation).
- `tests/integrations/test_cross_platform_flatten.py` (new, 11 tests): parametrized flatten + command-skill assertions for the 5 platforms, plus a Cursor no-regression guard (no skills surface, `.mdc` rules still produced).
- `tests/integrations/test_parity_with_legacy_installer.py`: removed the now-obsolete skills-verbatim byte-identical rows for claude, gemini, opencode (they flatten now; asserted in the dedicated tests); kept the tree-shaped commands/agents/rules rows and the codex prompts row.

## Verification

- Import + dry-run smoke: all 5 carry `flatten_skills_layout: True`; a claude dry-run flattens (no `ai-development/` category dir) and adds `presentify/SKILL.md`.
- `python -m pytest tests/integrations/test_cross_platform_flatten.py test_parity_with_legacy_installer.py test_install_workspace.py test_base_writeresult.py -q`: 80 passed.
- `python -m pytest tests/integrations/ -q` (full regression gate): **309 passed** (301 Phase-3 baseline + 11 new sweep tests - 3 removed obsolete parity rows).
- `python scripts/validate_unicode_safety.py`: 0 errors (the em-dash warnings are pre-existing catalog skill files, not the Phase 4 changes).

## Notes / follow-ups

- Token note (user-accepted): the flattened platforms now expose ~284 native skills (265 catalog + 19 command-skills); each platform advertises name+description on demand, alongside the existing `{{SKILL_INDEX}}` in the instruction file.
- Residual gaps #5 (OpenCode global dir) and #6 (Gemini IDE skill-dir) are recorded in the contract doc and will be reconciled into `docs/v3/v3.12/known-gaps.md` in Phase 6; the `~/.claude/skills` + `~/.agents/skills` cross-read aliases mitigate #5 on a full install.
- Next: Phase 5 (verify_platform_contracts.py + corrected `runner.py verify` paths + the `/update release` web-search re-verification step).
