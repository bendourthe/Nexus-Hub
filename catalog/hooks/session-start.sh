#!/usr/bin/env bash
# session-start.sh - SessionStart hook for Nexus-Hub
# Injects a brief catalog orientation at the start of every new Claude Code session,
# then (if present) surfaces the project-scoped digest of the previous session
# written by session-summary.sh on Stop / PreCompact / SessionEnd.
#
# Runtime controls:
#   NEXUS_DISABLED_HOOKS=session-start         skip this hook entirely
#   NEXUS_HOOK_PROFILE=minimal                 skip this hook entirely
#   NEXUS_SESSION_DIGEST=off                   skip digest read only
#   NEXUS_SESSION_DIGEST_PATH=<path>           override digest path (project-relative)
#   NEXUS_SESSION_START_MAX_CHARS=<int>        cap digest output (default 8000)
set -euo pipefail

_HOOK_NAME="session-start"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: session-start]"
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
# Print the tag and the message to stdout (SessionStart context the agent
# reads); every further argument is a continuation line printed as is.
_nexus_msg() {
  local line
  printf '%s %s\n' "$_NEXUS_TAG" "$1"
  shift
  for line in "$@"; do printf '%s\n' "$line"; done
}

# Banner: one line, facts read from real files only (v4.13.3). The version is
# printed only when VERSION holds one bounded semver line; any other payload
# (missing, empty, multi-line, over 32 characters) drops the version and never
# echoes the file. Version and index path come from the same resolved home.
HOME_DIR="${NEXUS_HOME:-$HOME/.nexus-hub}"
_version=""
if [ -f "$HOME_DIR/VERSION" ]; then
  _raw=$(head -c 64 "$HOME_DIR/VERSION" 2>/dev/null || true)
  _raw="${_raw%$'\r'}"
  if [[ "$_raw" != *$'\n'* ]] && [ "${#_raw}" -le 32 ] \
     && [[ "$_raw" =~ ^[0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.]+)?$ ]]; then
    _version="$_raw"
  fi
fi
if [ -n "$_version" ]; then
  _banner="Nexus-Hub v$_version active; full skill index: $(_nexus_esc "$HOME_DIR")/data/SKILL_INDEX.md"
else
  _banner="Nexus-Hub active; full skill index: $(_nexus_esc "$HOME_DIR")/data/SKILL_INDEX.md"
fi

# Git: one line. The harness already supplies branch and recent commits.
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  _branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "detached")
  _changed=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  _git_line="Git: $(_nexus_esc "$_branch"), $_changed changed file(s)"
else
  _git_line="Git: unavailable"
fi
_nexus_msg "$_banner" "$_git_line"

# --- Surface the last-session digest (memory-persistence subset) ---
if [[ "${NEXUS_SESSION_DIGEST:-on}" == "off" ]]; then
  exit 0
fi

PROJECT_ROOT="$(pwd)"
if command -v git >/dev/null 2>&1; then
  GIT_TOPLEVEL=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [ -n "$GIT_TOPLEVEL" ]; then
    PROJECT_ROOT="$GIT_TOPLEVEL"
  fi
fi

DIGEST_REL="${NEXUS_SESSION_DIGEST_PATH:-.nexus/context/last-session.md}"
DIGEST_PATH="$PROJECT_ROOT/$DIGEST_REL"

if [ -f "$DIGEST_PATH" ]; then
  MAX_CHARS="${NEXUS_SESSION_START_MAX_CHARS:-8000}"
  # Sanity-check the cap; fall back to default if it isn't a positive integer.
  if ! [[ "$MAX_CHARS" =~ ^[0-9]+$ ]] || [ "$MAX_CHARS" -le 0 ]; then
    MAX_CHARS=8000
  fi
  digest_content=$(head -c "$MAX_CHARS" "$DIGEST_PATH" 2>/dev/null || true)
  if [ -n "$digest_content" ]; then
    # If we truncated, note it so the agent can decide whether to read the full file.
    digest_size=$(wc -c < "$DIGEST_PATH" 2>/dev/null | tr -d ' ' || echo 0)
    _digest_rel=$(_nexus_esc "$DIGEST_REL")
    printf '\n'  # nexus: hook-msg-exempt blank separator before the digest
    if [ -n "$digest_size" ] && [ "$digest_size" -gt "$MAX_CHARS" ]; then
      _nexus_msg "Last session digest ($_digest_rel, capped at $MAX_CHARS chars):" "" "$digest_content" "" \
        "(digest truncated -- read $_digest_rel for the full file)"
    else
      _nexus_msg "Last session digest ($_digest_rel, capped at $MAX_CHARS chars):" "" "$digest_content"
    fi
  fi
fi

exit 0
