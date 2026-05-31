<#
.SYNOPSIS
    generate_release_changelog.ps1 - local conventional-commit release helper.

.DESCRIPTION
    PowerShell sibling of generate_release_changelog.py, kept in lockstep
    behavior parity per the AGENTS.md cross-platform rule. Parses
    conventional-commit messages since the last tag, computes the next
    semantic-version bump (major / minor / patch), and renders a
    Keep-a-Changelog section to stdout (or a -Out file), reporting the
    proposed bump on stderr.

    LOCAL only: shells out to the local git binary, makes no network call,
    needs no credentials. It does NOT replace the manual changelog flow in the
    update-version / generate-changelog skills - it is an optional helper.

.PARAMETER RepoRoot
    Repository root (defaults to CWD).
.PARAMETER FromTag
    Base tag (default: latest git tag).
.PARAMETER CurrentVersion
    Current version (default: derived from the base tag).
.PARAMETER CommitsFrom
    Read NUL-separated commit messages from this file instead of git (testing).
.PARAMETER Date
    Release date YYYY-MM-DD (default: today).
.PARAMETER Out
    Write the section to this file instead of stdout.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$FromTag,
    [string]$CurrentVersion,
    [string]$CommitsFrom,
    [string]$Date,
    [string]$Out
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SubjectRe = [regex]'^(?<type>[a-zA-Z]+)(?:\((?<scope>[^)]*)\))?(?<breaking>!)?:\s*(?<desc>.+?)\s*$'
$SemverRe  = [regex]'^v?(?<major>\d+)\.(?<minor>\d+)\.(?<patch>\d+)'

# type -> bump level (2=minor, 1=patch); types absent are non-release.
$ReleaseLevels = @{ feat = 2; feature = 2; fix = 1; bugfix = 1; perf = 1 }
$SectionMap = @{
    feat = "Added"; feature = "Added"; fix = "Fixed"; bugfix = "Fixed"; perf = "Changed";
    refactor = "Changed"; docs = "Changed"; style = "Changed"; test = "Changed";
    build = "Changed"; ci = "Changed"; chore = "Changed"; revert = "Removed";
    deprecate = "Deprecated"; deprecated = "Deprecated"
}
$SectionOrder = @("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")

function Parse-Commit($message) {
    $msg = "$message"
    $lines = $msg.Trim() -split "`n"
    $subject = if ($lines.Count -gt 0) { $lines[0].Trim() } else { "" }
    $breaking = $msg.Contains("BREAKING CHANGE") -or $msg.Contains("BREAKING-CHANGE")
    $m = $SubjectRe.Match($subject)
    if (-not $m.Success) {
        return [ordered]@{ type = $null; scope = $null; breaking = $breaking; description = $subject; raw = $subject }
    }
    if ($m.Groups["breaking"].Value -eq "!") { $breaking = $true }
    $scope = $m.Groups["scope"].Value.Trim()
    if (-not $scope) { $scope = $null }
    return [ordered]@{
        type        = $m.Groups["type"].Value.ToLowerInvariant()
        scope       = $scope
        breaking    = $breaking
        description = $m.Groups["desc"].Value.Trim()
        raw         = $subject
    }
}

function Get-Bump($commits) {
    $level = 0
    foreach ($c in $commits) {
        if ($c.breaking) { return "major" }
        $t = $c.type
        if ($t -and $ReleaseLevels.ContainsKey($t)) {
            if ($ReleaseLevels[$t] -gt $level) { $level = $ReleaseLevels[$t] }
        }
    }
    if ($level -eq 2) { return "minor" }
    if ($level -eq 1) { return "patch" }
    return $null
}

function Step-Version($current, $bump) {
    $m = $SemverRe.Match("$current".Trim())
    if (-not $m.Success) { throw "not a semantic version: $current" }
    $major = [int]$m.Groups["major"].Value
    $minor = [int]$m.Groups["minor"].Value
    $patch = [int]$m.Groups["patch"].Value
    switch ($bump) {
        "major" { return "$($major + 1).0.0" }
        "minor" { return "$major.$($minor + 1).0" }
        "patch" { return "$major.$minor.$($patch + 1)" }
        default { throw "unknown bump: $bump" }
    }
}

function Format-Entry($c) {
    $desc = if ($c.description) { $c.description } else { $c.raw }
    $prefix = if ($c.breaking) { "**BREAKING**: " } else { "" }
    if ($c.scope) { return "- $prefix**$($c.scope)**: $desc" }
    return "- $prefix$desc"
}

function Get-Sections($commits) {
    $sections = [ordered]@{}
    foreach ($c in $commits) {
        if ($null -eq $c.type) { continue }
        $text = "$($c.description) $($c.raw)"
        if ($text -match '(?i)\b(security|vulnerability|cve)\b') {
            $section = "Security"
        } elseif ($c.breaking) {
            $section = "Changed"
        } elseif ($SectionMap.ContainsKey($c.type)) {
            $section = $SectionMap[$c.type]
        } else {
            $section = "Changed"
        }
        if (-not $sections.Contains($section)) { $sections[$section] = New-Object System.Collections.ArrayList }
        [void]$sections[$section].Add((Format-Entry $c))
    }
    return $sections
}

function Render-Section($version, $when, $commits) {
    $sections = Get-Sections $commits
    $out = New-Object System.Collections.ArrayList
    [void]$out.Add("## [$version] - $when")
    [void]$out.Add("")
    $any = $false
    foreach ($name in $SectionOrder) {
        if (-not $sections.Contains($name) -or $sections[$name].Count -eq 0) { continue }
        $any = $true
        [void]$out.Add("### $name")
        foreach ($e in $sections[$name]) { [void]$out.Add($e) }
        [void]$out.Add("")
    }
    if (-not $any) {
        [void]$out.Add("_No conventional-commit changes since the last tag._")
        [void]$out.Add("")
    }
    return (($out -join "`n").TrimEnd() + "`n")
}

function Invoke-Git($gitArgs) {
    try {
        $output = & git @gitArgs 2>$null
        if ($LASTEXITCODE -eq 0) { return ($output -join "`n") }
    } catch { }
    return ""
}

function Get-LastTag($root) {
    $t = (Invoke-Git @("-C", $root, "describe", "--tags", "--abbrev=0")).Trim()
    if ($t) { return $t } else { return $null }
}

function Get-CommitsSince($tag, $root) {
    $rng = if ($tag) { "$tag..HEAD" } else { "HEAD" }
    $out = Invoke-Git @("-C", $root, "log", $rng, "--no-merges", "--format=%B%x00")
    return @($out -split "`0" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Get-VersionFromTag($tag) {
    if (-not $tag) { return $null }
    $m = $SemverRe.Match($tag)
    if (-not $m.Success) { return $null }
    return "$($m.Groups['major'].Value).$($m.Groups['minor'].Value).$($m.Groups['patch'].Value)"
}

# --- Main --------------------------------------------------------------------
$rootResolved = [System.IO.Path]::GetFullPath($RepoRoot)

if ($CommitsFrom) {
    $raw = [System.IO.File]::ReadAllText($CommitsFrom)
    $messages = @($raw -split "`0" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($messages.Count -le 1) {
        $messages = @($raw -split "(?m)\n[ \t]*\n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }
    $tag = $FromTag
} else {
    $tag = if ($FromTag) { $FromTag } else { Get-LastTag $rootResolved }
    $messages = Get-CommitsSince $tag $rootResolved
}

$commits = @($messages | ForEach-Object { Parse-Commit $_ })
$bump = Get-Bump $commits

$current = if ($CurrentVersion) { $CurrentVersion } else { Get-VersionFromTag $tag }
if (-not $current) {
    Write-Error "could not determine the current version; pass -CurrentVersion"
    exit 2
}

if ($null -eq $bump) {
    $base = if ($tag) { $tag } else { "the start of history" }
    [Console]::Error.WriteLine("No release-triggering conventional commits since $base; current version $current stands.")
    $nextVersion = $current
} else {
    $nextVersion = Step-Version $current $bump
    [Console]::Error.WriteLine("Proposed bump: $bump -> $nextVersion (from $current)")
}

$when = if ($Date) { $Date } else { (Get-Date).ToString("yyyy-MM-dd") }
$section = Render-Section $nextVersion $when $commits

if ($Out) {
    Set-Content -LiteralPath $Out -Value $section -Encoding utf8 -NoNewline
    [Console]::Error.WriteLine("Wrote changelog section to $Out")
} else {
    [Console]::Out.Write($section)
}
exit 0
