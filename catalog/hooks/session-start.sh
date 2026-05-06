#!/usr/bin/env bash
# session-start.sh - SessionStart hook for DevAI-Hub
# Injects a brief catalog orientation at the start of every new Claude Code session.
# Keeps output under 200 tokens to avoid context overhead.
set -euo pipefail

SKILL_COUNT=184
COMMAND_COUNT=32

cat <<EOF
DevAI-Hub is active (v1.1.1) - $SKILL_COUNT skills, $COMMAND_COUNT commands.

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
