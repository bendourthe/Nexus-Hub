#!/usr/bin/env bash
# require-powershell-description.sh - PreToolUse Hook for Claude Code
# Blocks PowerShell commands that lack a description.
#
# Accepts EITHER of these as proof that a description exists:
#   1. A non-empty "description" field in the tool input JSON
#   2. A description comment at the top of the command
#      (matches the new "# Description: ..." prefix and the legacy
#      bordered block; both are kept for backwards compatibility)
#
# The format-powershell-description.py hook (which runs before this
# hook) only adds the description prefix to commands that are NOT in
# the auto-approve allow list. Auto-approved commands carry their
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

# --- Check 2: Description comment in command (legacy / non-allowed commands) ---
# Matches both the new "# Description: ..." prefix and the legacy
# "# ===== Description ===== #" box header (case-insensitive via -i).
# The regex alternation accepts "desc:" too so any session formatted
# with the v1.2.1-rc "# desc:" prefix (a brief intermediate shape)
# still satisfies the check.
if [ -n "${COMMAND:-}" ]; then
  FIRST_LINE=$(printf '%s' "$COMMAND" | sed '/^[[:space:]]*$/d' | head -1)
  if printf '%s' "$FIRST_LINE" | grep -qi '^[[:space:]]*#.*\(desc:\|description\)'; then
    exit 0
  fi
fi

# --- Block and instruct the model to provide a description ---
MSG="BLOCKED: Missing required description.

Every PowerShell command must include a description. Provide it as the
\"description\" parameter in the PowerShell tool call (plain text, one
sentence, <=120 chars, no newlines). The format-powershell-description.py
hook formats it automatically.

Alternatively, the command may begin with a single-line description
prefix:

  # Description: Lists running processes whose name matches a pattern
  # ---
  Get-Process | Where-Object Name -like 'explorer*'

Add a description, then retry."

printf '%s\n' "$MSG"
printf '%s\n' "$MSG" >&2

exit 2
