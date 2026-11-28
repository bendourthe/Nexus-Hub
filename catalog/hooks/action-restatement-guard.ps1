<#
.SYNOPSIS
    PowerShell parity for action-restatement-guard.sh.

.DESCRIPTION
    Action Restatement Guard - Stop hook - Part of Nexus-Hub.

    Thin wrapper over _action_restatement.py (same directory). It gates, then delegates the
    decision to the helper: when the last assistant message asks the user to act AND points
    back to earlier text ("from earlier", "as above", "scroll up", ...), the helper prints a
    block decision with a reason so the agent rewrites the message under a
    "## Action needed" heading that restates every step. Detection lists, the false-positive
    policy, and the fail-open rules are documented in the helper header. Both siblings share
    the one helper so the two cannot drift apart.

    Fails open: any error, a missing interpreter or transcript, stop_hook_active, and a
    non-Claude payload all exit 0 with no output.

.NOTES
    Runtime controls (checked on EVERY invocation):
      Disable by name:          $env:NEXUS_DISABLED_HOOKS = "action-restatement-guard"
      Skip non-essential hooks: $env:NEXUS_HOOK_PROFILE = "minimal"
#>

$ErrorActionPreference = "SilentlyContinue"
$hookName = "action-restatement-guard"

$disabled = ($env:NEXUS_DISABLED_HOOKS -split ",") | ForEach-Object { $_.Trim() }
if ($disabled -contains $hookName) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

$helper = Join-Path $PSScriptRoot "_action_restatement.py"
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
# opens the Store exits non-zero, so both fall through to the next candidate.
foreach ($candidate in @("python3", "python")) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $candidate
    $psi.Arguments = '"' + $helper + '"'
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
