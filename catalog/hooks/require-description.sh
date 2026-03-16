#!/usr/bin/env bash
# require-description.sh - PreToolUse Hook for Claude Code
# Requires every Bash command to begin with a "# Description: ..." comment.
# The comment is visible in the approval dialog and documents intent before execution.
#
# How it works:
#   Claude Code pipes JSON to stdin before each Bash tool call.
#   This script extracts the command, checks that the first non-empty
#   line is a "# Description:" comment, and exits 0 (allow) or 2 (block).
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

# --- Check for # Description: prefix (case-insensitive) ---
if printf '%s' "$FIRST_LINE" | grep -qiE '^[[:space:]]*#[[:space:]]*description[[:space:]]*:'; then
  exit 0
fi

# --- Block and instruct the model to reformat ---
MSG="BLOCKED: Missing required description comment.

Every Bash command must start with a '# Description:' comment as its first line.
This comment is visible in the approval dialog and documents intent before execution.
Bash ignores lines starting with # so the comment has no runtime effect.

Format:
  # Description: <one sentence — what the command does and its impact>
  <your command>

Example:
  # Description: Lists all agent config files under the project directory
  find /c/Users/BEDOURTHE/.claude -type f -name '*.md'

Rewrite your command with this comment as line 1, then retry."

# Send to stdout so the model receives the blocking reason and can retry
printf '%s\n' "$MSG"
# Also send to stderr so the user sees it in the terminal
printf '%s\n' "$MSG" >&2

exit 2
