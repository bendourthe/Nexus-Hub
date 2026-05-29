<#
.SYNOPSIS
    Deterministic Volatility 3 triage wrapper (defensive). PowerShell sibling
    of volatility-runner.sh.

.DESCRIPTION
    Runs a fixed, read-only triage plugin set against a memory image using a
    locally-installed Volatility 3 ('vol') and writes each plugin's output to
    a per-case directory for review. Makes ZERO network calls; relies on the
    symbol tables bundled with the local Volatility 3 install. Never executes
    carved samples.

.PARAMETER ImagePath
    Path to the memory image to triage.

.PARAMETER OutputDir
    Directory for per-plugin output. Defaults to .\vol-triage-<image-basename>.

.PARAMETER Os
    Plugin family: windows (default), linux, or mac.

.EXAMPLE
    .\volatility-runner.ps1 -ImagePath capture.raw
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$ImagePath,

    [Parameter(Position = 1)]
    [string]$OutputDir,

    [ValidateSet('windows', 'linux', 'mac')]
    [string]$Os = 'windows'
)

$ErrorActionPreference = 'Stop'

function Write-InfoLine  { param([string]$Message) Write-Host "[INFO]  $Message" }
function Write-ErrorLine { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

# --- Preconditions ----------------------------------------------------------

if (-not (Get-Command vol -ErrorAction SilentlyContinue)) {
    Write-ErrorLine "Volatility 3 ('vol') not found on PATH. Install it first; this wrapper fetches nothing."
    exit 1
}

if (-not (Test-Path -LiteralPath $ImagePath -PathType Leaf)) {
    Write-ErrorLine "image not found: $ImagePath"
    exit 1
}

if (-not $OutputDir) {
    $OutputDir = ".\vol-triage-$(Split-Path -Leaf $ImagePath)"
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# --- Fixed triage plugin set (per OS family) --------------------------------

$plugins = switch ($Os) {
    'windows' { @('windows.pstree', 'windows.psscan', 'windows.dlllist', 'windows.malfind', 'windows.netscan', 'windows.handles', 'windows.cmdline') }
    'linux'   { @('linux.pstree', 'linux.pslist', 'linux.lsmod', 'linux.malfind', 'linux.sockstat', 'linux.bash') }
    'mac'     { @('mac.pstree', 'mac.pslist', 'mac.lsmod', 'mac.malfind', 'mac.netstat') }
}

# --- Run ---------------------------------------------------------------------

Write-InfoLine "Image:      $ImagePath"
Write-InfoLine "OS family:  $Os"
Write-InfoLine "Output dir: $OutputDir"

# Record the image hash for chain of custody (matches SKILL.md step 1).
try {
    $hash = Get-FileHash -LiteralPath $ImagePath -Algorithm SHA256
    "$($hash.Hash)  $ImagePath" | Out-File -FilePath (Join-Path $OutputDir 'image.sha256') -Encoding utf8
} catch {
    Write-ErrorLine "hashing failed: $($_.Exception.Message)"
}

$failed = 0
foreach ($plugin in $plugins) {
    $outFile = Join-Path $OutputDir "$plugin.txt"
    $errFile = Join-Path $OutputDir "$plugin.err"
    Write-InfoLine "Running $plugin ..."
    # Guard each plugin so one unsupported plugin does not abort the run.
    try {
        & vol -f $ImagePath $plugin > $outFile 2> $errFile
        if ($LASTEXITCODE -ne 0) {
            Write-ErrorLine "$plugin failed (see $plugin.err)"
            $failed++
        }
    } catch {
        Write-ErrorLine "$plugin failed: $($_.Exception.Message)"
        $failed++
    }
}

Write-InfoLine "Triage complete. $failed plugin(s) failed; output under $OutputDir"
Write-InfoLine "Review output statically. Do NOT execute any carved sample."
exit 0
