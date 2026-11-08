#!/usr/bin/env bash
# Lint on Write - PostToolUse Hook for Claude Code
# Runs the appropriate linter after Write/Edit tool calls.
# Part of Nexus-Hub
#
# How it works:
#   Claude Code pipes JSON to stdin after each Write/Edit tool call.
#   This script detects the file extension, finds the appropriate linter
#   on PATH, and runs it. Outputs warnings to stderr. Non-blocking (always exits 0).
#
# Supported linters:
#   eslint         (JS, TS, JSX, TSX)
#   pylint / ruff  (Python)
#   golangci-lint  (Go)
#   clippy hint    (Rust)

# Never fail loudly - always exit 0
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name: export NEXUS_DISABLED_HOOKS=lint-on-write
# Skip all non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
# Skip format/lint hooks only: export NEXUS_HOOK_PROFILE=no-format
_HOOK_NAME="lint-on-write"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "no-format" ]]; then exit 0; fi

# --- Read JSON from stdin ---
INPUT=$(cat)

# --- Extract file path ---
if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)
else
  FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//;s/"$//')
  if [ -z "$FILE_PATH" ]; then
    FILE_PATH=$(echo "$INPUT" | grep -o '"path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"path"[[:space:]]*:[[:space:]]*"//;s/"$//')
  fi
fi

[ -n "${FILE_PATH:-}" ] || exit 0
[ -f "$FILE_PATH" ] || exit 0

# --- ANSI colors ---
COLOR_YELLOW='\033[0;33m'
COLOR_RESET='\033[0m'

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: lint-on-write]"
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

# --- Determine linter by extension ---
EXT="${FILE_PATH##*.}"
EXT=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')

case "$EXT" in
  js|jsx|ts|tsx)
    if command -v eslint >/dev/null 2>&1; then
      LINT_OUTPUT=$(eslint --no-error-on-unmatched-pattern --format compact "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        _nexus_msg "$COLOR_YELLOW" "eslint warnings for $(_nexus_esc "$(basename "$FILE_PATH")"):"
        echo "$LINT_OUTPUT" >&2  # nexus: hook-msg-exempt relayed linter output
      fi
    elif command -v npx >/dev/null 2>&1 && [ -f "node_modules/.bin/eslint" ]; then
      LINT_OUTPUT=$(npx eslint --no-error-on-unmatched-pattern --format compact "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        _nexus_msg "$COLOR_YELLOW" "eslint warnings for $(_nexus_esc "$(basename "$FILE_PATH")"):"
        echo "$LINT_OUTPUT" >&2  # nexus: hook-msg-exempt relayed linter output
      fi
    fi
    ;;
  py|pyi)
    if command -v ruff >/dev/null 2>&1; then
      LINT_OUTPUT=$(ruff check "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        _nexus_msg "$COLOR_YELLOW" "ruff warnings for $(_nexus_esc "$(basename "$FILE_PATH")"):"
        echo "$LINT_OUTPUT" >&2  # nexus: hook-msg-exempt relayed linter output
      fi
    elif command -v pylint >/dev/null 2>&1; then
      LINT_OUTPUT=$(pylint --output-format=text --score=no "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        _nexus_msg "$COLOR_YELLOW" "pylint warnings for $(_nexus_esc "$(basename "$FILE_PATH")"):"
        echo "$LINT_OUTPUT" >&2  # nexus: hook-msg-exempt relayed linter output
      fi
    fi
    ;;
  go)
    if command -v golangci-lint >/dev/null 2>&1; then
      LINT_OUTPUT=$(golangci-lint run "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        _nexus_msg "$COLOR_YELLOW" "golangci-lint warnings for $(_nexus_esc "$(basename "$FILE_PATH")"):"
        echo "$LINT_OUTPUT" >&2  # nexus: hook-msg-exempt relayed linter output
      fi
    fi
    ;;
  rs)
    # Clippy requires cargo context, so provide a hint
    if command -v cargo >/dev/null 2>&1; then
      _nexus_msg "$COLOR_YELLOW" "Tip: run 'cargo clippy' to lint Rust files"
    fi
    ;;
esac

exit 0
