# Nexus-Hub v2.0.0 -- The Rename

**Release date**: 2026-05-20
**Type**: SemVer **major** (breaking)
**Plan**: [`plans/nexus-hub-rename.md`](plans/nexus-hub-rename.md)
**CHANGELOG block**: [`CHANGELOG.md` -> `## [2.0.0]`](../../CHANGELOG.md)

## Summary

v2.0.0 renames the project from **DevAI-Hub** to **Nexus-Hub** and modernizes the brand to align with the sibling project [Nexus](https://github.com/bendourthe/Nexus-AI), a local-first desktop AI Studio that consumes Nexus-Hub as its upstream skill harness. The rename touches every artifact category that carries the brand: the installed root, the plugin metadata, the three internal MCP servers, the extension package layout, the brand-bearing scripts, the on-disk `using-devai-hub` skill, the cursor rule file, every active documentation surface, and all five per-platform AI-instruction templates.

Beyond the rename itself, v2.0.0 ships a modernized installer (NEXUS-HUB ASCII banner, one-shot in-place migration of `~/.devai-hub/` to `~/.nexus-hub/`) and a rewritten README with explicit cross-linkage to the Nexus desktop app.

This is a **major** version bump because every public-facing identifier changes. There is no compatibility shim or symlink. The rationale and lifecycle for the no-shim decision are recorded in [`rename-decisions.md`](rename-decisions.md).

## How Nexus-Hub fits with Nexus

Nexus-Hub and [Nexus](https://github.com/bendourthe/Nexus-AI) are two halves of the same idea, split along a deliberate seam:

- **Nexus-Hub** (this repo) is the **catalog**: 203 curated skills, 33+ commands, 14 hooks, 10 agents, 4 rule families, plus 3 internal MCP servers (`nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`). It is content-only, platform-agnostic, and shipped via an installer that writes to `~/.nexus-hub/` and into each AI assistant's per-platform config locations.
- **Nexus** is a local-first desktop AI Studio that consumes Nexus-Hub as its skill feed. Nexus's own `AGENTS.md` names this repo as "the only external project we deliberately link to" -- the upstream feed for its skill harness.

The two projects are designed to be useful independently. You can install Nexus-Hub into any supported agent platform without touching Nexus, and Nexus can run with or without the upstream catalog wired in. The combination is what gives a single curated skill set to every agent surface a developer touches: terminal, IDE, desktop app, and CLI.

## Migration story

If you have an existing DevAI-Hub install at `~/.devai-hub/`, the v2.0.0 installer migrates it for you on first run. The migration is **one-way** and **one-shot** -- the installer prompts you once, performs an in-place rename, and prints a confirmation. There is no symlink, no alias, no shim. The rationale: this is a SemVer major bump, and SemVer permits breaking changes; a permanent shim would double the maintenance surface and introduce silent-failure modes; a one-shot installer migration is a single user-visible event that is easy to reason about.

What the installer **does**:

1. Prints the NEXUS-HUB ASCII banner.
2. Detects `~/.devai-hub/`. If found and `~/.nexus-hub/` does NOT exist, prompts: "Detected existing DevAI-Hub install. Migrate to Nexus-Hub? [Y/n]". On Y (default), renames the directory in place.
3. If both `~/.devai-hub/` and `~/.nexus-hub/` exist (e.g. a partial earlier attempt), offers a three-way choice: keep-new-delete-old, abort, or merge (best effort).
4. Detects user-set `DEVAI_*` exports in your shell rc files (best-effort `grep DEVAI_ ~/.bashrc ~/.zshrc ~/.profile $PROFILE`) and prints them as a migration hint.

What the installer **does NOT**:

- Modify your shell rc files. Renaming `DEVAI_*` env vars to `NEXUS_*` is left to you because shell-rc edits should not be ambiguous or surprising.
- Rewrite your own scripts, automation, or third-party tooling that references `~/.devai-hub/` or `devai_*` package names. Update those manually using the path table below.
- Rewrite your per-user `~/.claude/settings.json` / `~/.codex/config.toml` / `~/.gemini/settings.json` blocks that you customized. The installer-owned portions of those files are rewritten on the next installer pass; user-added blocks are left alone.

If you want a safety net before running the installer, copy `~/.devai-hub/` to a backup location:

```bash
# macOS / Linux
cp -R ~/.devai-hub ~/.devai-hub.backup

# Windows PowerShell
Copy-Item -Recurse ~\.devai-hub ~\.devai-hub.backup
```

## Old-path / new-path reference

| Surface | Old | New |
|---|---|---|
| Installed root | `~/.devai-hub/` | `~/.nexus-hub/` |
| Plugin name (`plugin.json`, `marketplace.json`) | `devai-hub` | `nexus-hub` |
| Display name (UI / marketing) | `DevAI Hub` | `Nexus Hub` |
| GitHub repo URL | `https://github.com/bendourthe/DevAI-Hub` | `https://github.com/bendourthe/Nexus-Hub` |
| MCP server key (skill catalog) | `devai-skill-server` | `nexus-skill-server` |
| MCP server key (code search) | `devai-code-search` | `nexus-code-search` |
| MCP server key (web fetch) | `devai-web-fetch` | `nexus-web-fetch` |
| Python module (skill server) | `devai_skill_server` | `nexus_skill_server` |
| Python module (code search) | `devai_code_search` | `nexus_code_search` |
| Python module (web fetch) | `devai_web_fetch` | `nexus_web_fetch` |
| Extension dir (skill server) | `extensions/devai-skill-server/` | `extensions/nexus-skill-server/` |
| Extension dir (code search) | `extensions/devai-code-search/` | `extensions/nexus-code-search/` |
| Extension dir (web fetch) | `extensions/devai-web-fetch/` | `extensions/nexus-web-fetch/` |
| Code-index storage | `<repo>/.devai/code-index/` | `<repo>/.nexus/code-index/` |
| Web-fetch config | `~/.devai/web-fetch.yaml` | `~/.nexus/web-fetch.yaml` |
| Brand-bearing skill dir | `catalog/skills/workflow/using-devai-hub/` | `catalog/skills/workflow/using-nexus-hub/` |
| Cursor rule file | `.cursor/rules/devai-hub.mdc` | `.cursor/rules/nexus-hub.mdc` |
| Benchmark script | `scripts/devai_mcp_benchmark.py` | `scripts/nexus_mcp_benchmark.py` |
| Permissions installer | `scripts/Install-DevAI-Permissions.ps1` | `scripts/Install-Nexus-Hub-Permissions.ps1` |
| Env var (install root) | `DEVAI_HUB_ROOT` | `NEXUS_HUB_ROOT` |
| Env var (hook profile) | `DEVAI_HOOK_PROFILE` | `NEXUS_HOOK_PROFILE` |
| Env var (disabled hooks) | `DEVAI_DISABLED_HOOKS` | `NEXUS_DISABLED_HOOKS` |
| Env var (old-docs guard) | `DEVAI_OLD_DOCS_GUARD` | `NEXUS_OLD_DOCS_GUARD` |
| Installer version variable | `DEVAI_HUB_VERSION` | `NEXUS_HUB_VERSION` |

## What's new beyond the rename

- **NEXUS-HUB ASCII banner** at the top of every installer run, in cyan, with a tagline and a version + GitHub URL line.
- **One-shot legacy-install migration** in both `installer.sh` and `installer.ps1`.
- **Rewritten README** opening with the Nexus logo (`assets/nexus_primary.png`), a one-paragraph pitch, a "Renamed from DevAI-Hub" callout, and a "How Nexus-Hub fits with Nexus" cross-link block that names Nexus as the desktop sibling project.
- **Updated platform compatibility matrix** in the README covering all eight supported surfaces: Claude Code, OpenAI Codex, Gemini (Antigravity), GitHub Copilot, Cursor, GitHub CLI, the Nexus desktop app, and the Nexus VS Code extension.

## Known carry-overs

Two open items from `docs/archive/v1/v1.3/known-gaps.md` carry forward into v2.0.0 and are scheduled for closeout in Phase 8 of the rename plan:

- **WN-001**: 4 pre-existing framework-specialist orphan-bundle warnings (FastAPI / Next.js / React reference files not linked from their parent SKILL.md). Fix planned: link each `references/<file>.md` from its parent SKILL.md.
- **WN-002**: Windows `make` and `shellcheck` unavailable on stock Python store distribution; cp1252 default codec breaks inline `python -c "import json; json.load(open(...))"` in the Makefile. Fix planned: pass `encoding='utf-8'` in the inline JSON-load invocations; document the Windows-developer prerequisites (`scoop install make`, `scoop install shellcheck`, `PYTHONUTF8=1`).

The full v2.0.0 known-gaps file is at [`known-gaps.md`](known-gaps.md).

## Coordinated follow-up (out-of-scope here, but tracked)

- **Update the sibling Nexus repo's README** to point at `bendourthe/Nexus-Hub` (currently links to `bendourthe/DevAI-Hub`). Handled in a follow-up commit on the [`Nexus-AI`](https://github.com/bendourthe/Nexus-AI) repo, not blocked by this release.
- **Rename the GitHub repository** from `DevAI-Hub` to `Nexus-Hub` on GitHub.com. Performed by the repo owner. GitHub's automatic redirect handles the transition window for any URLs still pointing at the old name.
- **Push the `v2.0.0` tag** to the remote. Cut locally during Phase 8 sub-task 8.5; the push is deferred to explicit user action per the CLAUDE.md global rule that destructive / remote-mutating git operations require user confirmation.

## Cross-references

- **Plan**: [`plans/nexus-hub-rename.md`](plans/nexus-hub-rename.md) -- the full 8-phase plan with sub-task prompts.
- **CHANGELOG**: [`../../CHANGELOG.md`](../../CHANGELOG.md) -- the `## [2.0.0]` block with the Keep-a-Changelog-formatted entry.
- **Known gaps**: [`known-gaps.md`](known-gaps.md) -- the open items and resolved carry-overs.
- **Rename decisions**: [`rename-decisions.md`](rename-decisions.md) -- naming canon, backward-compat policy, version-bump rationale.
- **Rename inventory**: [`rename-inventory.md`](rename-inventory.md) -- the per-file enumeration of every variant.
- **Documentation sync manifest**: [`documentation-sync-manifest.md`](documentation-sync-manifest.md) -- what was edited and what was preserved in Phase 7.1.
- **Config sync manifest**: [`config-sync-manifest.md`](config-sync-manifest.md) -- Phase 7.2 audit.
- **Gitignore audit**: [`gitignore-audit.md`](gitignore-audit.md) -- Phase 7.4 audit.
