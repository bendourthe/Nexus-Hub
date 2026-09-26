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
# Essential: stays on under NEXUS_HOOK_PROFILE=minimal. The only switch is the
# user's own NEXUS_DISABLED_HOOKS=user-edit-guard.

set -euo pipefail

_HOOK_NAME="user-edit-guard"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi

if [ -t 0 ]; then exit 0; fi
INPUT="$(cat)"
if [ -z "$INPUT" ]; then exit 0; fi

_HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_BUDGET="${NEXUS_EDIT_GUARD_TIMEOUT_SECONDS:-2}"

_find_helper() {
  local candidate
  for candidate in \
    "${NEXUS_EDIT_GUARD_SCRIPT:-}" \
    "$_HOOK_DIR/../skills/user-edit-preservation/scripts/edit_guard.py" \
    "$_HOOK_DIR/../skills/workflow/user-edit-preservation/scripts/edit_guard.py" \
    "$HOME/.claude/skills/user-edit-preservation/scripts/edit_guard.py"; do
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
    echo "[$_HOOK_NAME] WARNING (git worktree, not blocked): $message" >&2
    exit 0
  fi
  echo "[$_HOOK_NAME] BLOCKED: $message" >&2
  echo "Only the user may turn this check off, with NEXUS_DISABLED_HOOKS=$_HOOK_NAME." >&2
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
  0|2) exit "$status" ;;
  124) _fallback "the ${_BUDGET}-second budget ran out" ;;
  *) _fallback "edit_guard.py failed" ;;
esac
