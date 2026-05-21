# tasks-to-issues.ps1 -- Parse the strict-format task lines in a feature
# directory's tasks.md or plan.md and either dry-run the resulting
# gh issue create invocations or execute them sequentially.
#
# Usage:
#   tasks-to-issues.ps1 [-DryRun] [-FeatureDir DIR] [-RepoRoot DIR]
#
# Exit codes:
#   0  -- success (all tasks filed or all dry-run lines printed)
#   1  -- generic error (bad input, missing gh, malformed source)
#   2  -- usage error (bad flag)
#   3  -- pre-flight check failed (gh auth, repo not on GitHub)
#   4  -- partial failure (some tasks filed, then a gh call failed)
#
# Cross-platform parity: tasks-to-issues.sh implements the same flow on
# POSIX. Keep the two in lockstep per AGENTS.md.

[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$FeatureDir = '',
    [string]$RepoRoot = ''
)

$ErrorActionPreference = 'Stop'
$TASK_REGEX = '^- \[ \] T[0-9]{3,}( \[P\])?( \[US[0-9]+\])? .+$'

function Write-LogInfo  { param([string]$Message) [Console]::Error.WriteLine("[INFO]  $Message") }
function Write-LogError { param([string]$Message) [Console]::Error.WriteLine("[ERROR] $Message") }

function Stop-WithError {
    param([string]$Message, [int]$ExitCode = 1)
    Write-LogError $Message
    exit $ExitCode
}

# --- Resolve repo root ---------------------------------------------------

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        try {
            $resolved = (& git rev-parse --show-toplevel 2>$null)
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
                $RepoRoot = $resolved.Trim()
            }
        } catch {
            # ignore; fall back to current dir
        }
    }
    if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
        $RepoRoot = (Get-Location).Path
    }
}

if (-not (Test-Path $RepoRoot -PathType Container)) {
    Stop-WithError "Repo root does not exist: $RepoRoot"
}

# --- Pre-flight checks ---------------------------------------------------

$ghCmd = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghCmd) {
    Stop-WithError 'Install the GitHub CLI from https://cli.github.com and run "gh auth login" before re-trying.' 3
}

try { & gh auth status 2>$null | Out-Null } catch {}
if ($LASTEXITCODE -ne 0) {
    Stop-WithError 'gh is not authenticated. Run "gh auth login" before re-trying.' 3
}

$repoSlug = ''
try {
    $repoSlug = (& gh repo view --json nameWithOwner -q .nameWithOwner 2>$null)
} catch {}
if ([string]::IsNullOrWhiteSpace($repoSlug)) {
    Stop-WithError 'Working directory does not resolve to a GitHub repo. Configure the remote with "gh repo set-default" or run from a GitHub-tracked clone.' 3
}
$repoSlug = $repoSlug.Trim()

# --- Resolve feature directory + task source ----------------------------

if ([string]::IsNullOrWhiteSpace($FeatureDir)) {
    $featureJson = Join-Path $RepoRoot ".specify\feature.json"
    if (Test-Path $featureJson -PathType Leaf) {
        try {
            $parsed = Get-Content -Path $featureJson -Raw | ConvertFrom-Json -ErrorAction Stop
            if ($parsed.PSObject.Properties.Name -contains 'feature_directory') {
                $FeatureDir = "$($parsed.feature_directory)"
            }
        } catch {
            Write-LogInfo "Failed to parse $featureJson -- ignoring."
        }
    }
}

if ([string]::IsNullOrWhiteSpace($FeatureDir)) {
    $docsRoot = Join-Path $RepoRoot "docs"
    if (Test-Path $docsRoot -PathType Container) {
        $latestPlan = Get-ChildItem -Path $docsRoot -Recurse -Filter "*.md" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\plans\\[^\\]+\.md$' } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($latestPlan) {
            $FeatureDir = $latestPlan.Directory.FullName
        }
    }
}

if ([string]::IsNullOrWhiteSpace($FeatureDir)) {
    Stop-WithError "Could not resolve a feature directory. Pass -FeatureDir DIR explicitly."
}

# Allow relative paths.
if (-not [System.IO.Path]::IsPathRooted($FeatureDir)) {
    $FeatureDir = Join-Path $RepoRoot $FeatureDir
}

if (-not (Test-Path $FeatureDir -PathType Container)) {
    Stop-WithError "Feature directory does not exist: $FeatureDir"
}

$sourceFile = ''
$tasksMd = Join-Path $FeatureDir "tasks.md"
$planMd = Join-Path $FeatureDir "plan.md"

if (Test-Path $tasksMd -PathType Leaf) {
    $sourceFile = $tasksMd
} elseif (Test-Path $planMd -PathType Leaf) {
    $sourceFile = $planMd
} else {
    $fallback = Get-ChildItem -Path $FeatureDir -Filter "*.md" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($fallback) { $sourceFile = $fallback.FullName }
}

if ([string]::IsNullOrWhiteSpace($sourceFile) -or -not (Test-Path $sourceFile -PathType Leaf)) {
    Stop-WithError "No tasks.md, plan.md, or fallback <slug>.md found in $FeatureDir"
}

$mode = if ($DryRun) { 'dry-run' } else { 'execute' }
Write-LogInfo "Repo:           $repoSlug"
Write-LogInfo "Feature dir:    $FeatureDir"
Write-LogInfo "Source file:    $sourceFile"
Write-LogInfo "Mode:           $mode"

# --- Parse task lines ---------------------------------------------------

$lines = Get-Content -Path $sourceFile
$candidates = @()
for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match '^- \[ \] T[0-9]+') {
        $candidates += [pscustomobject]@{
            LineNo = $i + 1
            Body = $lines[$i]
        }
    }
}

if ($candidates.Count -eq 0) {
    Stop-WithError "No task lines found in $sourceFile. Re-run /generate-plan with the strict-format validator."
}

# Validate against the strict regex.
$violations = @()
foreach ($cand in $candidates) {
    if ($cand.Body -notmatch $TASK_REGEX) {
        $violations += "$($cand.LineNo): $($cand.Body)"
    }
}

if ($violations.Count -gt 0) {
    Write-LogError "Source file contains lines that look like tasks but do not match the strict regex:"
    foreach ($v in $violations) { [Console]::Error.WriteLine($v) }
    Stop-WithError "Re-run /generate-plan with the strict-format validator to fix these lines."
}

# --- Build per-task payload + drive gh ----------------------------------

$newlyCreated = 0
$skipped = 0
$failed = 0
$summaryRows = New-Object System.Collections.ArrayList

foreach ($cand in $candidates) {
    $lineBody = $cand.Body

    if ($lineBody -match '\[gh#[0-9]+\]') {
        $skipped++
        continue
    }

    # Decompose: "- [ ] T### [P]? [US#]? description"
    if ($lineBody -notmatch '^- \[ \] (T[0-9]{3,}) (.*)$') { continue }
    $taskId = $Matches[1]
    $rest = $Matches[2]

    $parallel = $false
    $userStory = ''

    if ($rest -match '^\[P\] (.*)$') {
        $parallel = $true
        $rest = $Matches[1]
    }

    if ($rest -match '^\[US([0-9]+)\] (.*)$') {
        $userStory = $Matches[1]
        $rest = $Matches[2]
    }

    $description = $rest

    # Extract trailing file path heuristically.
    $filePath = ''
    foreach ($token in ($description -split '\s+')) {
        if ($token -match '[\/.]') { $filePath = $token }
    }

    $labels = @('nexus-hub', 'spec-kit-task')
    if ($parallel) { $labels += 'parallel' }
    if (-not [string]::IsNullOrWhiteSpace($userStory)) { $labels += "user-story-$userStory" }
    $labelStr = ($labels -join ',')

    $title = "[$taskId] $description"
    if ($title.Length -gt 200) {
        $title = $title.Substring(0, 197) + '...'
    }

    $usLine = if ([string]::IsNullOrWhiteSpace($userStory)) { 'n/a' } else { "US$userStory" }
    $parallelLine = if ($parallel) { 'yes' } else { 'no' }
    $relSource = $sourceFile
    if ($sourceFile.StartsWith($RepoRoot)) {
        $relSource = $sourceFile.Substring($RepoRoot.Length).TrimStart('\','/')
    }
    $fileLine = if ([string]::IsNullOrWhiteSpace($filePath)) { 'n/a' } else { $filePath }

    $body = @"
Task: $taskId
File: $fileLine
Parallel: $parallelLine
User story: $usLine
Source: $relSource

Generated by /tasks-to-issues
"@

    if ($DryRun) {
        # Print the resolved gh invocation. Use single quotes for safety.
        $escapedTitle = $title -replace "'", "''"
        $escapedBody = $body -replace "'", "''"
        $escapedLabel = $labelStr -replace "'", "''"
        Write-Output "gh issue create --title '$escapedTitle' --body '$escapedBody' --label '$escapedLabel'"
        [void]$summaryRows.Add("$taskId | (dry-run) | $labelStr")
        continue
    }

    Write-LogInfo "Creating issue for $taskId ..."
    try {
        $issueUrl = (& gh issue create --title $title --body $body --label $labelStr 2>&1)
        if ($LASTEXITCODE -ne 0) {
            throw $issueUrl
        }
        $issueUrl = ($issueUrl | Select-Object -Last 1).Trim()
        $issueNum = $issueUrl.Split('/')[-1]
        Write-LogInfo "  -> $issueUrl"
        $newlyCreated++
        [void]$summaryRows.Add("$taskId | $issueUrl | $labelStr")

        # Rewrite the source file: append [gh#<num>] to the matched line.
        $newLines = @($lines)
        $idx = $cand.LineNo - 1
        $newLines[$idx] = "$($newLines[$idx]) [gh#$issueNum]"
        $tmp = "$sourceFile.tmp.$([System.Guid]::NewGuid().ToString('N'))"
        Set-Content -Path $tmp -Value $newLines -Encoding utf8
        if (Test-Path $sourceFile) { Remove-Item -Path $sourceFile -Force }
        Move-Item -Path $tmp -Destination $sourceFile
        $lines = $newLines
    } catch {
        $failed++
        Write-LogError "Issue creation for $taskId failed:"
        [Console]::Error.WriteLine($_)
        Write-LogError 'Already-created issues remain. Re-run /tasks-to-issues to file the rest.'
        exit 4
    }
}

# --- Final summary ------------------------------------------------------

Write-Output ""
Write-Output "Summary:"
Write-Output "T### | Issue URL | Labels"
foreach ($row in $summaryRows) { Write-Output $row }
Write-Output ""
Write-Output "Newly created: $newlyCreated"
Write-Output "Skipped (already filed): $skipped"
Write-Output "Failed: $failed"
