<#
.SYNOPSIS
    PowerShell parity for attribution-guard.sh.

.DESCRIPTION
    PreToolUse hook that blocks AI attribution (agent co-author trailers,
    generated-with footers, robot badges) on every publishing route. A thin
    adapter over `nexus_git_attribution.py scan`, which parses the payload and
    prints every message, so this script and attribution-guard.sh behave
    identically. Only trailer- and footer-position attribution blocks; a
    sentence that names a tool as its subject passes.

    When a body cannot be read safely, or Python is unavailable, the hook warns
    and passes.

    Essential: stays on under NEXUS_HOOK_PROFILE=minimal. The only switch is the
    user's own NEXUS_DISABLED_HOOKS=attribution-guard.

.NOTES
    The payload is forwarded as raw bytes, so non-ASCII body text reaches
    Python unchanged whatever the console code page is.
#>

$ErrorActionPreference = "Continue"
$hookName = "attribution-guard"

$disabled = $env:NEXUS_DISABLED_HOOKS
if ($disabled -and ($disabled.Split(',') -contains $hookName)) { exit 0 }

if (-not [Console]::IsInputRedirected) { exit 0 }
$buffer = New-Object System.IO.MemoryStream
[Console]::OpenStandardInput().CopyTo($buffer)
$inputBytes = $buffer.ToArray()
if ($inputBytes.Length -eq 0) {
    # Windows PowerShell 5.1 started without a console buffers stdin through its own reader,
    # leaving the raw handle drained; [Console]::In still holds the payload there.
    $fallbackText = [Console]::In.ReadToEnd()
    if ($fallbackText) { $inputBytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($fallbackText) }
}
if ($inputBytes.Length -eq 0) { exit 0 }

$budget = 5.0
if ($env:NEXUS_ATTRIBUTION_TIMEOUT_SECONDS) {
    $parsed = 0.0
    if ([double]::TryParse($env:NEXUS_ATTRIBUTION_TIMEOUT_SECONDS, [System.Globalization.NumberStyles]::Float,
            [System.Globalization.CultureInfo]::InvariantCulture, [ref]$parsed)) { $budget = $parsed }
}
$budgetLabel = $budget.ToString([System.Globalization.CultureInfo]::InvariantCulture)

function Write-CannotVerify {
    param([string]$Reason)
    [Console]::Error.WriteLine("[$hookName] WARNING: cannot verify body ($Reason); check it for AI attribution before publishing.")
    exit 0
}

$homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
$helper = $null
foreach ($candidate in @(
        $env:NEXUS_ATTRIBUTION_SCRIPT,
        (Join-Path $PSScriptRoot "..\..\scripts\nexus_git_attribution.py"),
        (Join-Path $homeDir ".nexus-hub\scripts\nexus_git_attribution.py"))) {
    if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) { $helper = $candidate; break }
}
if (-not $helper) { Write-CannotVerify "nexus_git_attribution.py not found" }

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
if (-not $python) { Write-CannotVerify "Python not found" }

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python
$psi.Arguments = '"' + $helper + '" scan'
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
$psi.StandardErrorEncoding = New-Object System.Text.UTF8Encoding($false)
$psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"

try {
    $process = [System.Diagnostics.Process]::Start($psi)
} catch {
    Write-CannotVerify "nexus_git_attribution.py failed"
}
$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
try {
    $process.StandardInput.BaseStream.Write($inputBytes, 0, $inputBytes.Length)
    $process.StandardInput.Close()
} catch {
    # A helper that exits before reading stdin is judged by its exit code below.
}

if (-not $process.WaitForExit([int]($budget * 1000))) {
    try { $process.Kill() } catch { }
    Write-CannotVerify "the $budgetLabel-second budget ran out"
}
$process.WaitForExit()
[Console]::Out.Write($stdoutTask.Result)
[Console]::Error.Write($stderrTask.Result)

$status = $process.ExitCode
if ($status -eq 0 -or $status -eq 2) { exit $status }
Write-CannotVerify "nexus_git_attribution.py failed"
