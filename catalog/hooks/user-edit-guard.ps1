<#
.SYNOPSIS
    PowerShell parity for user-edit-guard.sh.

.DESCRIPTION
    PreToolUse and PostToolUse hook that stops an agent from overwriting a file
    the user changed since the agent last read or wrote it. A thin adapter over
    the user-edit-preservation skill's edit_guard.py (`edit_guard.py hook`),
    which makes every decision and prints every message, so this script and
    user-edit-guard.sh behave identically.

    Budget: edit_guard.py gets 2 seconds (NEXUS_EDIT_GUARD_TIMEOUT_SECONDS).
    When Python or the helper is unavailable, or the budget runs out, a payload
    that looks like a write is blocked outside a git worktree and warned inside
    one; it is never passed silently outside a worktree.

    Essential: stays on under NEXUS_HOOK_PROFILE=minimal. The only switch is the
    user's own NEXUS_DISABLED_HOOKS=user-edit-guard.

.NOTES
    The payload is forwarded as raw bytes, so a non-ASCII path reaches Python
    unchanged whatever the console code page is.
#>

$ErrorActionPreference = "Continue"
$hookName = "user-edit-guard"

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
$inputText = (New-Object System.Text.UTF8Encoding($false)).GetString($inputBytes)

$budget = 2.0
if ($env:NEXUS_EDIT_GUARD_TIMEOUT_SECONDS) {
    $parsed = 0.0
    if ([double]::TryParse($env:NEXUS_EDIT_GUARD_TIMEOUT_SECONDS, [System.Globalization.NumberStyles]::Float,
            [System.Globalization.CultureInfo]::InvariantCulture, [ref]$parsed)) { $budget = $parsed }
}
$budgetLabel = $budget.ToString([System.Globalization.CultureInfo]::InvariantCulture)

function Invoke-Fallback {
    param([string]$Reason)
    if ($inputText -match '"hook_event_name"\s*:\s*"PostToolUse"') { exit 0 }
    if ($inputText -notmatch '"tool_name"\s*:\s*"(Write|Edit|MultiEdit|NotebookEdit)"|(^|[^A-Za-z])(cp|mv|Copy-Item|Move-Item)\s|shutil\.(copy|move)|>') {
        exit 0
    }
    $message = "Cannot verify this file against your last read or write ($Reason). Stop and ask the user before overwriting it (user-edit-preservation)."
    $inside = $null
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $inside = & git rev-parse --is-inside-work-tree 2>$null
    }
    if ("$inside".Trim() -eq "true") {
        [Console]::Error.WriteLine("[$hookName] WARNING (git worktree, not blocked): $message")
        exit 0
    }
    [Console]::Error.WriteLine("[$hookName] BLOCKED: $message")
    [Console]::Error.WriteLine("Only the user may turn this check off, with NEXUS_DISABLED_HOOKS=$hookName.")
    exit 2
}

$homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
$helper = $null
foreach ($candidate in @(
        $env:NEXUS_EDIT_GUARD_SCRIPT,
        (Join-Path $PSScriptRoot "..\skills\user-edit-preservation\scripts\edit_guard.py"),
        (Join-Path $PSScriptRoot "..\skills\workflow\user-edit-preservation\scripts\edit_guard.py"),
        (Join-Path $PSScriptRoot "..\..\.agents\skills\user-edit-preservation\scripts\edit_guard.py"),
        (Join-Path $homeDir ".claude\skills\user-edit-preservation\scripts\edit_guard.py"),
        (Join-Path $homeDir ".agents\skills\user-edit-preservation\scripts\edit_guard.py"))) {
    if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) { $helper = $candidate; break }
}
if (-not $helper) { Invoke-Fallback "edit_guard.py not found" }

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
if (-not $python) { Invoke-Fallback "Python not found" }

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python
$psi.Arguments = '"' + $helper + '" hook'
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
    Invoke-Fallback "edit_guard.py failed"
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
    Invoke-Fallback "the $budgetLabel-second budget ran out"
}
$process.WaitForExit()
[Console]::Out.Write($stdoutTask.Result)
[Console]::Error.Write($stderrTask.Result)

$status = $process.ExitCode
if ($status -eq 0 -or $status -eq 2) { exit $status }
Invoke-Fallback "edit_guard.py failed"
