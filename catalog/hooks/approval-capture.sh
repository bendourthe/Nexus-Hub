#!/usr/bin/env bash
# Prompt capture for the full-run approval-origin rule - Part of Nexus-Hub (v4.13.2)
#
# Thin adapter over ~/.nexus-hub/scripts/completion_gate.py (capture mode). The
# decision logic lives in that installed core, never in the working tree, so a
# repository cannot plant its own version. What "done" means is owned by the
# completion contract (implement-phase/references/completion-contract.md).
#
# A session with no bound full-run record is never affected: the core exits 0
# with no output. If Python or the core is missing, this hook allows the event.
#
# Runtime controls (checked on EVERY invocation):
#   Disable by name:          export NEXUS_DISABLED_HOOKS=approval-capture
#   Skip non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
set -uo pipefail

_HOOK_NAME="approval-capture"

case ",${NEXUS_DISABLED_HOOKS:-}," in
  *",$_HOOK_NAME,"*) exit 0 ;;
esac
if [ "${NEXUS_HOOK_PROFILE:-}" = "minimal" ]; then
  exit 0
fi

_core="${HOME}/.nexus-hub/scripts/completion_gate.py"
_python="$(command -v python3 || command -v python || true)"
if [ -z "$_python" ] || [ ! -f "$_core" ]; then
  if [ ! -t 0 ]; then cat >/dev/null 2>&1 || true; fi
  exit 0
fi

"$_python" "$_core" capture
exit $?
