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
      $env:NEXUS_WORKTREE_NOTICE = 'off'              skip the worktree placement notice
      $env:NEXUS_LANE_NOTICE = 'off'                  skip the idle minor-run lane notice
#>

$ErrorActionPreference = "Continue"

$hookName = "session-start"
$disabled = $env:NEXUS_DISABLED_HOOKS
if ($disabled -and $disabled.Split(',') -contains $hookName) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
$script:NexusTag = "[Nexus-Hub: session-start]"
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
# Print the tag and the message to stdout (SessionStart context the agent
# reads); every further line is printed as is.
function Write-NexusMessage {
    param([string]$Message, [string[]]$More = @())
    Write-Output "$script:NexusTag $Message"
    foreach ($line in $More) { Write-Output $line }
}

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
$indexShown = ConvertTo-NexusVisible $indexPath
if ($version) {
    $banner = "Nexus-Hub v$version active; full skill index: $indexShown"
} else {
    $banner = "Nexus-Hub active; full skill index: $indexShown"
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
    $gitLine = ("Git: {0}, {1} changed file(s)" -f (ConvertTo-NexusVisible $branch), $changed)
} else {
    $gitLine = "Git: unavailable"
}
Write-NexusMessage $banner @($gitLine)
Write-NexusMessage "Implementation status: use implement-phase/scripts/status_report.py; during a run its verbatim report replaces the Completed / Verified / Open / Next summary and any insight boxes; full at start/resume, new decisions and requests; compact at material checkpoints or after 5 minutes at a reporting boundary; no report on tool narration. Keep spaced Status, Goals, Decisions and Running headings."

# --- Worktree placement notice (v4.15.6) ---
# Local and read-only: runs the installed nexus_worktrees.py list for the
# current repository (git only, no network) and prints one line when a linked
# worktree sits outside <root>/<identity> or is prunable. Silent outside a
# repository, when the helper is not installed, on any error, and when clean.
$wtHelper = Join-Path (Join-Path $homeDir "scripts") "nexus_worktrees.py"
if ($inRepo -and ($env:NEXUS_WORKTREE_NOTICE -ne "off") -and (Test-Path -LiteralPath $wtHelper -PathType Leaf)) {
    $wtTop = (git rev-parse --show-toplevel 2>$null)
    if ($wtTop) {
        foreach ($wtPython in @("python3", "python")) {
            $wtJson = ""
            try {
                $wtPsi = New-Object System.Diagnostics.ProcessStartInfo
                $wtPsi.FileName = $wtPython
                $wtPsi.Arguments = '-B "' + $wtHelper + '" list --repo "' + $wtTop + '" --json'
                $wtPsi.UseShellExecute = $false
                $wtPsi.CreateNoWindow = $true
                $wtPsi.RedirectStandardOutput = $true
                $wtPsi.RedirectStandardError = $true
                $wtPsi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
                $wtPsi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
                $wtProc = [System.Diagnostics.Process]::Start($wtPsi)
                $wtOutTask = $wtProc.StandardOutput.ReadToEndAsync()
                $null = $wtProc.StandardError.ReadToEndAsync()
                if ($wtProc.WaitForExit(10000)) {
                    $wtJson = $wtOutTask.Result
                } else {
                    try { $wtProc.Kill() } catch { }
                }
            } catch { $wtJson = "" }
            if (-not $wtJson) { continue }
            try {
                $wtData = $wtJson | ConvertFrom-Json
                $wtLinked = @($wtData.worktrees | Where-Object { -not $_.main })
                $wtOutside = @($wtLinked | Where-Object { $_.in_policy -eq $false }).Count
                $wtPrunable = @($wtLinked | Where-Object { $_.prunable }).Count
                if ($wtOutside -or $wtPrunable) {
                    $wtDest = Join-Path ([string]$wtData.root) ([string]$wtData.identity)
                    $wtLine = "Worktrees: {0} outside {1}, {2} prunable. Run the worktree hygiene step (using-git-worktrees)." -f $wtOutside, $wtDest, $wtPrunable
                    Write-NexusMessage (ConvertTo-NexusVisible $wtLine)
                }
            } catch { }
            break
        }
    }
}
# --- end worktree placement notice ---

# --- Idle minor-run lane notice (v4.15.6) ---
# Local and read-only: when a live minor run record belongs to this repository,
# prints one line naming members with no worker, blocked lanes whose
# prerequisite shipped, and lanes waiting on the user. SessionStart also fires
# after compaction. Silent when lane_health.py is not installed, on any error,
# and when no member is idle. $env:NEXUS_LANE_NOTICE = 'off' skips it.
if ($inRepo -and ($env:NEXUS_LANE_NOTICE -ne "off")) {
    $lnScript = $null
    foreach ($lnTry in @($env:NEXUS_LANE_HEALTH,
            (Join-Path $homeDir "src/catalog/skills/workflow/implement-phase/scripts/lane_health.py"),
            (Join-Path $userHome ".claude/skills/implement-phase/scripts/lane_health.py"))) {
        if ($lnTry -and (Test-Path -LiteralPath $lnTry -PathType Leaf)) { $lnScript = $lnTry; break }
    }
    $lnTop = (git rev-parse --show-toplevel 2>$null)
    if ($lnScript -and $lnTop) {
        foreach ($lnPython in @("python3", "python")) {
            $lnOut = ""
            try {
                $lnPsi = New-Object System.Diagnostics.ProcessStartInfo
                $lnPsi.FileName = $lnPython
                $lnPsi.Arguments = '-B "' + $lnScript + '" notice --repo "' + $lnTop + '" --runs-dir "' + (Join-Path $homeDir "runs") + '"'
                $lnPsi.UseShellExecute = $false
                $lnPsi.CreateNoWindow = $true
                $lnPsi.RedirectStandardOutput = $true
                $lnPsi.RedirectStandardError = $true
                $lnPsi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
                $lnPsi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
                $lnProc = [System.Diagnostics.Process]::Start($lnPsi)
                $lnOutTask = $lnProc.StandardOutput.ReadToEndAsync()
                $null = $lnProc.StandardError.ReadToEndAsync()
                if ($lnProc.WaitForExit(10000)) {
                    if ($lnProc.ExitCode -ne 0) { continue }
                    $lnOut = $lnOutTask.Result
                } else {
                    try { $lnProc.Kill() } catch { }
                }
            } catch { continue }
            $lnLine = ([string]$lnOut).Trim()
            if ($lnLine) { Write-NexusMessage (ConvertTo-NexusVisible $lnLine) }
            break
        }
    }
}
# --- end idle minor-run lane notice ---

# --- Environment-fact replay (v4.15.5, opt-in: NEXUS_ENV_FACTS=on) ---
if ($env:NEXUS_ENV_FACTS -ceq "on") {
    $tlHelper = Join-Path $PSScriptRoot "_turn_ledger.py"
    if (Test-Path -LiteralPath $tlHelper) {
        $tlUtf8 = New-Object System.Text.UTF8Encoding($false)
        foreach ($tlPython in @("python3", "python")) {
            $tlDone = $false
            foreach ($tlMode in @("rotate", "facts")) {
                $tlPsi = New-Object System.Diagnostics.ProcessStartInfo
                $tlPsi.FileName = $tlPython
                $tlPsi.Arguments = '"' + $tlHelper + '" ' + $tlMode
                $tlPsi.UseShellExecute = $false
                $tlPsi.CreateNoWindow = $true
                $tlPsi.RedirectStandardOutput = $true
                $tlPsi.RedirectStandardError = $true
                $tlPsi.StandardOutputEncoding = $tlUtf8
                $tlPsi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
                try {
                    $tlProc = [System.Diagnostics.Process]::Start($tlPsi)
                    $tlOut = $tlProc.StandardOutput.ReadToEnd()
                    $null = $tlProc.StandardError.ReadToEnd()
                    $tlProc.WaitForExit()
                    if ($tlProc.ExitCode -ne 0) { break }
                    $tlDone = ($tlMode -eq "facts")
                    if ($tlMode -eq "facts" -and $tlOut.Trim()) {
                        [Console]::Out.Write($tlOut)  # nexus: hook-msg-exempt helper output carries the session-start tag and heading
                    }
                } catch { break }
            }
            if ($tlDone) { break }
        }
    }
}
# --- end environment-fact replay ---

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
            $digestShown = ConvertTo-NexusVisible $digestRel
            Write-Output ""  # nexus: hook-msg-exempt blank separator before the digest
            $more = @("", $digestText)
            if ($truncated) {
                $more += @("", ("(digest truncated -- read {0} for the full file)" -f $digestShown))
            }
            Write-NexusMessage ("Last session digest ({0}, capped at {1} chars):" -f $digestShown, $maxChars) $more
        }
    } catch {
        # Never fail the hook on read errors.
    }
}

exit 0
