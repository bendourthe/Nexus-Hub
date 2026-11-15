#!/usr/bin/env bash
# Old Version Docs Guard - PreToolUse Hook for Claude Code
# Warns when Write or Edit targets a historical version-bound docs path.
# Part of Nexus-Hub
#
# How it works:
#   Claude Code pipes JSON to stdin before each Write/Edit tool call.
#   This script extracts the file path, detects whether it lives inside
#   a recognized release directory older than the active version, and
#   emits an advisory warning to stderr if so.
#
#   Non-blocking by default (always exits 0). Set NEXUS_OLD_DOCS_GUARD=block
#   to upgrade to a hard block (exit 1).
#
# Active-version detection:
#   1. Latest canonical docs/releases/v*/v*/ directory by semantic version.
#   2. Otherwise, the first populated legacy layout: v-bucket, flat, versions.
#   3. If no recognized version directories exist, the hook is a no-op.
#
# Companion command: /refactor-docs proposes structured archival of historical
# version dirs instead of ad-hoc edits.

set -euo pipefail

# Never fail loudly on internal errors - always exit 0 unless blocking.
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name:           export NEXUS_DISABLED_HOOKS=old-version-docs-guard
# Skip all non-essential:    export NEXUS_HOOK_PROFILE=minimal
# Upgrade warning to block:  export NEXUS_OLD_DOCS_GUARD=block
_HOOK_NAME="old-version-docs-guard"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

_BLOCKING="${NEXUS_OLD_DOCS_GUARD:-warn}"

# --- ANSI colors ---
COLOR_YELLOW='\033[0;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: old-version-docs-guard]"
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

# --- Extract file path ---
# jq is preferred, but a host without it must not silently lose the guard: a
# hook whose failure mode is silence is indistinguishable from one that passed.
# Python 3 is the fallback because every supported platform already requires it.
if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)
elif command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
  _PY=$(command -v python3 || command -v python)
  FILE_PATH=$(printf '%s' "$INPUT" | "$_PY" -c 'import json,sys
try:
    d = json.load(sys.stdin).get("tool_input") or {}
    print(d.get("file_path") or d.get("path") or "")
except Exception:
    print("")' 2>/dev/null)
else
  exit 0
fi

[ -n "${FILE_PATH:-}" ] || exit 0

# Normalize separators (Windows paths -> POSIX).
NORM_PATH="${FILE_PATH//\\//}"

# --- Resolve the target version across canonical and legacy layouts ---
TARGET_VERSION=""
if [[ "$NORM_PATH" =~ (^|/)docs/(releases|archives)/v[0-9]+/v([0-9]+(\.[0-9]+){1,2})(/|$) ]]; then
  TARGET_VERSION="${BASH_REMATCH[3]}"
elif [[ "$NORM_PATH" =~ (^|/)docs/(archive/)?v[0-9]+/v([0-9]+(\.[0-9]+){1,2})(/|$) ]]; then
  TARGET_VERSION="${BASH_REMATCH[3]}"
elif [[ "$NORM_PATH" =~ (^|/)docs/(archive/)?versions/v[0-9]+/v([0-9]+(\.[0-9]+){1,2})(/|$) ]]; then
  TARGET_VERSION="${BASH_REMATCH[3]}"
elif [[ "$NORM_PATH" =~ (^|/)docs/(archive/)?v([0-9]+\.[0-9]+\.[0-9]+)(/|$) ]]; then
  TARGET_VERSION="${BASH_REMATCH[3]}"
else
  exit 0
fi

# --- Detect the active version from the resolved active container ---
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
scan_version_dirs() {
  local required_pattern="$1"
  shift
  local d bn candidate
  for d in "$@"; do
    [ -d "$d" ] || continue
    bn="$(basename "$d")"
    if [[ "$bn" =~ $required_pattern ]]; then
      candidate="${BASH_REMATCH[1]}"
      if [ -z "$ACTIVE_VERSION" ] || semver_gt "$candidate" "$ACTIVE_VERSION"; then
        ACTIVE_VERSION="$candidate"
      fi
    fi
  done
}

# Prefer the DECLARED project version over the newest directory on disk. A
# repository that keeps directories for roadmapped future work would otherwise
# resolve its active version to the furthest-future plan directory, making every
# write to the version actually being built warn while writes to future
# directories stayed silent -- fail-open and noisy at once.
_declared_version() {
  local manifest="$1"
  [ -f "$manifest" ] || return 1
  sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([0-9][0-9]*\.[0-9][0-9]*\)[^"]*".*/\1/p' "$manifest" | head -n 1
}
ACTIVE_VERSION="$(_declared_version "${DOCS_ROOT}/../.claude-plugin/plugin.json" || true)"

# Match the docs-layout-refactor resolution order. Once one layout yields an
# active candidate, later legacy layouts cannot override it.
[ -n "$ACTIVE_VERSION" ] ||
scan_version_dirs '^v([0-9]+(\.[0-9]+){1,2})$' "$DOCS_ROOT"/releases/v*/v*
if [ -z "$ACTIVE_VERSION" ]; then
  scan_version_dirs '^v([0-9]+(\.[0-9]+){1,2})$' "$DOCS_ROOT"/v*/v*
fi
if [ -z "$ACTIVE_VERSION" ]; then
  scan_version_dirs '^v([0-9]+\.[0-9]+\.[0-9]+)$' "$DOCS_ROOT"/v*
fi
if [ -z "$ACTIVE_VERSION" ]; then
  scan_version_dirs '^v([0-9]+(\.[0-9]+){1,2})$' "$DOCS_ROOT"/versions/v*/v*
fi

[ -n "$ACTIVE_VERSION" ] || exit 0

# Silent if target is the active version or newer.
if ! semver_gt "$ACTIVE_VERSION" "$TARGET_VERSION"; then
  exit 0
fi

# --- Emit warning ---
MSG="Writing to historical version v${TARGET_VERSION} under $(_nexus_esc "$NORM_PATH") (active is v${ACTIVE_VERSION}). Consider /update refactor to archive instead."

if [ "$_BLOCKING" = "block" ]; then
  _nexus_msg "$COLOR_RED" "$MSG"
  _nexus_msg "$COLOR_RED" "Blocked by NEXUS_OLD_DOCS_GUARD=block. Set it to 'warn' or unset to bypass."
  exit 1
fi

_nexus_msg "$COLOR_YELLOW" "$MSG"
exit 0
