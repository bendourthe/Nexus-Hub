#!/usr/bin/env bash
# require-description.sh - PreToolUse Hook for Claude Code
# Blocks Bash commands that lack a description.
#
# Accepts EITHER of these as proof that a description exists:
#   1. A non-empty "description" field in the tool input JSON
#   2. A bordered description block at the top of the command
#      (legacy format, still accepted for backwards compatibility)
#
# The format-bash-description.py hook (which runs before this hook)
# only adds the description box to commands that are NOT in the
# auto-approve allow list. Auto-approved commands carry their
# description in the "description" field instead.
#
# This hook blocks (exit 2) when neither is present.
#
# Part of DevAI-Hub

set -euo pipefail

# --- Read JSON from stdin ---
INPUT=$(cat)

# --- Extract description field ---
if command -v jq >/dev/null 2>&1; then
  DESCRIPTION=$(echo "$INPUT" | jq -r '.tool_input.description // empty' 2>/dev/null)
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
else
  # Fallback: basic JSON extraction via grep/sed
  DESCRIPTION=$(echo "$INPUT" | grep -o '"description"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"description"[[:space:]]*:[[:space:]]*"//;s/"$//')
  COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi

# --- Check 1: Non-empty description field ---
if [ -n "${DESCRIPTION:-}" ]; then
  exit 0
fi

# --- Check 2: Description block in command (legacy / non-allowed commands) ---
if [ -n "${COMMAND:-}" ]; then
  FIRST_LINE=$(printf '%s' "$COMMAND" | sed '/^[[:space:]]*$/d' | head -1)
  if printf '%s' "$FIRST_LINE" | grep -qi '^[[:space:]]*#.*Description'; then
    exit 0
  fi
fi

# --- Block and instruct the model to provide a description ---
MSG="BLOCKED: Missing required description.

Every Bash command must include a description. Provide it as the
\"description\" parameter in the Bash tool call (plain text, one
sentence or short paragraph). The format-bash-description.py hook
formats it automatically.

Alternatively, the command may begin with a bordered description block:

  # ================================ Description ================================ #
  # Lists all agent config files under the project directory                      #
  # ============================================================================= #
  find ~/.claude -type f -name '*.md'

Add a description, then retry."

printf '%s\n' "$MSG"
printf '%s\n' "$MSG" >&2

exit 2
