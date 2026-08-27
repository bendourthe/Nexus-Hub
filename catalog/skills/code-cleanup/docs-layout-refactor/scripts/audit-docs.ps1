<#
.SYNOPSIS
    PowerShell wrapper for audit-docs.py.

.DESCRIPTION
    The audit-docs.py helper is the canonical, cross-platform implementation.
    This wrapper detects a Python interpreter on PATH and forwards every
    argument verbatim. It exists so Windows users can invoke the helper
    without remembering which Python launcher is installed.

.EXAMPLE
    .\audit-docs.ps1 inventory --root .\docs

.EXAMPLE
    .\audit-docs.ps1 refgraph --root .\docs --repo-root .

.EXAMPLE
    .\audit-docs.ps1 canonicalize-layout --root .\docs
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyScript  = Join-Path $scriptDir "audit-docs.py"

if (-not (Test-Path $pyScript)) {
    Write-Error "audit-docs.py not found alongside the wrapper at $pyScript"
    exit 1
}

$pythonExe = $null
foreach ($candidate in @("python", "py", "python3")) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) {
        $pythonExe = $candidate
        break
    }
}

if (-not $pythonExe) {
    Write-Error "Python is not on PATH. Install Python 3.8+ or invoke audit-docs.py directly."
    exit 127
}

if ($pythonExe -eq "py") {
    & $pythonExe -3 $pyScript @args
} else {
    & $pythonExe $pyScript @args
}

exit $LASTEXITCODE
