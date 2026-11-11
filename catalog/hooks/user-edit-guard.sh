#!/usr/bin/env bash
# User Edit Guard - PreToolUse and PostToolUse Hook
# Stops an agent from overwriting a file the user changed since the agent last
# read or wrote it.
# Part of Nexus-Hub
#
# How it works:
#   A thin adapter over the user-edit-preservation skill's edit_guard.py
#   (`edit_guard.py hook`), which makes every decision and prints every message,
#   so this script and user-edit-guard.ps1 behave identically.
#   PreToolUse on Write, Edit, and Bash: a change onto an existing file that
#   changed since the agent's last record, or was never recorded, exits 2
#   outside a git worktree and warns inside one. Bash destinations come from
#   cp, mv, Copy-Item, Move-Item, shutil.copy, and > redirection.
#   PostToolUse on Read, Write, Edit, and Bash: records the file (and, after a
#   Bash command, every tracked file it touched) so the agent's own changes
#   never read as the user's.
#
# Budget: edit_guard.py gets 2 seconds (NEXUS_EDIT_GUARD_TIMEOUT_SECONDS). When
# Python or the helper is unavailable, or the budget runs out, a payload that
# looks like a write is blocked outside a git worktree and warned inside one;
# it is never passed silently outside a worktree.
#
# Essential: stays on under NEXUS_HOOK_PROFILE=minimal. Disable through the
# user's NEXUS_DISABLED_HOOKS=user-edit-guard or Settings protect_user_edits=false.

set -euo pipefail

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
if _nexus_guardrail_disabled protect_user_edits; then exit 0; fi

_HOOK_NAME="user-edit-guard"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: user-edit-guard]"
# Print the tag and the message to stderr; every further argument is a
# continuation line printed as is.
_nexus_msg() {
  local line
  printf '%s %s\n' "$_NEXUS_TAG" "$1" >&2
  shift
  for line in "$@"; do printf '%s\n' "$line" >&2; done
}

if [ -t 0 ]; then exit 0; fi
INPUT="$(cat)"
if [ -z "$INPUT" ]; then exit 0; fi

# Nexus Settings guard switches apply in every host permission mode.
_HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_BUDGET="${NEXUS_EDIT_GUARD_TIMEOUT_SECONDS:-2}"

_find_helper() {
  local candidate
  for candidate in \
    "${NEXUS_EDIT_GUARD_SCRIPT:-}" \
    "$_HOOK_DIR/../skills/user-edit-preservation/scripts/edit_guard.py" \
    "$_HOOK_DIR/../skills/workflow/user-edit-preservation/scripts/edit_guard.py" \
    "$_HOOK_DIR/../../.agents/skills/user-edit-preservation/scripts/edit_guard.py" \
    "$HOME/.claude/skills/user-edit-preservation/scripts/edit_guard.py" \
    "$HOME/.agents/skills/user-edit-preservation/scripts/edit_guard.py"; do
    if [ -n "$candidate" ] && [ -f "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

_find_python() {
  local candidate path
  for candidate in python3 python; do
    path="$(command -v "$candidate" 2>/dev/null || true)"
    [ -n "$path" ] || continue
    # Under WindowsApps sits either a Store-installed Python or the alias that only
    # opens the Store; probe it once so the alias is never mistaken for Python.
    if [[ "$path" == *WindowsApps* ]] && ! "$candidate" -c "import sys" >/dev/null 2>&1; then continue; fi
    printf '%s' "$candidate"
    return 0
  done
  return 1
}

_fallback() {
  # Python could not decide: $1 names why. Post steps and non-writing payloads pass.
  if printf '%s' "$INPUT" | grep -qE '"hook_event_name"[[:space:]]*:[[:space:]]*"PostToolUse"'; then exit 0; fi
  if ! printf '%s' "$INPUT" | grep -qE '"tool_name"[[:space:]]*:[[:space:]]*"(Write|Edit|MultiEdit|NotebookEdit)"|(^|[^A-Za-z])(cp|mv|Copy-Item|Move-Item)[[:space:]]|shutil\.(copy|move)|>'; then
    exit 0
  fi
  local message="Cannot verify this file against your last read or write ($1). Stop and ask the user before overwriting it (user-edit-preservation)."
  if [ "$(git rev-parse --is-inside-work-tree 2>/dev/null || true)" = "true" ]; then
    _nexus_msg "WARNING (git worktree, not blocked): $message"
    exit 0
  fi
  _nexus_msg "BLOCKED: $message" "Only the user may turn this check off, with NEXUS_DISABLED_HOOKS=$_HOOK_NAME."
  exit 2
}

HELPER="$(_find_helper)" || _fallback "edit_guard.py not found"
PYTHON="$(_find_python)" || _fallback "Python not found"

export PYTHONIOENCODING=utf-8
status=0
if command -v timeout >/dev/null 2>&1; then
  printf '%s' "$INPUT" | timeout "$_BUDGET" "$PYTHON" "$HELPER" hook || status=$?
else
  printf '%s' "$INPUT" | "$PYTHON" "$HELPER" hook || status=$?
fi

case "$status" in
  0) exit 0 ;;
  2)
    exit 2
    ;;
  124) _fallback "the ${_BUDGET}-second budget ran out" ;;
  *) _fallback "edit_guard.py failed" ;;
esac
