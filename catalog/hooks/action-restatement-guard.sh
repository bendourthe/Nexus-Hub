#!/usr/bin/env bash
# Action Restatement Guard - Stop hook - Part of Nexus-Hub
#
# Thin wrapper over _action_restatement.py (same directory). It gates, then delegates
# the decision to the helper: when the last assistant message asks the user to act AND
# points back to earlier text ("from earlier", "as above", "scroll up", ...), the helper
# prints {"decision":"block","reason":...} so the agent rewrites the message under a
# "## Action needed" heading that restates every step. Detection lists, the false-positive
# policy (code spans ignored, heading-scoped check, no block on a missing heading alone),
# and the fail-open rules are documented in the helper header.
#
# Fails open: any error, a missing interpreter or transcript, stop_hook_active, and a
# non-Claude payload all exit 0 with no output.
#
# Runtime controls (checked on EVERY invocation):
#   Disable by name:          export NEXUS_DISABLED_HOOKS=action-restatement-guard
#   Skip non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
set -uo pipefail
trap 'exit 0' ERR

_HOOK_NAME="action-restatement-guard"
case ",${NEXUS_DISABLED_HOOKS:-}," in
  *",$_HOOK_NAME,"*) exit 0 ;;
esac
if [ "${NEXUS_HOOK_PROFILE:-}" = "minimal" ]; then exit 0; fi

# One subshell resolves the helper path; `pwd -W` (Git Bash) gives the mixed path a Windows
# Python needs, and plain `pwd` elsewhere. Builtins only, because each fork is slow on MSYS.
_src="${BASH_SOURCE[0]//\\//}"
case "$_src" in */*) _src_dir="${_src%/*}" ;; *) _src_dir="." ;; esac
_dir="$(cd "$_src_dir" 2>/dev/null && { pwd -W 2>/dev/null || pwd; })"
_helper="$_dir/_action_restatement.py"
if [ -z "$_dir" ] || [ ! -f "$_helper" ]; then exit 0; fi

# Read the payload once so a failed interpreter (a Store stub exits non-zero) can fall
# back to the next candidate without losing it.
IFS= read -r -d '' _in || true
[ -n "$_in" ] || exit 0
for _candidate in python3 python; do
  command -v "$_candidate" >/dev/null 2>&1 || continue
  if _out="$(printf '%s' "$_in" | "$_candidate" "$_helper" 2>/dev/null)"; then
    if [ -n "$_out" ]; then printf '%s\n' "$_out"; fi
    break
  fi
done
exit 0
