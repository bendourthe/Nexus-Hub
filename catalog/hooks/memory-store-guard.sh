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
# is NEXUS_MEMORY_ALLOW_IN_REPO=1, the same switch the store honors, plus the
# host's full-access mode (docs/policy/permission-mode-contract.md).

set -euo pipefail

_HOOK_NAME="memory-store-guard"

case "${NEXUS_MEMORY_ALLOW_IN_REPO:-}" in
  1|true|yes|on|TRUE|YES|ON) exit 0 ;;
esac

COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: memory-store-guard]"
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

INPUT=$(cat)
# Full access (Claude Code or Codex permission_mode "bypassPermissions"): the
# user chose to run without approval gates, so this Nexus-Hub guard steps aside.
# Contract: docs/policy/permission-mode-contract.md
_HOST_MODE=""
if command -v jq >/dev/null 2>&1; then
  _HOST_MODE=$(printf '%s' "$INPUT" | jq -r 'if type == "object" and (.permission_mode | type) == "string" then .permission_mode else empty end' 2>/dev/null || true)
elif command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
  _MODE_PYTHON=$(command -v python3 || command -v python)
  _HOST_MODE=$(printf '%s' "$INPUT" | "$_MODE_PYTHON" -c '
import json, sys
try:
    payload = json.load(sys.stdin)
    mode = payload.get("permission_mode") if isinstance(payload, dict) else None
    if isinstance(mode, str):
        print(mode)
except (ValueError, TypeError):
    pass' 2>/dev/null || true)
fi
if [ "$_HOST_MODE" = "bypassPermissions" ]; then exit 0; fi

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
  _nexus_msg "$COLOR_RED" "BLOCKED: $1" \
    "Relocate the store outside the repository, or set NEXUS_MEMORY_ALLOW_IN_REPO=1 if you accept that this log can be committed."
  exit 2
}

if [ -n "${FILE_PATH:-}" ] && _is_store_artifact "$FILE_PATH"; then
  if _inside_git "$FILE_PATH"; then
    _block "refusing to write nexus-memory artifact '$(_nexus_esc "$FILE_PATH")' inside a git working tree"
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
