# Claude plugin marketplace submission (v3.20.3)

**Status**: draft for the maintainer. Do not open an external PR or submit the form from this document.
**Date**: 2026-08-24
**Package**: `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` at the Nexus-Hub repo root
**Local validation**: `claude plugin validate . --strict` passed on 2026-08-24 with Claude Code 2.1.156

---

## What this is

Nexus-Hub already ships a Claude Code plugin/marketplace pair so a Claude Code user can subscribe to the catalog without running the multi-platform installer. This document is the packet the maintainer needs to ask Anthropic to list that plugin in the official directory.

The installer remains the primary path. The plugin is a subscribe-style alternative for Claude Code only.

---

## Skill exposure decision

Ship the **full catalog**, not a curated bundle.

- The installer default is the full catalog. A plugin that shipped a bundle would fork the product and drift from `data/skills.json`.
- Bundles already exist as installer `--profile` / `--modules` / `--bundles`. Duplicating that as a second plugin is a second selector language.
- Claude Code plugin discovery is one level per listed path. `.claude-plugin/plugin.json` therefore lists each `catalog/skills/<category>` directory (23 paths). `tests/validators/test_claude_plugin_manifests.py` fails if that list drifts from disk.
- Hooks stay off the plugin. They belong to the installer (`catalog/hooks/settings.json` into the user's Claude settings). Shipping them here would double-register for anyone who also ran the installer, and would pull host-specific hook scripts into a Claude-only subscribe path.

Commands: `./catalog/commands`. Agents: `./catalog/agents`. No `mcpServers` (MCP registry policy: no new outbound wrapper).

---

## Target and current process

| Item | Value |
|---|---|
| Official directory repo | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| Official listing command (after acceptance) | `/plugin install nexus-hub@claude-plugins-official` |
| Live submission path (fetched 2026-08-24) | [plugin directory submission form](https://clau.de/plugin-directory-submission) |
| Community marketplace (not the goal) | in-app `/plugin` submit forms add to `anthropics/claude-plugins-community`, not the official directory ([docs](https://code.claude.com/docs/en/discover-plugins)) |

The plan named a PR against `anthropics/claude-plugins-official`. As of 2026-08-24 that repo's README points partners at the form, not at a CONTRIBUTING PR checklist. Inclusion in the official directory remains Anthropic's discretion. Do not open a PR unless Anthropic asks for one after the form.

This repo is also its own marketplace (not a reserved name):

```
/plugin marketplace add bendourthe/Nexus-Hub
/plugin install nexus-hub@nexus-hub
```

---

## Proposed listing metadata

Use these values on the form. They match `.claude-plugin/plugin.json`.

| Field | Value |
|---|---|
| Plugin name | `nexus-hub` |
| Display name | Nexus Hub |
| Version pin source | `.claude-plugin/plugin.json` `version` (currently 3.20.2; bump at `/update release`) |
| Description | Enterprise-grade skill harness for AI coding assistants. Full catalog for Claude Code (skills, commands, agents). The installer remains the primary multi-platform path and the only path that installs hooks. |
| Author | Benjamin Dourthe |
| Homepage | https://github.com/bendourthe/Nexus-Hub |
| Repository | https://github.com/bendourthe/Nexus-Hub |
| License | MIT |
| Source | git `bendourthe/Nexus-Hub`, plugin root `./` |
| Category | development |

Do not set a second `version` on the marketplace entry. Claude Code uses `plugin.json` without warning if both are set ([version management](https://code.claude.com/docs/en/plugin-marketplaces)).

---

## Trailing-pin caveat

Official and community marketplace listings pin a plugin to a git SHA. Users of that listing keep the cached copy until Anthropic (or the community catalog) moves the pin. That SHA can lag tagged Nexus-Hub releases, so marketplace users may trail `main`.

Consequences:

- The installer (`nexus-hub upgrade`, or re-running the one-line install) tracks tagged releases. Use it when currency matters.
- This repo's own marketplace can be added from a tag (`bendourthe/Nexus-Hub@vX.Y.Z`) when a user wants a specific release without waiting on the official pin.
- README documents the plugin as a subscribe-style alternative, not a replacement, and states this lag explicitly.

---

## Maintainer send checklist

- [ ] Re-run `claude plugin validate . --strict` on the commit that will be submitted.
- [ ] Confirm `.claude-plugin/plugin.json` `version` matches the latest GitHub Release tag.
- [ ] Submit https://clau.de/plugin-directory-submission with the metadata table above. Do not open `anthropics/claude-plugins-official` unless they ask.
- [ ] After listing, add the official install line to README next to the self-marketplace commands, still below the installer.
- [ ] Record the listing SHA and date in this file (or a follow-up known-gaps resolved note).

---

## Local schema contract (CI)

`tests/validators/test_claude_plugin_manifests.py` asserts marketplace `owner` + `plugins`, plugin `source` `./`, no duplicate version on the marketplace entry, and that `plugin.json` `skills` matches `catalog/skills/` on disk. CI does not run `claude plugin validate` (the Claude CLI is not a CI dependency). Re-run that command before sending the form.
