#!/usr/bin/env bash
# compress-output.sh - PreToolUse Hook for Claude Code (Nexus-Hub).
# Pipes a Bash command's stdout through the internal nexus-context-compressor
# engine before it enters the context window, the same hook point the external
# `rtk` binary used. The deterministic engine compresses structured output (JSON
# arrays, code); logs and prose pass through unchanged. Dropped spans are
# persisted to a local CCR store so the agent can fetch them back via the
# `context_retrieve` MCP tool -- compression is non-lossy.
#
# How it works:
#   Claude Code pipes JSON to stdin before each Bash tool call. This script
#   reads the proposed command and, when compression is enabled and the engine
#   is importable, emits a PreToolUse `updatedInput` that wraps the command so
#   its stdout is piped through `python -m nexus_context_compressor compress`.
#   The original exit status is preserved via ${PIPESTATUS[0]}; stderr is left
#   untouched. The compressor CLI is itself fail-open (it returns the original
#   text on any internal error), and this hook never rewrites unless the engine
#   imports cleanly, so a command's output can never be lost.
#
# Opt-in (default OFF):
#   export NEXUS_CONTEXT_COMPRESS=1     # enable output compression
# Disable for one command:
#   NEXUS_CONTEXT_COMPRESS=0 <command>
#
# Windows: hooks require a Unix shell. On Windows, Claude Code uses the
#   CLAUDE.md-injected instruction block instead (see guides/RTK_CONTEXT_COMPRESSION.md),
#   which tells the agent to pipe noisy structured output through
#   `python -m nexus_context_compressor compress` explicitly.
#
# Requires `jq` for the rewrite (to safely splice the new command into
# tool_input); without it the hook is inert (no compression, command unmodified).

set -euo pipefail

# --- Opt-in gate (default OFF) -------------------------------------------
# Inert unless explicitly enabled, mirroring the protected-branch guard in
# git-guardrails.sh. This keeps the hook from rewriting commands -- and from
# spawning a Python import check per Bash call -- for users who have not opted in.
if [ "${NEXUS_CONTEXT_COMPRESS:-0}" != "1" ]; then
  exit 0
fi

# --- jq gate -------------------------------------------------------------
# The rewrite needs jq to read the command and splice the new one back into
# tool_input without mangling the JSON. Without jq the hook is inert.
if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

# --- Read JSON from stdin and extract the command ------------------------
INPUT=$(cat)
# `// empty` yields an empty string (not "null") for a missing command; `|| true`
# keeps a non-match from tripping `set -e`/`pipefail`.
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)

# No command (non-Bash tool, or empty): allow unchanged.
if [ -z "${COMMAND:-}" ]; then
  exit 0
fi

# Idempotency: never wrap a command that already routes through the compressor
# (re-entrancy, or a command the user wrote by hand).
if echo "$COMMAND" | grep -q 'nexus_context_compressor'; then
  exit 0
fi

# --- Resolve a Python interpreter ----------------------------------------
PYBIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYBIN="$candidate"
    break
  fi
done
if [ -z "$PYBIN" ]; then
  exit 0
fi

# --- Fail-open guard: only rewrite if the engine imports cleanly ----------
# If the package is not installed/importable, piping output through it would
# emit nothing and lose the command's output. Skip the rewrite entirely in that
# case so the command runs raw.
if ! "$PYBIN" -c "import nexus_context_compressor" >/dev/null 2>&1; then
  exit 0
fi

# --- Build the rewritten command -----------------------------------------
# Wrap the original command in a group so the WHOLE command's stdout (not just
# its last pipeline stage) flows through the compressor, then restore the
# original exit status. ${PIPESTATUS[0]} must reach the target shell literally,
# so it lives in printf's single-quoted format string (never expanded here).
# %s args are substituted literally, so a command containing % is safe.
# shellcheck disable=SC2016  # ${PIPESTATUS[0]} is intentionally literal: it must
# be expanded by the TARGET shell that runs the rewritten command, not here.
NEW=$(printf '{ %s ; } | %s -m nexus_context_compressor compress; exit ${PIPESTATUS[0]}' "$COMMAND" "$PYBIN")

# Emit the PreToolUse decision: allow the (rewritten) tool call. Preserve every
# other tool_input field and replace only .command.
echo "$INPUT" | jq \
  --arg cmd "$NEW" \
  '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", updatedInput: (.tool_input + {command: $cmd})}}'

exit 0
