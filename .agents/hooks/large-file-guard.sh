#!/usr/bin/env bash
# Large File Guard - PreToolUse Hook for Claude Code
# Warns before writing files that exceed size thresholds.
# Part of Nexus-Hub
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
# Disable by name: export NEXUS_DISABLED_HOOKS=large-file-guard
# Skip all non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
_HOOK_NAME="large-file-guard"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

# --- Configuration ---
MAX_LINES="${LARGE_FILE_MAX_LINES:-500}"
MAX_BYTES="${LARGE_FILE_MAX_BYTES:-51200}"

# --- ANSI colors ---
COLOR_YELLOW='\033[0;33m'
COLOR_RESET='\033[0m'

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: large-file-guard]"
# Make CR, LF, ESC and the other C0 control characters in an echoed value
# visible, so a file name or command cannot start a forged tagged line.
_nexus_esc() {
  local s=$1 ctrl i c r
  ctrl=$'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x7f'
  for ((i = 0; i < ${#ctrl}; i++)); do
    c=${ctrl:i:1}
    case $c in
      $'\t') r='\t' ;; $'\n') r='\n' ;; $'\r') r='\r' ;; $'\x1b') r='\x1b' ;; $'\x7f') r='\x7f' ;;
      *) printf -v r '%s%02x' '\x' $((i + 1)) ;;
    esac
    s=${s//"$c"/"$r"}
  done
  printf '%s' "$s"
}
# Print the tag and the message to stderr; every further argument is a
# continuation line printed as is. $1 is an optional color code for the tag.
_nexus_msg() {
  local color=$1 message=$2 line
  shift 2
  printf '%b%s%b %s\n' "$color" "$_NEXUS_TAG" "${color:+$COLOR_RESET}" "$message" >&2
  for line in "$@"; do printf '%s\n' "$line" >&2; done
}

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
  _nexus_msg "$COLOR_YELLOW" "Warning: $(_nexus_esc "$FILENAME") has $LINE_COUNT lines (threshold: $MAX_LINES). Consider splitting this file into smaller modules."
fi

# --- Check byte size ---
BYTE_COUNT=$(echo "$CONTENT" | wc -c | tr -d ' ')
if [ "$BYTE_COUNT" -gt "$MAX_BYTES" ] 2>/dev/null; then
  KB_SIZE=$((BYTE_COUNT / 1024))
  KB_THRESHOLD=$((MAX_BYTES / 1024))
  _nexus_msg "$COLOR_YELLOW" "Warning: $(_nexus_esc "$FILENAME") is ${KB_SIZE}KB (threshold: ${KB_THRESHOLD}KB). Consider splitting this file into smaller modules."
fi

# Advisory only - never block
exit 0
