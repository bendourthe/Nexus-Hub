#!/usr/bin/env bash
# autonomy-guard.sh - Block execution-trigger writes while autonomy is active.
#
# Disabling this hook while autonomy is active is unsupported. The runtime
# controls remain available for consistency with the rest of the hook catalog.
set -euo pipefail

_HOOK_NAME="autonomy-guard"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

PROJECT_ROOT="$(pwd)"
if command -v git >/dev/null 2>&1; then
  GIT_TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -n "$GIT_TOPLEVEL" ]; then PROJECT_ROOT="$GIT_TOPLEVEL"; fi
fi

if [ ! -f "$PROJECT_ROOT/.nexus-hub/autonomy-state.json" ]; then exit 0; fi

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
  echo "AUTONOMY BLOCKED: autonomy state exists, but the Nexus-Hub guard engine was not found." >&2
  exit 2
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "AUTONOMY BLOCKED: autonomy state exists, but Python is unavailable for the guard." >&2
  exit 2
fi

"$PYTHON_BIN" "$ENGINE" guard --project "$PROJECT_ROOT"
