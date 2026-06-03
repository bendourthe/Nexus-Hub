---
description: Sync a repo to its current state and, at release scope, ship it - documentation, devlog, gitignore, version bump, changelog, refactor, config repair, commit message, and the full release flow. Use to "update the docs", "bump the version", "write the changelog", "sync the devlog", "refactor the project layout", "fix my config", "prepare a release", "commit this", "ship v3.0.0". SKIP - authoring a brand-new doc from scratch (use the relevant generator) or reviewing without changing anything (use /review).
---

# /update Command

Sync a repository to its current state and, at `release` scope, ship it. `/update` consolidates every "bring the repo up to date" action: documentation and README, devlog, gitignore, version bump (atomic across every version-carrying surface), changelog, docs/project refactor, platform-config repair, commit message, and the end-to-end release flow that commits, tags, and pushes. Bare invocation asks for a scope.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive logic lives in the retained skills; this file resolves scope and delegates. `/update release` is the flow `/implement` hands off to on a plan's final phase.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `docs`, `devlog`, `gitignore`, `version`, `changelog`, `refactor`, `config`, `commit`, `release`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. release   (recommended) - the full ship flow: docs + devlog + gitignore + version + changelog + refactor, then commit, tag, push
        2. docs      - sync README, API docs, architecture docs, inline guides
        3. devlog    - append a DEVLOG entry for recent changes
        4. gitignore - audit .gitignore, clean the index, recommend LFS
        5. version   - bump the version atomically across every surface (drift-guarded)
        6. changelog - regenerate / extend CHANGELOG.md from git history
        7. refactor  - reorganize docs/ and project artifacts to conventions
        8. config    - validate and repair installed platform configs (drift repair)
        9. commit    - generate a structured commit message for the staged changes

      Reply with a number or a scope name.

- `release` runs the focused scopes in order - `docs`, then `devlog`, then `gitignore`, then `version`, then `changelog`, then `refactor` - then cleans up, commits, tags, and pushes as one flow. It keeps every confirmation gate: never create a tag or push without explicit user confirmation.

## Delegation

Dispatch the resolved scope to the retained skill(s):

      docs      -> update-documentation (+ generate-readme for the README)
      devlog    -> update-devlog (+ generate-devlog to bootstrap when no DEVLOG exists)
      gitignore -> update-gitignore
      version   -> update-version, gated by scripts/check_version_sync.py (see below)
      changelog -> generate-changelog
      refactor  -> refactor-docs + refactor-project
      config    -> update-config (built-in) + config-consistency-checker / nexus-hub doctor (see below)
      commit    -> generate-commit-message
      release   -> docs -> devlog -> gitignore -> version -> changelog -> refactor, then clean up, commit, tag, push

Pass any remaining arguments through unchanged. Heavy logic stays in the retained skills; this file owns only scope resolution and the release sequencing.

## version scope (atomic, drift-guarded)

The `version` scope MUST use `scripts/check_version_sync.py` so every version-carrying surface is bumped as one atomic set: `.claude-plugin/plugin.json` (canonical), `scripts/installer.sh` (`NEXUS_HUB_VERSION`), `scripts/installer.ps1` (`$script:NexusHubVersion`), `data/marketplace.json`, the latest `CHANGELOG.md` heading, and the README / AGENTS.md catalog-version prose. Run the guard before and after the bump: it must report a clean in-sync tree afterward. This closes the v2.4.0 drift class (installers stuck at one version while `plugin.json` moved to the next) systemically - a mismatch fails the build rather than shipping.

## config scope (platform-config drift repair)

The `config` scope validates installed platform configs and repairs drift, reusing the `config-consistency-checker` skill / `nexus-hub doctor`. In particular, a Codex `~/.codex/config.toml` that defines `[permissions.*]` profiles MUST set `default_permissions`, or the config fails to load. Repairing an already-broken user config (a `[permissions.*]` table present but `default_permissions` missing) requires TOML-aware insertion of `default_permissions` before the first `[permissions...]` table, and the idempotency guard must NOT skip such a config - it is broken, not already-fixed. When Codex's elevated-sandbox setup fails on Windows, optionally surface the `[windows] sandbox = "unelevated"` recommendation.

## Notes

- This command replaces deprecated `/update-documentation`, `/update-devlog`, `/generate-devlog`, `/generate-readme`, `/update-gitignore`, `/update-version`, `/generate-changelog`, `/generate-commit-message`, `/refactor-docs`, and `/refactor-project`. The old names forward here via deprecation shims through v3.x (removed at v4.0.0).
- `/commit` is retained as a permanent convenience alias forwarding to `/update commit` (high-frequency mid-dev use).
- Keep this dispatcher thin. The update procedures live in the retained skills; this file owns only scope resolution, the release sequence, and the version-sync / config-repair contracts above.
