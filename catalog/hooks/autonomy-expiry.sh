#!/usr/bin/env bash
# autonomy-expiry.sh - SessionStart TTL reversion for project-local autonomy.
#
# This hook is intentionally cheap when no autonomy state exists. It delegates
# all state and config behavior to scripts/lib/autonomy.py so shell platforms do
# not grow a second implementation of the safety gates.
set -euo pipefail

PROJECT_ROOT="$(pwd)"
if command -v git >/dev/null 2>&1; then
  GIT_TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -n "$GIT_TOPLEVEL" ]; then
    PROJECT_ROOT="$GIT_TOPLEVEL"
  fi
fi

if [ ! -f "$PROJECT_ROOT/.nexus-hub/autonomy-state.json" ]; then
  exit 0
fi

ENGINE="${NEXUS_AUTONOMY_ENGINE:-}"
if [ -z "$ENGINE" ] && [ -f "$PROJECT_ROOT/scripts/lib/autonomy.py" ]; then
  ENGINE="$PROJECT_ROOT/scripts/lib/autonomy.py"
fi
if [ -z "$ENGINE" ] && [ -n "${NEXUS_HUB_HOME:-}" ] && [ -f "$NEXUS_HUB_HOME/scripts/lib/autonomy.py" ]; then
  ENGINE="$NEXUS_HUB_HOME/scripts/lib/autonomy.py"
fi
if [ -z "$ENGINE" ] && [ -f "$HOME/.nexus-hub/scripts/lib/autonomy.py" ]; then
  ENGINE="$HOME/.nexus-hub/scripts/lib/autonomy.py"
fi
if [ -z "$ENGINE" ] || [ ! -f "$ENGINE" ]; then
  echo "ERROR: autonomy state exists, but the Nexus-Hub autonomy engine was not found." >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "ERROR: autonomy state exists, but Python is unavailable for TTL reversion." >&2
  exit 1
fi

"$PYTHON_BIN" "$ENGINE" expire --project "$PROJECT_ROOT"
