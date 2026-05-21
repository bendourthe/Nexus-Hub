# new-feature.ps1 -- Resolve the next feature-directory prefix and create the
# directory under specs/. Used by /generate-plan --specs-layout (and other
# spec-driven commands) to pick a sequential or timestamp prefix without
# coupling the agent flow to git branch state.
#
# Usage:
#   scripts\new-feature.ps1 <slug>
#   scripts\new-feature.ps1 -Style sequential <slug>
#   scripts\new-feature.ps1 -Style timestamp <slug>
#   scripts\new-feature.ps1 -RepoRoot C:\path\to\repo <slug>
#
# Behavior:
# - Reads .specify\init-options.json at the repo root for the key
#   "branch_numbering" (values: sequential | timestamp). Falls back to
#   sequential when the file is missing or unreadable.
# - Sequential mode scans specs\*\ for directories matching ^[0-9]{3}- and
#   picks the next available three-digit number (start at 001 on empty).
# - Timestamp mode uses UTC time formatted as YYYYMMDD-HHMMSS.
# - Creates the resolved directory under specs\<prefix>-<slug>\.
# - Writes .specify\feature.json with {"feature_directory": "..."}.
# - Prints the resolved relative directory path on stdout. Exits non-zero
#   on collision unless -Force is passed.
#
# Cross-platform parity: scripts/new-feature.sh implements the same
# behavior on POSIX. Keep the two in lockstep per AGENTS.md.

[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Slug,

    [Parameter(Mandatory = $false)]
    [ValidateSet('sequential', 'timestamp', '')]
    [string]$Style = '',

    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = '',

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Write-LogInfo  { param([string]$Message) [Console]::Error.WriteLine("[INFO]  $Message") }
function Write-LogError { param([string]$Message) [Console]::Error.WriteLine("[ERROR] $Message") }

function Show-Usage {
    [Console]::Error.WriteLine(@'
Usage: new-feature.ps1 [-Style sequential|timestamp] [-RepoRoot PATH] [-Force] <slug>

Resolves the next specs\<prefix>-<slug>\ directory and creates it.
Prints the relative path on stdout.
'@)
}

if ([string]::IsNullOrWhiteSpace($Slug)) {
    Show-Usage
    exit 2
}

# Sanitize the slug to [a-z0-9-]+ defensively.
$sanitized = $Slug.ToLowerInvariant()
$sanitized = ($sanitized -replace '[ _]', '-')
$sanitized = ($sanitized -replace '[^a-z0-9-]', '')
if ([string]::IsNullOrWhiteSpace($sanitized)) {
    Write-LogError "Slug sanitized to empty string -- refusing"
    exit 1
}

$reserved = @('index', 'readme', 'template')
if ($reserved -contains $sanitized) {
    Write-LogError "Reserved slug: $sanitized"
    exit 1
}

# --- Resolve repo root ---------------------------------------------------

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        try {
            $resolved = (& git rev-parse --show-toplevel 2>$null)
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
                $RepoRoot = $resolved.Trim()
            }
        } catch {
            # ignore; fall back to current dir
        }
    }
    if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
        $RepoRoot = (Get-Location).Path
    }
}

if (-not (Test-Path $RepoRoot -PathType Container)) {
    Write-LogError "Repo root does not exist: $RepoRoot"
    exit 1
}

# --- Resolve numbering style --------------------------------------------

$initOptions = Join-Path $RepoRoot ".specify\init-options.json"
if ([string]::IsNullOrWhiteSpace($Style) -and (Test-Path $initOptions -PathType Leaf)) {
    try {
        $raw = Get-Content -Path $initOptions -Raw -ErrorAction Stop
        $parsed = $raw | ConvertFrom-Json -ErrorAction Stop
        if ($parsed.PSObject.Properties.Name -contains 'branch_numbering') {
            $candidate = "$($parsed.branch_numbering)"
            if (@('sequential', 'timestamp') -contains $candidate) {
                $Style = $candidate
            }
        }
    } catch {
        Write-LogInfo "Failed to parse $initOptions -- defaulting to sequential"
    }
}

if ([string]::IsNullOrWhiteSpace($Style)) {
    $Style = 'sequential'
}

# --- Resolve prefix -----------------------------------------------------

$specsDir = Join-Path $RepoRoot "specs"
if (-not (Test-Path $specsDir -PathType Container)) {
    New-Item -ItemType Directory -Path $specsDir | Out-Null
}

$prefix = ''
if ($Style -eq 'sequential') {
    $next = 1
    Get-ChildItem -Path $specsDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.Name -match '^([0-9]{3})-') {
            $existing = [int]$Matches[1]
            if ($existing -ge $next) {
                $next = $existing + 1
            }
        }
    }
    $prefix = '{0:D3}' -f $next
} else {
    $prefix = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
}

# --- Construct and create directory -------------------------------------

$dirName = "$prefix-$sanitized"
$target = Join-Path $specsDir $dirName

if (Test-Path $target -PathType Container) {
    if (-not $Force) {
        Write-LogError "Directory already exists: $target (pass -Force to reuse)"
        exit 3
    }
}

New-Item -ItemType Directory -Force -Path $target | Out-Null

# --- Persist feature.json ----------------------------------------------

$specifyDir = Join-Path $RepoRoot ".specify"
if (-not (Test-Path $specifyDir -PathType Container)) {
    New-Item -ItemType Directory -Path $specifyDir | Out-Null
}

$featureJson = Join-Path $specifyDir "feature.json"
$relPath = "specs/$dirName"

$jsonPayload = @{
    feature_directory = $relPath
} | ConvertTo-Json -Depth 3

# Write atomically: write to a temp file, then move.
$tmpFile = "$featureJson.tmp.$([System.Guid]::NewGuid().ToString('N'))"
$jsonPayload | Out-File -FilePath $tmpFile -Encoding utf8 -NoNewline
if (Test-Path $featureJson) {
    Remove-Item -Path $featureJson -Force
}
Move-Item -Path $tmpFile -Destination $featureJson

# --- Output -------------------------------------------------------------

Write-Output $relPath
Write-LogInfo "Created $relPath (style=$Style, prefix=$prefix)"
Write-LogInfo "Persisted $featureJson"
