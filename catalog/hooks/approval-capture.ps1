<#
.SYNOPSIS
    PowerShell parity for approval-capture.sh.

.DESCRIPTION
    Prompt capture for the full-run approval-origin rule - Part of Nexus-Hub (v4.13.2).

    Thin adapter over ~/.nexus-hub/scripts/completion_gate.py (capture mode). The
    decision logic lives in that installed core, never in the working tree, so a
    repository cannot plant its own version. What "done" means is owned by the
    completion contract (implement-phase/references/completion-contract.md).

    A session with no bound full-run record is never affected: the core exits 0
    with no output. If Python or the core is missing, this hook allows the event.

.NOTES
    Runtime controls (checked on EVERY invocation):
      Disable by name:          $env:NEXUS_DISABLED_HOOKS = "approval-capture"
      Skip non-essential hooks: $env:NEXUS_HOOK_PROFILE = "minimal"
#>

$ErrorActionPreference = "Continue"
$hookName = "approval-capture"

$disabled = ($env:NEXUS_DISABLED_HOOKS -split ",") | ForEach-Object { $_.Trim() }
if ($disabled -contains $hookName) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

$homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
$core = Join-Path $homeDir ".nexus-hub\scripts\completion_gate.py"
$python = $null
foreach ($candidate in @("python3", "python")) {
    $command = Get-Command $candidate -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { continue }
    # Under WindowsApps sits either a Store-installed Python or the alias that only
    # opens the Store; probe it once so the alias is never mistaken for Python.
    if ($command.Source -match 'WindowsApps') {
        & $command.Source -c "import sys" *> $null
        if ($LASTEXITCODE -ne 0) { continue }
    }
    $python = $command.Source
    break
}

# The payload passes through as raw bytes: decoding it through [Console]::In depends on the
# console input encoding, which on the hosted Windows runner (UTF-8) left a byte-order mark
# the core could not parse, so every gate and capture silently did nothing (v4.13.2 PR #365).
$inputBytes = [byte[]]@()
if ([Console]::IsInputRedirected) {
    $buffer = New-Object System.IO.MemoryStream
    try { [Console]::OpenStandardInput().CopyTo($buffer) } catch { }
    $inputBytes = $buffer.ToArray()
    if ($inputBytes.Length -eq 0) {
        # Windows PowerShell 5.1 started without a console buffers stdin through its own reader,
        # leaving the raw handle drained; [Console]::In still holds the payload there.
        try { $fallbackText = [Console]::In.ReadToEnd() } catch { $fallbackText = "" }
        if ($fallbackText) { $inputBytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($fallbackText) }
    }
}
if (-not $python -or -not (Test-Path -LiteralPath $core)) { exit 0 }

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python
$psi.Arguments = '"' + $core + '" capture'
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$utf8 = New-Object System.Text.UTF8Encoding($false)
$psi.StandardOutputEncoding = $utf8
$psi.StandardErrorEncoding = $utf8
$psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
$proc = [System.Diagnostics.Process]::Start($psi)
try {
    $proc.StandardInput.BaseStream.Write($inputBytes, 0, $inputBytes.Length)
    # Close the raw stream, not a StreamWriter: closing the writer can append a byte-order mark.
    $proc.StandardInput.BaseStream.Flush()
    $proc.StandardInput.BaseStream.Close()
} catch {
    # A core that exits before reading stdin is judged by its exit code below.
}
$out = $proc.StandardOutput.ReadToEnd()
$err = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
if ($out) { [Console]::Out.Write($out) }
if ($err) { [Console]::Error.Write($err) }
exit $proc.ExitCode
