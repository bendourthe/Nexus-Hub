#!/usr/bin/env bash
# require-description.sh - PreToolUse Hook for Claude Code
# Advisory hook: reminds the model to describe Bash commands before execution.
#
# Preferred behavior (direct conversation):
#   Claude outputs a plain-text sentence in the chat BEFORE the tool call.
#   The sentence appears in regular font; the command appears in the approval dialog.
#
# Fallback behavior (subagents / automated contexts):
#   Claude includes "# ─── Description: ... ───" as the first line of the command.
#
# This hook warns (exit 0) when neither is detectable — it never blocks.
# It cannot detect preceding chat output, so it only checks for the comment fallback.
#
# Part of DevAI-Hub
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

# --- Check for description comment (both formats accepted) ---
# New format: # ─── Description: <text> ───
# Legacy format: # Description: <text>
if printf '%s' "$FIRST_LINE" | grep -qiE '^[[:space:]]*#.*description[[:space:]]*:'; then
  exit 0
fi

# --- Warn (advisory only — do not block) ---
MSG="ADVISORY: No description detected for this command.

Preferred: output a plain-text sentence in the chat BEFORE this tool call.
Fallback (subagents / automated contexts): add a description comment as line 1.

Fallback format:
  # ─── Description: <one sentence — what the command does and its impact> ───
  <your command>

Example:
  # ─── Description: Lists all agent config files under the project directory ───
  find /c/Users/BEDOURTHE/.claude -type f -name '*.md'"

# Send advisory to stdout (visible to the model) and stderr (visible in terminal)
printf '%s\n' "$MSG"
printf '%s\n' "$MSG" >&2

# Exit 0: allow the command to proceed
exit 0
