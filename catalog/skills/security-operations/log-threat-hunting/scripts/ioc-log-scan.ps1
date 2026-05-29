<#
.SYNOPSIS
    Local, read-only IOC sweep over a log file (defensive). PowerShell sibling
    of ioc-log-scan.sh.

.DESCRIPTION
    Matches every indicator in an IOC list file (one indicator per line; blank
    lines and lines starting with '#' are ignored) against a target log file
    using fixed-string (literal) matching, and reports the per-indicator match
    count plus the matching lines. Purely local: makes NO network calls.

.PARAMETER LogFile
    Path to the log file to scan.

.PARAMETER IocFile
    Path to the IOC list file (one indicator per line).

.PARAMETER MaxLines
    Max matching lines printed per indicator (default 5; 0 = unlimited).

.EXAMPLE
    .\ioc-log-scan.ps1 -LogFile auth.log -IocFile iocs.txt
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$LogFile,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$IocFile,

    [int]$MaxLines = 5
)

$ErrorActionPreference = 'Stop'

function Write-InfoLine  { param([string]$Message) Write-Host "[INFO]  $Message" }
function Write-ErrorLine { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

if (-not (Test-Path -LiteralPath $LogFile -PathType Leaf)) {
    Write-ErrorLine "log file not found: $LogFile"
    exit 2
}
if (-not (Test-Path -LiteralPath $IocFile -PathType Leaf)) {
    Write-ErrorLine "IOC list not found: $IocFile"
    exit 2
}
if ($MaxLines -lt 0) {
    Write-ErrorLine "MaxLines must be a non-negative integer"
    exit 2
}

Write-InfoLine "Log file:  $LogFile"
Write-InfoLine "IOC list:  $IocFile"

$indicators = 0
$totalHits = 0

foreach ($rawIoc in Get-Content -LiteralPath $IocFile) {
    $ioc = $rawIoc.Trim()
    if ([string]::IsNullOrEmpty($ioc)) { continue }
    if ($ioc.StartsWith('#')) { continue }

    $indicators++
    # -SimpleMatch = fixed-string (literal) match, mirroring grep -F.
    $matches = Select-String -LiteralPath $LogFile -Pattern $ioc -SimpleMatch
    $count = @($matches).Count

    if ($count -gt 0) {
        $totalHits += $count
        Write-Host ""
        Write-Host "=== IOC: $ioc  (matches: $count) ==="
        $toShow = if ($MaxLines -eq 0) { $matches } else { $matches | Select-Object -First $MaxLines }
        foreach ($m in $toShow) {
            Write-Host ("{0}:{1}" -f $m.LineNumber, $m.Line)
        }
    }
}

Write-Host ""
Write-Host "[SUMMARY] $indicators indicator(s) scanned, $totalHits total matching line(s)."
exit 0
