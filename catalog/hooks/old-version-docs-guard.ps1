<#
.SYNOPSIS
    PowerShell parity for old-version-docs-guard.sh.

.DESCRIPTION
    PreToolUse hook that reads a Claude Code JSON payload from stdin, detects
    whether the target file path is inside a recognized historical release directory
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

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
$script:NexusTag = "[Nexus-Hub: old-version-docs-guard]"
# Make CR, LF, ESC and the other C0 control characters in an echoed value
# visible, so a file name or command cannot start a forged tagged line.
function ConvertTo-NexusVisible {
    param([string]$Value)
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in "$Value".ToCharArray()) {
        $code = [int]$ch
        if ($code -eq 9) { [void]$sb.Append('\t') }
        elseif ($code -eq 10) { [void]$sb.Append('\n') }
        elseif ($code -eq 13) { [void]$sb.Append('\r') }
        elseif ($code -lt 32 -or $code -eq 127) { [void]$sb.Append(('\x{0:x2}' -f $code)) }
        else { [void]$sb.Append($ch) }
    }
    return $sb.ToString()
}
# Print the tag and the message to stderr; every further line is printed as is.
function Write-NexusMessage {
    param([string]$Message, [string[]]$More = @())
    [Console]::Error.WriteLine("$script:NexusTag $Message")
    foreach ($line in $More) { [Console]::Error.WriteLine($line) }
}

$blocking = if ($env:NEXUS_OLD_DOCS_GUARD) { $env:NEXUS_OLD_DOCS_GUARD } else { "warn" }

# --- Read JSON from stdin ---
# Hook payloads are UTF-8 whatever the console code page is (WN-37): decode the raw
# handle and reply through UTF-8 writers rather than calling SetConsoleCP.
$hookUtf8 = New-Object System.Text.UTF8Encoding($false)
$raw = (New-Object System.IO.StreamReader([Console]::OpenStandardInput(), $hookUtf8, $true)).ReadToEnd()
# Windows PowerShell 5.1 without a console drains the raw handle into [Console]::In.
if (-not $raw) { $raw = [Console]::In.ReadToEnd() }
$utf8Writer = New-Object System.IO.StreamWriter([Console]::OpenStandardOutput(), $hookUtf8); $utf8Writer.AutoFlush = $true; [Console]::SetOut($utf8Writer)
$utf8Writer = New-Object System.IO.StreamWriter([Console]::OpenStandardError(), $hookUtf8); $utf8Writer.AutoFlush = $true; [Console]::SetError($utf8Writer)
if (-not $raw) { exit 0 }

try {
    $payload = $raw | ConvertFrom-Json
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

# Resolve the target version across canonical and legacy layouts.
$targetVersion = $null
if ($normPath -match '(^|/)docs/(releases|archives)/v[0-9]+/v([0-9]+(\.[0-9]+){1,2})(/|$)') {
    $targetVersion = $matches[3]
} elseif ($normPath -match '(^|/)docs/(archive/)?v[0-9]+/v([0-9]+(\.[0-9]+){1,2})(/|$)') {
    $targetVersion = $matches[3]
} elseif ($normPath -match '(^|/)docs/(archive/)?versions/v[0-9]+/v([0-9]+(\.[0-9]+){1,2})(/|$)') {
    $targetVersion = $matches[3]
} elseif ($normPath -match '(^|/)docs/(archive/)?v([0-9]+\.[0-9]+\.[0-9]+)(/|$)') {
    $targetVersion = $matches[3]
} else {
    exit 0
}

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

# --- Detect active version from the resolved active container ---
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

function Get-LatestVersion {
    param([object[]]$Directories, [string]$Pattern)
    $latest = $null
    foreach ($d in @($Directories)) {
        if ($d.Name -match $Pattern) {
            $candidate = $matches[1]
            if (-not $latest -or (Test-SemverGt $candidate $latest)) {
                $latest = $candidate
            }
        }
    }
    return $latest
}

function Get-VersionChildren {
    param([string]$Container)
    if (-not (Test-Path $Container -PathType Container)) { return @() }
    $children = @()
    foreach ($parent in @(Get-ChildItem -Path $Container -Directory -ErrorAction SilentlyContinue)) {
        $children += @(Get-ChildItem -Path $parent.FullName -Directory -ErrorAction SilentlyContinue)
    }
    return $children
}

function Get-DeclaredVersion {
    # Prefer the DECLARED project version over the newest directory on disk. A
    # repository that keeps directories for roadmapped future work would
    # otherwise resolve its active version to the furthest-future plan
    # directory, making every write to the version actually being built warn
    # while writes to future directories stayed silent.
    param([string]$DocsRoot)
    $manifest = Join-Path (Split-Path -Parent $DocsRoot) '.claude-plugin/plugin.json'
    if (-not (Test-Path -LiteralPath $manifest)) { return $null }
    try {
        $raw = Get-Content -LiteralPath $manifest -Raw -ErrorAction Stop | ConvertFrom-Json
    } catch { return $null }
    $version = [string]$raw.version
    if ($version -match '^([0-9]+\.[0-9]+)') { return $matches[1] }
    return $null
}

$active = Get-DeclaredVersion $docsRoot

# Match the docs-layout-refactor resolution order. A populated canonical layout
# wins; later legacy layouts are consulted only when the earlier one is absent.
if (-not $active) {
    $active = Get-LatestVersion @(Get-VersionChildren (Join-Path $docsRoot 'releases')) '^v([0-9]+(\.[0-9]+){1,2})$'
}
if (-not $active) {
    $active = Get-LatestVersion @(Get-VersionChildren $docsRoot) '^v([0-9]+(\.[0-9]+){1,2})$'
}
if (-not $active) {
    $active = Get-LatestVersion @(Get-ChildItem -Path $docsRoot -Directory -ErrorAction SilentlyContinue) '^v([0-9]+\.[0-9]+\.[0-9]+)$'
}
if (-not $active) {
    $active = Get-LatestVersion @(Get-VersionChildren (Join-Path $docsRoot 'versions')) '^v([0-9]+(\.[0-9]+){1,2})$'
}
if (-not $active) { exit 0 }

# Silent if target is the active version or newer.
if (-not (Test-SemverGt $active $targetVersion)) { exit 0 }

# --- Emit warning (stderr) ---
$msg = "Writing to historical version v$targetVersion under $(ConvertTo-NexusVisible $normPath) (active is v$active). Consider /update refactor to archive instead."

if ($blocking -eq "block") {
    Write-NexusMessage $msg
    Write-NexusMessage "Blocked by NEXUS_OLD_DOCS_GUARD=block. Set it to 'warn' or unset to bypass."
    exit 1
}

Write-NexusMessage $msg
exit 0
