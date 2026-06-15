<#
.SYNOPSIS
    discover-sessions.ps1 - Locate local prior-context source files (zero-outbound).

.DESCRIPTION
    PowerShell sibling of discover-sessions.sh, kept in lockstep behavior parity
    per the AGENTS.md cross-platform rule. Prints one "tool<TAB>path" line per
    discovered source file across the known local roots. The output is designed
    to be piped into extract-session.py / extract-session.ps1, which uses the
    "tool" tag to select the right parser.

    Sources:
      - JSONL session logs: Claude Code, Codex, Cursor (scanned by default)
      - Obsidian vault notes (.md), selected with -Tool obsidian
      - Exported ChatGPT history (conversations.json), selected with -Tool chatgpt
      - Exported Gemini history ("My Activity" JSON), selected with -Tool gemini

    The default (no -Tool) scan covers ONLY the three JSONL tools, so existing
    behavior is unchanged. The Obsidian / ChatGPT / Gemini sources are opt-in via
    -Tool (with a sensible default root) or -Root, and emit nothing when absent.

    This script only reads the local filesystem: no network call is made.

.PARAMETER Tool
    Restrict to one source: claude | codex | cursor (JSONL), or
    obsidian | chatgpt | gemini (the non-JSONL sources).
.PARAMETER Root
    Scan custom directories. Tagged by -Tool when that tool is
    obsidian/chatgpt/gemini, else "custom" (JSONL) - the unchanged legacy behavior.

.EXAMPLE
    .\discover-sessions.ps1
.EXAMPLE
    .\discover-sessions.ps1 -Tool obsidian
.EXAMPLE
    .\discover-sessions.ps1 -Root C:\path\to\vault -Tool obsidian
#>
[CmdletBinding()]
param(
    [ValidateSet("claude", "codex", "cursor", "obsidian", "chatgpt", "gemini")]
    [string]$Tool,
    [string[]]$Root = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Emit *.jsonl transcripts under a directory, tagged with the given tool.
function Write-JsonlMatches {
    param([string]$ToolName, [string]$Dir)
    if (-not $Dir -or -not (Test-Path -LiteralPath $Dir -PathType Container)) { return }
    Get-ChildItem -LiteralPath $Dir -Recurse -File -Filter *.jsonl -ErrorAction SilentlyContinue |
        ForEach-Object { "{0}`t{1}" -f $ToolName, $_.FullName }
}

# Emit Obsidian notes: locate vault roots by the .obsidian marker and print
# their *.md notes; fall back to a plain *.md folder when no marker is found.
function Write-ObsidianMatches {
    param([string]$Dir)
    if (-not $Dir -or -not (Test-Path -LiteralPath $Dir -PathType Container)) { return }
    $markers = @(Get-ChildItem -LiteralPath $Dir -Recurse -Directory -Filter ".obsidian" -ErrorAction SilentlyContinue)
    if ($markers.Count -gt 0) {
        foreach ($marker in $markers) {
            $vault = Split-Path -Parent $marker.FullName
            Get-ChildItem -LiteralPath $vault -Recurse -File -Filter *.md -ErrorAction SilentlyContinue |
                Where-Object { $_.FullName -notmatch '[\\/]\.obsidian[\\/]' } |
                ForEach-Object { "obsidian`t{0}" -f $_.FullName }
        }
    } else {
        Get-ChildItem -LiteralPath $Dir -Recurse -File -Filter *.md -ErrorAction SilentlyContinue |
            ForEach-Object { "obsidian`t{0}" -f $_.FullName }
    }
}

# Emit exported ChatGPT/Gemini history files. In "default" mode (a broad
# download root) match only the canonical export name to avoid noise; in
# "explicit" mode (a user-supplied -Root) emit all .json / .md export files.
function Write-ExportMatches {
    param([string]$ToolName, [string]$Dir, [string]$Mode)
    if (-not $Dir -or -not (Test-Path -LiteralPath $Dir -PathType Container)) { return }
    if ($Mode -eq "default") {
        $namePat = if ($ToolName -eq "chatgpt") { "conversations.json" } else { "*ctivity*.json" }
        Get-ChildItem -LiteralPath $Dir -Recurse -File -Filter $namePat -ErrorAction SilentlyContinue |
            ForEach-Object { "{0}`t{1}" -f $ToolName, $_.FullName }
    } else {
        foreach ($pat in @("*.json", "*.md")) {
            Get-ChildItem -LiteralPath $Dir -Recurse -File -Filter $pat -ErrorAction SilentlyContinue |
                ForEach-Object { "{0}`t{1}" -f $ToolName, $_.FullName }
        }
    }
}

$homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
$claudeRoot   = Join-Path $homeDir ".claude/projects"
$codexRoot    = Join-Path $homeDir ".codex"
$cursorRoot   = Join-Path $homeDir ".cursor"
$obsidianRoot = Join-Path $homeDir "Documents"
$chatgptRoot  = Join-Path $homeDir "Downloads"
$geminiRoot   = Join-Path $homeDir "Downloads"

# Custom -Root: tag by the new sources when requested, else "custom" JSONL.
if ($Root.Count -gt 0) {
    foreach ($d in $Root) {
        switch ($Tool) {
            "obsidian" { Write-ObsidianMatches -Dir $d }
            "chatgpt"  { Write-ExportMatches -ToolName "chatgpt" -Dir $d -Mode "explicit" }
            "gemini"   { Write-ExportMatches -ToolName "gemini" -Dir $d -Mode "explicit" }
            default    { Write-JsonlMatches -ToolName "custom" -Dir $d }
        }
    }
    return
}

# No custom root: scan default roots. The empty (no -Tool) case covers ONLY the
# three JSONL tools, exactly as before.
switch ($Tool) {
    "obsidian" { Write-ObsidianMatches -Dir $obsidianRoot }
    "chatgpt"  { Write-ExportMatches -ToolName "chatgpt" -Dir $chatgptRoot -Mode "default" }
    "gemini"   { Write-ExportMatches -ToolName "gemini" -Dir $geminiRoot -Mode "default" }
    "claude"   { Write-JsonlMatches -ToolName "claude" -Dir $claudeRoot }
    "codex"    { Write-JsonlMatches -ToolName "codex" -Dir $codexRoot }
    "cursor"   { Write-JsonlMatches -ToolName "cursor" -Dir $cursorRoot }
    default {
        Write-JsonlMatches -ToolName "claude" -Dir $claudeRoot
        Write-JsonlMatches -ToolName "codex" -Dir $codexRoot
        Write-JsonlMatches -ToolName "cursor" -Dir $cursorRoot
    }
}
