<#
.SYNOPSIS
    PowerShell parity for _notify_common.sh - shared end-of-task notification helpers.

.DESCRIPTION
    Dot-sourced by notify-on-complete.ps1 (Stop) and notify-attention-required.ps1
    (Notification). The leading underscore marks it a shared module rather than a
    registerable hook, matching the _skill_rules.py convention; it is never
    registered in settings.json and never invoked directly.

    Contract: docs/releases/v3/v3.15/development/end-of-task-notification-contract.md

    Everything here is fail-open. A notification is a convenience, so no helper
    may abort a turn: each one degrades to a usable default instead of throwing.

.NOTES
    This is the native Windows path rather than a translation of the bash
    version's inline PowerShell, so it avoids that nested-quoting fragility
    entirely (the same reasoning behind the original notify-on-complete.ps1).
#>

Set-StrictMode -Off
$ErrorActionPreference = "Continue"

function Get-NexusNotifyLabel {
    <#
    .SYNOPSIS
        Return "<repo> (<branch>)" for the current workspace.
    .DESCRIPTION
        Resolution order is git root, then $env:CLAUDE_PROJECT_DIR, then the
        current location, then the literal "unknown". The current directory's
        leaf alone is NOT sufficient: it names whatever subdirectory the hook
        happened to run in, which is how a toast reading "Task complete in work"
        was produced in the field. The branch is included because worktrees of
        one repo are routinely open simultaneously.
    #>
    $root = $null
    try {
        # Capture the native command's output FULLY before touching it.
        #
        # Do NOT write `& git ... | Select-Object -First 1`. Piping a native
        # command straight into `Select-Object -First 1` stops the upstream
        # pipeline early (StopUpstreamCommandsException, PS3+), which can
        # terminate git before $LASTEXITCODE is assigned. That leaves the exit
        # code unset or stale, so this resolution failed INTERMITTENTLY under
        # load and the label silently degraded to the current directory's leaf
        # (observed as "hooks" instead of "Nexus-Hub"). Capture, then index.
        $out = & git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) {
            $first = @($out)[0]
            if (-not [string]::IsNullOrWhiteSpace($first)) { $root = $first.Trim() }
        }
    } catch { }

    if ([string]::IsNullOrWhiteSpace($root) -and -not [string]::IsNullOrWhiteSpace($env:CLAUDE_PROJECT_DIR)) {
        $root = $env:CLAUDE_PROJECT_DIR
    }
    if ([string]::IsNullOrWhiteSpace($root)) {
        try { $root = (Get-Location).Path } catch { }
    }

    $name = $null
    if (-not [string]::IsNullOrWhiteSpace($root)) {
        try { $name = Split-Path $root -Leaf } catch { }
    }
    if ([string]::IsNullOrWhiteSpace($name)) { $name = "unknown" }

    # Omit the branch entirely rather than emitting empty parentheses. "HEAD"
    # means a detached checkout, which names nothing useful to a reader.
    $branch = $null
    try {
        # Same capture-then-index discipline as the root lookup above: piping a
        # native command into `Select-Object -First 1` can stop git before
        # $LASTEXITCODE is set, which dropped the branch intermittently.
        $b = & git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0 -and $b) {
            $firstBranch = @($b)[0]
            if (-not [string]::IsNullOrWhiteSpace($firstBranch)) { $branch = $firstBranch.Trim() }
        }
    } catch { }

    if (-not [string]::IsNullOrWhiteSpace($branch) -and $branch -ne "HEAD") {
        return "$name ($branch)"
    }
    return $name
}

function Test-NexusNotifySuppressed {
    <#
    .SYNOPSIS
        Return $true when this invocation must stay silent.
    .DESCRIPTION
        Layer 3 (the switch FILE) is the one that works mid-session. An
        environment variable cannot silence a hook inside an already-running
        editor, because a child process inherits its parent's environment block
        rather than the registry, so a newly-set variable never reaches a
        process tree that was already launched. The file is stat-ed on every
        invocation, so creating it takes effect on the very next notification
        with no restart.
    #>
    param([Parameter(Mandatory = $true)][string]$HookName)

    $disabled = $env:NEXUS_DISABLED_HOOKS
    if (-not [string]::IsNullOrWhiteSpace($disabled)) {
        if (($disabled -split ',' | ForEach-Object { $_.Trim() }) -contains $HookName) { return $true }
    }
    if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { return $true }

    $switchFile = $env:NEXUS_NOTIFY_DISABLED_FILE
    if ([string]::IsNullOrWhiteSpace($switchFile)) {
        # NOT $home: that is a readonly automatic variable in PowerShell, and
        # assigning to it is an error. HOME is checked before USERPROFILE so a
        # Git Bash / MSYS environment resolves the same path the .sh sibling uses.
        $userHome = $env:HOME
        if ([string]::IsNullOrWhiteSpace($userHome)) { $userHome = $env:USERPROFILE }
        if ([string]::IsNullOrWhiteSpace($userHome)) { return $false }
        $switchFile = Join-Path $userHome ".nexus-hub/notifications-disabled"
    }
    if (Test-Path -LiteralPath $switchFile) { return $true }

    return $false
}

function Send-NexusNotification {
    <#
    .SYNOPSIS
        Raise one desktop notification, or no-op.
    .DESCRIPTION
        Picks the first available backend and never reports failure: a headless
        session or a host with no notifier is a silent no-op, not an error.

        NotifyIcon is chosen over a WinRT toast on purpose: a toast needs an
        AppUserModelId registration or a third-party module, while this works on
        a stock PowerShell 5.1 host with no install.

        The linger is why the process stays alive briefly: disposing the icon too
        early can cancel a queued toast on Windows 10/11. It is configurable so
        the shortest safe value can be MEASURED on a live desktop rather than
        guessed; see the known limitation in the contract doc.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string]$Message
    )

    # Dry run: print the notification instead of raising it. This exists so the
    # label can be asserted by test without popping a real desktop toast on the
    # developer's screen (and so the .sh/.ps1 pair can be compared on the exact
    # same observable). Also handy for debugging a label resolution by hand.
    if (-not [string]::IsNullOrWhiteSpace($env:NEXUS_NOTIFY_DRY_RUN)) {
        [Console]::Out.Write("$Title`t$Message`n")
        return
    }

    if ($env:OS -eq "Windows_NT" -or $IsWindows) {
        try {
            Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
            Add-Type -AssemblyName System.Drawing -ErrorAction Stop
            $linger = 5500
            if (-not [string]::IsNullOrWhiteSpace($env:NEXUS_NOTIFY_LINGER_MS)) {
                try { $linger = [int]$env:NEXUS_NOTIFY_LINGER_MS } catch { $linger = 5500 }
            }
            $notify = New-Object System.Windows.Forms.NotifyIcon
            $notify.Icon = [System.Drawing.SystemIcons]::Information
            $notify.BalloonTipTitle = $Title
            $notify.BalloonTipText = $Message
            $notify.Visible = $true
            $notify.ShowBalloonTip(5000)
            Start-Sleep -Milliseconds $linger
            $notify.Dispose()
            return
        } catch {
            # Headless session, no WinForms, or no interactive desktop: fall through.
        }
    }

    if (Get-Command notify-send -ErrorAction SilentlyContinue) {
        try { & notify-send $Title $Message --expire-time=5000 2>$null | Out-Null; return } catch { }
    }
    if (Get-Command osascript -ErrorAction SilentlyContinue) {
        try { & osascript -e "display notification `"$Message`" with title `"$Title`"" 2>$null | Out-Null; return } catch { }
    }
}
