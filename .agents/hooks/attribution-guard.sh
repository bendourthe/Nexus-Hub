#!/usr/bin/env bash
# Attribution Guard - PreToolUse Hook
# Blocks AI attribution (agent co-author trailers, generated-with footers,
# robot badges) on every publishing route.
# Part of Nexus-Hub
#
# How it works:
#   A thin adapter over `nexus_git_attribution.py scan`, which parses the
#   payload and prints every message, so this script and attribution-guard.ps1
#   behave identically. Routes: git commit and git tag messages (-m, -F,
#   heredocs), gh pr/issue/release create/edit/comment bodies (--body,
#   --body-file, --notes, --fill), gh api body fields, and GitHub MCP tools.
#   A Write or Edit to CHANGELOG.md or docs/ warns on the same patterns.
#   Only trailer- and footer-position attribution blocks; a sentence that names
#   a tool as its subject ("generated with pandoc") passes.
#
# When a body cannot be read safely (stdin, a FIFO, a device, over 1 MB, an
# unexpanded variable), or Python is unavailable, the hook warns and passes.
#
# Essential: stays on under NEXUS_HOOK_PROFILE=minimal. The only switch is the
# user's own NEXUS_DISABLED_HOOKS=attribution-guard.

set -euo pipefail

_HOOK_NAME="attribution-guard"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi

if [ -t 0 ]; then exit 0; fi
INPUT="$(cat)"
if [ -z "$INPUT" ]; then exit 0; fi

_HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_BUDGET="${NEXUS_ATTRIBUTION_TIMEOUT_SECONDS:-5}"

_warn() {
  echo "[$_HOOK_NAME] WARNING: cannot verify body ($1); check it for AI attribution before publishing." >&2
  exit 0
}

HELPER=""
for candidate in \
  "${NEXUS_ATTRIBUTION_SCRIPT:-}" \
  "$_HOOK_DIR/../../scripts/nexus_git_attribution.py" \
  "$HOME/.nexus-hub/scripts/nexus_git_attribution.py"; do
  if [ -n "$candidate" ] && [ -f "$candidate" ]; then HELPER="$candidate"; break; fi
done
[ -n "$HELPER" ] || _warn "nexus_git_attribution.py not found"

PYTHON=""
for candidate in python3 python; do
  path="$(command -v "$candidate" 2>/dev/null || true)"
  [ -n "$path" ] || continue
  # Under WindowsApps sits either a Store-installed Python or the alias that only
  # opens the Store; probe it once so the alias is never mistaken for Python.
  if [[ "$path" == *WindowsApps* ]] && ! "$candidate" -c "import sys" >/dev/null 2>&1; then continue; fi
  PYTHON="$candidate"; break
done
[ -n "$PYTHON" ] || _warn "Python not found"

export PYTHONIOENCODING=utf-8
status=0
if command -v timeout >/dev/null 2>&1; then
  printf '%s' "$INPUT" | timeout "$_BUDGET" "$PYTHON" "$HELPER" scan || status=$?
else
  printf '%s' "$INPUT" | "$PYTHON" "$HELPER" scan || status=$?
fi

case "$status" in
  0|2) exit "$status" ;;
  124) _warn "the ${_BUDGET}-second budget ran out" ;;
  *) _warn "nexus_git_attribution.py failed" ;;
esac
