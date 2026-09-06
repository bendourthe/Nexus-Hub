#!/usr/bin/env bash
# Notify on Complete - Stop Hook for Claude Code - Part of Nexus-Hub
#
# Trigger B of the end-of-task notification contract: the agent finished
# responding and handed control back, so a human's attention is warranted.
#
# Contract: docs/releases/v3/v3.15/development/end-of-task-notification-contract.md
#
# What this hook deliberately does NOT do (v3.15.10):
#   - It is NOT registered on SubagentStop. A sub-agent finishing is a sub-task
#     milestone, not a reason to interrupt a human. Wiring it is the single
#     change most likely to reintroduce the per-turn storm this release removed,
#     so its absence is asserted by test.
#   - It does NOT label the notification with basename "$(pwd)". That named
#     whatever subdirectory the hook ran in, which produced a field toast
#     reading "Task complete in work".
#
# Fails silently when no notification mechanism is available; always exits 0.
#
# Runtime controls (all checked on EVERY invocation):
#   Disable by name:  export NEXUS_DISABLED_HOOKS=notify-on-complete
#   Skip non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
#   Disable mid-session:  touch ~/.nexus-hub/notifications-disabled
#
# The file switch is the one that works inside a running editor. An environment
# variable cannot, because a child process inherits its parent's environment
# block rather than the registry.

# Never fail loudly - always exit 0.
trap 'exit 0' ERR

_HOOK_NAME="notify-on-complete"

# shellcheck source=./_notify_common.sh
_NOTIFY_COMMON="$(dirname "${BASH_SOURCE[0]:-$0}")/_notify_common.sh"
if [ ! -r "$_NOTIFY_COMMON" ]; then
  # The shared helper is missing: stay silent rather than notify without a label.
  exit 0
fi
# shellcheck disable=SC1090
. "$_NOTIFY_COMMON"

if nexus_notify_suppressed "$_HOOK_NAME"; then
  exit 0
fi

# Drain stdin so the harness never blocks on an unread pipe. The Stop payload
# carries no field this hook needs: the label comes from the workspace, not the
# payload, and a duration is not a reason to notify or stay silent.
if [ ! -t 0 ]; then
  cat >/dev/null 2>&1 || true
fi

nexus_notify_send "Claude Code" "Task complete - $(nexus_notify_label)"

exit 0
