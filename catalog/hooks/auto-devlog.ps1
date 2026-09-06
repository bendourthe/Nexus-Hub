<#
.SYNOPSIS
    PowerShell parity for auto-devlog.sh.

.DESCRIPTION
    Stop hook that prepends a session summary to docs/DEVLOG.md when enough commits
    have landed since the last entry. Always exits 0; every failure path leaves the
    DEVLOG untouched.

    Preconditions, all of which must hold or the hook is a silent no-op:
      * git is available and the CWD is inside a repository;
      * docs/DEVLOG.md exists at the repo root;
      * DEVLOG.md was NOT modified in the last 5 minutes (double-run guard);
      * at least AUTO_DEVLOG_MIN_COMMITS commits (default 2) since the last entry.

    Optional AI enrichment: set AUTO_DEVLOG_AI=1 to have the claude CLI write a
    richer entry. On any failure it falls through to the deterministic summary, so
    enabling it can never lose the entry.

.NOTES
    Two implementation notes where this version is cleaner than the .sh sibling
    without changing behavior:

      * mtime: the bash version branches on GNU vs BSD `stat`. .NET exposes
        LastWriteTime directly, so no probing is needed.
      * insertion: the bash version uses awk (not `sed -i`) to dodge BSD/GNU
        portability. Here the file is read, the entry spliced, and the whole file
        written back with BOM-less UTF-8, which is both simpler and avoids the BOM
        class of defect found in v3.15.6 Phase 3.
#>

$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "auto-devlog"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

# --- Opt-in gate (parity with auto-devlog.sh) ---
# This gate was MISSING until v3.18.0, so this hook was effectively opt-OUT on
# PowerShell while its .sh sibling was opt-in: it wrote to docs/DEVLOG.md at every
# session end for users who never asked for it. Both implementations now require
# the same explicit opt-in.
if ($env:AUTO_DEVLOG -ne "1") { exit 0 }

# --- Configuration ---
$minCommits = if ($env:AUTO_DEVLOG_MIN_COMMITS) { [int]$env:AUTO_DEVLOG_MIN_COMMITS } else { 2 }
$skipIfModifiedWithin = 300   # seconds; prevents a double run within 5 minutes

# --- Dependencies ---
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { exit 0 }

# --- Must be inside a git repo with a DEVLOG.md ---
$gitRoot = (& git rev-parse --show-toplevel 2>$null | Out-String).Trim()
if (-not $gitRoot) { exit 0 }
$devlog = Join-Path $gitRoot "docs/DEVLOG.md"
if (-not (Test-Path -LiteralPath $devlog -PathType Leaf)) { exit 0 }

# --- Index-format guard: never prepend narrative into a per-release index ---
# docs/DEVLOG.md may be a bounded per-release INDEX (a header plus one table row
# per release) rather than an append-only narrative log. Prepending an entry into
# that table corrupts it silently. Detect the index header and stand down;
# session narrative belongs in the per-version development/history/ file.
try {
    $indexHeader = Select-String -LiteralPath $devlog -Pattern '^\s*\|\s*Date\s*\|\s*Version\s*\|' | Select-Object -First 1
    if ($indexHeader) {
        [Console]::Error.WriteLine("[auto-devlog] docs/DEVLOG.md is a per-release index; skipping. Session narrative belongs in docs/v*/*/development/history/.")
        exit 0
    }
} catch { exit 0 }

# --- Drain stdin (Stop hooks receive a JSON payload) ---
if ([Console]::IsInputRedirected) { $null = [Console]::In.ReadToEnd() }

# --- Double-run guard: skip if DEVLOG.md was modified recently ---
try {
    $ageSeconds = ((Get-Date) - (Get-Item -LiteralPath $devlog).LastWriteTime).TotalSeconds
    if ($ageSeconds -lt $skipIfModifiedWithin) { exit 0 }
} catch { exit 0 }

# --- Parse the date of the last DEVLOG entry ---
# Matches heading formats: ## [YYYY-MM-DD ...] or ## [YYYY-MM-DD HH:MM ...]
$lastEntryDate = $null
try {
    $firstHeading = Select-String -LiteralPath $devlog -Pattern '^## \[' | Select-Object -First 1
    if ($firstHeading -and ($firstHeading.Line -match '\d{4}-\d{2}-\d{2}')) {
        $lastEntryDate = $Matches[0]
    }
} catch { }

# --- Count commits since the last entry ---
$afterArg = if ($lastEntryDate) { $lastEntryDate } else { "7 days ago" }
$commitCount = 0
try {
    $lines = @(& git -C $gitRoot log --oneline --after=$afterArg 2>$null)
    $commitCount = @($lines | Where-Object { $_ -ne '' }).Count
} catch { $commitCount = 0 }
if ($commitCount -lt $minCommits) { exit 0 }

# --- Gather session data ---
$timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm")
$branch = (& git -C $gitRoot rev-parse --abbrev-ref HEAD 2>$null | Out-String).Trim()
if (-not $branch) { $branch = "unknown" }

$recentCommits = @(& git -C $gitRoot log --oneline --after=$afterArg 2>$null | Select-Object -First 10)
$baseHash = ""
if ($lastEntryDate) {
    $baseHash = (& git -C $gitRoot log --format=%H --before=$lastEntryDate -1 2>$null | Out-String).Trim()
} else {
    $recentCommits = @(& git -C $gitRoot log --oneline -10 2>$null)
}

$filesChanged = @()
try {
    if ($baseHash) {
        $filesChanged = @(& git -C $gitRoot diff --name-only $baseHash HEAD 2>$null | Select-Object -First 20)
    } else {
        $filesChanged = @(& git -C $gitRoot diff --name-only "HEAD~$commitCount" HEAD 2>$null | Select-Object -First 20)
    }
} catch { $filesChanged = @() }

# --- Optional AI enrichment path ---
# Uses a compact inline prompt rather than the full update-devlog command, whose
# iterative refinement loop is unsuitable for non-interactive --print mode.
if ($env:AUTO_DEVLOG_AI -eq "1" -and (Get-Command claude -ErrorAction SilentlyContinue)) {
    $projectName = Split-Path $gitRoot -Leaf
    $aiPrompt = @"
You are updating docs/DEVLOG.md for the '$projectName' project.
Read docs/DEVLOG.md to understand its exact heading style and section format.
Write ONE new entry to prepend above the first ## heading, using timestamp: $timestamp.
Base it on these commits:
$($recentCommits -join "`n")

Files changed:
$($filesChanged -join "`n")

Write ONLY the entry block - no preamble, no commentary. Then write the updated file.
"@
    $aiOk = $false
    try {
        & claude --print --max-turns 1 $aiPrompt *> $null
        $aiOk = ($LASTEXITCODE -eq 0)
    } catch { $aiOk = $false }

    if ($aiOk) {
        [Console]::Error.WriteLine("[auto-devlog] AI entry written to DEVLOG.md")
        exit 0
    }
    # Fall through to the deterministic entry on failure.
    [Console]::Error.WriteLine("[auto-devlog] AI enrichment failed - writing shell summary instead.")
}

# --- Build the deterministic entry ---
$sb = New-Object System.Text.StringBuilder
[void]$sb.Append("## [$timestamp] - Session auto-summary [auto]`n`n")
[void]$sb.Append("### What Changed`n`n")
foreach ($line in $recentCommits) {
    if ($line -ne '') { [void]$sb.Append("- $line`n") }
}
if ($filesChanged.Count -gt 0) {
    [void]$sb.Append("`n### Files Modified`n`n")
    foreach ($line in $filesChanged) {
        if ($line -ne '') { [void]$sb.Append("- ``$line```n") }
    }
}
[void]$sb.Append("`n### Current Status`n`nAuto-captured at session end on branch ``$branch``. Review and annotate as needed.`n`n---`n`n")
$entry = $sb.ToString()

# --- Prepend above the first ## heading (DEVLOG is newest-first) ---
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $lines = [System.IO.File]::ReadAllLines($devlog)
    $firstH2 = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^## \[') { $firstH2 = $i; break }
    }

    if ($firstH2 -ge 0) {
        $head = if ($firstH2 -gt 0) { $lines[0..($firstH2 - 1)] } else { @() }
        $tail = $lines[$firstH2..($lines.Count - 1)]
        $body = (($head -join "`n") + $(if ($head.Count) { "`n" } else { "" }) +
                 $entry + ($tail -join "`n") + "`n")
        [System.IO.File]::WriteAllText($devlog, $body, $utf8NoBom)
    } else {
        # No existing ## heading found; append to the end.
        [System.IO.File]::AppendAllText($devlog, "`n$entry", $utf8NoBom)
    }
} catch {
    exit 0
}

$sinceLabel = if ($lastEntryDate) { $lastEntryDate } else { "7 days ago" }
[Console]::Error.WriteLine("[auto-devlog] entry prepended ($commitCount commits since $sinceLabel)")

exit 0
