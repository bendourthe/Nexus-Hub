#!/usr/bin/env bash
# Turn-end completion gate for a full /implement run - Part of Nexus-Hub (v4.13.2)
#
# Thin adapter over ~/.nexus-hub/scripts/completion_gate.py (stop mode). The
# decision logic lives in that installed core, never in the working tree, so a
# repository cannot plant its own version. What "done" means is owned by the
# completion contract (implement-phase/references/completion-contract.md).
#
# A session with no bound full-run record is never affected: the core exits 0
# with no output. If Python or the core is missing, this hook allows the event.
# A schema-2 (minor) record is judged by the core through check-minor and
# score-minor; this adapter has no scope logic (v4.13.6).
#
# Runtime controls (checked on EVERY invocation):
#   Disable by name:          export NEXUS_DISABLED_HOOKS=completion-gate
#   Skip non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
set -uo pipefail

_HOOK_NAME="completion-gate"

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

# v4.13.7: the core reads usage-guard.py and _usage_probe.py from this hook's
# own directory to confirm a usage-limit handoff (never from the repository).
_hook_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || true)"
if [ -n "$_hook_dir" ] && command -v cygpath >/dev/null 2>&1; then
  _hook_dir="$(cygpath -m "$_hook_dir" 2>/dev/null || printf '%s' "$_hook_dir")"
fi
export NEXUS_GATE_HOOK_DIR="$_hook_dir"

"$_python" "$_core" stop
exit $?
