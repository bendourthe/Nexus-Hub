#!/usr/bin/env bash
# Notify on Complete - Stop Hook for Claude Code
# Sends a desktop notification when Claude Code finishes a task.
# Part of Nexus-Hub
#
# How it works:
#   Fires on the Stop event (after Claude finishes responding).
#   Detects the OS and uses the appropriate notification mechanism.
#   Fails silently if no notification system is available.
#
# Supported platforms:
#   macOS:              osascript (Notification Center)
#   Linux:              notify-send (libnotify)
#   Windows / Git Bash: powershell toast notification

# Never fail loudly - always exit 0
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name: export NEXUS_DISABLED_HOOKS=notify-on-complete
# Skip all non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
_HOOK_NAME="notify-on-complete"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

TITLE="Claude Code"
PROJECT_NAME=$(basename "$(pwd)" 2>/dev/null || echo "unknown")
MESSAGE="Task complete in $PROJECT_NAME"

# Attempt to read session duration from stdin JSON
INPUT=$(cat 2>/dev/null || true)
if [ -n "$INPUT" ] && command -v jq >/dev/null 2>&1; then
  DURATION=$(echo "$INPUT" | jq -r '.session_duration // .duration // empty' 2>/dev/null)
  if [ -n "${DURATION:-}" ]; then
    MESSAGE="Task complete in $PROJECT_NAME (${DURATION})"
  fi
fi

# --- macOS ---
if command -v osascript >/dev/null 2>&1; then
  osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\"" >/dev/null 2>&1
  exit 0
fi

# --- Linux (notify-send) ---
if command -v notify-send >/dev/null 2>&1; then
  notify-send "$TITLE" "$MESSAGE" --expire-time=5000 >/dev/null 2>&1
  exit 0
fi

# --- Windows / Git Bash (powershell) ---
if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -NoProfile -NonInteractive -Command "
    [void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
    \$notify = New-Object System.Windows.Forms.NotifyIcon
    \$notify.Icon = [System.Drawing.SystemIcons]::Information
    \$notify.BalloonTipTitle = '$TITLE'
    \$notify.BalloonTipText = '$MESSAGE'
    \$notify.Visible = \$true
    \$notify.ShowBalloonTip(5000)
    Start-Sleep -Milliseconds 5500
    \$notify.Dispose()
  " >/dev/null 2>&1
  exit 0
fi

# No notification system found - fail silently
exit 0
