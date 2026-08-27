<#
.SYNOPSIS
    PowerShell parity for session-summary.sh.

.DESCRIPTION
    Stop / PreCompact / SessionEnd hook for Nexus-Hub. Two jobs:
      1. Append a one-line entry to $HOME/.claude/session-log.md (mirrors .sh).
      2. Write a compact, project-scoped context digest at
         `.nexus/context/last-session.md` so the next SessionStart can read it.

    The digest is the local-only reverse-engineered subset of ECC's
    memory-persistence pattern (legacy migration source: docs/archive/v2/v2.3/plans/adoption-ecc-cybersec-skills.md
    T007). No network calls; reads/writes are local only.

.NOTES
    Runtime controls (all optional):
      $env:NEXUS_DISABLED_HOOKS = 'session-summary'  skip both jobs
      $env:NEXUS_HOOK_PROFILE   = 'minimal'           skip both jobs
      $env:NEXUS_SESSION_DIGEST = 'off'               skip digest write only
      $env:NEXUS_SESSION_DIGEST_PATH = '<path>'       override digest path (project-relative)
#>

$ErrorActionPreference = "Continue"

$hookName = "session-summary"
$disabled = $env:NEXUS_DISABLED_HOOKS
if ($disabled -and $disabled.Split(',') -contains $hookName) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

$logFile = Join-Path $HOME ".claude\session-log.md"

# --- Ensure log file exists with headers ---
if (-not (Test-Path $logFile)) {
    $logDir = Split-Path $logFile -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    @(
        "# Claude Code Session Log",
        "",
        "| Date | Project | Duration | Files Changed |",
        "|------|---------|----------|---------------|"
    ) | Out-File -FilePath $logFile -Encoding utf8
}

# --- Gather data ---
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$projectName = Split-Path (Get-Location).Path -Leaf

# Try to read duration from stdin JSON.
$duration = "N/A"
try {
    $stdin = [Console]::In.ReadToEnd()
    if ($stdin) {
        $payload = $stdin | ConvertFrom-Json -ErrorAction Stop
        $parsed = $null
        if ($payload.PSObject.Properties.Name -contains 'session_duration') { $parsed = $payload.session_duration }
        elseif ($payload.PSObject.Properties.Name -contains 'duration') { $parsed = $payload.duration }
        if ($parsed) { $duration = "$parsed" }
    }
} catch {}

# --- Git data ---
$filesChanged = "N/A"
$changedFiles = @()
$inRepo = $false
try {
    $null = git rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -eq 0) { $inRepo = $true }
} catch {}

if ($inRepo) {
    $diffStat = git diff --stat HEAD 2>$null | Select-Object -Last 1
    if ($diffStat) {
        $m = [regex]::Match($diffStat, '(\d+)\s+file')
        if ($m.Success) { $filesChanged = $m.Groups[1].Value }
    } else {
        $filesChanged = "0"
    }
    $diffNames = git diff --name-only HEAD 2>$null
    if ($diffNames) { $changedFiles = $diffNames | Select-Object -First 30 }
}

# --- Append entry to global session log ---
"| $timestamp | $projectName | $duration | $filesChanged |" |
    Add-Content -Path $logFile -Encoding utf8

# --- Write project-scoped context digest ---
if ($env:NEXUS_SESSION_DIGEST -eq "off") { exit 0 }

$projectRoot = (Get-Location).Path
if ($inRepo) {
    try {
        $gitTop = (git rev-parse --show-toplevel 2>$null)
        if ($LASTEXITCODE -eq 0 -and $gitTop) { $projectRoot = $gitTop }
    } catch {}
}

$digestRel = if ($env:NEXUS_SESSION_DIGEST_PATH) { $env:NEXUS_SESSION_DIGEST_PATH } else { ".nexus/context/last-session.md" }
$digestPath = Join-Path $projectRoot $digestRel
$digestDir = Split-Path $digestPath -Parent

try {
    if (-not (Test-Path $digestDir)) {
        New-Item -ItemType Directory -Path $digestDir -Force | Out-Null
    }
} catch { exit 0 }

# --- Build git context for the digest ---
$branch = "unknown"
$statusLine = "not a git repo"
$recentCommits = @()
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
    $recentCommits = git log --oneline -5 2>$null
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Last session digest")
$lines.Add("")
$lines.Add("Generated: $timestamp")
$lines.Add("Project: $projectName")
$lines.Add("Duration: $duration")
$lines.Add("")
$lines.Add("## Git context")
$lines.Add("")
# NOTE (v3.15.6): this line previously read "- Branch: `$branch`" in a
# double-quoted string, which is broken twice over, because the backtick is
# PowerShell's escape character: `$branch emitted the LITERAL text "$branch"
# instead of the value, and the trailing backtick escaped the closing quote so the
# string never terminated. The result was a parse error that made this entire hook
# non-functional on Windows from v3.11.0 until the v3.15.6 AST gate caught it.
# Single quotes plus concatenation avoids the escape rules entirely and matches
# the .sh sibling's output exactly (a markdown code span around the value).
$lines.Add('- Branch: `' + $branch + '`')
$lines.Add("- Status: $statusLine")
$lines.Add("")
if ($recentCommits -and $recentCommits.Count -gt 0) {
    $lines.Add("## Recent commits")
    $lines.Add("")
    $lines.Add('```')
    foreach ($c in $recentCommits) { $lines.Add($c) }
    $lines.Add('```')
    $lines.Add("")
}
if ($changedFiles -and $changedFiles.Count -gt 0) {
    $lines.Add("## Files touched this session")
    $lines.Add("")
    $lines.Add('```')
    foreach ($f in $changedFiles) { $lines.Add($f) }
    $lines.Add('```')
    $lines.Add("")
}

# Atomic write: temp file + Move-Item.
$tmp = "$digestPath.tmp.$PID"
try {
    $lines -join "`n" | Out-File -FilePath $tmp -Encoding utf8 -NoNewline
    Move-Item -Path $tmp -Destination $digestPath -Force
} catch {
    if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
}

exit 0
