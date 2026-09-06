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
#
# Limitation (read this before trusting it): these are fixed regexes matched
# against the RAW command string, not an argv decomposition. Quoting, unusual
# spacing, environment indirection, and equivalent alternate flags can all evade
# them, and a flag nobody listed will pass silently. This hook is
# defense-in-depth, NOT a boundary. See the "Limits and Honest Boundaries"
# section of catalog/skills/security-operations/agentic-endpoint-hardening/SKILL.md.

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
  # Execution indirection via git metadata (group B of the canonical
  # execution-trigger surface list). Both settings name something git EXECUTES on
  # ordinary operations, so writing either turns a routine git command into
  # arbitrary code execution. The leading `(-c\s+\S+\s+)*` tolerates other -c
  # options appearing first, so interleaving them is not an evasion.
  'git\s+(-c\s+\S+\s+)*-c\s*core\.hooksPath\s*=:::Redirects git hooks to an agent-chosen directory, so a later git operation executes it'
  'git\s+(-c\s+\S+\s+)*-c\s*core\.fsmonitor\s*=:::Sets the filesystem-monitor command git runs on ordinary operations, which is arbitrary execution'
)

# --- Read JSON from stdin ---
INPUT=$(cat)

# Extract the command from tool_input.command
# The `|| true` on both branches is load-bearing under `set -euo pipefail`: a
# grep that matches nothing, or jq on a malformed payload, returns non-zero, and a
# failing command substitution in an assignment ABORTS the script with exit 1
# instead of reaching the allow path below. Without it this hook exited 1 on any
# payload carrying no command (empty, malformed, or a non-Bash tool call).
if command -v jq >/dev/null 2>&1; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)
else
  # Fallback: basic JSON extraction via grep/sed
  COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//' || true)
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

# --- Persistent execution-indirection guard (group B, `git config` form) ---
# core.hooksPath and core.fsmonitor are reachable two ways: inline for a single
# invocation (`git -c key=value ...`, caught by the pattern list above) and
# PERSISTENTLY via `git config`, which writes the value into .git/config so it
# applies to every later operation. The persistent form needs its own check
# because a read of the same key is harmless: `git config --get core.hooksPath`
# only inspects, so matching the key alone would false-positive on a diagnostic
# command. Flag the write forms and let the read forms through.
if echo "$COMMAND" | grep -qE '(^|[;&|]|[[:space:]])git([[:space:]]|$).*config' \
   && echo "$COMMAND" | grep -qE 'core\.(hooksPath|fsmonitor)' \
   && ! echo "$COMMAND" | grep -qE '\-\-(get|get-all|get-regexp|get-urlmatch|list|unset|unset-all)([[:space:]]|=|$)'; then
  echo "BLOCKED: '$COMMAND' persists a git execution-indirection setting (core.hooksPath / core.fsmonitor). Git executes the named directory or command on ordinary operations, so this turns a later routine git call into arbitrary execution. The user has prevented you from doing this." >&2
  exit 2
fi

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
