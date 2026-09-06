#!/usr/bin/env bash
# Session Summary - Stop / PreCompact / SessionEnd Hook for Claude Code
# Part of Nexus-Hub.
#
# Two jobs:
#   1. Append a one-line entry to ~/.claude/session-log.md (existing behavior).
#   2. Persist a compact, project-scoped context digest at
#      `.nexus/context/last-session.md` (relative to the git root, or cwd
#      when not in a repo) so the next SessionStart can read it back.
#
# The digest is the local-only reverse-engineered subset of ECC's
# memory-persistence pattern (legacy migration source: docs/archive/v2/v2.3/plans/adoption-ecc-cybersec-skills.md
# T007). It contains:
#   - Timestamp + project name + duration
#   - Active branch and short git status
#   - Last 5 commits (oneline)
#   - Files touched during the session (git diff HEAD)
#
# Runtime controls:
#   NEXUS_DISABLED_HOOKS=session-summary   skip both jobs
#   NEXUS_HOOK_PROFILE=minimal             skip both jobs
#   NEXUS_SESSION_DIGEST=off               skip digest write only
#   NEXUS_SESSION_DIGEST_PATH=<path>       override digest path (project-relative)

# Never fail loudly - always exit 0
trap 'exit 0' ERR

# --- Runtime Controls ---
_HOOK_NAME="session-summary"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

LOG_FILE="$HOME/.claude/session-log.md"

# --- Ensure log file exists with headers ---
if [ ! -f "$LOG_FILE" ]; then
  mkdir -p "$HOME/.claude" 2>/dev/null || true
  {
    echo "# Claude Code Session Log"
    echo ""
    echo "| Date | Project | Duration | Files Changed |"
    echo "|------|---------|----------|---------------|"
  } > "$LOG_FILE"
fi

# --- Gather data ---
TIMESTAMP=$(date "+%Y-%m-%d %H:%M" 2>/dev/null || echo "unknown")
PROJECT_NAME=$(basename "$(pwd)" 2>/dev/null || echo "unknown")

# Try to get duration from stdin JSON
INPUT=$(cat 2>/dev/null || true)
DURATION="N/A"
if [ -n "$INPUT" ] && command -v jq >/dev/null 2>&1; then
  PARSED_DURATION=$(echo "$INPUT" | jq -r '.session_duration // .duration // empty' 2>/dev/null)
  if [ -n "${PARSED_DURATION:-}" ]; then
    DURATION="$PARSED_DURATION"
  fi
fi

# Count files changed via git, and capture the file list for the digest
FILES_CHANGED="N/A"
CHANGED_FILES=""
if command -v git >/dev/null 2>&1; then
  DIFF_STAT=$(git diff --stat HEAD 2>/dev/null | tail -1)
  if [ -n "$DIFF_STAT" ]; then
    NUM_FILES=$(echo "$DIFF_STAT" | grep -o '[0-9]\+ file' | grep -o '[0-9]\+')
    if [ -n "$NUM_FILES" ]; then
      FILES_CHANGED="$NUM_FILES"
    fi
  else
    FILES_CHANGED="0"
  fi
  CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null | head -30 || true)
fi

# --- Append entry to global session log ---
echo "| $TIMESTAMP | $PROJECT_NAME | $DURATION | $FILES_CHANGED |" >> "$LOG_FILE"

# --- Write project-scoped context digest ---
if [[ "${NEXUS_SESSION_DIGEST:-on}" == "off" ]]; then
  exit 0
fi

# Project root: prefer git toplevel, fall back to cwd.
PROJECT_ROOT="$(pwd)"
if command -v git >/dev/null 2>&1; then
  GIT_TOPLEVEL=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [ -n "$GIT_TOPLEVEL" ]; then
    PROJECT_ROOT="$GIT_TOPLEVEL"
  fi
fi

DIGEST_REL="${NEXUS_SESSION_DIGEST_PATH:-.nexus/context/last-session.md}"
DIGEST_PATH="$PROJECT_ROOT/$DIGEST_REL"
DIGEST_DIR="$(dirname "$DIGEST_PATH")"

mkdir -p "$DIGEST_DIR" 2>/dev/null || exit 0

BRANCH="unknown"
GIT_STATUS_LINE="not a git repo"
RECENT_COMMITS=""
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  staged=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
  modified=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
  untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
  if [ "$staged" = "0" ] && [ "$modified" = "0" ] && [ "$untracked" = "0" ]; then
    GIT_STATUS_LINE="clean"
  else
    GIT_STATUS_LINE="${staged} staged, ${modified} modified, ${untracked} untracked"
  fi
  RECENT_COMMITS=$(git log --oneline -5 2>/dev/null || true)
fi

# Use a temp file + atomic rename so a partial write never leaves a corrupt digest.
TMP_DIGEST="$(mktemp "${DIGEST_DIR}/.last-session.XXXXXX" 2>/dev/null || echo "${DIGEST_PATH}.tmp.$$")"
{
  echo "# Last session digest"
  echo ""
  echo "Generated: $TIMESTAMP"
  echo "Project: $PROJECT_NAME"
  echo "Duration: $DURATION"
  echo ""
  echo "## Git context"
  echo ""
  echo "- Branch: \`$BRANCH\`"
  echo "- Status: $GIT_STATUS_LINE"
  echo ""
  if [ -n "$RECENT_COMMITS" ]; then
    echo "## Recent commits"
    echo ""
    echo '```'
    echo "$RECENT_COMMITS"
    echo '```'
    echo ""
  fi
  if [ -n "$CHANGED_FILES" ]; then
    echo "## Files touched this session"
    echo ""
    echo '```'
    echo "$CHANGED_FILES"
    echo '```'
    echo ""
  fi
} > "$TMP_DIGEST" 2>/dev/null || { rm -f "$TMP_DIGEST" 2>/dev/null; exit 0; }
mv -f "$TMP_DIGEST" "$DIGEST_PATH" 2>/dev/null || true

exit 0
