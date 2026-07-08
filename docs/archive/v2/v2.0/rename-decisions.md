# Rename Decisions -- Naming Canon and Backward-Compatibility Policy

**Phase**: v2.0.0 Phase 1 sub-task 1.3
**Captured**: 2026-05-19
**Source plan**: `docs/archive/v2/v2.0/plans/nexus-hub-rename.md`
**Purpose**: Lock in the canonical name forms, the GitHub repo URL, the installed-root path, the MCP server name scheme, the backward-compatibility policy, and the SemVer rationale before any rename work touches the catalog or installer. Downstream phases reference this file as the source of truth for these decisions; if any decision is reopened, this file MUST be updated first.

---

## 1. Canonical name forms

All seven forms are locked. Every artifact must use the form appropriate to its context. The variant table in `docs/archive/v2/v2.0/rename-inventory.md` Section 3 enumerates the mechanical replacements implementing this canon.

| Form | Use when |
|---|---|
| `Nexus-Hub` | Display name in prose, Markdown headings, READMEs, commit subject lines, sentence-cased UI strings. **The default form.** |
| `Nexus Hub` | UI / marketing two-word form (rare; reserved for places where the hyphen is awkward, e.g. inside a `<title>` tag). |
| `nexus-hub` | Kebab-case identifier: plugin name, npm-style package id, GitHub repo segment, URL slug. |
| `nexus_hub` | Snake-case identifier: Python module-level identifiers, env-var middle segments. |
| `NEXUS_HUB` | Upper-snake: environment-variable prefix (e.g. `NEXUS_HUB_VERSION`, `NEXUS_HUB_HOOKS_DEBUG`). |
| `NEXUS-HUB` | ASCII-banner wordmark only (the installer banner text). |
| `nexus-` | MCP server name prefix (e.g. `nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`). Matching Python packages use `nexus_<purpose>`. |

The legacy forms `DevAI-Hub`, `DevAI Hub`, `devai-hub`, `devai_hub`, `DEVAI_HUB`, `DEVAI-HUB` are retired effective v2.0.0. They appear in `CHANGELOG.md`, the README "renamed from" callout, and `docs/archive/`/frozen historical version directories ONLY.

---

## 2. GitHub repository URL

| Position | Value |
|---|---|
| Canonical URL | `https://github.com/bendourthe/Nexus-Hub` |
| Legacy URL | `https://github.com/bendourthe/DevAI-Hub` (handled by GitHub's automatic rename redirect) |
| Owner | `bendourthe` (unchanged) |

GitHub's automatic redirect handles inbound traffic to the old URL on a best-effort basis. Every in-repo string reference (homepage, repository, clone hints in installers, README links, badges, `pyproject.toml` URLs) MUST be updated to the canonical URL during the rename. The actual GitHub-side rename (renaming the repo on github.com) is out of scope for this plan -- the maintainer performs that action manually after this branch lands.

---

## 3. Installed root

| Path | Use |
|---|---|
| `~/.nexus-hub/` | Canonical installed root for v2.0.0+. |
| `~/.devai-hub/` | Legacy root; detected by the installer and migrated in place once (see Section 5). |

Layout inside `~/.nexus-hub/` mirrors the existing `~/.devai-hub/` layout exactly. No schema change inside the directory tree. The same subdirectories (`skills/`, `commands/`, `hooks/`, `agents/`, `rules/`, `scripts/`, `templates/`, `mcp-configs/`, `style-guides/`, ...) are populated; only the parent dot-folder name changes.

Per-platform install targets (e.g. `~/.claude/skills/`, `~/.codex/prompts/`, `~/.gemini/workflows/`) are unchanged -- they belong to the host AI assistant, not to Nexus-Hub. The installer continues to write into those locations following the same per-platform layout established in v1.x.

---

## 4. MCP server name scheme

The three internal MCP servers are renamed:

| Old key (in `catalog/mcp-configs/mcp-servers.json`) | New key | Python package |
|---|---|---|
| `devai-skill-server` | `nexus-skill-server` | `nexus_skill_server` |
| `devai-code-search` | `nexus-code-search` | `nexus_code_search` |
| `devai-web-fetch` | `nexus-web-fetch` | `nexus_web_fetch` |

The MCP `command` and `args` fields in each registry entry update accordingly (e.g. `python -m nexus_skill_server`). The `docs/policy/mcp-reverse-engineering-matrix.md` rows that classify the three internal servers as Decision-Tree bucket 1 ("Local-only") update their `Key` and `Path` columns to the new names.

External MCP entries in the registry are unaffected by this rename.

---

## 5. Backward-compatibility policy

**Decision**: in-place installer migration. **No symlinks. No shims. No alias subcommands.**

### 5.1 Rationale

1. SemVer permits breaking changes at a major bump. `v1.4.0` -> `v2.0.0` is the right vehicle for a rename.
2. A compatibility shim doubles the maintenance surface: every new skill, command, hook, env var, or path would need to be wired through both names indefinitely. The cost compounds with every release.
3. An installer migration is a single user-visible event. After the upgrade run, the user's machine has exactly one root (`~/.nexus-hub/`), and no further compatibility logic needs to live in the codebase.
4. The installed root is not part of any SemVer-stable API today. No third-party tool, hook, or skill in the catalog reads `~/.devai-hub/` by path string -- the access pattern is always "relative to the installed root", which the installer parameterizes. The rename is therefore safe to migrate with a `mv`.

### 5.2 Migration logic (both installers)

Implemented at the top of `installer.sh` and `installer.ps1` in Phase 3 sub-task 3.3. Pseudocode:

```text
migrate_legacy_install():
    legacy  = $HOME/.devai-hub
    current = $HOME/.nexus-hub

    if exists(legacy) and not exists(current):
        prompt: "Detected existing DevAI-Hub install. Migrate to Nexus-Hub? [Y/n]"
        if user_says_yes (default Y):
            mv legacy current
            print "Migrated <legacy> -> <current>"
        else:
            print "Migration declined. Remove <legacy> manually or rerun with --force."
            exit 1

    elif exists(legacy) and exists(current):
        prompt: "Both <legacy> and <current> exist. Choose:
                 [k]eep new + delete old, [a]bort + handle manually, [m]erge (best effort)"
        case k: rm -rf legacy
        case m: cp -R legacy/* current/ ; rm -rf legacy
        case *: exit 1

    else:
        # fresh install or already migrated -- no action
        pass
```

The PowerShell variant uses `Move-Item`, `Remove-Item -Recurse -Force`, `Copy-Item -Recurse`, and `Read-Host` (no `-Confirm:$true` interactives that would block CI).

### 5.3 Environment variables

User-set environment variables that follow the legacy pattern (e.g. `DEVAI_HUB_VERSION`, `DEVAI_OLD_DOCS_GUARD`, `DEVAI_HOOKS_DEBUG`) are NOT modified by the installer. The installer prints a one-time migration hint that lists the variables it found in the user's shell rc files via:

```text
grep DEVAI_ ~/.bashrc ~/.zshrc ~/.profile $PROFILE 2>/dev/null
```

The hint suggests the user replace each `DEVAI_*` with the corresponding `NEXUS_*` form. The installer does NOT edit shell rc files (too invasive; risk of corrupting custom user configuration). This is left explicitly to the user.

### 5.4 Plugin / marketplace migration

The plugin's `name` field changes from `devai-hub` to `nexus-hub` in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. A user who pinned the plugin by name in any GitHub Action, marketplace integration, or custom workflow MUST update that pin. This is called out in the CHANGELOG `### Breaking changes` subsection at Phase 7 sub-task 7.5.

### 5.5 What we explicitly do NOT do

- Ship a `~/.devai-hub` -> `~/.nexus-hub` symlink on the user's machine. Rejected: keeps the legacy name alive indefinitely; complicates future cleanup; differs cross-platform (symlinks on Windows require admin or developer mode).
- Ship a `nexus-hub` PowerShell / bash alias for the old `devai-hub` command. Rejected: there is no `devai-hub` command today, so there is no alias to ship.
- Maintain a `compatibility-shim` branch that publishes the v1.x catalog under both names. Rejected: doubles release work for no concrete user benefit.
- Defer the rename. Rejected: the rename's rationale is the alignment with the sibling Nexus product launched at v1.0.0; further delay misaligns the two repos longer.

---

## 6. Version semantics

This rename is a SemVer **MAJOR** bump:

| From | To |
|---|---|
| `v1.4.0` | `v2.0.0` |

Justification: every one of the following is a breaking change:

- Installed-root path (`~/.devai-hub/` -> `~/.nexus-hub/`).
- Plugin canonical id (`devai-hub` -> `nexus-hub`) -- breaks any GitHub Action or marketplace pin.
- MCP server registry keys (3 keys renamed).
- Environment-variable prefix (`DEVAI_HUB_*` / `DEVAI_*` -> `NEXUS_HUB_*` / `NEXUS_*`).
- Python package names for all three extensions.
- GitHub repository URL (handled by GitHub's automatic redirect, but in-repo references all change).
- Cursor rule filename (`.cursor/rules/devai-hub.mdc` -> `nexus-hub.mdc`).
- `devai-code-search` index dir (`.devai/` -> `.nexus/`) and its ignore file.

The CHANGELOG `## [2.0.0]` block at Phase 7 sub-task 7.5 lists each breaking change explicitly under `### Breaking changes` and provides one-sentence remediation steps for each.

Future point releases (`v2.0.1`, `v2.1.0`, ...) do NOT carry any of the legacy `DevAI` strings. Any post-`v2.0.0` reintroduction would require its own rationale.

---

## 7. References

- Implementation map: `docs/archive/v2/v2.0/plans/nexus-hub-rename.md` (Phases 2-8).
- Mechanical variant table: `docs/archive/v2/v2.0/rename-inventory.md` Section 3.
- Pre-rename baselines: `docs/archive/v2/v2.0/baselines/{validate-skills,hook-tests,extension-tests}-pre.txt`.
- Carry-over known-gaps from v1.3.0 (resolved at v2.0.0 Phase 8 sub-task 8.3): WN-001 (orphan-bundle warnings), WN-002 (Windows make/shellcheck + UTF-8).
