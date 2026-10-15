---
name: setup
description: "Run the /setup command. Bootstrap and configure a project or repo - scaffold CLAUDE.md, directory structure, .gitignore, README/DEVLOG/CHANGELOG, or install the opt-in pre-commit AI review hook. Use to \"set up this project\", \"bootstrap the repo\", \"initialize CLAUDE.md\", \"scaffold a new project\", \"install the pre-commit hook\", \"add a commit review hook\". SKIP - updating docs on an already-set-up project (use /update docs) or describing an existing project (use /describe)."
disable-model-invocation: true
---

# /setup Command

Bootstrap and configure a project. `/setup` scaffolds a new or inherited project (CLAUDE.md configuration, directory structure, .gitignore, README / DEVLOG / CHANGELOG) and can install the opt-in git pre-commit hook that pipes every staged diff through an AI CLI to catch secrets, debug artifacts, and unfinished TODOs.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive setup logic lives in the retained skills; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `project`, `hooks`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. project  (recommended) - bootstrap CLAUDE.md, scaffolding, .gitignore, README / DEVLOG / CHANGELOG
        2. hooks    - install the opt-in pre-commit AI review hook (secrets, debug artifacts, unfinished TODOs)

      Reply with a number or a scope name.

## Delegation

Dispatch the resolved scope to the retained skill:

      project  -> setup-project (detection-first governance bootstrap: git init + initial commit, a vX.Y.Z version, a develop+main branch model, the per-version docs tree, living `docs/handbooks/` and `docs/decisions/`, and real README / CHANGELOG / DEVLOG - creating ONLY what is missing, so it is safe on an inherited repo)
      hooks    -> the hooks install steps below (auto-detects the available AI CLI: claude / gemini / antigravity-cli / codex / opencode)

Pass any remaining arguments through unchanged. Heavy logic stays in the retained skills; this file only resolves scope and delegates.

## hooks scope

The installer ships the hook sources to `~/.nexus-hub/hooks/<cli>-diff-review.sh` (one per CLI) and never wires them into a repository. To install one, from inside the target repository:

1. Detect which supported CLIs are on `PATH` (`claude`, `gemini`, `agy` for Antigravity CLI, `codex`, `opencode`). If several are present, ask the user to pick one; if none is, stop and say so.
2. If `.git/hooks/pre-commit` already exists, show it and ask before replacing it.
3. Copy the chosen `~/.nexus-hub/hooks/<cli>-diff-review.sh` to `.git/hooks/pre-commit` and make it executable (`chmod +x`; Git for Windows runs it through its bundled bash).
4. Tell the user the bypasses the hook header documents: `NEXUS_DIFF_REVIEW_DISABLE=1` for one commit, `NEXUS_DIFF_REVIEW_MAX_BYTES` to raise the diff-size cap, and `rm .git/hooks/pre-commit` to uninstall.

Project setup preserves the existing handbook map and topic or legacy layout. A missing tree delegates to `technical-documentation` through `references/handbook-refresh.md` for code-grounded content; empty folders do not establish completion.

## Notes

- This command replaces `/setup-project` and `/install-pre-commit-review-hook` (removed in v3.2.0).
- Keep this dispatcher thin. The setup procedures live in the retained skills; this file owns only scope resolution and delegation.
