# Config Sync Manifest -- v2.0.0 Phase 7.2

**Date**: 2026-05-20
**Phase**: 7.2 (run `/update-config` audit for settings references)
**Plan**: [`docs/archives/v2/v2.0/plans/nexus-hub-rename.md`](plans/nexus-hub-rename.md)

## Purpose

Audit every `settings.json`, hook configuration, and config-bearing snippet for stale brand references or stale `~/.devai-hub/` paths.

## Surfaces audited

| Surface | Status |
|---|---|
| `catalog/hooks/settings.json` (the harness-level hook registration template) | Clean. Already updated in Phase 5.1; no `DevAI-Hub`, `devai-hub`, `devai_hub`, `DEVAI_HUB`, or `~/.devai-hub/` strings remain. |
| `configs/permissions/*.json` (the permission-config payloads shipped to user platforms) | Clean. Verified: no brand strings, no legacy install-path strings. |
| `templates/ai-instructions/*.md` (the five per-platform instruction templates, plus generic-instructions and coding-instructions) | Clean. Phase 5.2 swept all five in lockstep. |
| `catalog/mcp-configs/mcp-servers.json` | Clean. Phase 4.2 renamed every internal-server key and module path. |
| Inline `settings.json` snippets embedded in skill bodies, command bodies, and reference files under `catalog/` | Clean. Phase 5.1 catalog sweep + Phase 5.2 templates sweep eliminated every stale path and brand string. |

## User-level surfaces flagged (NOT edited)

`/update-config` deliberately does not modify per-user Claude Code configuration:

| Surface | Why flagged | Recommended user action |
|---|---|---|
| `~/.claude/settings.json` (user level) | May carry references to `~/.devai-hub/scripts/...`, `~/.devai-hub/hooks/...`, or to `DEVAI_*` env vars in `env:` blocks. | Re-running `scripts/installer.sh` / `scripts/installer.ps1` after the v2.0.0 upgrade rewrites the relevant entries; the installer's one-shot migration (Phase 3.3) handles the install root. The CHANGELOG v2.0.0 entry calls this out explicitly. |
| `~/.codex/config.toml` | May reference DevAI paths in legacy entries. | Same as above; re-run the installer. |
| `~/.gemini/settings.json` | Same. | Same as above. |
| VS Code `settings.json` (Copilot config) | Pure flag (`github.copilot.chat.codeGeneration.useInstructionFiles`); does not carry installer-path strings. | No action required. |
| Shell rc files (`~/.bashrc`, `~/.zshrc`, `$PROFILE`) | May carry user-set `DEVAI_*` env vars (`DEVAI_HUB_ROOT`, `DEVAI_HOOK_PROFILE`, `DEVAI_DISABLED_HOOKS`). | The installer's migration step lists detected `DEVAI_*` exports as a hint; the user is responsible for renaming. Documented in `docs/archive/v2/v2.0/RELEASE_NOTES.md`. |

## Verification

```
grep -rn "DevAI-Hub\|devai-hub\|devai_hub\|DEVAI_HUB" catalog/hooks/settings.json catalog/mcp-configs/mcp-servers.json configs/ templates/
```

returns nothing.

## Cross-references

- Sub-task 7.1 already covered the operator-facing prose in `docs/permissions-setup.md` that explains the permissions config layout.
- Sub-task 7.4 covers `.gitignore`.
- Sub-task 7.5 covers `CHANGELOG.md` and `docs/archive/v2/v2.0/RELEASE_NOTES.md`, where the migration story (user-level env-var rename) is documented for the operator.
