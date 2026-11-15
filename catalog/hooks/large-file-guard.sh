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

# Read Settings on every invocation. Only JSON false disables this protection.
_nexus_guardrail_disabled() {
  local guard_home="${HOME:-${USERPROFILE:-}}" guard_file
  [ -n "$guard_home" ] || return 1
  guard_file="$guard_home/.nexus-hub/guardrails.json"
  [ -f "$guard_file" ] || return 1
  if command -v jq >/dev/null 2>&1; then
    jq -e -s --arg key "$1" 'length == 1 and (.[0] | type) == "object" and .[0][$key] == false' "$guard_file" >/dev/null 2>&1
    return $?
  fi
  local guard_py guard_verdict
  for guard_py in python3 python; do
    command -v "$guard_py" >/dev/null 2>&1 || continue
    guard_verdict=$("$guard_py" -c 'import json, sys
try:
    with open(sys.argv[1], encoding="utf-8-sig") as stream:
        config = json.load(stream)
    print("disabled" if isinstance(config, dict) and config.get(sys.argv[2]) is False else "enabled")
except (OSError, ValueError, TypeError):
    print("enabled")' "$guard_file" "$1" 2>/dev/null) || continue
    guard_verdict=${guard_verdict//$'\r'/}
    if [ "$guard_verdict" = "disabled" ]; then return 0; fi
    if [ "$guard_verdict" = "enabled" ]; then return 1; fi
  done
  return 1
}
if _nexus_guardrail_disabled warn_large_files; then exit 0; fi

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

# --- Extract content with jq or the installed Python 3 fallback ---
if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty' 2>/dev/null)
else
  _LARGE_FILE_PYTHON=""
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c 'import json, sys; sys.exit(sys.version_info[0] < 3)' >/dev/null 2>&1; then
      _LARGE_FILE_PYTHON="$candidate"
      break
    fi
  done
  [ -n "$_LARGE_FILE_PYTHON" ] || exit 0
  _large_file_field() {
    printf '%s' "$INPUT" | "$_LARGE_FILE_PYTHON" -c 'import json, sys
try:
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    fields = payload.get("tool_input", {}) if isinstance(payload, dict) else {}
    if not isinstance(fields, dict):
        fields = {}
    for key in sys.argv[1:]:
        value = fields.get(key)
        if isinstance(value, str) and value:
            sys.stdout.buffer.write(value.encode("utf-8"))
            break
except (ValueError, TypeError, UnicodeError):
    pass' "$@"
  }
  FILE_PATH=$(_large_file_field file_path path)
  CONTENT=$(_large_file_field content)
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
