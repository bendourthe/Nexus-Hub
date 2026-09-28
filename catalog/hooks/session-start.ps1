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

# Banner: one line, facts read from real files only (v4.13.3). The version is
# printed only when VERSION holds one bounded semver line; any other payload
# (missing, empty, multi-line, over 32 characters) drops the version and never
# echoes the file. Version and index path come from the same resolved home.
$userHome = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
$homeDir = if ($env:NEXUS_HOME) { $env:NEXUS_HOME } else { Join-Path $userHome ".nexus-hub" }
$version = ""
$versionFile = Join-Path $homeDir "VERSION"
if (Test-Path -LiteralPath $versionFile -PathType Leaf) {
    try {
        $bytes = [System.IO.File]::ReadAllBytes($versionFile)
        $raw = [System.Text.Encoding]::UTF8.GetString($bytes, 0, [Math]::Min($bytes.Length, 64))
        $raw = $raw -replace '(\r?\n)+$', ''
        $raw = $raw -replace '\r$', ''
        if (($raw -notmatch "`n") -and ($raw.Length -le 32) -and ($raw -match '^[0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.]+)?$')) {
            $version = $raw
        }
    } catch { $version = "" }
}
$indexPath = "$homeDir/data/SKILL_INDEX.md"
if ($version) {
    Write-Output "Nexus-Hub v$version active; full skill index: $indexPath"
} else {
    Write-Output "Nexus-Hub active; full skill index: $indexPath"
}

# Git: one line. The harness already supplies branch and recent commits.
$inRepo = $false
if (Get-Command git -ErrorAction SilentlyContinue) {
    $null = git rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -eq 0) { $inRepo = $true }
}
if ($inRepo) {
    $branch = (git symbolic-ref --short HEAD 2>$null)
    if (-not $branch) { $branch = "detached" }
    $changed = @(git status --porcelain 2>$null | Where-Object { $_ -ne "" }).Count
    Write-Output ("Git: {0}, {1} changed file(s)" -f $branch, $changed)
} else {
    Write-Output "Git: unavailable"
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
