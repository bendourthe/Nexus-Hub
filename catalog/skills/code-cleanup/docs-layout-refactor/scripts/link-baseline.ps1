<# Capture and compare unresolved relative Markdown links in tracked files. #>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("baseline", "diff")]
    [string]$Command,
    [string]$Root = ".",
    [Alias("out")]
    [string]$OutputPath,
    [Alias("before")]
    [string]$BeforePath,
    [Alias("after")]
    [string]$AfterPath,
    [Alias("rename-map")]
    [string]$RenameMap
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Convert-ToPosix {
    param([string]$Path)
    return $Path.Replace("\", "/")
}

function Read-RenameMap {
    # old<TAB>new pairs. `git diff --name-status -M` rename rows are
    # R<score><TAB>old<TAB>new, so the last two fields win.
    param([string]$Path)
    $map = @{}
    if (-not (Test-Path -LiteralPath $Path)) { throw "cannot read rename map $Path" }
    foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line.TrimStart().StartsWith("#")) { continue }
        $fields = @($line.TrimEnd("`n") -split "`t" | Where-Object { $_ -ne "" })
        if ($fields.Count -lt 2) { throw "invalid rename map at ${Path}: expected old<TAB>new" }
        [void]($map[$fields[$fields.Count - 2]] = $fields[$fields.Count - 1])
    }
    return $map
}

function Get-PrefixMap {
    # Mirrors _derive_prefix_map in link-baseline.py: candidate directory
    # renames, kept only when nearly every mapped file under the prefix agrees.
    param([hashtable]$FileMap)
    $candidates = @{}
    foreach ($old in $FileMap.Keys) {
        $new = $FileMap[$old]
        $oldParts = $old -split "/"
        $newParts = $new -split "/"
        for ($depth = 1; $depth -lt $oldParts.Count; $depth++) {
            $tailLen = $oldParts.Count - $depth
            if ($tailLen -ge $newParts.Count) { continue }
            $oldTail = ($oldParts[$depth..($oldParts.Count - 1)]) -join "/"
            $newTail = ($newParts[($newParts.Count - $tailLen)..($newParts.Count - 1)]) -join "/"
            if ($oldTail -ne $newTail) { continue }
            $oldPrefix = ($oldParts[0..($depth - 1)]) -join "/"
            $newPrefix = ($newParts[0..($newParts.Count - $tailLen - 1)]) -join "/"
            if (-not $newPrefix -or $oldPrefix -eq $newPrefix) { continue }
            [void]($candidates["$oldPrefix`t$newPrefix"] = $true)
        }
    }
    $kept = New-Object System.Collections.ArrayList
    foreach ($key in $candidates.Keys) {
        $parts = $key -split "`t"
        $oldPrefix = $parts[0]; $newPrefix = $parts[1]
        $under = 0; $mismatched = 0
        foreach ($old in $FileMap.Keys) {
            if ($old -eq $oldPrefix -or $old.StartsWith("$oldPrefix/")) {
                $under++
                if ($FileMap[$old] -ne ($newPrefix + $old.Substring($oldPrefix.Length))) { $mismatched++ }
            }
        }
        if ($under -ge 2 -and ($mismatched * 20) -le $under) {
            [void]$kept.Add([pscustomobject]@{ Old = $oldPrefix; New = $newPrefix })
        }
    }
    return @($kept | Sort-Object -Property @{Expression = { $_.Old.Length }; Descending = $true}, Old)
}

function Convert-ProjectedPath {
    param([string]$Path, [hashtable]$FileMap, $Prefixes)
    if ($FileMap.ContainsKey($Path)) { return $FileMap[$Path] }
    foreach ($rule in $Prefixes) {
        if ($Path -eq $rule.Old) { return $rule.New }
        if ($Path.StartsWith("$($rule.Old)/")) { return $rule.New + $Path.Substring($rule.Old.Length) }
    }
    return $Path
}

function Get-LinkKey {
    param($Record)
    $separator = [char]31
    return "$($Record.source)$separator$($Record.link)$separator$($Record.resolved_target)"
}

function Get-RelativePath {
    param([string]$BasePath, [string]$TargetPath)
    $separator = [System.IO.Path]::DirectorySeparatorChar
    $baseUri = New-Object System.Uri(($BasePath.TrimEnd("\", "/") + $separator))
    $targetUri = New-Object System.Uri($TargetPath)
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString())
}

function Read-Ndjson {
    param([string]$Path)
    $lineNumber = 0
    foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
        $lineNumber++
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $record = $line | ConvertFrom-Json
            if ($null -eq $record.source -or $null -eq $record.link -or $null -eq $record.resolved_target) {
                throw "missing required field"
            }
            Write-Output $record
        } catch {
            throw "Invalid NDJSON at ${Path}:${lineNumber}: $($_.Exception.Message)"
        }
    }
}

function Convert-Records {
    param([object[]]$Records)
    return @($Records | Sort-Object source, link, resolved_target | ForEach-Object {
        [ordered]@{
            source = $_.source
            link = $_.link
            resolved_target = $_.resolved_target
        }
    })
}

try {
    if ($Command -eq "baseline") {
        if ([string]::IsNullOrWhiteSpace($OutputPath)) { throw "Missing required option --out" }
        $root = [System.IO.Path]::GetFullPath($Root)
        $out = [System.IO.Path]::GetFullPath($OutputPath)
        if (-not [System.IO.Directory]::Exists($root)) {
            throw "Repository root not found at $root"
        }
        $tracked = & git -C $root ls-files
        if ($LASTEXITCODE -ne 0) {
            throw "git ls-files failed with exit $LASTEXITCODE"
        }
        $records = @{}
        $pattern = [regex]'!?\[[^\]]*\]\((?<destination>[^)]+)\)'
        $inlineCode = [regex]'`[^`]*`'
        $fencePattern = [regex]'^\s*(?<fence>`{3,}|~{3,})'
        foreach ($relative in $tracked) {
            $extension = [System.IO.Path]::GetExtension($relative).ToLowerInvariant()
            if ($extension -notin @(".md", ".markdown")) { continue }
            $source = [System.IO.Path]::GetFullPath((Join-Path $root $relative))
            $text = [System.IO.File]::ReadAllText($source)
            $fence = $null
            foreach ($line in ($text -split "`r?`n")) {
                $fenceMatch = $fencePattern.Match($line)
                if ($fenceMatch.Success) {
                    $marker = $fenceMatch.Groups["fence"].Value.Substring(0, 1)
                    if ($fence -eq $marker) { $fence = $null } else { $fence = $marker }
                    continue
                }
                if ($null -ne $fence) { continue }
                $scanLine = $inlineCode.Replace($line, "")
                foreach ($match in $pattern.Matches($scanLine)) {
                    $raw = $match.Groups["destination"].Value.Trim()
                    if ($raw.StartsWith("<")) {
                        $close = $raw.IndexOf(">")
                        if ($close -lt 0) { continue }
                        $value = $raw.Substring(1, $close - 1)
                    } else {
                        $value = ($raw -split '\s+', 2)[0]
                    }
                    if ([string]::IsNullOrWhiteSpace($value) -or $value.StartsWith("#") -or $value.StartsWith("//") -or $value.StartsWith("\\")) { continue }
                    $uri = $null
                    if ([System.Uri]::TryCreate($value, [System.UriKind]::RelativeOrAbsolute, [ref]$uri) -and $uri.IsAbsoluteUri) { continue }
                    $pathOnly = ($value -split '[?#]', 2)[0]
                    if ([string]::IsNullOrWhiteSpace($pathOnly)) { continue }
                    $pathOnly = [System.Uri]::UnescapeDataString($pathOnly)
                    if ($pathOnly.StartsWith("/")) {
                        $target = [System.IO.Path]::GetFullPath((Join-Path $root $pathOnly.TrimStart("/")))
                    } else {
                        $target = [System.IO.Path]::GetFullPath((Join-Path ([System.IO.Path]::GetDirectoryName($source)) $pathOnly))
                    }
                    if ([System.IO.File]::Exists($target) -or [System.IO.Directory]::Exists($target)) { continue }
                    $displayTarget = Convert-ToPosix (Get-RelativePath $root $target)
                    $record = [pscustomobject]@{
                        source = Convert-ToPosix $relative
                        link = $raw
                        resolved_target = $displayTarget
                    }
                    [void]($records[(Get-LinkKey $record)] = $record)
                }
            }
        }
        $lines = @(Convert-Records @($records.Values) | ForEach-Object { $_ | ConvertTo-Json -Compress })
        $parent = [System.IO.Path]::GetDirectoryName($out)
        if ($parent) { [System.IO.Directory]::CreateDirectory($parent) | Out-Null }
        $body = if ($lines.Count -gt 0) { ($lines -join "`n") + "`n" } else { "" }
        [System.IO.File]::WriteAllText($out, $body, $Utf8NoBom)
        [ordered]@{ unresolved = $records.Count; output = $out } | ConvertTo-Json -Compress
        exit 0
    }

    if ([string]::IsNullOrWhiteSpace($BeforePath)) { throw "Missing required option --before" }
    if ([string]::IsNullOrWhiteSpace($AfterPath)) { throw "Missing required option --after" }
    $useRenameMap = -not [string]::IsNullOrWhiteSpace($RenameMap)
    $fileMap = $null; $prefixes = @()
    if ($useRenameMap) {
        $fileMap = Read-RenameMap $RenameMap
        $prefixes = Get-PrefixMap $fileMap
    }
    # With a rename map the identity drops `link` and projects the before-side
    # into post-move coordinates; a correct repair rewrites the link text, so
    # keeping it would count every repair as fixed AND newly broken.
    $keyOf = {
        param($r, $project)
        if ($project) {
            $s = Convert-ProjectedPath $r.source $fileMap $prefixes
            $t = Convert-ProjectedPath $r.resolved_target $fileMap $prefixes
            return "$s$([char]31)$([char]31)$t"
        }
        if ($useRenameMap) { return "$($r.source)$([char]31)$([char]31)$($r.resolved_target)" }
        return (Get-LinkKey $r)
    }
    $beforeMap = @{}
    foreach ($record in @(Read-Ndjson $BeforePath)) {
        [void]($beforeMap[(& $keyOf $record $useRenameMap)] = $record)
    }
    $afterMap = @{}
    foreach ($record in @(Read-Ndjson $AfterPath)) {
        [void]($afterMap[(& $keyOf $record $false)] = $record)
    }
    $newKeys = @($afterMap.Keys | Where-Object { -not $beforeMap.ContainsKey($_) })
    $fixedKeys = @($beforeMap.Keys | Where-Object { -not $afterMap.ContainsKey($_) })
    $unchangedKeys = @($afterMap.Keys | Where-Object { $beforeMap.ContainsKey($_) })
    $report = [ordered]@{
        newly_broken = Convert-Records @($newKeys | ForEach-Object { $afterMap[$_] })
        fixed = Convert-Records @($fixedKeys | ForEach-Object { $beforeMap[$_] })
        unchanged = Convert-Records @($unchangedKeys | ForEach-Object { $afterMap[$_] })
        totals = [ordered]@{
            before = $beforeMap.Count
            after = $afterMap.Count
            newly_broken = $newKeys.Count
            fixed = $fixedKeys.Count
            unchanged = $unchangedKeys.Count
        }
    }
    $report | ConvertTo-Json -Depth 6 -Compress
    if ($newKeys.Count -gt 0) { exit 1 }
    exit 0
} catch {
    [Console]::Error.WriteLine("Error: $($_.Exception.Message)")
    exit 2
}
