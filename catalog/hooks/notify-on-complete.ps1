<#
.SYNOPSIS
    PowerShell parity for notify-on-complete.sh.

.DESCRIPTION
    Trigger B of the end-of-task notification contract: the agent finished
    responding and handed control back, so a human's attention is warranted.

    Contract: docs/releases/v3/v3.15/development/end-of-task-notification-contract.md

    What this hook deliberately does NOT do (v3.15.10):
      - It is NOT registered on SubagentStop. A sub-agent finishing is a sub-task
        milestone, not a reason to interrupt a human. Wiring it is the single
        change most likely to reintroduce the per-turn storm this release
        removed, so its absence is asserted by test.
      - It does NOT label the notification with the current directory's leaf.
        That named whatever subdirectory the hook ran in, which produced a field
        toast reading "Task complete in work".

    Fails silently when no notification mechanism is available; always exits 0.

.NOTES
    Runtime controls (all checked on EVERY invocation):
      Disable by name:          $env:NEXUS_DISABLED_HOOKS = "notify-on-complete"
      Skip non-essential hooks: $env:NEXUS_HOOK_PROFILE = "minimal"
      Disable mid-session:      New-Item ~/.nexus-hub/notifications-disabled

    The file switch is the one that works inside a running editor. An
    environment variable cannot, because a child process inherits its parent's
    environment block rather than the registry.
#>

# Never fail loudly - always exit 0.
$ErrorActionPreference = "Continue"

$hookName = "notify-on-complete"

$notifyCommon = Join-Path $PSScriptRoot "_notify_common.ps1"
if (-not (Test-Path -LiteralPath $notifyCommon)) {
    # The shared helper is missing: stay silent rather than notify without a label.
    exit 0
}
. $notifyCommon

if (Test-NexusNotifySuppressed -HookName $hookName) { exit 0 }

# Drain stdin so the harness never blocks on an unread pipe. The Stop payload
# carries no field this hook needs: the label comes from the workspace, not the
# payload, and a duration is not a reason to notify or stay silent.
if ([Console]::IsInputRedirected) {
    try { [void][Console]::In.ReadToEnd() } catch { }
}

Send-NexusNotification -Title "Claude Code" -Message ("Task complete - " + (Get-NexusNotifyLabel))

exit 0
