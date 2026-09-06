#!/usr/bin/env bash
# Notify on Attention Required - Notification Hook for Claude Code - Part of Nexus-Hub
#
# Trigger A of the end-of-task notification contract: the agent is BLOCKED on the
# human. Claude Code's `Notification` event fires when the agent needs permission
# to use a tool, and when it has been idle waiting for input.
#
# Contract: docs/releases/v3/v3.15/development/end-of-task-notification-contract.md
#
# This is the notification that was missing before v3.15.10, and the one most
# worth having: it fires when the agent is sitting blocked on a permission prompt
# while the human is in another window. The old behavior notified on every turn
# ending, which buried this case in noise instead of surfacing it.
#
# Fails silently when no notification mechanism is available; always exits 0.
#
# Runtime controls (all checked on EVERY invocation):
#   Disable by name:  export NEXUS_DISABLED_HOOKS=notify-attention-required
#   Skip non-essential hooks: export NEXUS_HOOK_PROFILE=minimal
#   Disable mid-session:  touch ~/.nexus-hub/notifications-disabled
#
# The file switch is the one that works inside a running editor. An environment
# variable cannot, because a child process inherits its parent's environment
# block rather than the registry.

# Never fail loudly - always exit 0.
trap 'exit 0' ERR

_HOOK_NAME="notify-attention-required"

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

# Drain stdin so the harness never blocks on an unread pipe. The Notification
# payload may carry a human-readable `message`, but it is NOT used as the body:
# the harness's own wording varies by trigger, while this hook's job is to say
# WHICH workspace wants attention. The payload is read and discarded.
if [ ! -t 0 ]; then
  cat >/dev/null 2>&1 || true
fi

nexus_notify_send "Claude Code" "Needs your input - $(nexus_notify_label)"

exit 0
