#!/usr/bin/env bash
# Git Guardrails - PreToolUse Hook for Claude Code
# Blocks dangerous git commands before execution.
# Part of Nexus-Hub
#
# How it works:
#   Claude Code pipes JSON to stdin before each Bash tool call.
#   This script extracts the command, checks it against dangerous
#   patterns, and exits 2 (block) or 0 (allow).
#
# To customize: edit the DANGEROUS_PATTERNS array below.
# Format: "regex_pattern:::Human-readable description"

set -euo pipefail

# --- Dangerous patterns ---
# Each line: "extended_regex:::description"
DANGEROUS_PATTERNS=(
  'git\s+push\s+.*--force:::Force push overwrites remote history'
  'git\s+push\s+-[a-zA-Z]*f:::Force push overwrites remote history'
  'git\s+push\s+.*--force-with-lease:::Force-with-lease push overwrites remote history'
  'git\s+reset\s+--hard:::Hard reset discards all uncommitted work'
  'git\s+clean\s+-[a-zA-Z]*f:::Clean -f permanently deletes untracked files'
  'git\s+branch\s+-D:::Force-delete branch without merge check'
  'git\s+checkout\s+\.:::Discards all working tree changes'
  'git\s+checkout\s+--\s+\.:::Discards all working tree changes'
  'git\s+restore\s+\.:::Discards all working tree changes'
  'git\s+stash\s+drop:::Permanently loses stashed work'
  'git\s+stash\s+clear:::Permanently loses all stashed work'
  'rm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+\.git:::Destroys the entire repository'
)

# --- Read JSON from stdin ---
INPUT=$(cat)

# Extract the command from tool_input.command
if command -v jq >/dev/null 2>&1; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
else
  # Fallback: basic JSON extraction via grep/sed
  COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi

# If we couldn't extract a command, allow (don't block non-Bash tools)
if [ -z "${COMMAND:-}" ]; then
  exit 0
fi

# --- Check command against each pattern ---
for entry in "${DANGEROUS_PATTERNS[@]}"; do
  PATTERN="${entry%%:::*}"
  DESC="${entry##*:::}"

  if echo "$COMMAND" | grep -qE "$PATTERN"; then
    echo "BLOCKED: '$COMMAND' matches dangerous git pattern. $DESC. The user has prevented you from doing this." >&2
    exit 2
  fi
done

# --- Protected-branch guard (opt-in via NEXUS_PROTECTED_BRANCHES) ---
# When a project declares protected (release-only) branches, block a direct
# `git commit` on them so feature/version work goes through a feature branch.
# Inert by default: does nothing unless NEXUS_PROTECTED_BRANCHES is set.
#   Configure : NEXUS_PROTECTED_BRANCHES="main develop"   (space- or comma-separated)
#   Override  : NEXUS_PROTECTED_BRANCH_ALLOW=1            (allow one legitimate commit)
# Targets `git commit` only -- release merges (`git merge --no-ff` on the
# protected branch) and pushes are intentionally NOT blocked.
if [ -n "${NEXUS_PROTECTED_BRANCHES:-}" ] \
   && [ "${NEXUS_PROTECTED_BRANCH_ALLOW:-0}" != "1" ] \
   && echo "$COMMAND" | grep -qE '(^|[;&|]|[[:space:]])git[[:space:]]+commit([[:space:]]|$)'; then
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
  if [ -n "$CURRENT_BRANCH" ]; then
    PROTECTED_LIST=$(echo "${NEXUS_PROTECTED_BRANCHES}" | tr ',' ' ')
    for b in $PROTECTED_LIST; do
      if [ "$b" = "$CURRENT_BRANCH" ]; then
        echo "BLOCKED: direct commit to protected branch '${CURRENT_BRANCH}'. Branch off the integration branch first (e.g. 'git checkout -b feat/<slug>') and commit there; the protected branch receives release merges only. To allow this one commit, set NEXUS_PROTECTED_BRANCH_ALLOW=1." >&2
        exit 2
      fi
    done
  fi
fi

# Command is safe
exit 0
