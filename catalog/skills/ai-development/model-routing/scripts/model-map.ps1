<#
.SYNOPSIS
    Cross-platform entry point for model-map.py.

.DESCRIPTION
    Resolves Python 3 and forwards all arguments to the deterministic routing
    scorer and provider-map validator/renderer.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    [Console]::Error.WriteLine('Error: Python 3 is required to run model-map.py.')
    exit 127
}

& $python.Source (Join-Path $PSScriptRoot 'model-map.py') @args
exit $LASTEXITCODE
