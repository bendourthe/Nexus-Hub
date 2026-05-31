<#
.SYNOPSIS
    extract-session.ps1 - Local session-log digest extractor for the session-query skill.

.DESCRIPTION
    PowerShell sibling of extract-session.py, kept in lockstep behavior parity per
    the AGENTS.md cross-platform rule. Reads LOCAL AI session-log JSONL files
    (Claude Code / Codex / Cursor, or any NDJSON transcript) and emits a
    topic / branch / time-windowed digest of prior investigation context.

    Strictly read-only and ZERO-outbound: it makes no network call, opens no
    connection, and imports nothing that reaches off-device.

.PARAMETER Paths
    One or more JSONL file paths (positional).
.PARAMETER Root
    Recursively discover *.jsonl under this directory.
.PARAMETER Topic
    Comma-separated, case-insensitive substrings matched against record text.
.PARAMETER Branch
    Branch name; matches a record's branch field or a text mention.
.PARAMETER Since
    ISO-8601 lower bound (inclusive) on record timestamps.
.PARAMETER Until
    ISO-8601 upper bound (inclusive) on record timestamps.
.PARAMETER Tool
    Tool label applied to passed/discovered files.
.PARAMETER MaxSnippets
    Cap on matched snippets per session (default 20).
.PARAMETER Out
    Write the JSON digest to this path instead of stdout.

.EXAMPLE
    .\extract-session.ps1 session.jsonl -Topic "auth,token" -Since 2026-05-01
.EXAMPLE
    .\extract-session.ps1 -Root ~/.claude/projects -Branch feature/login
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true, Position = 0)]
    [string[]]$Paths = @(),
    [string]$Root,
    [string]$Topic = "",
    [string]$Branch,
    [string]$Since,
    [string]$Until,
    [string]$Tool = "unknown",
    [int]$MaxSnippets = 20,
    [string]$Out
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TsKeys     = @("ts", "timestamp", "time", "created_at", "createdAt", "date")
$RoleKeys   = @("role", "event", "type", "speaker", "author")
$TextKeys   = @("prompt_sample", "prompt", "text", "content", "message", "summary")
$BranchKeys = @("branch", "git_branch", "gitBranch", "ref")
$SnippetMaxChars = 240

function ConvertTo-Utc($value) {
    if ($null -eq $value -or $value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)) {
        return $null
    }
    $dto = [DateTimeOffset]::MinValue
    if ([DateTimeOffset]::TryParse(
            $value.Trim(),
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::AssumeUniversal -bor [System.Globalization.DateTimeStyles]::AdjustToUniversal,
            [ref]$dto)) {
        return $dto.UtcDateTime
    }
    return $null
}

function Get-FirstKey($obj, $keys) {
    if ($null -eq $obj) { return $null }
    foreach ($k in $keys) {
        $prop = $obj.PSObject.Properties[$k]
        if ($prop -and $null -ne $prop.Value -and "$($prop.Value)" -ne "") {
            return $prop.Value
        }
    }
    return $null
}

function Get-Text($value) {
    if ($null -eq $value) { return "" }
    if ($value -is [string]) { return $value }
    if ($value -is [System.Collections.IEnumerable]) {
        $parts = @()
        foreach ($block in $value) {
            if ($block -is [string]) { $parts += $block }
            elseif ($block -is [psobject]) {
                $inner = Get-FirstKey $block @("text", "content", "value")
                if ($inner -is [string]) { $parts += $inner }
            }
        }
        return ($parts -join " ")
    }
    if ($value -is [psobject]) {
        $inner = Get-FirstKey $value @("text", "content", "value")
        if ($inner -is [string]) { return $inner }
    }
    return ""
}

function Get-Records($path) {
    $records = New-Object System.Collections.ArrayList
    try {
        $lines = [System.IO.File]::ReadAllLines($path)
    } catch {
        return $records
    }
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrEmpty($trimmed)) { continue }
        try {
            $obj = $trimmed | ConvertFrom-Json -ErrorAction Stop
        } catch {
            continue
        }
        if ($obj -is [psobject]) { [void]$records.Add($obj) }
    }
    return $records
}

function Get-SessionDigest($path, $tool, $topics, $branch, $since, $until, $maxSnippets) {
    $topicsLc = @($topics | Where-Object { $_ } | ForEach-Object { $_.ToLowerInvariant() })
    $branchLc = if ($branch) { $branch.ToLowerInvariant() } else { $null }
    $hasWindow = ($since -is [datetime]) -or ($until -is [datetime])

    $recordsTotal = 0
    $recordsMatched = 0
    $timestamps = New-Object System.Collections.Generic.List[datetime]
    $branches = New-Object System.Collections.Generic.HashSet[string]
    $snippets = New-Object System.Collections.ArrayList

    foreach ($record in (Get-Records $path)) {
        $recordsTotal++
        $ts = ConvertTo-Utc (Get-FirstKey $record $TsKeys)
        if ($null -ne $ts) { [void]$timestamps.Add([datetime]$ts) }

        if ($hasWindow) {
            if ($null -eq $ts) { continue }
            if (($since -is [datetime]) -and ($ts -lt $since)) { continue }
            if (($until -is [datetime]) -and ($ts -gt $until)) { continue }
        }

        $text = Get-Text (Get-FirstKey $record $TextKeys)
        $textLc = $text.ToLowerInvariant()

        $recBranch = Get-FirstKey $record $BranchKeys
        if ($recBranch -is [string] -and $recBranch) { [void]$branches.Add($recBranch) }

        if ($topicsLc.Count -gt 0) {
            $hit = $false
            foreach ($t in $topicsLc) { if ($textLc.Contains($t)) { $hit = $true; break } }
            if (-not $hit) { continue }
        }
        if ($null -ne $branchLc) {
            $fieldHit = ($recBranch -is [string]) -and $recBranch.ToLowerInvariant().Contains($branchLc)
            if (-not $fieldHit -and -not $textLc.Contains($branchLc)) { continue }
        }

        $recordsMatched++
        if ($snippets.Count -lt $maxSnippets -and $text.Trim()) {
            $role = Get-FirstKey $record $RoleKeys
            $snipTs = $null
            if ($null -ne $ts) { $snipTs = $ts.ToString("o") }
            $snipRole = $null
            if ($role -is [string]) { $snipRole = $role }
            $trimmed = $text.Trim()
            $cut = [Math]::Min($SnippetMaxChars, $trimmed.Length)
            $snippet = [ordered]@{
                ts   = $snipTs
                role = $snipRole
                text = $trimmed.Substring(0, $cut)
            }
            [void]$snippets.Add($snippet)
        }
    }

    $anyFilter = ($topicsLc.Count -gt 0) -or ($null -ne $branchLc) -or $hasWindow
    if ($anyFilter -and $recordsMatched -eq 0) { return $null }

    # Compute first/last timestamp after the loop to avoid running comparisons.
    $firstStr = $null
    $lastStr = $null
    if ($timestamps.Count -gt 0) {
        $sorted = @($timestamps | Sort-Object)
        $firstStr = $sorted[0].ToString("o")
        $lastStr = $sorted[$sorted.Count - 1].ToString("o")
    }

    return [ordered]@{
        tool            = $tool
        path            = "$path"
        first_ts        = $firstStr
        last_ts         = $lastStr
        records_total   = $recordsTotal
        records_matched = $recordsMatched
        branches        = @($branches | Sort-Object)
        snippets        = @($snippets)
    }
}

# --- Resolve input paths -----------------------------------------------------
$allPaths = New-Object System.Collections.ArrayList
foreach ($p in $Paths) { [void]$allPaths.Add($p) }

if ($Root) {
    $rootResolved = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Root -ErrorAction SilentlyContinue).Path)
    if ($rootResolved -and (Test-Path -LiteralPath $rootResolved)) {
        Get-ChildItem -LiteralPath $rootResolved -Recurse -File -Filter *.jsonl |
            Sort-Object FullName |
            ForEach-Object { [void]$allPaths.Add($_.FullName) }
    }
}

if ($allPaths.Count -eq 0 -and -not [Console]::IsInputRedirected) {
    # nothing on stdin and no inputs
} elseif ($allPaths.Count -eq 0) {
    foreach ($line in [Console]::In.ReadToEnd() -split "`n") {
        $t = $line.Trim()
        if (-not $t) { continue }
        if ($t.Contains("`t")) { $t = ($t -split "`t", 2)[1] }
        [void]$allPaths.Add($t)
    }
}

# De-duplicate, preserve order.
$seen = New-Object System.Collections.Generic.HashSet[string]
$ordered = New-Object System.Collections.ArrayList
foreach ($p in $allPaths) { if ($seen.Add("$p")) { [void]$ordered.Add($p) } }

# --- Parse filters -----------------------------------------------------------
# NOTE: PowerShell variable names are case-insensitive, so a local named $since
# would alias the [string]-typed $Since parameter and coerce $null to "".
# Use distinct local names ($topicList / $sinceDt / $untilDt) to stay clean.
$topicList = @($Topic -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$sinceDt = $null
$untilDt = $null
if (-not [string]::IsNullOrWhiteSpace($Since)) {
    $sinceDt = ConvertTo-Utc $Since
    if ($sinceDt -isnot [datetime]) { Write-Error "--since is not a valid ISO-8601 timestamp: $Since"; exit 2 }
}
if (-not [string]::IsNullOrWhiteSpace($Until)) {
    $untilDt = ConvertTo-Utc $Until
    if ($untilDt -isnot [datetime]) { Write-Error "--until is not a valid ISO-8601 timestamp: $Until"; exit 2 }
}

# --- Build digest ------------------------------------------------------------
$sessions = New-Object System.Collections.ArrayList
foreach ($path in $ordered) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
    $result = Get-SessionDigest $path $Tool $topicList $Branch $sinceDt $untilDt $MaxSnippets
    if ($null -ne $result) { [void]$sessions.Add($result) }
}

$snippetsTotal = 0
foreach ($s in $sessions) { $snippetsTotal += $s.snippets.Count }

$querySince = $null
if ($sinceDt -is [datetime]) { $querySince = $sinceDt.ToString("o") }
$queryUntil = $null
if ($untilDt -is [datetime]) { $queryUntil = $untilDt.ToString("o") }

$digest = [ordered]@{
    query   = [ordered]@{
        topics = @($topicList)
        branch = $Branch
        since  = $querySince
        until  = $queryUntil
    }
    sessions = @($sessions)
    summary  = [ordered]@{
        files_scanned  = $ordered.Count
        files_matched  = $sessions.Count
        snippets_total = $snippetsTotal
    }
}

$payload = $digest | ConvertTo-Json -Depth 8
if ($Out) {
    Set-Content -LiteralPath $Out -Value $payload -Encoding utf8
} else {
    Write-Output $payload
}
