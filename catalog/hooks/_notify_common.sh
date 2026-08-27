#!/usr/bin/env bash
# Shared helpers for the end-of-task notification hooks - Part of Nexus-Hub
#
# Sourced by notify-on-complete.sh (Stop) and notify-attention-required.sh
# (Notification). The leading underscore marks it as a shared module rather than
# a registerable hook, matching the _skill_rules.py convention; it is never
# registered in settings.json and never invoked directly.
#
# Contract: docs/releases/v3/v3.15/development/end-of-task-notification-contract.md
#
# Everything here is fail-open. A notification is a convenience, so no helper
# may abort a turn: each one degrades to a usable default instead of erroring.

# nexus_notify_label - print "<repo> (<branch>)" for the current workspace.
#
# Resolution order is git root, then $CLAUDE_PROJECT_DIR, then $PWD, then the
# literal "unknown". `basename "$(pwd)"` alone is NOT sufficient: it names
# whatever subdirectory the hook happened to run in, which is how a toast
# reading "Task complete in work" was produced in the field. The branch is
# included because worktrees of one repo are routinely open simultaneously.
nexus_notify_label() {
  local root name branch
  root=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [ -z "$root" ] && [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    root="$CLAUDE_PROJECT_DIR"
  fi
  if [ -z "$root" ]; then
    root=$(pwd 2>/dev/null || true)
  fi

  name=$(basename "$root" 2>/dev/null || true)
  if [ -z "$name" ]; then
    name="unknown"
  fi

  # Omit the branch entirely rather than emitting empty parentheses. "HEAD"
  # means a detached checkout, which names nothing useful to a reader.
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  if [ -n "$branch" ] && [ "$branch" != "HEAD" ]; then
    printf '%s (%s)' "$name" "$branch"
  else
    printf '%s' "$name"
  fi
}

# nexus_notify_suppressed HOOK_NAME - return 0 when this invocation must stay silent.
#
# Layer 3 (the switch FILE) is the one that works mid-session. An environment
# variable cannot silence a hook inside an already-running editor, because a
# child process inherits its parent's environment block rather than the
# registry, so a newly-set variable never reaches a process tree that was
# already launched. The file is stat-ed on every invocation, so creating it
# takes effect on the very next notification with no restart.
nexus_notify_suppressed() {
  local hook_name="$1" disabled switch_file
  disabled="${NEXUS_DISABLED_HOOKS:-}"
  case ",${disabled}," in
    *",${hook_name},"*) return 0 ;;
  esac
  if [ "${NEXUS_HOOK_PROFILE:-full}" = "minimal" ]; then
    return 0
  fi
  switch_file="${NEXUS_NOTIFY_DISABLED_FILE:-${HOME}/.nexus-hub/notifications-disabled}"
  if [ -e "$switch_file" ]; then
    return 0
  fi
  return 1
}

# nexus_notify_send TITLE MESSAGE - raise one desktop notification, or no-op.
#
# Picks the first available backend and never reports failure: a headless
# session or a host with no notifier is a silent no-op, not an error.
nexus_notify_send() {
  local title="$1" message="$2" linger

  # Dry run: print the notification instead of raising it. This exists so the
  # label can be asserted by test without popping a real desktop toast on the
  # developer's screen (and so the .sh/.ps1 pair can be compared on the exact
  # same observable). Also handy for debugging a label resolution by hand.
  if [ -n "${NEXUS_NOTIFY_DRY_RUN:-}" ]; then
    printf '%s\t%s\n' "$title" "$message"
    return 0
  fi

  if command -v osascript >/dev/null 2>&1; then
    osascript -e "display notification \"${message}\" with title \"${title}\"" >/dev/null 2>&1 || true
    return 0
  fi

  if command -v notify-send >/dev/null 2>&1; then
    notify-send "$title" "$message" --expire-time=5000 >/dev/null 2>&1 || true
    return 0
  fi

  # Windows / Git Bash. NotifyIcon is chosen over a WinRT toast on purpose: a
  # toast needs an AppUserModelId registration or a third-party module, while
  # this works on a stock PowerShell 5.1 host with no install.
  #
  # The linger is why a powershell.exe lives briefly per notification: disposing
  # the icon too early can cancel a queued toast on Windows 10/11. It is
  # configurable so the shortest safe value can be MEASURED on a live desktop
  # rather than guessed; see the known limitation in the contract doc.
  if command -v powershell.exe >/dev/null 2>&1; then
    linger="${NEXUS_NOTIFY_LINGER_MS:-5500}"
    NEXUS_NOTIFY_TITLE="$title" NEXUS_NOTIFY_MESSAGE="$message" \
    NEXUS_NOTIFY_LINGER_MS="$linger" powershell.exe -NoProfile -NonInteractive -Command '
      try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        Add-Type -AssemblyName System.Drawing -ErrorAction Stop
        $n = New-Object System.Windows.Forms.NotifyIcon
        $n.Icon = [System.Drawing.SystemIcons]::Information
        $n.BalloonTipTitle = $env:NEXUS_NOTIFY_TITLE
        $n.BalloonTipText = $env:NEXUS_NOTIFY_MESSAGE
        $n.Visible = $true
        $n.ShowBalloonTip(5000)
        Start-Sleep -Milliseconds ([int]$env:NEXUS_NOTIFY_LINGER_MS)
        $n.Dispose()
      } catch { }
    ' >/dev/null 2>&1 || true
    return 0
  fi

  return 0
}
