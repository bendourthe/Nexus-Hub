#!/usr/bin/env bash
# Auto-Format on Write - PostToolUse Hook for Claude Code
# Automatically formats files after Write/Edit tool calls.
# Part of Nexus-Hub
#
# How it works:
#   Claude Code pipes JSON to stdin after each Write/Edit tool call.
#   This script detects the file extension, finds the appropriate formatter
#   on PATH, and runs it. Non-blocking (always exits 0).
#
# Supported formatters:
#   prettier       (JS, TS, JSX, TSX, CSS, SCSS, JSON, HTML, YAML, MD)
#   black / ruff   (Python)
#   gofmt          (Go)
#   rustfmt        (Rust)
#   clang-format   (C, C++, ObjC)

# Never fail loudly - always exit 0
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name: export NEXUS_DISABLED_HOOKS=auto-format-on-write
# Skip all non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
# Skip format/lint hooks only: export NEXUS_HOOK_PROFILE=no-format
_HOOK_NAME="auto-format-on-write"
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

# --- Determine formatter by extension ---
EXT="${FILE_PATH##*.}"
EXT=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')

case "$EXT" in
  js|jsx|ts|tsx|css|scss|less|json|html|htm|yaml|yml|md|mdx|vue|svelte|graphql)
    if command -v prettier >/dev/null 2>&1; then
      prettier --write "$FILE_PATH" >/dev/null 2>&1
    elif command -v npx >/dev/null 2>&1 && [ -f "node_modules/.bin/prettier" ]; then
      npx prettier --write "$FILE_PATH" >/dev/null 2>&1
    fi
    ;;
  py|pyi)
    if command -v black >/dev/null 2>&1; then
      black --quiet "$FILE_PATH" >/dev/null 2>&1
    elif command -v ruff >/dev/null 2>&1; then
      ruff format "$FILE_PATH" >/dev/null 2>&1
    fi
    ;;
  go)
    if command -v gofmt >/dev/null 2>&1; then
      gofmt -w "$FILE_PATH" >/dev/null 2>&1
    fi
    ;;
  rs)
    if command -v rustfmt >/dev/null 2>&1; then
      rustfmt "$FILE_PATH" >/dev/null 2>&1
    fi
    ;;
  c|h|cpp|cc|cxx|hpp|hxx|m|mm)
    if command -v clang-format >/dev/null 2>&1; then
      clang-format -i "$FILE_PATH" >/dev/null 2>&1
    fi
    ;;
esac

exit 0
