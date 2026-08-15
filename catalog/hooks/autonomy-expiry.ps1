<#
.SYNOPSIS
    PowerShell parity for autonomy-expiry.sh.

.DESCRIPTION
    SessionStart TTL reversion for project-local autonomy. All state and config
    behavior is delegated to scripts/lib/autonomy.py so Windows and POSIX use
    one safety-critical implementation.
#>

$ErrorActionPreference = "Continue"

$projectRoot = (Get-Location).Path
try {
    $gitTop = (& git rev-parse --show-toplevel 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -eq 0 -and $gitTop) { $projectRoot = $gitTop }
} catch {}

$statePath = Join-Path $projectRoot ".nexus-hub/autonomy-state.json"
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { exit 0 }

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
    [Console]::Error.WriteLine("ERROR: autonomy state exists, but the Nexus-Hub autonomy engine was not found.")
    exit 1
}

$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) {
    [Console]::Error.WriteLine("ERROR: autonomy state exists, but Python is unavailable for TTL reversion.")
    exit 1
}

& $python.Source $engine expire --project $projectRoot
exit $LASTEXITCODE
