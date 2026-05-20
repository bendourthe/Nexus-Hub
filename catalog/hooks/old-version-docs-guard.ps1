<#
.SYNOPSIS
    PowerShell parity for old-version-docs-guard.sh.

.DESCRIPTION
    PreToolUse hook that reads a Claude Code JSON payload from stdin, detects
    whether the target file path is inside a docs/v<old-version>/ directory
    that is older than the active version, and emits an advisory warning.

    Non-blocking by default. Set $env:NEXUS_OLD_DOCS_GUARD = 'block' to upgrade
    to a hard block (exit 1).

    This script mirrors the .sh implementation so Windows users who run hooks
    through PowerShell get the same guardrail.

.NOTES
    Companion command: /refactor-docs proposes structured archival of
    historical version dirs instead of ad-hoc edits.
#>

# Never fail loudly on internal errors.
$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "old-version-docs-guard"
$disabled = $env:NEXUS_DISABLED_HOOKS
if ($disabled -and $disabled.Split(',') -contains $hookName) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

$blocking = if ($env:NEXUS_OLD_DOCS_GUARD) { $env:NEXUS_OLD_DOCS_GUARD } else { "warn" }

# --- Read JSON from stdin ---
$input = [Console]::In.ReadToEnd()
if (-not $input) { exit 0 }

try {
    $payload = $input | ConvertFrom-Json
} catch {
    exit 0
}

$filePath = $null
if ($payload.tool_input.PSObject.Properties.Name -contains 'file_path') {
    $filePath = $payload.tool_input.file_path
} elseif ($payload.tool_input.PSObject.Properties.Name -contains 'path') {
    $filePath = $payload.tool_input.path
}
if (-not $filePath) { exit 0 }

# Normalize separators.
$normPath = $filePath -replace '\\', '/'

# Match docs/v<num>(.<num>)*/ at any depth.
if ($normPath -notmatch '(^|/)docs/v([0-9]+(\.[0-9]+){0,2})(/|$)') {
    exit 0
}
$targetVersion = $matches[2]

# --- Locate docs root by walking up from CWD ---
function Find-DocsRoot {
    $dir = (Get-Location).Path
    while ($dir -and $dir -ne ([System.IO.Path]::GetPathRoot($dir))) {
        $candidate = Join-Path $dir "docs"
        if (Test-Path $candidate -PathType Container) { return $candidate }
        $dir = Split-Path $dir -Parent
    }
    return $null
}

$docsRoot = Find-DocsRoot
if (-not $docsRoot) { exit 0 }

# --- Detect active version (latest docs/v*/ by semver order) ---
function Test-SemverGt {
    param([string]$a, [string]$b)
    $aParts = ($a -split '\.') + @('0', '0', '0') | Select-Object -First 3
    $bParts = ($b -split '\.') + @('0', '0', '0') | Select-Object -First 3
    for ($i = 0; $i -lt 3; $i++) {
        $av = [int]$aParts[$i]
        $bv = [int]$bParts[$i]
        if ($av -gt $bv) { return $true }
        if ($av -lt $bv) { return $false }
    }
    return $false
}

$active = $null
foreach ($d in Get-ChildItem -Path $docsRoot -Directory -ErrorAction SilentlyContinue) {
    if ($d.Name -match '^v([0-9]+(\.[0-9]+){0,2})$') {
        $candidate = $matches[1]
        if (-not $active) {
            $active = $candidate
        } elseif (Test-SemverGt $candidate $active) {
            $active = $candidate
        }
    }
}
if (-not $active) { exit 0 }

# Silent if target is the active version or newer.
if (-not (Test-SemverGt $active $targetVersion)) { exit 0 }

# --- Emit warning (stderr) ---
$msg = "[old-version-docs-guard] Writing to historical version dir docs/v$targetVersion/ (active is v$active). Consider /refactor-docs to archive instead."

if ($blocking -eq "block") {
    [Console]::Error.WriteLine($msg)
    [Console]::Error.WriteLine("[old-version-docs-guard] Blocked by NEXUS_OLD_DOCS_GUARD=block. Set it to 'warn' or unset to bypass.")
    exit 1
}

[Console]::Error.WriteLine($msg)
exit 0
