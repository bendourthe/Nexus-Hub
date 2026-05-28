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

SKILL_COUNT=184
COMMAND_COUNT=33

cat <<EOF
Nexus-Hub is active (v1.1.5) - $SKILL_COUNT skills, $COMMAND_COUNT commands.

Quick navigation:
  /search-skills <keyword>   Find the right skill for your task
  /commands-cheatsheet       List all available commands

Full index: data/SKILL_INDEX.md
EOF

# Git context -- only if inside a git repo
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  staged=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
  modified=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
  untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')

  if [ "$staged" = "0" ] && [ "$modified" = "0" ] && [ "$untracked" = "0" ]; then
    status_line="clean"
  else
    status_line="${staged} staged, ${modified} modified, ${untracked} untracked"
  fi

  echo ""
  echo "Git context:"
  printf "  Branch:  %s\n" "$branch"
  printf "  Status:  %s\n" "$status_line"
  echo "  Recent commits:"
  git log --oneline -3 2>/dev/null | sed 's/^/    /' || true
fi

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
    echo ""
    echo "Last session digest ($DIGEST_REL, capped at $MAX_CHARS chars):"
    echo ""
    printf '%s\n' "$digest_content"
    # If we truncated, note it so the agent can decide whether to read the full file.
    digest_size=$(wc -c < "$DIGEST_PATH" 2>/dev/null | tr -d ' ' || echo 0)
    if [ -n "$digest_size" ] && [ "$digest_size" -gt "$MAX_CHARS" ]; then
      echo ""
      echo "(digest truncated -- read $DIGEST_REL for the full file)"
    fi
  fi
fi

exit 0
