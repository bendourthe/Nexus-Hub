# End-of-Task Notification Contract (v3.15.10)

**Status**: locked for v3.15.10 Phase 1
**Date**: 2026-08-04
**Applies to**: `catalog/hooks/notify-on-complete.{sh,ps1}`, `catalog/hooks/notify-attention-required.{sh,ps1}`, `catalog/hooks/_notify_common.{sh,ps1}`

This is the contract Phases 2 and 3 port to other platforms. It exists because the pre-v3.15.10 behavior notified on a signal that did not mean what its hook name claimed.

## The problem being fixed

A single hook was registered on the `Stop` chain and named `notify-on-complete`. `Stop` fires when the assistant finishes responding, which happens at the end of **every** conversational turn, not when a task is done. Three consequences were observed in the field on 2026-08-04:

1. **Notification storms.** A session driven by background monitors produces many short turns (each completed background task re-invokes the agent), so one long task generated a burst of toasts. None of them meant "your task is finished".
2. **Meaningless labels.** The message was built from `basename "$(pwd)"`, which reports whatever directory the hook happened to run in. One observed toast read `Task complete in work`, naming a directory that could not be located anywhere in the maintainer's checkout, worktrees, or temp session directories.
3. **An opt-out that could not opt out.** The hook's only kill switch was the `NEXUS_DISABLED_HOOKS` environment variable. Setting it had no effect on a running session, because a child process inherits its parent's environment **block**, not the registry. Measured the same day: the User-scope value read back correctly while a freshly spawned child under the running editor read it as empty, with 4 `claude`, 39 `Code`, and 19 `Cursor` processes live.

## Trigger set

Exactly two triggers. Both mean "a human's attention is now warranted".

| Trigger | Claude Code event | Fires when | Message |
|---|---|---|---|
| **A - attention required** | `Notification` | The agent needs permission to use a tool, or has been idle waiting for input | `Needs your input - <label>` |
| **B - task complete** | `Stop` | The agent finished responding and handed control back | `Task complete - <label>` |

### Events that MUST NOT be wired

- **`SubagentStop`** - a sub-agent finishing is a sub-task milestone, not a reason to interrupt a human. This is the single change most likely to reintroduce the storm this release removes, so its absence is asserted by test rather than merely documented.
- **`PostToolUse`** - fires per tool call. Notifying here is strictly worse than the behavior being replaced.
- **`PreToolUse`**, **`UserPromptSubmit`**, **`PreCompact`**, **`SessionStart`** - none of these mean the agent is waiting on the human for a decision.

### Why trigger B still rides `Stop`

There is no separate "the whole task is done" event, because from the harness's perspective a turn ending *is* the agent handing control back. Trigger B is therefore honest about what it can know: it fires when the agent stopped generating and is waiting on you. What changes versus the old behavior is not the event but everything around it. The label identifies the workspace, sub-task completions no longer fire at all, and the kill switch actually works.

An explicit non-goal: this contract does NOT try to infer "task fully complete" versus "stopped to ask something". Trigger A covers the ask-something case through a genuinely different event, and a heuristic that guessed between them would be wrong in both directions.

## Label format

    <repo> (<branch>)

Resolution order for `<repo>`, first non-empty wins:

1. `basename` of `git rev-parse --show-toplevel`
2. `basename` of `$CLAUDE_PROJECT_DIR`
3. `basename` of the current working directory
4. the literal `unknown`

`<branch>` comes from `git rev-parse --abbrev-ref HEAD`. It is omitted entirely (no empty parentheses) when there is no branch, or when the result is `HEAD` (a detached checkout, which names nothing useful).

**Why the git root and not `pwd`.** `basename "$(pwd)"` names a subdirectory whenever the hook runs anywhere below the repository root, which is how `Task complete in work` was produced. The git root is stable regardless of where inside the tree the hook executes.

**Why the branch matters.** Worktrees of one repository are routinely open at once. During v3.15.9 the maintainer had both `Nexus-Hub` and `Nexus-Hub-worktrees/v3.15.8-platform-parity` checked out; without the branch, both announce themselves identically.

## Kill switch

Suppression is checked on **every invocation**, in this order:

1. `NEXUS_DISABLED_HOOKS` contains the hook name (retained for backward compatibility)
2. `NEXUS_HOOK_PROFILE=minimal` (retained)
3. **The switch file exists**: `$NEXUS_NOTIFY_DISABLED_FILE`, defaulting to `~/.nexus-hub/notifications-disabled`

Layer 3 is the one that works mid-session. The hook script and the switch file are both read from disk on every invocation, so creating the file takes effect on the very next notification with no restart. An environment variable cannot do this, for the process-inheritance reason recorded above.

To silence notifications immediately:

```bash
mkdir -p ~/.nexus-hub && touch ~/.nexus-hub/notifications-disabled
```

To restore them, delete that file. Any opt-out mechanism added later MUST be checkable from something the hook reads at run time; an environment-only check is not a valid kill switch for an already-running session.

## Dry-run mode (testability)

Setting `NEXUS_NOTIFY_DRY_RUN` to any non-empty value makes both hooks print `<title>\t<message>` to stdout instead of raising a desktop notification.

This exists because the label is otherwise unobservable: without it a test either pops real toasts onto the developer's screen or cannot assert what the notification would have said. It also gives the `.sh` and `.ps1` implementations the exact same observable, so a single assertion doubles as the parity check. It is useful by hand too, for confirming how a label resolves in a given directory:

```bash
NEXUS_NOTIFY_DRY_RUN=1 bash catalog/hooks/notify-on-complete.sh </dev/null
```

## Invariants

- **Always exit 0.** A notification hook must never fail a turn. Every path, including a malformed payload, an absent notifier, and a headless session, exits 0.
- **No new dependency.** No module install, no package manager, no network call. On Windows the notification uses `System.Windows.Forms.NotifyIcon`, which is present on a stock PowerShell 5.1 host and needs no AppUserModelId registration.
- **Shell parity.** Every `.sh` has a `.ps1` sibling. `catalog/hooks/tests/test_hook_sibling_parity.py` fails when either is missing, when a `.ps1` does not parse, or when the pair disagrees on an exit code.
- **One notification per trigger.** Neither hook loops or re-notifies.

## Known limitation carried forward

The Windows path keeps the tray icon alive for 5.5 seconds after `ShowBalloonTip(5000)` so the balloon renders before the icon is disposed, which means a short-lived `powershell.exe` per notification. The v3.15.10 plan proposed shortening it. It was **not** shortened: disposing a `NotifyIcon` too early can cancel a queued toast on Windows 10 and 11, and verifying the shortest safe duration requires observing the rendered result on a live desktop, which no automated test in this repository can do. The duration is exposed as `NEXUS_NOTIFY_LINGER_MS` so it can be measured and tuned deliberately rather than guessed. Reducing the default remains open.

## Platform portability (Phases 2 and 3)

Trigger A depends on the host exposing an event that means "waiting on the human". Claude Code has one (`Notification`). Whether any other platform does is a first-party documentation question deliberately deferred to Phase 3, which must verify each event name before shipping a hook: an unverified event name produces a hook that silently never fires, exactly the defect `escalation-trigger.sh` shipped with for four minor versions.

Two platforms are already known to be permanently out of reach for notifications and are recorded as such rather than attempted:

- **GitHub Copilot** exposes no hook surface (instruction file plus opt-in skills only).
- **OpenCode**'s `plugins/` is a JS/TS Bun runtime, not a shell or python hook host (documented non-gap DF-4).

Both still receive the v3.15.10 end-of-task summary rule through their instruction files, so they are covered for that deliverable even though they cannot be covered for this one.
