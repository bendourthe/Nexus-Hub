# Nexus-Hub v2.0.0 -- The Rename

**Status**: in progress. This file is a stub written during Phase 6 of the [`nexus-hub-rename`](plans/nexus-hub-rename.md) plan so the new README's link target resolves. The full release notes are written in Phase 7 sub-task 7.5 (`/update-devlog` + CHANGELOG + RELEASE_NOTES). Until then, treat this file as a placeholder.

## Summary (placeholder)

v2.0.0 renames the repository, distributed artifact, plugin metadata, installer, MCP servers, extensions, scripts, skills, commands, hooks, agents, rules, templates, and every documentation surface from DevAI-Hub to **Nexus-Hub**. It also modernizes the installer (ASCII-art NEXUS-HUB banner, one-shot legacy-install migration) and the README (explicit linkage to the sibling [Nexus](https://github.com/bendourthe/Nexus-AI) project).

## Breaking changes (placeholder list)

- Installed root: `~/.devai-hub/` -> `~/.nexus-hub/`
- Plugin name: `devai-hub` -> `nexus-hub`
- MCP server names: `devai-skill-server` -> `nexus-skill-server` (and the other two)
- Environment-variable prefix: `DEVAI_*` -> `NEXUS_*`
- GitHub URL: `bendourthe/DevAI-Hub` -> `bendourthe/Nexus-Hub`

## Migration

The v2.0.0 installer detects `~/.devai-hub/` on first run and offers a one-shot in-place migration. No symlinks, no compatibility shims. Backup your `~/.devai-hub/` before running the installer if you want a safety net.

## Plan, CHANGELOG, and known-gaps

- Plan: [plans/nexus-hub-rename.md](plans/nexus-hub-rename.md)
- CHANGELOG: [`CHANGELOG.md`](../../CHANGELOG.md) (`## [2.0.0]` block lands in Phase 7 sub-task 7.5)
- Known gaps: [known-gaps.md](known-gaps.md)
