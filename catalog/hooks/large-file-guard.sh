#!/usr/bin/env bash
# Large File Guard - PreToolUse Hook for Claude Code
# Warns before writing files that exceed size thresholds.
# Part of DevAI-Hub
#
# How it works:
#   Claude Code pipes JSON to stdin before each Write tool call.
#   This script checks the content size against configurable thresholds
#   and outputs an advisory warning to stderr if exceeded.
#   Non-blocking (always exits 0).
#
# Thresholds (configurable via environment variables):
#   LARGE_FILE_MAX_LINES  (default: 500)
#   LARGE_FILE_MAX_BYTES  (default: 51200 = 50KB)

# Never fail loudly - always exit 0
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name: export DEVAI_DISABLED_HOOKS=large-file-guard
# Skip all non-essential hooks: export DEVAI_HOOK_PROFILE=minimal
_HOOK_NAME="large-file-guard"
_DISABLED="${DEVAI_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${DEVAI_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

# --- Configuration ---
MAX_LINES="${LARGE_FILE_MAX_LINES:-500}"
MAX_BYTES="${LARGE_FILE_MAX_BYTES:-51200}"

# --- ANSI colors ---
COLOR_YELLOW='\033[0;33m'
COLOR_RESET='\033[0m'

# --- Read JSON from stdin ---
INPUT=$(cat)

# --- Extract content (requires jq for reliable multi-line extraction) ---
if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty' 2>/dev/null)
else
  # Without jq we cannot reliably extract multi-line content
  exit 0
fi

[ -n "${CONTENT:-}" ] || exit 0
[ -n "${FILE_PATH:-}" ] || exit 0

FILENAME=$(basename "$FILE_PATH" 2>/dev/null || echo "$FILE_PATH")

# --- Check line count ---
LINE_COUNT=$(echo "$CONTENT" | wc -l | tr -d ' ')
if [ "$LINE_COUNT" -gt "$MAX_LINES" ] 2>/dev/null; then
  echo -e "${COLOR_YELLOW}[large-file-guard]${COLOR_RESET} Warning: $FILENAME has $LINE_COUNT lines (threshold: $MAX_LINES). Consider splitting this file into smaller modules." >&2
fi

# --- Check byte size ---
BYTE_COUNT=$(echo "$CONTENT" | wc -c | tr -d ' ')
if [ "$BYTE_COUNT" -gt "$MAX_BYTES" ] 2>/dev/null; then
  KB_SIZE=$((BYTE_COUNT / 1024))
  KB_THRESHOLD=$((MAX_BYTES / 1024))
  echo -e "${COLOR_YELLOW}[large-file-guard]${COLOR_RESET} Warning: $FILENAME is ${KB_SIZE}KB (threshold: ${KB_THRESHOLD}KB). Consider splitting this file into smaller modules." >&2
fi

# Advisory only - never block
exit 0
