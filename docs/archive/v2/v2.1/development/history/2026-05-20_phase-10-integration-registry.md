# Session History: Phase 10 -- Integration Registry + Expanded Platform Support

**Date**: 2026-05-20
**Phase**: 10 of `docs/archive/v2/v2.1/plans/adoption-spec-kit.md`
**Outcome**: G12 (Integration Registry) pulled forward from v2.2.0 to v2.1.0; 4 new platforms supported (Windsurf, Antigravity 2.0, Gemini CLI, Nexus-AI); 11 total platforms in the registry.

## Goal

Implement Phase 10 (G12 Integration Registry refactor) and expand Nexus-Hub's supported-platform list so the installer seamlessly distributes the harness across: Claude Code, Gemini (all variants including CLI), Antigravity 1.0 + 2.0, Codex, GitHub Copilot, GitHub CLI, Cursor, OpenCode, Nexus-AI, and Windsurf.

## Approach

The original plan scoped Phase 10 at v2.2.0 because of the "substantially larger" parity-test burden. The user revised mid-implementation: prioritize the cross-platform expansion in v2.1.0 by treating the registry as ADDITIVE -- legacy installer copy paths for the original 4 platforms (Claude / Gemini / Codex / Copilot) remain canonical and unchanged; the registry only dispatches for the NEW extended platforms.

### Sub-tasks completed

1. **ADR-001** (`docs/archive/v2/v2.1/adr/adr-001-integration-registry.md`) -- 5 sections, 5 alternatives considered and rejected.
2. **Class hierarchy** under `scripts/lib/integrations/`:
   - `base.py`: `IntegrationBase`, `MarkdownIntegration`, `TomlIntegration`, `YamlIntegration`, `SkillsIntegration` with cooperative-super MRO.
   - `manifest.py`: `InstallManifest` for tracking and teardown.
   - `__init__.py`: `INTEGRATION_REGISTRY`, `_register_builtins()` in alphabetical order.
   - `runner.py`: CLI with `list / install / teardown` subcommands.
3. **11 per-platform subclasses**: claude, codex, cursor, gemini, gemini-cli, opencode, windsurf, antigravity (1.0), antigravity2 (2.0), copilot, nexus-ai.
4. **Tests** under `tests/integrations/`: 19 new assertions (5 registry + 11 install + 3 teardown/path-safety).
5. **Installer wiring**: bash gains `install_extended_platforms_workspace/global`; PowerShell gains `Install-ExtendedPlatformsWorkspace/Global`. Both gracefully skip when Python is absent.
6. **Installer copy block**: `scripts/lib/integrations/` is recursively copied to `~/.nexus-hub/scripts/lib/integrations/`.
7. **Documentation updates**: CHANGELOG `[2.1.0]` block, RELEASE_NOTES "Phase 10 addendum" + 11-platform table, AGENTS.md distribution-channels row + platform-coverage-caveats rewrite, known-gaps DF-001 entry.

## Troubleshooting log

**Issue: Multi-mixin install_workspace silently drops second mixin behavior.**
- **Symptom**: Initial smoke install for Windsurf produced only `.windsurf/rules/nexus-hub-rules.md` and `.windsurf/rules/`; the expected `.windsurf/skills/` and `.windsurf/workflows/` did not appear.
- **Root cause**: `MarkdownIntegration.install_workspace` did not call `super().install_workspace(ctx)` at the end; Python's MRO stopped at the first mixin and `SkillsIntegration.install_workspace` was never reached.
- **Fix**: Made both `MarkdownIntegration` and `SkillsIntegration` end their `install_xxx` methods with `super().install_xxx(ctx)`; turned `IntegrationBase.install_global` and `install_workspace` into explicit cooperative-root no-ops (no log spam at the chain terminus).
- **Verification**: re-ran the smoke install; `.windsurf/skills/`, `.windsurf/workflows/`, and `.nexus-ai/{skills,commands,agents,rules,hooks}/` all populated correctly.

**Issue: `runner.py install --dry-run` printed "Manifest written to: ..." even though no file was written.**
- **Symptom**: The "Manifest written" line appeared in dry-run mode, misleadingly suggesting the manifest was persisted.
- **Root cause**: The `print()` was outside the `if not args.dry_run:` block.
- **Fix**: Moved the print inside the conditional and added a `(dry-run: manifest not written)` branch for the else case.

## Assumptions and decisions

1. **Treat the integration registry as additive in v2.1.0**. The original plan's byte-identical parity tests for the legacy installer copy paths were the heaviest sub-task. Deferring those tests to v2.2.0 trades a strict-parity refactor for the cross-platform expansion the user requested. Recorded as DF-001 in known-gaps.

2. **Use cooperative-super for multi-mixin subclasses**. Alternative considered: have each subclass explicitly call both `MarkdownIntegration.install_workspace(self, ctx)` and `SkillsIntegration.install_workspace(self, ctx)`. Rejected because it requires every new subclass author to remember the explicit pattern; cooperative-super lets the base classes own the contract.

3. **Skip Python availability gracefully**. The legacy installers do not require Python on PATH (they shell out to `safe_copy` / `Safe-Copy` for file operations). The extended-platform install path requires Python. Both installers now check `command -v python3 || command -v python` (bash) and `Get-Command python | py | python3` (PowerShell) before invoking the runner; if absent, the installer prints a yellow advisory and continues without aborting.

4. **Antigravity 1.0 keeps `.gemini/antigravity/` as its on-disk root** even though the IDE itself uses an in-app Customizations menu. This matches the legacy installer's behavior (`scripts/installer.ps1` line 1065 writes to `$globalGeminiDir\antigravity\global_workflows`) and gives users a single Markdown-readable surface they can edit by hand.

5. **Antigravity 2.0 uses `.agent/` as its root**, matching the CLI tool's documented convention. The Gemini CLI documentation released at Google I/O 2026 indicates the migration path from Gemini CLI to Antigravity CLI; both share `~/.gemini/` for the global instruction file but the per-tool workflows now diverge.

6. **Nexus-AI integration writes to `.nexus-ai/`** as a workspace root and `~/.nexus-ai/` as the global root. The full catalog mirror (skills + commands + agents + rules + hooks + mcp-configs + templates) is intentional because Nexus-AI is the primary downstream consumer of Nexus-Hub and expects the entire catalog on disk.

## Testing results

- `python -m pytest -q tests` returns 38 passed (19 `tests/installer/` + 19 `tests/integrations/`).
- `python scripts/validate_skills.py --bundles-only` returns 0 errors / 0 warnings across 210 skill bundles.
- `extensions/nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch` test suites all green (37 + 36+1skip + 23 passed -- unchanged from v2.1.0 Phase 9 baseline).
- `bash -n scripts/installer.sh` clean.
- PowerShell parser check on `scripts/installer.ps1` clean.
- End-to-end smoke install of windsurf+antigravity2+gemini-cli+nexus-ai into `/tmp/nexus-hub-test/` succeeded; expected paths populated; manifest persisted; teardown unwound cleanly.

## Next steps

1. Push the v2.1.0 tag once the user confirms.
2. v2.2.0 (future): implement DF-001 -- byte-identical parity tests across Claude / Codex / Cursor / Gemini / OpenCode and migrate the legacy installer copy paths into the registry. See ADR-001 alternatives section for the parity-test plan.
3. v2.2.0 or later: consider adding more platforms (Goose, Jules, Aider, Forge, Qwen, Kiro, Tabnine, Mistral Vibe) via additional registry subclasses -- the ADR-001 "Decision" section calls these out as the natural extension targets once the registry is the canonical install path.
