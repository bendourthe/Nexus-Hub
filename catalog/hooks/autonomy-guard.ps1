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

$hookName = "autonomy-guard"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

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
    [Console]::Error.WriteLine("AUTONOMY BLOCKED: autonomy state exists, but the Nexus-Hub guard engine was not found.")
    exit 2
}

$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) {
    [Console]::Error.WriteLine("AUTONOMY BLOCKED: autonomy state exists, but Python is unavailable for the guard.")
    exit 2
}

# Hook invocations always provide one UTF-8 JSON payload on standard input.
# Windows PowerShell can consume redirected -File input into its automatic
# pipeline enumerator before Console APIs see it, especially under hosted pwsh.
$pipelineInput = @($input)
if ($pipelineInput.Count -gt 0) {
    $raw = $pipelineInput -join [Environment]::NewLine
} else {
    $stdin = [Console]::OpenStandardInput()
    $reader = [System.IO.StreamReader]::new($stdin, [System.Text.Encoding]::UTF8, $true)
    try {
        $raw = $reader.ReadToEnd()
    } finally {
        $reader.Dispose()
    }
}
$raw | & $python.Source $engine guard --project $projectRoot
exit $LASTEXITCODE
