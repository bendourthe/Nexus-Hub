# Worktree Organization

Summary: how Nexus-Hub places, creates, lists, audits and migrates linked Git worktrees under one configured root. Read it before creating a worktree by hand, when `nexus-hub worktree` refuses a request, when a guard blocks a `git worktree` command, or before moving existing worktrees. Key topics: layout and root policy, commands and exit codes, what the guard covers and does not cover, and the migration contract.

## Layout

New linked worktrees live at `<root>/<repository-identity>/<worktree-name>`. Main repositories stay where they are.

- **Root:** the `NEXUS_WORKTREE_ROOT` variable, then `config/worktrees.json` (`{"root": "<absolute path>"}`) under the Nexus-Hub home, then `~/.worktrees`.
- **Identity:** the folder name of the main checkout plus eight hex characters hashed from Git's canonical common directory, so two clones with one name or one remote never share a folder.
- **Name:** a short readable form of the requested name. A name that changes while it is sanitized (a slash, a space, capitals, a reserved Windows name, Unicode) gets a six-character hash suffix, so `feat/x` and `feat-x` stay apart.

The root is refused when it is relative, a network or UNC path, inside a repository, inside a tool directory (`.claude`, `.cursor`, `.vscode`, `.idea`, `.codex`, `.gemini`, `.windsurf`, `.agents`) or the Nexus-Hub home, in a synchronized folder, a symlink or junction, or on a volume that is not mounted. A repository file never sets it, and an invalid override is an error, never a silent fallback. A root on another local volume is supported.

Shared root and children are not independent clones: a linked worktree still depends on its main repository's Git storage.

## Commands

Run these in any terminal where `nexus-hub` is on the path. Every action prints JSON with `--json`.

- `nexus-hub worktree path --repo <checkout> --name <name> --json` resolves the destination and writes nothing.
- `nexus-hub worktree create --repo <checkout> --branch <branch> --base <commit> --name <name>` creates a new branch and its worktree. It is serialized per repository and rechecks the destination under the lock. Running it again for the same branch and name reports `exists`.
- `nexus-hub worktree list --repo <checkout> --json` shows registered worktrees, their canonical destinations and whether each is in policy.
- `nexus-hub worktree audit --machine --json --output <new-report>` scans every fixed local volume, read-only, and writes a coverage report. `--root <dir>` limits it, `--deep` removes the dependency-folder exclusion hints, `--max-seconds` and `--resume` split a long scan.

Exit codes: 0 complete, 2 refused before any change, 3 partial or could not verify. A refusal prints `{"status": "refused", "code": ...}`. A partial audit is never exit 0, and it leaves a checkpoint that `--resume` continues.

## Enforcement Coverage

The `worktree-policy` guard is a PreToolUse hook for the Bash and PowerShell tools. It reads only the proposed command, never runs it, and refuses a recognized `git worktree add` or `git worktree move` whose destination is not `<root>/<identity>/<name>`. It also refuses a worktree mutation it cannot certify: a destination built from a variable, substitution or wildcard, or a mutation inside `bash -c`, `eval`, `iex` and similar wrappers.

- **Always on:** it does not honor `NEXUS_HOOK_PROFILE=minimal` or `NEXUS_DISABLED_HOOKS`, and it applies in every host permission mode. The only override is changing the root.
- **Covered:** Claude Code (through `settings.json`), Cursor (through the imported Claude settings), and Antigravity (through the `run_command` hook group).
- **Not covered:** a plain terminal, an IDE git panel, Codex and Copilot agent worktrees, Cursor's own agent worktrees, git aliases, scripts that call Git, and any host that does not run Nexus-Hub hooks. Use `nexus-hub worktree create` there. `audit` reports a worktree placed elsewhere.
- **Native tools:** `EnterWorktree` with `name` creates inside `.claude/worktrees/`, which this policy forbids. Create with `nexus-hub worktree create`, then enter by `path`.

This is organizational enforcement inside supported Nexus-Hub surfaces, not an operating-system boundary.

## Migration

`nexus-hub worktree migrate` is delivered in the next phase of this release; until then no worktree is moved by this tooling.
