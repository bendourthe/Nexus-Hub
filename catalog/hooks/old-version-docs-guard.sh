#!/usr/bin/env bash
# Old Version Docs Guard - PreToolUse Hook for Claude Code
# Warns when Write or Edit targets a historical docs/v<old-version>/ path.
# Part of Nexus-Hub
#
# How it works:
#   Claude Code pipes JSON to stdin before each Write/Edit tool call.
#   This script extracts the file path, detects whether it lives inside
#   a docs/v<version>/ directory older than the active version, and
#   emits an advisory warning to stderr if so.
#
#   Non-blocking by default (always exits 0). Set DEVAI_OLD_DOCS_GUARD=block
#   to upgrade to a hard block (exit 1).
#
# Active-version detection:
#   1. Latest docs/v*/ directory by semantic version order.
#   2. If no docs/v*/ directories exist, the hook is a no-op.
#
# Companion command: /refactor-docs proposes structured archival of historical
# version dirs instead of ad-hoc edits.

set -euo pipefail

# Never fail loudly on internal errors - always exit 0 unless blocking.
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name:           export DEVAI_DISABLED_HOOKS=old-version-docs-guard
# Skip all non-essential:    export DEVAI_HOOK_PROFILE=minimal
# Upgrade warning to block:  export DEVAI_OLD_DOCS_GUARD=block
_HOOK_NAME="old-version-docs-guard"
_DISABLED="${DEVAI_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${DEVAI_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

_BLOCKING="${DEVAI_OLD_DOCS_GUARD:-warn}"

# --- ANSI colors ---
COLOR_YELLOW='\033[0;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

# --- Read JSON from stdin ---
INPUT=$(cat)

# --- Extract file path (requires jq) ---
if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)
else
  exit 0
fi

[ -n "${FILE_PATH:-}" ] || exit 0

# Normalize separators (Windows paths -> POSIX).
NORM_PATH="${FILE_PATH//\\//}"

# --- Check whether the path is inside docs/v<version>/ ---
# Match docs/v<num>(.<num>)*/ at any depth (relative or absolute path).
if [[ ! "$NORM_PATH" =~ (^|/)docs/v([0-9]+(\.[0-9]+){0,2})(/|$) ]]; then
  exit 0
fi
TARGET_VERSION="${BASH_REMATCH[2]}"

# --- Detect the active version by scanning docs/v*/ directories ---
# Walks upward from the current working directory to find the repo root that
# contains docs/. Falls back to the current directory if docs/ is found there.
find_docs_root() {
  local dir
  dir="$(pwd)"
  while [ "$dir" != "/" ] && [ -n "$dir" ]; do
    if [ -d "$dir/docs" ]; then
      echo "$dir/docs"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

DOCS_ROOT="$(find_docs_root || true)"
[ -n "${DOCS_ROOT:-}" ] || exit 0

# Numeric semver comparison: "1.2.3" > "0.9.7" etc.
# Returns 0 if $1 > $2, 1 otherwise.
semver_gt() {
  local a="$1" b="$2"
  local -a A B
  IFS=. read -ra A <<< "$a"
  IFS=. read -ra B <<< "$b"
  local i
  for ((i = 0; i < 3; i++)); do
    local av="${A[i]:-0}" bv="${B[i]:-0}"
    if [ "$av" -gt "$bv" ]; then return 0; fi
    if [ "$av" -lt "$bv" ]; then return 1; fi
  done
  return 1
}

ACTIVE_VERSION=""
for d in "$DOCS_ROOT"/v*; do
  [ -d "$d" ] || continue
  bn="$(basename "$d")"
  if [[ "$bn" =~ ^v([0-9]+(\.[0-9]+){0,2})$ ]]; then
    candidate="${BASH_REMATCH[1]}"
    if [ -z "$ACTIVE_VERSION" ]; then
      ACTIVE_VERSION="$candidate"
    elif semver_gt "$candidate" "$ACTIVE_VERSION"; then
      ACTIVE_VERSION="$candidate"
    fi
  fi
done

[ -n "$ACTIVE_VERSION" ] || exit 0

# Silent if target is the active version or newer.
if ! semver_gt "$ACTIVE_VERSION" "$TARGET_VERSION"; then
  exit 0
fi

# --- Emit warning ---
MSG="[old-version-docs-guard] Writing to historical version dir docs/v${TARGET_VERSION}/ (active is v${ACTIVE_VERSION}). Consider /refactor-docs to archive instead."

if [ "$_BLOCKING" = "block" ]; then
  echo -e "${COLOR_RED}${MSG}${COLOR_RESET}" >&2
  echo -e "${COLOR_RED}[old-version-docs-guard] Blocked by DEVAI_OLD_DOCS_GUARD=block. Set it to 'warn' or unset to bypass.${COLOR_RESET}" >&2
  exit 1
fi

echo -e "${COLOR_YELLOW}${MSG}${COLOR_RESET}" >&2
exit 0
