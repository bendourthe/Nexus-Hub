#!/usr/bin/env bash
# require-description.sh - PreToolUse Hook for Claude Code
# Blocks Bash commands that lack a description block.
#
# Preferred behavior (direct conversation):
#   Claude outputs a plain-text sentence in the chat BEFORE the tool call,
#   AND prefixes the command with the bordered description block.
#
# Required behavior (all contexts including subagents):
#   The command must begin with a bordered description block:
#     # ------------------------------------- Description ------------------------------------- #
#     # <one sentence>
#     # --------------------------------------------------------------------------------------- #
#
# This hook blocks (exit 2) when no description block is detected.
#
# Part of DevAI-Hub

set -euo pipefail

# --- Read JSON from stdin ---
INPUT=$(cat)

# --- Extract command field ---
if command -v jq >/dev/null 2>&1; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
else
  # Fallback: basic JSON extraction via grep/sed (no embedded newlines)
  COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi

# If command could not be extracted, allow (do not block non-Bash calls)
if [ -z "${COMMAND:-}" ]; then
  exit 0
fi

# --- Strip leading blank lines to find the first real line ---
FIRST_LINE=$(printf '%s' "$COMMAND" | sed '/^[[:space:]]*$/d' | head -1)

# --- Check for description block (all accepted formats) ---
# New bordered format:  # ------------------------------------- Description ------------------------------------- #
# Legacy single-line:   # ─── Description: <text> ───
# Legacy plain:         # Description: <text>
if printf '%s' "$FIRST_LINE" | grep -qi '^[[:space:]]*#.*Description'; then
  exit 0
fi

# --- Block and instruct the model to reformat ---
MSG="BLOCKED: Missing required description block.

Every Bash command must begin with a bordered description block.
This block is visible in the approval dialog and documents intent before execution.
Bash ignores lines starting with # so the block has no runtime effect.

Format:
  # ------------------------------------- Description ------------------------------------- #
  # <one sentence — what the command does and its impact>
  # --------------------------------------------------------------------------------------- #
  <your command>

Example:
  # ------------------------------------- Description ------------------------------------- #
  # Lists all agent config files under the project directory
  # --------------------------------------------------------------------------------------- #
  find /c/Users/BEDOURTHE/.claude -type f -name '*.md'

Rewrite your command with this block as the first 3 lines, then retry."

# Send to stdout so the model receives the blocking reason and can retry
printf '%s\n' "$MSG"
# Also send to stderr so the user sees it in the terminal
printf '%s\n' "$MSG" >&2

exit 2
