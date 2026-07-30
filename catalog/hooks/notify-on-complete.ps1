<#
.SYNOPSIS
    PowerShell parity for notify-on-complete.sh.

.DESCRIPTION
    Stop hook that raises a desktop notification when the agent finishes a task.
    Fails silently when no notification mechanism is available; always exits 0.

    The bash sibling detects the OS and picks osascript (macOS), notify-send
    (Linux), or a PowerShell balloon tip (Windows / Git Bash). This version IS the
    Windows path, called directly rather than shelled out to from bash, so it
    avoids the nested-quoting fragility of the bash version's inline PowerShell.

.NOTES
    Notification backend order:
      1. Windows toast via the WinRT/BurntToast-free NotifyIcon balloon (works on
         stock Windows PowerShell 5.1, no module install).
      2. notify-send, if present (PowerShell on Linux).
      3. osascript, if present (PowerShell on macOS).
      4. Silent no-op.

    Reads an optional duration from the Stop payload on stdin to enrich the
    message, matching the .sh sibling's `.session_duration // .duration` lookup.
#>

# Never fail loudly - always exit 0.
$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "notify-on-complete"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

$title = "Claude Code"
$projectName = try { Split-Path (Get-Location).Path -Leaf } catch { "unknown" }
$message = "Task complete in $projectName"

# --- Optional duration from the Stop payload ---
if ([Console]::IsInputRedirected) {
    $raw = [Console]::In.ReadToEnd()
    if ($raw) {
        try {
            $payload = $raw | ConvertFrom-Json
            $names = if ($payload) { $payload.PSObject.Properties.Name } else { @() }
            $duration = if ($names -contains 'session_duration') { $payload.session_duration }
                        elseif ($names -contains 'duration') { $payload.duration }
                        else { $null }
            if ($duration) { $message = "Task complete in $projectName ($duration)" }
        } catch {
            # Malformed payload: keep the default message.
        }
    }
}

# --- Windows balloon notification ---
# NotifyIcon is chosen over a WinRT toast on purpose: toasts need an AppUserModelId
# registration or a third-party module, while this works on a stock 5.1 host.
if ($env:OS -eq "Windows_NT" -or $IsWindows) {
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        Add-Type -AssemblyName System.Drawing -ErrorAction Stop
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.BalloonTipTitle = $title
        $notify.BalloonTipText = $message
        $notify.Visible = $true
        $notify.ShowBalloonTip(5000)
        Start-Sleep -Milliseconds 5500
        $notify.Dispose()
        exit 0
    } catch {
        # Headless session, no WinForms, or no interactive desktop: fall through.
    }
}

# --- notify-send (PowerShell on Linux) ---
if (Get-Command notify-send -ErrorAction SilentlyContinue) {
    try {
        & notify-send $title $message --expire-time=5000 2>$null | Out-Null
        exit 0
    } catch { }
}

# --- osascript (PowerShell on macOS) ---
if (Get-Command osascript -ErrorAction SilentlyContinue) {
    try {
        & osascript -e "display notification `"$message`" with title `"$title`"" 2>$null | Out-Null
        exit 0
    } catch { }
}

# No notification system found - fail silently.
exit 0
