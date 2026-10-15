<#
.SYNOPSIS
    extract-session.ps1 - Local session-log digest extractor for the session-query skill.

.DESCRIPTION
    PowerShell sibling of extract-session.py, kept in lockstep behavior parity per
    the AGENTS.md cross-platform rule. Reads LOCAL prior-context sources and emits
    a topic / branch / time-windowed digest of prior investigation context.

    Supported sources, selected per file by a source tag (the "tool" column from
    discover-sessions, or -Tool):
      - AI session-log JSONL (Claude Code / Codex / Cursor, or any NDJSON) - default
      - Obsidian vault notes (.md with frontmatter, headings, and [[backlinks]])
      - Exported ChatGPT history (conversations.json)
      - Exported Gemini history (Google Takeout "My Activity" JSON)

    Strictly read-only and ZERO-outbound: it makes no network call, opens no
    connection, and imports nothing that reaches off-device. Every source reads
    files on disk only.

.PARAMETER Paths
    One or more source file paths (positional).
.PARAMETER Root
    Recursively discover source files under this directory.
.PARAMETER Topic
    Comma-separated, case-insensitive substrings matched against record text.
.PARAMETER Branch
    Branch name; matches a record's branch field or a text mention.
.PARAMETER Since
    ISO-8601 lower bound (inclusive) on record timestamps.
.PARAMETER Until
    ISO-8601 upper bound (inclusive) on record timestamps.
.PARAMETER Tool
    Source label/parser: claude | codex | cursor | custom (JSONL) or
    obsidian | chatgpt | gemini. Untagged inputs auto-detect by file extension.
.PARAMETER MaxSnippets
    Cap on matched snippets per session (default 20).
.PARAMETER Out
    Write the JSON digest to this path instead of stdout.

.EXAMPLE
    .\extract-session.ps1 session.jsonl -Topic "auth,token" -Since 2026-05-01
.EXAMPLE
    .\extract-session.ps1 -Root ~/.claude/projects -Branch feature/login
.EXAMPLE
    .\extract-session.ps1 note.md -Tool obsidian -Topic "auth"
.EXAMPLE
    .\extract-session.ps1 -Root ~/Downloads/chatgpt -Tool chatgpt -Topic deploy
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
# Obsidian frontmatter keys that may carry a note timestamp, in priority order.
$ObsidianTsKeys = @("updated", "modified", "date", "created", "ctime", "mtime")
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

function ConvertFrom-EpochSeconds($value) {
    # Convert Unix epoch-seconds (ChatGPT create_time) to an ISO-8601 string.
    if ($null -eq $value -or $value -is [bool]) { return $null }
    $d = [double]0
    if ($value -is [int] -or $value -is [long] -or $value -is [int64] -or $value -is [double] -or $value -is [decimal]) {
        $d = [double]$value
    } elseif ($value -is [string]) {
        if (-not [double]::TryParse(
                $value,
                [System.Globalization.NumberStyles]::Float,
                [System.Globalization.CultureInfo]::InvariantCulture,
                [ref]$d)) {
            return $null
        }
    } else {
        return $null
    }
    try {
        $epoch = New-Object DateTime(1970, 1, 1, 0, 0, 0, ([DateTimeKind]::Utc))
        return $epoch.AddSeconds($d).ToString("o")
    } catch {
        return $null
    }
}

function Test-IsObject($v) {
    if ($null -eq $v) { return $false }
    return ($v -is [System.Management.Automation.PSCustomObject])
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

function Read-JsonFile($path) {
    try {
        $raw = [System.IO.File]::ReadAllText($path)
    } catch {
        return $null
    }
    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
    try {
        return ($raw | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        return $null
    }
}

# --- Obsidian vault notes ----------------------------------------------------

function Split-Frontmatter($raw) {
    # Minimal key: value scan of a leading frontmatter block (no YAML library).
    $fm = @{}
    if (-not $raw.StartsWith("---")) { return [pscustomobject]@{ fm = $fm; body = $raw } }
    $lines = $raw -split '\r?\n'
    if ($lines.Count -eq 0 -or $lines[0].Trim() -ne "---") { return [pscustomobject]@{ fm = $fm; body = $raw } }
    $end = -1
    for ($i = 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i].Trim() -eq "---") { $end = $i; break }
        $line = $lines[$i]
        $idx = $line.IndexOf(":")
        if ($idx -gt 0) {
            $key = $line.Substring(0, $idx).Trim().ToLowerInvariant()
            $value = $line.Substring($idx + 1).Trim().Trim('"').Trim("'")
            if ($key -and $value) { $fm[$key] = $value }
        }
    }
    if ($end -lt 0) { return [pscustomobject]@{ fm = @{}; body = $raw } }
    $body = ""
    if (($end + 1) -le ($lines.Count - 1)) {
        $body = ($lines[($end + 1)..($lines.Count - 1)] -join "`n")
    }
    return [pscustomobject]@{ fm = $fm; body = $body }
}

function Split-MdSections($body) {
    $sections = New-Object System.Collections.ArrayList
    $heading = ""
    $buf = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($body -split '\r?\n')) {
        $stripped = $line.TrimStart()
        $isHeading = $false
        if ($stripped.StartsWith("#")) {
            $hashes = 0
            while ($hashes -lt $stripped.Length -and $stripped[$hashes] -eq '#') { $hashes++ }
            if ($hashes -ge 1 -and $hashes -le 6 -and $stripped.Length -gt $hashes -and
                ($stripped[$hashes] -eq ' ' -or $stripped[$hashes] -eq "`t")) {
                $isHeading = $true
            }
        }
        if ($isHeading) {
            if ($heading -or ($buf -join "").Trim()) {
                [void]$sections.Add([pscustomobject]@{ heading = $heading; body = ($buf -join "`n") })
            }
            $heading = $stripped.Trim()
            $buf = New-Object System.Collections.Generic.List[string]
        } else {
            $buf.Add($line)
        }
    }
    if ($heading -or ($buf -join "").Trim()) {
        [void]$sections.Add([pscustomobject]@{ heading = $heading; body = ($buf -join "`n") })
    }
    return $sections
}

function Get-ObsidianRecords($path) {
    $records = New-Object System.Collections.ArrayList
    try {
        $raw = [System.IO.File]::ReadAllText($path)
    } catch {
        return $records
    }
    $split = Split-Frontmatter $raw
    $fm = $split.fm
    $body = $split.body
    $tsIso = $null
    foreach ($k in $ObsidianTsKeys) {
        if ($fm.ContainsKey($k)) {
            $dt = ConvertTo-Utc $fm[$k]
            if ($dt -is [datetime]) { $tsIso = $dt.ToString("o"); break }
        }
    }
    if ($null -eq $tsIso) {
        try { $tsIso = ([System.IO.File]::GetLastWriteTimeUtc($path)).ToString("o") } catch { $tsIso = $null }
    }
    $title = if ($fm.ContainsKey("title")) { $fm["title"] } else { [System.IO.Path]::GetFileNameWithoutExtension($path) }
    $tags = if ($fm.ContainsKey("tags")) { $fm["tags"] } else { $null }
    $titleText = if ($tags) { "$title tags: $tags" } else { "$title" }
    [void]$records.Add([pscustomobject]@{ ts = $tsIso; role = "note"; text = $titleText })
    foreach ($sec in @(Split-MdSections $body)) {
        if ($sec.heading) { $text = ($sec.heading + "`n" + $sec.body).Trim() } else { $text = $sec.body.Trim() }
        if ($text) { [void]$records.Add([pscustomobject]@{ ts = $tsIso; role = "note"; text = $text }) }
    }
    return $records
}

# --- Exported ChatGPT history ------------------------------------------------

function Get-ChatgptRecords($path) {
    $records = New-Object System.Collections.ArrayList
    $data = Read-JsonFile $path
    if ($null -eq $data) { return $records }
    $conversations = @($data)
    foreach ($conv in $conversations) {
        if (-not (Test-IsObject $conv)) { continue }
        $title = Get-FirstKey $conv @("title")
        $convCt = Get-FirstKey $conv @("create_time")
        $mapping = Get-FirstKey $conv @("mapping")
        $messages = New-Object System.Collections.ArrayList
        if (Test-IsObject $mapping) {
            foreach ($prop in $mapping.PSObject.Properties) {
                $node = $prop.Value
                $msg = Get-FirstKey $node @("message")
                if (Test-IsObject $msg) { [void]$messages.Add($msg) }
            }
            $messages = @($messages | Sort-Object {
                $c = Get-FirstKey $_ @("create_time")
                if ($null -eq $c) { [double]0 } else { try { [double]$c } catch { [double]0 } }
            })
        } else {
            $msgs = Get-FirstKey $conv @("messages")
            # @() normalizes a single-element list that ConvertFrom-Json unrolled.
            if ($null -ne $msgs -and $msgs -isnot [string]) {
                foreach ($m in @($msgs)) { if (Test-IsObject $m) { [void]$messages.Add($m) } }
            }
        }
        $first = $true
        foreach ($msg in $messages) {
            $author = Get-FirstKey $msg @("author")
            $role = $null
            if (Test-IsObject $author) { $role = Get-FirstKey $author @("role") }
            if ($null -eq $role) { $role = Get-FirstKey $msg @("role") }
            $content = Get-FirstKey $msg @("content")
            $text = ""
            if (Test-IsObject $content) {
                # ConvertFrom-Json unrolls a single-element "parts" array to a
                # scalar string, so accept either a string or an enumerable.
                $parts = Get-FirstKey $content @("parts")
                if ($parts -is [string]) {
                    $text = $parts.Trim()
                } elseif ($null -ne $parts -and $parts -is [System.Collections.IEnumerable]) {
                    $acc = @()
                    foreach ($p in $parts) { if ($p -is [string]) { $acc += $p } }
                    $text = ($acc -join " ").Trim()
                }
            } elseif ($content -is [string]) {
                $text = $content.Trim()
            }
            if (-not $text) { $text = (Get-Text (Get-FirstKey $msg $TextKeys)).Trim() }
            if (-not $text) { continue }
            $tsIso = ConvertFrom-EpochSeconds (Get-FirstKey $msg @("create_time"))
            if ($null -eq $tsIso) { $tsIso = ConvertFrom-EpochSeconds $convCt }
            if ($null -eq $tsIso) {
                $dt = ConvertTo-Utc (Get-FirstKey $msg $TsKeys)
                if ($dt -is [datetime]) { $tsIso = $dt.ToString("o") }
            }
            if ($first -and ($title -is [string]) -and $title) { $text = "[$title] $text"; $first = $false }
            $roleOut = $null
            if ($role -is [string]) { $roleOut = $role }
            [void]$records.Add([pscustomobject]@{ ts = $tsIso; role = $roleOut; text = $text })
        }
    }
    return $records
}

# --- Exported Gemini history (Google Takeout "My Activity") ------------------

function Get-GeminiRecords($path) {
    $records = New-Object System.Collections.ArrayList
    $data = Read-JsonFile $path
    if ($null -eq $data) { return $records }
    $entries = @()
    if ($data -is [System.Array]) {
        $entries = $data
    } elseif (Test-IsObject $data) {
        $act = Get-FirstKey $data @("activity")
        if ($null -ne $act -and $act -isnot [string]) {
            # @() normalizes a single-element activity list that was unrolled.
            $entries = @($act)
        } elseif (($data.PSObject.Properties.Name -contains "time") -and ($data.PSObject.Properties.Name -contains "title")) {
            # A single-entry export unrolls to one object rather than a 1-list.
            $entries = @($data)
        } else {
            return $records
        }
    } else {
        return $records
    }
    foreach ($entry in $entries) {
        if (-not (Test-IsObject $entry)) { continue }
        $tsIso = $null
        $rawTs = Get-FirstKey $entry @("time")
        if ($rawTs -is [string]) {
            $dt = ConvertTo-Utc $rawTs
            if ($dt -is [datetime]) { $tsIso = $dt.ToString("o") } else { $tsIso = $rawTs }
        }
        $title = Get-FirstKey $entry @("title")
        $text = if ($title -is [string]) { $title } else { "" }
        $extra = @()
        foreach ($k in @("subtitles", "details")) {
            $v = Get-FirstKey $entry @($k)
            # @() normalizes a single-element list that ConvertFrom-Json unrolled.
            if ($null -ne $v -and $v -isnot [string]) {
                foreach ($item in @($v)) {
                    if (Test-IsObject $item) {
                        $nm = Get-FirstKey $item @("name")
                        if ($nm -is [string]) { $extra += $nm }
                    } elseif ($item -is [string]) {
                        $extra += $item
                    }
                }
            }
        }
        if ($extra.Count -gt 0) { $text = ($text + " " + ($extra -join " ")).Trim() }
        $text = "$text".Trim()
        if (-not $text) { continue }
        [void]$records.Add([pscustomobject]@{ ts = $tsIso; role = "user"; text = $text })
    }
    return $records
}

function Get-JsonExportRecords($path) {
    # Auto-detect an untyped .json export (ChatGPT vs Gemini) and parse it.
    $data = Read-JsonFile $path
    if ($null -eq $data) { return (New-Object System.Collections.ArrayList) }
    $sample = $null
    if ($data -is [System.Array]) {
        if ($data.Count -gt 0) { $sample = $data[0] }
    } else {
        $sample = $data
    }
    if (Test-IsObject $sample) {
        $names = @($sample.PSObject.Properties.Name)
        if (($names -contains "mapping") -or ($names -contains "messages")) { return (Get-ChatgptRecords $path) }
        if (($names -contains "time") -and ($names -contains "title")) { return (Get-GeminiRecords $path) }
    }
    return (New-Object System.Collections.ArrayList)
}

function Get-NormalizedRecords($path, $tool) {
    $tag = if ($tool) { "$tool".Trim().ToLowerInvariant() } else { "" }
    $suffix = ([System.IO.Path]::GetExtension($path)).ToLowerInvariant()
    switch ($tag) {
        "obsidian" { return (Get-ObsidianRecords $path) }
        "chatgpt"  { return (Get-ChatgptRecords $path) }
        "gemini"   { return (Get-GeminiRecords $path) }
    }
    if ($tag -eq "" -or $tag -eq "unknown" -or $tag -eq "custom") {
        if ($suffix -eq ".md") { return (Get-ObsidianRecords $path) }
        if ($suffix -eq ".json") { return (Get-JsonExportRecords $path) }
    }
    return (Get-Records $path)
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

    foreach ($record in @(Get-NormalizedRecords $path $tool)) {
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

# Per-source glob patterns used when -Root is scanned with a source -Tool.
function Get-RootPatterns($tool) {
    switch (("$tool").ToLowerInvariant()) {
        "obsidian" { return @("*.md") }
        "chatgpt"  { return @("*.json", "*.md") }
        "gemini"   { return @("*.json", "*.md") }
        default    { return @("*.jsonl") }
    }
}

# --- Resolve input (tool, path) pairs ----------------------------------------
$pairs = New-Object System.Collections.ArrayList
$defaultTool = $Tool
foreach ($p in $Paths) { [void]$pairs.Add([pscustomobject]@{ tool = $defaultTool; path = $p }) }

if ($Root) {
    $resolved = Resolve-Path -LiteralPath $Root -ErrorAction SilentlyContinue
    if ($resolved) {
        $rootResolved = [System.IO.Path]::GetFullPath($resolved.Path)
        if ($rootResolved -and (Test-Path -LiteralPath $rootResolved)) {
            $rootMatches = New-Object System.Collections.ArrayList
            foreach ($pat in (Get-RootPatterns $defaultTool)) {
                Get-ChildItem -LiteralPath $rootResolved -Recurse -File -Filter $pat -ErrorAction SilentlyContinue |
                    ForEach-Object { [void]$rootMatches.Add($_.FullName) }
            }
            foreach ($m in @($rootMatches | Sort-Object -Unique)) {
                [void]$pairs.Add([pscustomobject]@{ tool = $defaultTool; path = $m })
            }
        }
    }
}

if ($pairs.Count -eq 0 -and [Console]::IsInputRedirected) {
    foreach ($line in [Console]::In.ReadToEnd() -split "`n") {
        $t = $line.Trim()
        if (-not $t) { continue }
        $tool = $defaultTool
        if ($t.Contains("`t")) {
            $segs = $t -split "`t", 2
            $tool = $segs[0]
            $t = $segs[1]
        }
        [void]$pairs.Add([pscustomobject]@{ tool = $tool; path = $t })
    }
}

# De-duplicate by path, preserve order (keep the first tool seen).
$seen = New-Object System.Collections.Generic.HashSet[string]
$ordered = New-Object System.Collections.ArrayList
foreach ($pair in $pairs) { if ($seen.Add("$($pair.path)")) { [void]$ordered.Add($pair) } }

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
foreach ($pair in $ordered) {
    if (-not (Test-Path -LiteralPath $pair.path -PathType Leaf)) { continue }
    $result = Get-SessionDigest $pair.path $pair.tool $topicList $Branch $sinceDt $untilDt $MaxSnippets
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
