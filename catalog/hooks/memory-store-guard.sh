#!/usr/bin/env bash
# Memory Store Guard - PreToolUse Hook for Claude Code
# Blocks writing or committing a relocated nexus-memory store that sits
# inside a git working tree.
# Part of Nexus-Hub
#
# How it works:
#   Claude Code pipes JSON to stdin before Write, Edit, or Bash.
#   This script recognizes nexus-memory artifacts (entries.log,
#   tree/level_*, .nexus-memory-store) and exits 2 when the target
#   lives in a git working tree, or when a git add/commit would stage
#   them.
#
# Like secret-scan, this is a security gate: it does not honor
# NEXUS_HOOK_PROFILE=minimal or NEXUS_DISABLED_HOOKS. The only override
# is NEXUS_MEMORY_ALLOW_IN_REPO=1, the same switch the store honors.

set -euo pipefail

_HOOK_NAME="memory-store-guard"

case "${NEXUS_MEMORY_ALLOW_IN_REPO:-}" in
  1|true|yes|on|TRUE|YES|ON) exit 0 ;;
esac

COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

INPUT=$(cat)

_norm() {
  printf '%s' "${1//\\//}"
}

_extract_field() {
  # $1 = python expression against tool_input, used only as a last resort.
  local jq_expr="$1"
  local py_key="$2"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$INPUT" | jq -r "$jq_expr" 2>/dev/null || true
    return
  fi
  local py=""
  if command -v python3 >/dev/null 2>&1; then
    py="python3"
  elif command -v python >/dev/null 2>&1; then
    py="python"
  fi
  if [ -n "$py" ]; then
    printf '%s' "$INPUT" | "$py" -c "
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    raise SystemExit(0)
tool = data.get('tool_input') or {}
value = tool.get('$py_key') or ''
if not value and '$py_key' == 'file_path':
    value = tool.get('path') or ''
print(value)
" 2>/dev/null || true
    return
  fi
}

FILE_PATH="$(_norm "$(_extract_field '.tool_input.file_path // .tool_input.path // empty' 'file_path')")"
COMMAND="$(_extract_field '.tool_input.command // empty' 'command')"

_is_store_artifact() {
  local norm base dir parent
  norm="$(_norm "$1")"
  [ -n "$norm" ] || return 1
  base="${norm##*/}"
  dir="${norm%/*}"
  [ "$dir" = "$norm" ] && dir="."

  if [ "$base" = ".nexus-memory-store" ]; then
    return 0
  fi
  if [[ "$norm" == *".nexus-hub/memory/"* ]]; then
    case "$base" in
      entries.log|entries.lock|config.json|.nexus-memory-store) return 0 ;;
    esac
    if [[ "$norm" == */tree/level_* ]]; then
      return 0
    fi
  fi
  if [ "$base" = "entries.log" ] || [ "$base" = "entries.lock" ]; then
    if [ -f "$dir/.nexus-memory-store" ]; then
      return 0
    fi
    if [ -f "$dir/config.json" ] && grep -q '"record_width"' "$dir/config.json" 2>/dev/null; then
      return 0
    fi
    if [ "$(basename "$dir")" = "memory" ]; then
      return 0
    fi
  fi
  if [[ "$norm" == */tree/level_* ]]; then
    parent="$(dirname "$dir")"
    if [ -f "$parent/.nexus-memory-store" ]; then
      return 0
    fi
    if [ -f "$parent/config.json" ] && grep -q '"record_width"' "$parent/config.json" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

_inside_git() {
  local probe
  probe="$1"
  if [ -d "$probe" ]; then
    :
  else
    probe="$(dirname "$probe")"
  fi
  command -v git >/dev/null 2>&1 || return 1
  [ "$(git -C "$probe" rev-parse --is-inside-work-tree 2>/dev/null || true)" = "true" ]
}

_block() {
  echo -e "${COLOR_RED}[memory-store-guard] BLOCKED${COLOR_RESET}: $1" >&2
  echo "Relocate the store outside the repository, or set NEXUS_MEMORY_ALLOW_IN_REPO=1 if you accept that this log can be committed." >&2
  exit 2
}

if [ -n "${FILE_PATH:-}" ] && _is_store_artifact "$FILE_PATH"; then
  if _inside_git "$FILE_PATH"; then
    _block "refusing to write nexus-memory artifact '$FILE_PATH' inside a git working tree"
  fi
fi

if [ -n "${COMMAND:-}" ]; then
  if echo "$COMMAND" | grep -qE '(^|[;&|[:space:]])git[[:space:]]+(add|commit|rm)([[:space:]]|$)'; then
    if echo "$COMMAND" | grep -qE '(^|[[:space:]/\\])(entries\.log|entries\.lock|\.nexus-memory-store|tree/level_)'; then
      _block "refusing to git-stage a nexus-memory store artifact"
    fi
    if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      staged="$(git diff --cached --name-only 2>/dev/null || true)"
      if [ -n "$staged" ]; then
        while IFS= read -r rel; do
          [ -n "$rel" ] || continue
          if _is_store_artifact "$rel" || _is_store_artifact "$(pwd)/$rel"; then
            _block "refused staged nexus-memory artifact '$rel'"
          fi
        done <<< "$staged"
      fi
    fi
  fi
fi

exit 0
