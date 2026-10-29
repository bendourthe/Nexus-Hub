# Decision: Console Window Guard Scope

Status: implemented - the console-window guard scans the project a command actually runs in, ignores read-only commands that merely name a script, and skips `.tmp/` scratch.

Hook maintainers and anyone diagnosing a console-window-guard block read this before widening or narrowing what the guard checks. It records the observed false blocks, the three scope corrections, and the stricter change deliberately left open.

**Date**: 2026-10-28. **Release**: maintenance, follows v4.14.2. Amends [`2026-10-19-windows-console-window-guard.md`](2026-10-19-windows-console-window-guard.md).

## Problem

Session transcripts recorded 24 guard blocks across three projects (Nexus-Hub, and two other repositories). In every one, the flagged code was not code the blocked command would run:

- A release session in a separate worktree was blocked, including for a read-only `git show -- scripts/installer.sh`, because the session's starting checkout held untracked scratch scripts under `.tmp/` and an older copy of one test.
- A session reading header files in another worktree (`cd <other worktree> && for f in ...`), and running a Nexus-Hub helper, was blocked by the starting project's own CI scripts.
- A one-off scratch script was blocked by server code that only runs inside Linux containers.

Three causes: the scan root was always the session's starting folder, not the folder the command enters; the October 22 widening to build, installer and helper commands matched a script name anywhere in the command, including as an argument to a read-only program; and untracked agent scratch under `.tmp/` was scanned like product code.

## Decision

- **Scan where the command runs.** A command that starts by entering a directory (`cd X &&`, `cd X;`, `pushd X`, `Set-Location X;`, `Push-Location X;`, `sl X;`, including Git Bash `/c/...` paths) is scanned from that directory's project root. A target that does not exist falls back to the session folder, so nothing becomes less guarded by a typo.
- **Read-only segments are not launches.** The command is split at `&&`, `||`, `;`, `|` and newlines; a segment whose program is a read-only or printing command (`git`, `gh`, `cat`, `head`, `tail`, `grep`, `rg`, `ls`, `wc`, `diff`, `cmp`, `echo`, `printf`, `sha256sum`, `stat`, `file`, `cut`, `sort`, `uniq`, `tr`, `Get-Content`, `Select-String`, `Get-ChildItem`, `Test-Path`, `Get-Item`, `Write-Output`, `Write-Host`, `Out-String`, `Measure-Object`, `Select-Object`) does not trigger the scan. Every other segment is checked exactly as before, so `git status && python helper.py` is still guarded.
- **`.tmp/` is skipped** like `node_modules/` and `build/`.

What counts as a window-unsafe launch, the exception marker, the scan budget and the disable switches are unchanged.

## Alternatives considered

Rejected alternative: turn the guard off (`NEXUS_CONSOLE_GUARD=off`) or remove it. The console-window flood it prevents was real, and the false blocks all trace to scope, not to the launch rules.

Rejected alternative: scan only tracked files. A test file the agent has just written and not yet committed is exactly what a test run executes; dropping untracked files would miss it. Skipping the `.tmp/` scratch convention removes the observed false block without that gap.

Rejected alternative: exempt any command that runs an absolute-path interpreter. That would remove the external-helper check (`python <path>/helper.py`), which inspects real launches.

Deferred, not rejected: downgrade findings that cannot open a window under the agent's own windowless console (a plain launch without `CREATE_NO_WINDOW` started from the agent's shell) from a block to a warning, keeping hard blocks for `DETACHED_PROCESS`, `CREATE_NEW_CONSOLE` and visible `Start-Process`. The 2026-10-19 measurement supports it, but it changes the original decision's rejected-advisory choice and needs its own maintainer decision.

## Consequences

A guard block now names code in the project the command runs in. A read-only inspection command never blocks. Projects that keep scratch under a differently named untracked folder still have it scanned; add the folder to `.gitignore` or `.git/info/exclude` to exclude it. Regression tests in `catalog/hooks/tests/test_console_window_guard.py` cover each change and that a launch after a read-only segment is still guarded.
