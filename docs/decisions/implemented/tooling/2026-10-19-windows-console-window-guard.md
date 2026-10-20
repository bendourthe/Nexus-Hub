# Decision: Windows Console Window Guard

Status: implemented - a PreToolUse hook blocks a Windows test run while the project has a window-unsafe process launch, and Nexus-Hub holds itself to the same rule.

Hook maintainers, test authors, and anyone diagnosing console windows that flash on Windows read this before adding a process launch to a hook, script, or test. It records the measured cause, the three-layer guard (hook, self-check, authoring rules), the reasoned-exception marker, and the designs rejected.

**Date**: 2026-10-19. **Release**: maintenance, ships with v4.14.1.

## Problem

On Windows, a console program started by a process that has no console opens a new window that takes keyboard focus. A test suite that starts hundreds of git, bash, PowerShell, or Python children from such a process makes the machine unusable until it ends. The earlier fix gave the native readers a no-window flag and gave Nexus-Hub's own pytest suites a `conftest.py` guard, but nothing stopped a new launch from reintroducing the problem, five PowerShell hooks started Python with `UseShellExecute = $false` and no `CreateNoWindow`, Node test helpers in the usage monitors started processes without `windowsHide`, and other projects had no protection at all.

Measurement on 2026-10-19 (Windows 11, Claude Code in VS Code) showed that the agent's Bash tool, its background tasks, and its Monitor commands all run inside a console that has no window (`GetConsoleProcessList` reports four attached processes, `GetConsoleWindow` returns 0). Their ordinary children inherit that console and open no window. Windows therefore appear only when a launch leaves that console: a host that starts a hook without a console, an explicit `DETACHED_PROCESS` or `CREATE_NEW_CONSOLE`, `Start-Process`, or a Node `child_process` call from a console-less process (an IDE test runner or extension host) without `windowsHide`. A read-only watcher that logs every visible console window confirmed a deliberate test window within one poll and recorded none during later agent work.

## Decision

`catalog/hooks/console-window-guard.py`, registered as a PreToolUse hook for Bash and PowerShell, acts only on Windows and only on a command that runs a test runner (pytest, tox, npm, pnpm, yarn or bun test, vitest, jest, Playwright, go test, cargo test, dotnet test, Maven or Gradle test, Pester, make test, and the repository-native CI profile runner). It lists the project's tracked and untracked-but-not-ignored files through `git ls-files`, pre-filters them on byte markers, and blocks the command (exit 2) when it finds:

- Python test code that starts processes in a project with no `conftest.py` `CREATE_NO_WINDOW` guard, with a ready-to-paste guard in the message.
- An explicit `DETACHED_PROCESS` or `CREATE_NEW_CONSOLE` launch, including the raw `0x8` and `0x10` forms.
- A PowerShell `ProcessStartInfo` without `CreateNoWindow = $true`, or `Start-Process` without `-NoNewWindow` or `-WindowStyle Hidden`.
- A Node `child_process` call without `windowsHide`.
- Go test code that calls `exec.Command` in a project with no Windows `HideWindow` / `CREATE_NO_WINDOW` helper.

A deliberate launch is accepted when its line or the line above carries `nexus: console-window-ok` with a reason. The hook is disabled with `NEXUS_DISABLED_HOOKS=console-window-guard` or `NEXUS_CONSOLE_GUARD=off`. Nexus-Hub runs the same scan on its own tree in `test_console_window_guard.py`, so a new unsafe launch fails CI, and the Python, TypeScript, and Go testing rules state the window-safe form for each language.

## Alternatives considered

Rejected alternative: wrap every agent shell command in a windowless launcher. The measurement above shows those commands already run in a windowless console, so a wrapper would change nothing while touching every command.

Rejected alternative: an advisory warning that lets the test run continue. A warning arrives after the windows have already taken the keyboard, which is the harm the user asked to prevent.

Rejected alternative: scan every file with `os.walk`. On this repository a cold walk took 54 seconds because it read vendored and generated trees; `git ls-files` plus a byte pre-filter scans the same tree in under a second.

Rejected alternative: rely on the existing `conftest.py` guard alone. It protects only Python suites that already have it, and only the processes pytest starts; hooks, Node helpers, Go tests, and other projects stay unprotected.

## Consequences

A Windows test run in any project is stopped, with exact fixes, until its process launches are window-safe or marked with a reason. The scan is heuristic: a launch hidden behind an unusual wrapper is not seen, and a flagged launch that is safe in practice (for example a macOS-only call) needs a reasoned marker. The guard does not change how agent hosts start hooks; a host that starts a console program without a console remains outside Nexus-Hub's control, and the read-only watcher used for the diagnosis is the way to identify one.
