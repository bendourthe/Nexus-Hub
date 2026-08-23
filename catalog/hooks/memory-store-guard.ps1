<#
.SYNOPSIS
    PowerShell parity for memory-store-guard.sh.

.DESCRIPTION
    PreToolUse hook that blocks writing or committing a relocated
    nexus-memory store that sits inside a git working tree.

    Like secret-scan, this is a security gate: it does not honor
    NEXUS_HOOK_PROFILE=minimal or NEXUS_DISABLED_HOOKS. The only
    override is NEXUS_MEMORY_ALLOW_IN_REPO=1.

.NOTES
    Mirrors the .sh implementation so Windows users who run hooks
    through PowerShell get the same guardrail.
#>

$ErrorActionPreference = "Continue"

$allow = $env:NEXUS_MEMORY_ALLOW_IN_REPO
if ($allow -and @("1", "true", "yes", "on") -contains $allow.ToLowerInvariant()) {
    exit 0
}

if (-not [Console]::IsInputRedirected) { exit 0 }
$inputText = [Console]::In.ReadToEnd()
if (-not $inputText) { exit 0 }

try {
    $payload = $inputText | ConvertFrom-Json
} catch {
    exit 0
}

function Get-NormalizedPath {
    param([string]$PathValue)
    if (-not $PathValue) { return "" }
    return ($PathValue -replace '\\', '/')
}

function Test-StoreArtifact {
    param([string]$PathValue)
    $norm = Get-NormalizedPath $PathValue
    if (-not $norm) { return $false }
    $base = [System.IO.Path]::GetFileName($norm)
    $dir = [System.IO.Path]::GetDirectoryName($norm)
    if (-not $dir) { $dir = "." }

    if ($base -eq ".nexus-memory-store") { return $true }
    if ($norm -match '\.nexus-hub/memory/') {
        if (@("entries.log", "entries.lock", "config.json", ".nexus-memory-store") -contains $base) {
            return $true
        }
        if ($norm -match '/tree/level_') { return $true }
    }
    if ($base -eq "entries.log" -or $base -eq "entries.lock") {
        if (Test-Path -LiteralPath (Join-Path $dir ".nexus-memory-store") -PathType Leaf) {
            return $true
        }
        $cfg = Join-Path $dir "config.json"
        if ((Test-Path -LiteralPath $cfg -PathType Leaf) -and ((Get-Content -LiteralPath $cfg -Raw -ErrorAction SilentlyContinue) -match '"record_width"')) {
            return $true
        }
        if ([System.IO.Path]::GetFileName($dir) -eq "memory") { return $true }
    }
    if ($norm -match '/tree/level_') {
        $parent = Split-Path -Parent $dir
        if ($parent -and (Test-Path -LiteralPath (Join-Path $parent ".nexus-memory-store") -PathType Leaf)) {
            return $true
        }
        $cfg = if ($parent) { Join-Path $parent "config.json" } else { $null }
        if ($cfg -and (Test-Path -LiteralPath $cfg -PathType Leaf) -and ((Get-Content -LiteralPath $cfg -Raw -ErrorAction SilentlyContinue) -match '"record_width"')) {
            return $true
        }
    }
    return $false
}

function Test-InsideGit {
    param([string]$PathValue)
    $probe = $PathValue
    if (-not (Test-Path -LiteralPath $probe -PathType Container)) {
        $probe = Split-Path -Parent $probe
    }
    if (-not $probe) { return $false }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { return $false }
    $result = & git -C $probe rev-parse --is-inside-work-tree 2>$null
    return ($LASTEXITCODE -eq 0 -and "$result".Trim() -eq "true")
}

function Write-Blocked {
    param([string]$Message)
    [Console]::Error.WriteLine("[memory-store-guard] BLOCKED: $Message")
    [Console]::Error.WriteLine("Relocate the store outside the repository, or set NEXUS_MEMORY_ALLOW_IN_REPO=1 if you accept that this log can be committed.")
    exit 2
}

$filePath = $null
if ($payload.tool_input -and $payload.tool_input.PSObject.Properties.Name -contains "file_path") {
    $filePath = $payload.tool_input.file_path
} elseif ($payload.tool_input -and $payload.tool_input.PSObject.Properties.Name -contains "path") {
    $filePath = $payload.tool_input.path
}

$command = $null
if ($payload.tool_input -and $payload.tool_input.PSObject.Properties.Name -contains "command") {
    $command = [string]$payload.tool_input.command
}

if ($filePath -and (Test-StoreArtifact $filePath) -and (Test-InsideGit $filePath)) {
    Write-Blocked "refusing to write nexus-memory artifact '$filePath' inside a git working tree"
}

if ($command -and ($command -match '(^|[;&|\s])git\s+(add|commit|rm)(\s|$)')) {
    if ($command -match '(^|[\s/\\])(entries\.log|entries\.lock|\.nexus-memory-store|tree/level_)') {
        Write-Blocked "refusing to git-stage a nexus-memory store artifact"
    }
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $inside = & git rev-parse --is-inside-work-tree 2>$null
        if ($LASTEXITCODE -eq 0 -and "$inside".Trim() -eq "true") {
            $staged = & git diff --cached --name-only 2>$null
            foreach ($rel in @($staged)) {
                if (-not $rel) { continue }
                $abs = Join-Path (Get-Location).Path $rel
                if ((Test-StoreArtifact $rel) -or (Test-StoreArtifact $abs)) {
                    Write-Blocked "refused staged nexus-memory artifact '$rel'"
                }
            }
        }
    }
}

exit 0
