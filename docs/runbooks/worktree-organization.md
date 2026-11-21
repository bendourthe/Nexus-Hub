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

`nexus-hub worktree migrate` moves existing worktrees to their canonical destinations. The only mutation input is one reviewed manifest file. Main repositories, removal and branch deletion are never touched here: removal stays with `scripts/cleanup_merged.py`.

### Steps

1. Run the audit and keep its report: `nexus-hub worktree audit --machine --json --output <new-report>`.
2. Propose: `nexus-hub worktree migrate --dry-run --inventory <report> --manifest <new-manifest>`. This writes the manifest, a notice file per item under the Nexus-Hub state directory, and nothing else. It prints the manifest's SHA-256.
3. Review the manifest. Every item names a disposition (`move`, `retain`, `pending`, `exception-pending`, `remove-candidate`), a reason and an owner. Edit nothing: any change alters the digest and apply refuses.
4. Approve each item you accept, as the person who owns the decision: `nexus-hub worktree migrate --approve --manifest <manifest> --expect-sha256 <digest> --item <id> --approver <name>`. This writes a local approval receipt bound to the digest. Planning approval, a green test run and an agent's own judgment are not approval.
5. Hand the notice for each moved worktree to the agent or person working in it. The owner checkpoints their work and acknowledges: `nexus-hub worktree migrate --ack --manifest <manifest> --expect-sha256 <digest> --item <id> --token <token> --checkpoint-note "<what was saved>"`. The absence of a detected process is not consent.
6. Apply: `nexus-hub worktree migrate --apply --manifest <manifest> --expect-sha256 <digest>`. Exit 0 means every item moved and verified or is retained; exit 3 means at least one item is pending or refused, listed with a code and an owner.

### What a move preserves and checks

Immediately before an item moves, the executor revalidates the repository identity, HEAD, branch, working and index state, the untracked and ignored inventory, the destination's ownership, the approval and the acknowledgment. It locks the repository, builds a preservation package (the index, the tracked-change patch, copies of untracked files, and a hashed inventory of ignored files) outside every worktree, and moves with `git worktree move`. Afterward it compares the registry, the repository's back-pointer, HEAD, branch, status, index bytes, patch and every inventory entry against the manifest. Any difference leaves the item pending with a receipt.

It refuses, and never forces: a locked worktree (it is never unlocked), a worktree with submodules, a move across volumes, a path bound to a live signed run, a destination that exists or changed, a changed source, a competing writer, a repository lock held by another operation, and an ancestor that became a symlink or junction.

Cooperative-writer boundary: the final ancestor check runs just before Git starts. A writer that replaces a destination ancestor after that point cannot be stopped from inside this process. Close editors and stop agents on the repository first, which is why the owner acknowledgment is required.

### Interruption and recovery

Each item writes a receipt (`started`, `preserved`, `moving`, `verified`) and re-running the same apply continues. A receipt in `moving` with the source still present is revalidated from the start. A receipt in `moving` with the destination registered and the source gone is verified against the manifest and then marked recovered. Anything else, or any difference from the manifest, stays `pending` as `recovery-ambiguous` or `recovery-unverified`. Nothing is reset, stashed, unlocked, pruned or removed automatically.

### Path-bound state to reopen

The proposal lists files that embed the old absolute path: editor settings (`.vscode`, `.idea`), `.claude/settings.local.json`, virtual environment configuration, task scripts, native controllers and live agent working directories. A virtual environment created inside the folder holds absolute paths; recreate it after the move. Reopen the editor and the shell at the new location, and do not recreate the old path. An optional smoke command per item (`--smoke <path>=<JSON argv list>`) is bound into the manifest and runs at the destination after the move; its result is part of the item result.

### Signed runs

A worktree named by a live signed run record finishes in place. When the run reaches its valid terminal result, propose again and move or retire it. No record or signature is edited. A new owner-specific relocation adapter is out of scope.
