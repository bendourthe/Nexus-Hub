<#
.SYNOPSIS
    PowerShell parity for autonomy-guard.sh.

.DESCRIPTION
    Blocks Write and Edit calls targeting execution-trigger paths while project
    autonomy state exists. Policy remains in scripts/lib/autonomy.py so both
    shells enforce the same canonical list and symlink-aware matcher.

.NOTES
    Disabling this hook while autonomy is active is unsupported. The standard
    runtime controls remain available for consistency with the hook catalog.
#>

$ErrorActionPreference = "Continue"

function Write-AutonomyDebug {
    param([string]$Message)
    if (-not $env:NEXUS_AUTONOMY_DEBUG_FILE) { return }
    try {
        $encoding = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::AppendAllText($env:NEXUS_AUTONOMY_DEBUG_FILE, "$PID|$Message`n", $encoding)
    } catch {}
}

$hookName = "autonomy-guard"
Write-AutonomyDebug "start|get-location=$((Get-Location).Path)|process-cwd=$([Environment]::CurrentDirectory)"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) {
    Write-AutonomyDebug "exit|disabled"
    exit 0
}
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") {
    Write-AutonomyDebug "exit|minimal-profile"
    exit 0
}

$projectRoot = (Get-Location).Path
try {
    $gitTop = (& git rev-parse --show-toplevel 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -eq 0 -and $gitTop) { $projectRoot = $gitTop }
} catch {}
Write-AutonomyDebug "root|$projectRoot"

$statePath = Join-Path $projectRoot ".nexus-hub/autonomy-state.json"
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    Write-AutonomyDebug "exit|state-missing|$statePath"
    exit 0
}
Write-AutonomyDebug "state|found|$statePath"

$engine = $env:NEXUS_AUTONOMY_ENGINE
if (-not $engine) {
    $candidate = Join-Path $projectRoot "scripts/lib/autonomy.py"
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $engine = $candidate }
}
if (-not $engine -and $env:NEXUS_HUB_HOME) {
    $candidate = Join-Path $env:NEXUS_HUB_HOME "scripts/lib/autonomy.py"
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $engine = $candidate }
}
if (-not $engine) {
    $candidate = Join-Path $HOME ".nexus-hub/scripts/lib/autonomy.py"
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $engine = $candidate }
}
if (-not $engine -or -not (Test-Path -LiteralPath $engine -PathType Leaf)) {
    Write-AutonomyDebug "exit|engine-missing|$engine"
    [Console]::Error.WriteLine("AUTONOMY BLOCKED: autonomy state exists, but the Nexus-Hub guard engine was not found.")
    exit 2
}
Write-AutonomyDebug "engine|found|$engine"

$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) {
    Write-AutonomyDebug "exit|python-missing"
    [Console]::Error.WriteLine("AUTONOMY BLOCKED: autonomy state exists, but Python is unavailable for the guard.")
    exit 2
}
Write-AutonomyDebug "python|$($python.Source)"

# Hook invocations always provide one UTF-8 JSON payload on standard input.
# Windows PowerShell can consume redirected -File input into its automatic
# pipeline enumerator before Console APIs see it, especially under hosted pwsh.
$pipelineInput = @($input)
if ($pipelineInput.Count -gt 0) {
    $raw = $pipelineInput -join [Environment]::NewLine
    Write-AutonomyDebug "input|pipeline|count=$($pipelineInput.Count)|length=$($raw.Length)"
} else {
    $stdin = [Console]::OpenStandardInput()
    $reader = [System.IO.StreamReader]::new($stdin, [System.Text.Encoding]::UTF8, $true)
    try {
        $raw = $reader.ReadToEnd()
    } finally {
        $reader.Dispose()
    }
    Write-AutonomyDebug "input|handle|length=$($raw.Length)"
}
$raw | & $python.Source $engine guard --project $projectRoot
Write-AutonomyDebug "exit|engine|code=$LASTEXITCODE"
exit $LASTEXITCODE
