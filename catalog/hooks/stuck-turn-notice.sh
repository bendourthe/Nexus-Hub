#!/usr/bin/env bash
# Stuck-Turn Notice - PostToolUse / PostToolUseFailure hook - Part of Nexus-Hub (v4.15.5)
#
# Thin wrapper over _turn_ledger.py (same directory). It gates, then delegates:
# the helper keeps a per-user hashed log of tool outcomes under
# ~/.nexus-hub/state/<project hash>/ and prints at most one advisory notice per
# turn when a turn repeats a failing command, fails six tool calls, or changes
# one file four times. Advisory only: it never blocks and always exits 0.
#
# OPT-IN (provisional default, decision T018 pending): the helper runs only when
# NEXUS_STUCK_NOTICE=on (notice) or NEXUS_ENV_FACTS=on (fact collection).
#
# Runtime controls (checked on EVERY invocation):
#   Disable by name:          export NEXUS_DISABLED_HOOKS=stuck-turn-notice
#   Skip non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
#   Notice on:                export NEXUS_STUCK_NOTICE=on
#   Purge state:              delete ~/.nexus-hub/state/<project hash>/
set -uo pipefail
trap 'exit 0' ERR

_HOOK_NAME="stuck-turn-notice"
case ",${NEXUS_DISABLED_HOOKS:-}," in
  *",$_HOOK_NAME,"*) exit 0 ;;
esac
if [ "${NEXUS_HOOK_PROFILE:-}" = "minimal" ]; then exit 0; fi
if [ "${NEXUS_STUCK_NOTICE:-off}" != "on" ] && [ "${NEXUS_ENV_FACTS:-off}" != "on" ]; then
  exit 0
fi

# One subshell resolves the helper path; `pwd -W` (Git Bash) gives the mixed path a Windows
# Python needs, and plain `pwd` elsewhere. Builtins only, because each fork is slow on MSYS.
_src="${BASH_SOURCE[0]//\\//}"
case "$_src" in */*) _src_dir="${_src%/*}" ;; *) _src_dir="." ;; esac
_dir="$(cd "$_src_dir" 2>/dev/null && { pwd -W 2>/dev/null || pwd; })"
_helper="$_dir/_turn_ledger.py"
if [ -z "$_dir" ] || [ ! -f "$_helper" ]; then exit 0; fi

# Read the payload once so a failed interpreter (a Store stub exits non-zero) can fall
# back to the next candidate without losing it.
IFS= read -r -d '' _in || true
for _candidate in python3 python; do
  command -v "$_candidate" >/dev/null 2>&1 || continue
  if _out="$(printf '%s' "$_in" | "$_candidate" "$_helper" record 2>/dev/null)"; then
    if [ -n "$_out" ]; then printf '%s\n' "$_out"; fi
    break
  fi
done
exit 0
