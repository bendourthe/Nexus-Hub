#!/usr/bin/env bash
# Lint on Write - PostToolUse Hook for Claude Code
# Runs the appropriate linter after Write/Edit tool calls.
# Part of DevAI-Hub
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
# Disable by name: export DEVAI_DISABLED_HOOKS=lint-on-write
# Skip all non-essential hooks: export DEVAI_HOOK_PROFILE=minimal
# Skip format/lint hooks only: export DEVAI_HOOK_PROFILE=no-format
_HOOK_NAME="lint-on-write"
_DISABLED="${DEVAI_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${DEVAI_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi
if [[ "${DEVAI_HOOK_PROFILE:-full}" == "no-format" ]]; then exit 0; fi

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

# --- Determine linter by extension ---
EXT="${FILE_PATH##*.}"
EXT=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')

case "$EXT" in
  js|jsx|ts|tsx)
    if command -v eslint >/dev/null 2>&1; then
      LINT_OUTPUT=$(eslint --no-error-on-unmatched-pattern --format compact "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        echo -e "${COLOR_YELLOW}[lint]${COLOR_RESET} eslint warnings for $(basename "$FILE_PATH"):" >&2
        echo "$LINT_OUTPUT" >&2
      fi
    elif command -v npx >/dev/null 2>&1 && [ -f "node_modules/.bin/eslint" ]; then
      LINT_OUTPUT=$(npx eslint --no-error-on-unmatched-pattern --format compact "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        echo -e "${COLOR_YELLOW}[lint]${COLOR_RESET} eslint warnings for $(basename "$FILE_PATH"):" >&2
        echo "$LINT_OUTPUT" >&2
      fi
    fi
    ;;
  py|pyi)
    if command -v ruff >/dev/null 2>&1; then
      LINT_OUTPUT=$(ruff check "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        echo -e "${COLOR_YELLOW}[lint]${COLOR_RESET} ruff warnings for $(basename "$FILE_PATH"):" >&2
        echo "$LINT_OUTPUT" >&2
      fi
    elif command -v pylint >/dev/null 2>&1; then
      LINT_OUTPUT=$(pylint --output-format=text --score=no "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        echo -e "${COLOR_YELLOW}[lint]${COLOR_RESET} pylint warnings for $(basename "$FILE_PATH"):" >&2
        echo "$LINT_OUTPUT" >&2
      fi
    fi
    ;;
  go)
    if command -v golangci-lint >/dev/null 2>&1; then
      LINT_OUTPUT=$(golangci-lint run "$FILE_PATH" 2>&1) || true
      if [ -n "$LINT_OUTPUT" ]; then
        echo -e "${COLOR_YELLOW}[lint]${COLOR_RESET} golangci-lint warnings for $(basename "$FILE_PATH"):" >&2
        echo "$LINT_OUTPUT" >&2
      fi
    fi
    ;;
  rs)
    # Clippy requires cargo context, so provide a hint
    if command -v cargo >/dev/null 2>&1; then
      echo -e "${COLOR_YELLOW}[lint]${COLOR_RESET} Tip: run 'cargo clippy' to lint Rust files" >&2
    fi
    ;;
esac

exit 0
