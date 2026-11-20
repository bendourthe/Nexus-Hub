<#
.SYNOPSIS
    PowerShell parity for stuck-turn-notice.sh.

.DESCRIPTION
    Stuck-Turn Notice - PostToolUse / PostToolUseFailure hook - Part of Nexus-Hub (v4.15.5).

    Thin wrapper over _turn_ledger.py (same directory). It gates, then delegates the hashed
    per-user outcome log and the one-notice-per-turn decision to the helper. Advisory only:
    it never blocks and always exits 0.

    OPT-IN (provisional default, decision T018 pending): the helper runs only when
    NEXUS_STUCK_NOTICE=on (notice) or NEXUS_ENV_FACTS=on (fact collection).

.NOTES
    Runtime controls (checked on EVERY invocation):
      Disable by name:          $env:NEXUS_DISABLED_HOOKS = "stuck-turn-notice"
      Skip non-essential hooks: $env:NEXUS_HOOK_PROFILE = "minimal"
      Notice on:                $env:NEXUS_STUCK_NOTICE = "on"
      Purge state:              delete ~/.nexus-hub/state/<project hash>/
#>

$ErrorActionPreference = "SilentlyContinue"
$hookName = "stuck-turn-notice"

$disabled = ($env:NEXUS_DISABLED_HOOKS -split ",") | ForEach-Object { $_.Trim() }
if ($disabled -contains $hookName) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }
if ($env:NEXUS_STUCK_NOTICE -cne "on" -and $env:NEXUS_ENV_FACTS -cne "on") { exit 0 }

$helper = Join-Path $PSScriptRoot "_turn_ledger.py"
if (-not (Test-Path -LiteralPath $helper)) { exit 0 }

# The payload passes through as raw bytes so a console input encoding cannot add a byte-order mark.
$inputBytes = [byte[]]@()
if ([Console]::IsInputRedirected) {
    $buffer = New-Object System.IO.MemoryStream
    try { [Console]::OpenStandardInput().CopyTo($buffer) } catch { }
    $inputBytes = $buffer.ToArray()
    if ($inputBytes.Length -eq 0) {
        try { $fallbackText = [Console]::In.ReadToEnd() } catch { $fallbackText = "" }
        if ($fallbackText) { $inputBytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($fallbackText) }
    }
}
if ($inputBytes.Length -eq 0) { exit 0 }

$utf8 = New-Object System.Text.UTF8Encoding($false)
# Try each interpreter by starting it directly: a missing one throws, and the Store alias that only
# opens the Store exits non-zero, so both fall through to the next candidate. Skipping Get-Command
# saves startup time on every tool call.
foreach ($candidate in @("python3", "python")) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $candidate
    $psi.Arguments = '"' + $helper + '" record'
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $utf8
    $psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
        try {
            $proc.StandardInput.BaseStream.Write($inputBytes, 0, $inputBytes.Length)
            $proc.StandardInput.BaseStream.Flush()
            $proc.StandardInput.BaseStream.Close()
        } catch { }
        $out = $proc.StandardOutput.ReadToEnd()
        $null = $proc.StandardError.ReadToEnd()
        $proc.WaitForExit()
        if ($proc.ExitCode -eq 0) {
            if ($out) { [Console]::Out.Write($out) }
            break
        }
    } catch { }
}
exit 0
