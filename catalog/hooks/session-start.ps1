<#
.SYNOPSIS
    PowerShell parity for session-start.sh.

.DESCRIPTION
    SessionStart hook for Nexus-Hub. Prints a brief catalog orientation and the
    git context, then surfaces the project-scoped digest of the previous session
    written by session-summary.ps1 (or .sh) on Stop / PreCompact / SessionEnd.

.NOTES
    Runtime controls (all optional):
      $env:NEXUS_DISABLED_HOOKS = 'session-start'    skip this hook entirely
      $env:NEXUS_HOOK_PROFILE   = 'minimal'           skip this hook entirely
      $env:NEXUS_SESSION_DIGEST = 'off'               skip digest read only
      $env:NEXUS_SESSION_DIGEST_PATH = '<path>'       override digest path (project-relative)
      $env:NEXUS_SESSION_START_MAX_CHARS = '<int>'    cap digest output (default 8000)
#>

$ErrorActionPreference = "Continue"

$hookName = "session-start"
$disabled = $env:NEXUS_DISABLED_HOOKS
if ($disabled -and $disabled.Split(',') -contains $hookName) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

$skillCount = 184
$commandCount = 33

Write-Output "Nexus-Hub is active (v1.1.5) - $skillCount skills, $commandCount commands."
Write-Output ""
Write-Output "Quick navigation:"
Write-Output "  /search-skills <keyword>   Find the right skill for your task"
Write-Output "  /commands-cheatsheet       List all available commands"
Write-Output ""
Write-Output "Full index: data/SKILL_INDEX.md"

# --- Git context ---
$inRepo = $false
try {
    $null = git rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -eq 0) { $inRepo = $true }
} catch { $inRepo = $false }

if ($inRepo) {
    $branch = (git symbolic-ref --short HEAD 2>$null)
    if (-not $branch) { $branch = (git rev-parse --short HEAD 2>$null) }
    if (-not $branch) { $branch = "unknown" }

    $staged    = (git diff --cached --name-only 2>$null | Measure-Object -Line).Lines
    $modified  = (git diff --name-only 2>$null        | Measure-Object -Line).Lines
    $untracked = (git ls-files --others --exclude-standard 2>$null | Measure-Object -Line).Lines

    if ($staged -eq 0 -and $modified -eq 0 -and $untracked -eq 0) {
        $statusLine = "clean"
    } else {
        $statusLine = "$staged staged, $modified modified, $untracked untracked"
    }

    Write-Output ""
    Write-Output "Git context:"
    Write-Output ("  Branch:  {0}" -f $branch)
    Write-Output ("  Status:  {0}" -f $statusLine)
    Write-Output "  Recent commits:"
    $log = git log --oneline -3 2>$null
    if ($log) {
        foreach ($line in $log) { Write-Output ("    {0}" -f $line) }
    }
}

# --- Surface the last-session digest ---
if ($env:NEXUS_SESSION_DIGEST -eq "off") { exit 0 }

$projectRoot = (Get-Location).Path
try {
    $gitTop = (git rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -eq 0 -and $gitTop) { $projectRoot = $gitTop }
} catch {}

$digestRel = if ($env:NEXUS_SESSION_DIGEST_PATH) { $env:NEXUS_SESSION_DIGEST_PATH } else { ".nexus/context/last-session.md" }
$digestPath = Join-Path $projectRoot $digestRel

if (Test-Path $digestPath -PathType Leaf) {
    $maxCharsRaw = if ($env:NEXUS_SESSION_START_MAX_CHARS) { $env:NEXUS_SESSION_START_MAX_CHARS } else { "8000" }
    $maxChars = 0
    if (-not [int]::TryParse($maxCharsRaw, [ref]$maxChars) -or $maxChars -le 0) {
        $maxChars = 8000
    }

    try {
        # Read as UTF-8 so we count characters consistently with the .sh sibling's byte cap.
        $bytes = [System.IO.File]::ReadAllBytes($digestPath)
        $digestText = [System.Text.Encoding]::UTF8.GetString($bytes)
        $truncated = $false
        if ($digestText.Length -gt $maxChars) {
            $digestText = $digestText.Substring(0, $maxChars)
            $truncated = $true
        }

        if ($digestText) {
            Write-Output ""
            Write-Output ("Last session digest ({0}, capped at {1} chars):" -f $digestRel, $maxChars)
            Write-Output ""
            Write-Output $digestText
            if ($truncated) {
                Write-Output ""
                Write-Output ("(digest truncated -- read {0} for the full file)" -f $digestRel)
            }
        }
    } catch {
        # Never fail the hook on read errors.
    }
}

exit 0
