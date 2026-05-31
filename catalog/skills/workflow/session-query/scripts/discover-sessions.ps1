<#
.SYNOPSIS
    discover-sessions.ps1 - Locate local AI session-log JSONL files (zero-outbound).

.DESCRIPTION
    PowerShell sibling of discover-sessions.sh, kept in lockstep behavior parity
    per the AGENTS.md cross-platform rule. Prints one "tool<TAB>path" line per
    discovered *.jsonl transcript across the known local session-log roots for
    Claude Code, Codex, and Cursor. The output is designed to be piped into
    extract-session.py / extract-session.ps1.

    This script only reads the local filesystem: no network call is made.

.PARAMETER Tool
    Restrict to one known tool root: claude | codex | cursor.
.PARAMETER Root
    Scan custom directories (labelled "custom") instead of the known roots.

.EXAMPLE
    .\discover-sessions.ps1
.EXAMPLE
    .\discover-sessions.ps1 -Tool claude
.EXAMPLE
    .\discover-sessions.ps1 -Root C:\path\to\logs
#>
[CmdletBinding()]
param(
    [ValidateSet("claude", "codex", "cursor")]
    [string]$Tool,
    [string[]]$Root = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-RootMatches {
    param([string]$ToolName, [string]$Dir)
    if (-not $Dir -or -not (Test-Path -LiteralPath $Dir -PathType Container)) { return }
    Get-ChildItem -LiteralPath $Dir -Recurse -File -Filter *.jsonl -ErrorAction SilentlyContinue |
        ForEach-Object { "{0}`t{1}" -f $ToolName, $_.FullName }
}

if ($Root.Count -gt 0) {
    foreach ($d in $Root) { Write-RootMatches -ToolName "custom" -Dir $d }
    return
}

$homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
$claudeRoot = Join-Path $homeDir ".claude/projects"
$codexRoot  = Join-Path $homeDir ".codex"
$cursorRoot = Join-Path $homeDir ".cursor"

if (-not $Tool -or $Tool -eq "claude") { Write-RootMatches -ToolName "claude" -Dir $claudeRoot }
if (-not $Tool -or $Tool -eq "codex")  { Write-RootMatches -ToolName "codex"  -Dir $codexRoot }
if (-not $Tool -or $Tool -eq "cursor") { Write-RootMatches -ToolName "cursor" -Dir $cursorRoot }
