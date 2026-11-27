#!/usr/bin/env bash
# Consume typed implementation reconciliation through the installed trusted core.
set -euo pipefail

_HOOK_NAME="implementation-state"
_skip() {
  if [ ! -t 0 ]; then cat >/dev/null 2>&1 || true; fi
  exit 0
}
IFS=',' read -r -a _disabled <<< "${NEXUS_DISABLED_HOOKS:-}"
for _entry in "${_disabled[@]}"; do
  if [ "${_entry//[[:space:]]/}" = "$_HOOK_NAME" ]; then _skip; fi
done
if [ "${NEXUS_HOOK_PROFILE:-}" = "minimal" ]; then _skip; fi

_core="${HOME:-}/.nexus-hub/scripts/completion_gate.py"
_python="$(command -v python3 || command -v python || true)"
if [ -z "$_python" ] || [ ! -f "$_core" ]; then _skip; fi
# stdin is inherited unchanged, including non-ASCII bytes and line endings.
_status=0
"$_python" -B "$_core" reconcile-stop || _status=$?
exit "$_status"
