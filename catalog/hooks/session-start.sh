#!/usr/bin/env bash
# session-start.sh — SessionStart hook for DevAI-Hub
# Injects a brief catalog orientation at the start of every new Claude Code session.
# Keeps output under 200 tokens to avoid context overhead.
set -euo pipefail

SKILL_COUNT=183
COMMAND_COUNT=32

cat <<EOF
DevAI-Hub is active (v0.9.2) — $SKILL_COUNT skills, $COMMAND_COUNT commands.

Quick navigation:
  /search-skills <keyword>   Find the right skill for your task
  /commands_cheatsheet       List all available commands

Full index: data/SKILL_INDEX.md
EOF
