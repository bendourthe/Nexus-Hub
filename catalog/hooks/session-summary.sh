#!/usr/bin/env bash
# Session Summary - Stop Hook for Claude Code
# Appends a one-line summary to ~/.claude/session-log.md after each session.
# Part of Nexus-Hub
#
# How it works:
#   Fires on the Stop event. Records timestamp, project name, and
#   files changed (from git diff) to a persistent session log.
#
# Log format: | YYYY-MM-DD HH:MM | project-name | duration | files-changed |

# Never fail loudly - always exit 0
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name: export DEVAI_DISABLED_HOOKS=session-summary
# Skip all non-essential hooks: export DEVAI_HOOK_PROFILE=minimal
_HOOK_NAME="session-summary"
_DISABLED="${DEVAI_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${DEVAI_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

LOG_FILE="$HOME/.claude/session-log.md"

# --- Ensure log file exists with headers ---
if [ ! -f "$LOG_FILE" ]; then
  mkdir -p "$HOME/.claude" 2>/dev/null || true
  {
    echo "# Claude Code Session Log"
    echo ""
    echo "| Date | Project | Duration | Files Changed |"
    echo "|------|---------|----------|---------------|"
  } > "$LOG_FILE"
fi

# --- Gather data ---
TIMESTAMP=$(date "+%Y-%m-%d %H:%M" 2>/dev/null || echo "unknown")
PROJECT_NAME=$(basename "$(pwd)" 2>/dev/null || echo "unknown")

# Try to get duration from stdin JSON
INPUT=$(cat 2>/dev/null || true)
DURATION="N/A"
if [ -n "$INPUT" ] && command -v jq >/dev/null 2>&1; then
  PARSED_DURATION=$(echo "$INPUT" | jq -r '.session_duration // .duration // empty' 2>/dev/null)
  if [ -n "${PARSED_DURATION:-}" ]; then
    DURATION="$PARSED_DURATION"
  fi
fi

# Count files changed via git
FILES_CHANGED="N/A"
if command -v git >/dev/null 2>&1; then
  DIFF_STAT=$(git diff --stat HEAD 2>/dev/null | tail -1)
  if [ -n "$DIFF_STAT" ]; then
    NUM_FILES=$(echo "$DIFF_STAT" | grep -o '[0-9]\+ file' | grep -o '[0-9]\+')
    if [ -n "$NUM_FILES" ]; then
      FILES_CHANGED="$NUM_FILES"
    fi
  else
    FILES_CHANGED="0"
  fi
fi

# --- Append entry ---
echo "| $TIMESTAMP | $PROJECT_NAME | $DURATION | $FILES_CHANGED |" >> "$LOG_FILE"

exit 0
