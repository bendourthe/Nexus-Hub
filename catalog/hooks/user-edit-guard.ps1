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

    Essential: stays on under NEXUS_HOOK_PROFILE=minimal. Disable through the
    user's NEXUS_DISABLED_HOOKS=user-edit-guard or Settings protect_user_edits=false.

.NOTES
    The payload is forwarded as raw bytes, so a non-ASCII path reaches Python
    unchanged whatever the console code page is.
#>

$ErrorActionPreference = "Continue"

# Read Settings on every invocation. Only an exact JSON false disables a guard.
function Test-NexusGuardrailDisabled {
    param([string]$Key)
    $guardHome = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
    if (-not $guardHome) { return $false }
    try {
        $guardFile = Join-Path $guardHome '.nexus-hub/guardrails.json'
        if (-not (Test-Path -LiteralPath $guardFile -PathType Leaf)) { return $false }
        # PowerShell 7 unwraps a one-element JSON array into its object, so require a top-level object first.
        $guardText = (Get-Content -LiteralPath $guardFile -Raw -ErrorAction Stop).TrimStart([char]0xFEFF, ' ', "`t", "`r", "`n")
        if (-not $guardText.StartsWith('{')) { return $false }
        $guardSettings = $guardText | ConvertFrom-Json -ErrorAction Stop
        if ($guardSettings -isnot [pscustomobject]) { return $false }
        $guardProperty = $guardSettings.PSObject.Properties | Where-Object { $_.Name -ceq $Key } | Select-Object -First 1
        return ($null -ne $guardProperty -and $guardProperty.Value -is [bool] -and -not $guardProperty.Value)
    } catch { return $false }
}
if (Test-NexusGuardrailDisabled -Key "protect_user_edits") { exit 0 }
$hookName = "user-edit-guard"

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
$script:NexusTag = "[Nexus-Hub: user-edit-guard]"
# Print the tag and the message to stderr; every further line is printed as is.
function Write-NexusMessage {
    param([string]$Message, [string[]]$More = @())
    [Console]::Error.WriteLine("$script:NexusTag $Message")
    foreach ($line in $More) { [Console]::Error.WriteLine($line) }
}

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

# Nexus Settings guard switches apply in every host permission mode.
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
        Write-NexusMessage "WARNING (git worktree, not blocked): $message"
        exit 0
    }
    Write-NexusMessage "BLOCKED: $message" @("Only the user may turn this check off, with NEXUS_DISABLED_HOOKS=$hookName.")
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
$psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
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
    # Close the raw stream, not the StreamWriter: closing the writer flushes it and, where the
    # console input encoding is UTF-8, appends a byte-order mark after the payload.
    $process.StandardInput.BaseStream.Flush()
    $process.StandardInput.BaseStream.Close()
} catch {
    # A helper that exits before reading stdin is judged by its exit code below.
}

if (-not $process.WaitForExit([int]($budget * 1000))) {
    try { $process.Kill() } catch { }
    Invoke-Fallback "the $budgetLabel-second budget ran out"
}
$process.WaitForExit()
[Console]::Out.Write($stdoutTask.Result)
[Console]::Error.Write($stderrTask.Result)  # nexus: hook-msg-exempt relays edit_guard.py output verbatim

$status = $process.ExitCode
if ($status -eq 0 -or $status -eq 2) { exit $status }
Invoke-Fallback "edit_guard.py failed"
