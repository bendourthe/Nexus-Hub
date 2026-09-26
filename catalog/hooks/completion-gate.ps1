<#
.SYNOPSIS
    PowerShell parity for completion-gate.sh.

.DESCRIPTION
    Turn-end completion gate for a full /implement run - Part of Nexus-Hub (v4.13.2).

    Thin adapter over ~/.nexus-hub/scripts/completion_gate.py (stop mode). The
    decision logic lives in that installed core, never in the working tree, so a
    repository cannot plant its own version. What "done" means is owned by the
    completion contract (implement-phase/references/completion-contract.md).

    A session with no bound full-run record is never affected: the core exits 0
    with no output. If Python or the core is missing, this hook allows the event.

.NOTES
    Runtime controls (checked on EVERY invocation):
      Disable by name:          $env:NEXUS_DISABLED_HOOKS = "completion-gate"
      Skip non-essential hooks: $env:NEXUS_HOOK_PROFILE = "minimal"
#>

$ErrorActionPreference = "Continue"
$hookName = "completion-gate"

$disabled = ($env:NEXUS_DISABLED_HOOKS -split ",") | ForEach-Object { $_.Trim() }
if ($disabled -contains $hookName) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

$homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
$core = Join-Path $homeDir ".nexus-hub\scripts\completion_gate.py"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }

$payload = ""
if ([Console]::IsInputRedirected) {
    try { $payload = [Console]::In.ReadToEnd() } catch { $payload = "" }
}
if (-not $python -or -not (Test-Path -LiteralPath $core)) { exit 0 }

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python.Source
$psi.Arguments = '"' + $core + '" stop'
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$utf8 = New-Object System.Text.UTF8Encoding($false)
$psi.StandardOutputEncoding = $utf8
$psi.StandardErrorEncoding = $utf8
$proc = [System.Diagnostics.Process]::Start($psi)
$writer = New-Object System.IO.StreamWriter($proc.StandardInput.BaseStream, $utf8)
$writer.Write($payload)
$writer.Close()
$out = $proc.StandardOutput.ReadToEnd()
$err = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
if ($out) { [Console]::Out.Write($out) }
if ($err) { [Console]::Error.Write($err) }
exit $proc.ExitCode
