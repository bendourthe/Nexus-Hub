<#
.SYNOPSIS
    PowerShell parity for html-responsive-guard.sh.

.DESCRIPTION
    PreToolUse hook for Write and Edit that blocks fixed px/ch max-width
    declarations on text-bearing HTML/CSS selectors. Malformed, irrelevant, or
    incomplete payloads fail open.
#>

$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "html-responsive-guard"
$disabled = $env:NEXUS_DISABLED_HOOKS
if ($disabled -and ($disabled.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

# --- Read JSON from stdin ---
if (-not [Console]::IsInputRedirected) { exit 0 }
$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }

try { $payload = $raw | ConvertFrom-Json } catch { exit 0 }
if (-not $payload -or -not $payload.tool_input) { exit 0 }

$names = $payload.tool_input.PSObject.Properties.Name
$filePath = if ($names -contains 'file_path') { $payload.tool_input.file_path }
            elseif ($names -contains 'path') { $payload.tool_input.path }
            else { $null }
$hasContent = ($names -contains 'content') -and ($payload.tool_input.content -is [string])
$hasNewString = ($names -contains 'new_string') -and ($payload.tool_input.new_string -is [string])
$content = if ($hasContent) { $payload.tool_input.content } else { $null }
$newString = if ($hasNewString) { $payload.tool_input.new_string } else { $null }
$oldString = if (($names -contains 'old_string') -and ($payload.tool_input.old_string -is [string])) { $payload.tool_input.old_string } else { $null }
$replaceAll = ($names -contains 'replace_all') -and ($payload.tool_input.replace_all -is [bool]) -and $payload.tool_input.replace_all

if ([string]::IsNullOrEmpty($filePath) -or (-not $hasContent -and -not $hasNewString)) { exit 0 }
if ($filePath -notmatch '(?i)\.(html?|xhtml|css)$') { exit 0 }

$rulePath = 'catalog/rules/html/responsive-layout.md'
$maxWidthPattern = '(?i)\bmax-width\s*:\s*([^;{}]+)'
$fixedUnitPattern = '(?i)-?(?:\d+(?:\.\d+)?|\.\d+)\s*(?:px|ch)\b'
$customPropertyPattern = '(?i)(--[a-z0-9_-]+)\s*:\s*([^;{}]+)'
$varStartPattern = '(?i)\bvar\s*\('
$customNamePattern = '(?i)^--[a-z0-9_-]+$'
$importantPattern = '(?i)\s*!\s*important\s*$'
$cssWidePattern = '(?i)^(?:inherit|initial|unset|revert|revert-layer)$'
$maxEditBytes = 5 * 1024 * 1024
$mediaTags = @('img', 'video', 'canvas', 'svg', 'picture', 'iframe', 'object', 'embed', 'figure')
$textTags = @('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'figcaption', 'dd', 'dt', 'label', 'legend', 'caption', 'summary', 'time', 'address', 'code')
$containerNames = @('container', 'wrapper', 'shell', 'layout', 'page', 'frame', 'viewport', 'inner', 'outer')
$mediaNames = @('media', 'image', 'video', 'visual', 'artwork', 'illustration')
$textNames = @('copy', 'text', 'prose', 'paragraph', 'title', 'subtitle', 'heading', 'headline', 'description', 'intro', 'lead', 'caption', 'label', 'message', 'note', 'summary')

function Test-NamedToken {
    param([string]$Name, [string[]]$Candidates)
    foreach ($part in @($Name.ToLowerInvariant() -split '[-_]')) {
        if ($Candidates -contains $part) { return $true }
    }
    return $false
}

function Get-TerminalTarget {
    param([string]$Selector)
    $parts = @($Selector.Trim() -split '\s+|[>+~]' | Where-Object { $_ })
    if ($parts.Count -eq 0) { return '' }
    return $parts[-1]
}

function Get-TargetTokens {
    param([string]$Target)
    $result = New-Object System.Collections.Generic.List[string]
    foreach ($match in [regex]::Matches($Target, '[.#]([a-z0-9_-]+)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
        $result.Add($match.Groups[1].Value.ToLowerInvariant())
    }
    return $result
}

function Test-DirectTag {
    param([string]$Target, [string[]]$Tags)
    $match = [regex]::Match($Target.Trim(), '^([a-z][a-z0-9:-]*)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    return $match.Success -and ($Tags -contains $match.Groups[1].Value.ToLowerInvariant())
}

function Test-PermittedTarget {
    param([string]$Target)
    if (Test-DirectTag $Target $mediaTags) { return $true }
    foreach ($token in @(Get-TargetTokens $Target)) {
        if (Test-NamedToken $token ($containerNames + $mediaNames)) { return $true }
    }
    return $false
}

function Test-TextTarget {
    param([string]$Target)
    if (Test-DirectTag $Target $textTags) { return $true }
    foreach ($token in @(Get-TargetTokens $Target)) {
        if (Test-NamedToken $token $textNames) { return $true }
    }
    return $false
}

function Test-TextSelector {
    param([string]$Selector)
    foreach ($part in @($Selector -split ',')) {
        $target = Get-TerminalTarget $part
        if (-not $target -or (Test-DirectTag $target $mediaTags)) { continue }
        if (Test-TextTarget $target) { return $true }
        if (Test-PermittedTarget $target) { continue }
    }
    return $false
}

function Test-InlineText {
    param([string]$Tag, [string]$Attributes)
    $tagName = $Tag.ToLowerInvariant()
    if ($mediaTags -contains $tagName) { return $false }
    if ($textTags -contains $tagName) { return $true }

    $attributeNames = New-Object System.Collections.Generic.List[string]
    foreach ($pattern in @('(?is)\bclass\s*=\s*(["''])(.*?)\1', '(?is)\bid\s*=\s*(["''])(.*?)\1')) {
        $match = [regex]::Match($Attributes, $pattern)
        if ($match.Success) {
            foreach ($name in @($match.Groups[2].Value -split '\s+')) {
                if ($name) { $attributeNames.Add($name) }
            }
        }
    }
    foreach ($name in $attributeNames) {
        if (Test-NamedToken $name $textNames) { return $true }
    }
    foreach ($name in $attributeNames) {
        if (Test-NamedToken $name ($containerNames + $mediaNames)) { return $false }
    }
    return $false
}

function Get-LocalCustomPropertyDeclarations {
    param([string]$Source)
    $declarations = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal)
    foreach ($match in [regex]::Matches($Source, $customPropertyPattern)) {
        $name = $match.Groups[1].Value
        $rawValue = $match.Groups[2].Value.Trim()
        $important = [regex]::IsMatch($rawValue, $importantPattern)
        $value = [regex]::Replace($rawValue, $importantPattern, '').Trim()
        if (-not $declarations.ContainsKey($name) -or $important -or -not $declarations[$name].Important) {
            $declarations[$name] = [pscustomobject]@{
                Value = $value
                Important = $important
            }
        }
    }
    return ,$declarations
}

function Get-LocalCustomProperties {
    param([string]$Source)
    $declarations = Get-LocalCustomPropertyDeclarations $Source
    $properties = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
    foreach ($name in $declarations.Keys) {
        $properties[$name] = $declarations[$name].Value
    }
    return ,$properties
}

function Get-SelectorKey {
    param([string]$Selector)
    return [regex]::Replace($Selector.Trim(), '\s+', ' ')
}

function Get-SelectorCustomPropertyDeclarations {
    param([string]$Source)
    $bodiesBySelector = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal)
    foreach ($match in [regex]::Matches($Source, '([^{}]+)\{([^{}]*)\}', [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
        $key = Get-SelectorKey $match.Groups[1].Value
        if (-not $bodiesBySelector.ContainsKey($key)) {
            $bodiesBySelector[$key] = New-Object System.Collections.Generic.List[string]
        }
        [void]$bodiesBySelector[$key].Add($match.Groups[2].Value)
    }

    $declarationsBySelector = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal)
    foreach ($key in $bodiesBySelector.Keys) {
        $declarationsBySelector[$key] = Get-LocalCustomPropertyDeclarations ([string]::Join(';', @($bodiesBySelector[$key])))
    }
    return ,$declarationsBySelector
}

function Get-SelectorCustomProperties {
    param([string]$Source)
    $declarationsBySelector = Get-SelectorCustomPropertyDeclarations $Source
    $propertiesBySelector = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal)
    foreach ($selector in $declarationsBySelector.Keys) {
        $properties = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
        foreach ($name in $declarationsBySelector[$selector].Keys) {
            $properties[$name] = $declarationsBySelector[$selector][$name].Value
        }
        $propertiesBySelector[$selector] = $properties
    }
    return ,$propertiesBySelector
}

function Test-RootSelector {
    param([string]$Selector)
    foreach ($part in @($Selector -split ',')) {
        if (@(':root', 'html') -contains $part.Trim().ToLowerInvariant()) { return $true }
    }
    return $false
}

function Test-MatchingTerminalTarget {
    param([string]$Selector, [string]$CandidateSelector)
    foreach ($currentPart in @($Selector -split ',')) {
        $currentTarget = Get-TerminalTarget $currentPart
        $currentTokens = @(Get-TargetTokens $currentTarget)
        $currentTagMatch = [regex]::Match($currentTarget, '^([a-z][a-z0-9:-]*)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        foreach ($candidatePart in @($CandidateSelector -split ',')) {
            $candidateTarget = Get-TerminalTarget $candidatePart
            $candidateTokens = @(Get-TargetTokens $candidateTarget)
            foreach ($token in $currentTokens) {
                if ($candidateTokens -contains $token) { return $true }
            }
            $candidateTagMatch = [regex]::Match($candidateTarget, '^([a-z][a-z0-9:-]*)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            if ($currentTagMatch.Success -and $candidateTagMatch.Success -and $currentTagMatch.Groups[1].Value -ieq $candidateTagMatch.Groups[1].Value) {
                return $true
            }
        }
    }
    return $false
}

function Add-CustomPropertyCandidate {
    param(
        [System.Collections.Generic.Dictionary[string,object]]$Candidates,
        [string]$Name,
        [string]$Value,
        [bool]$Guaranteed,
        [AllowNull()][string]$Selector = $null,
        [bool]$Important = $false
    )
    if (-not $Candidates.ContainsKey($Name)) {
        $Candidates[$Name] = [pscustomobject]@{
            Values = New-Object System.Collections.Generic.List[string]
            Definitions = New-Object System.Collections.Generic.List[object]
            Guaranteed = $false
        }
    }
    [void]$Candidates[$Name].Values.Add($Value)
    [void]$Candidates[$Name].Definitions.Add([pscustomobject]@{
        Value = $Value
        Selector = $Selector
        Important = $Important
    })
    $Candidates[$Name].Guaranteed = $Candidates[$Name].Guaranteed -or $Guaranteed
}

function Get-CustomPropertyCandidates {
    param([string]$CssSource, [string]$HtmlSource = '')
    $candidates = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal)
    $selectorDeclarations = Get-SelectorCustomPropertyDeclarations $CssSource
    foreach ($selector in $selectorDeclarations.Keys) {
        $guaranteed = Test-RootSelector $selector
        foreach ($name in $selectorDeclarations[$selector].Keys) {
            $declaration = $selectorDeclarations[$selector][$name]
            Add-CustomPropertyCandidate $candidates $name $declaration.Value $guaranteed $selector $declaration.Important
        }
    }
    foreach ($match in [regex]::Matches($HtmlSource, '(?is)\bstyle\s*=\s*(["''])(.*?)\1')) {
        $localDeclarations = Get-LocalCustomPropertyDeclarations $match.Groups[2].Value
        foreach ($name in $localDeclarations.Keys) {
            $declaration = $localDeclarations[$name]
            Add-CustomPropertyCandidate $candidates $name $declaration.Value $false $null $declaration.Important
        }
    }
    if ($selectorDeclarations.Count -eq 0 -and -not $HtmlSource) {
        $localDeclarations = Get-LocalCustomPropertyDeclarations $CssSource
        foreach ($name in $localDeclarations.Keys) {
            $declaration = $localDeclarations[$name]
            Add-CustomPropertyCandidate $candidates $name $declaration.Value $false $null $declaration.Important
        }
    }
    return ,$candidates
}

function Get-TopLevelVarCalls {
    param([string]$Value)
    $calls = New-Object System.Collections.Generic.List[object]
    $startRegex = [regex]::new($varStartPattern)
    $cursor = 0
    while ($cursor -lt $Value.Length) {
        $match = $startRegex.Match($Value, $cursor)
        if (-not $match.Success) { break }
        $openIndex = $Value.IndexOf('(', $match.Index)
        $depth = 1
        $quote = ''
        $escaped = $false
        $index = $openIndex + 1
        while ($index -lt $Value.Length -and $depth -gt 0) {
            $char = $Value.Substring($index, 1)
            if ($quote) {
                if ($escaped) {
                    $escaped = $false
                } elseif ($char -eq '\') {
                    $escaped = $true
                } elseif ($char -eq $quote) {
                    $quote = ''
                }
            } elseif ($char -eq '"' -or $char -eq "'") {
                $quote = $char
            } elseif ($char -eq '(') {
                $depth++
            } elseif ($char -eq ')') {
                $depth--
            }
            $index++
        }
        if ($depth -gt 0) {
            [void]$calls.Add([pscustomobject]@{
                Name = $null; Fallback = $null; Start = $match.Index; End = $Value.Length; Valid = $false
            })
            break
        }

        $end = $index
        $content = $Value.Substring($openIndex + 1, $end - $openIndex - 2)
        $comma = -1
        $nested = 0
        $quote = ''
        $escaped = $false
        for ($offset = 0; $offset -lt $content.Length; $offset++) {
            $char = $content.Substring($offset, 1)
            if ($quote) {
                if ($escaped) {
                    $escaped = $false
                } elseif ($char -eq '\') {
                    $escaped = $true
                } elseif ($char -eq $quote) {
                    $quote = ''
                }
            } elseif ($char -eq '"' -or $char -eq "'") {
                $quote = $char
            } elseif ($char -eq '(') {
                $nested++
            } elseif ($char -eq ')') {
                if ($nested -gt 0) { $nested-- }
            } elseif ($char -eq ',' -and $nested -eq 0) {
                $comma = $offset
                break
            }
        }
        if ($comma -lt 0) {
            $name = $content.Trim()
            $fallback = $null
        } else {
            $name = $content.Substring(0, $comma).Trim()
            $fallback = $content.Substring($comma + 1).Trim()
        }
        [void]$calls.Add([pscustomobject]@{
            Name = $name
            Fallback = $fallback
            Start = $match.Index
            End = $end
            Valid = [regex]::IsMatch($name, $customNamePattern)
        })
        $cursor = $end
    }
    return $calls
}

function Get-CssValueFixedState {
    param(
        [string]$Value,
        [System.Collections.Generic.Dictionary[string,object]]$Candidates,
        [System.Collections.Generic.Dictionary[string,string]]$LocalProperties,
        [System.Collections.Generic.Dictionary[string,bool]]$LocalPriorities = $null,
        [string]$Selector = '',
        [string[]]$Seen = @(),
        [System.Collections.Generic.Dictionary[string,object]]$Memo = $null,
        [int]$Depth = 0
    )
    if ([regex]::IsMatch($Value.Trim(), $cssWidePattern)) {
        return [System.Tuple[bool,bool]]::new($false, $true)
    }
    $calls = @(Get-TopLevelVarCalls $Value)
    $outside = New-Object System.Text.StringBuilder
    $cursor = 0
    foreach ($call in $calls) {
        [void]$outside.Append($Value.Substring($cursor, $call.Start - $cursor))
        $cursor = $call.End
        if (-not $call.Valid) { return [System.Tuple[bool,bool]]::new($true, $true) }
    }
    [void]$outside.Append($Value.Substring($cursor))
    $directValue = $outside.ToString()
    if ([regex]::IsMatch($directValue, $fixedUnitPattern)) {
        return [System.Tuple[bool,bool]]::new($true, $false)
    }
    if ($Depth -ge 32) { return [System.Tuple[bool,bool]]::new($true, $true) }
    if ($null -eq $Memo) {
        $Memo = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal)
    }

    $mayBeInvalid = $false
    foreach ($call in $calls) {
        $name = $call.Name
        $fallback = $call.Fallback
        if ($Seen -ccontains $name) {
            $definitionState = [System.Tuple[bool,bool]]::new($false, $true)
        } elseif ($Memo.ContainsKey($name)) {
            $definitionState = $Memo[$name]
        } else {
            if ($LocalProperties.ContainsKey($name)) {
                $possibleValues = New-Object System.Collections.Generic.List[string]
                [void]$possibleValues.Add($LocalProperties[$name])
                $mayBeAbsent = $false
                $localImportant = $null -ne $LocalPriorities -and $LocalPriorities.ContainsKey($name) -and $LocalPriorities[$name]
                if ($Selector -and $Candidates.ContainsKey($name)) {
                    foreach ($definition in $Candidates[$name].Definitions) {
                        $candidateSelector = [string]$definition.Selector
                        if (
                            $candidateSelector -and
                            (Get-SelectorKey $candidateSelector) -cne (Get-SelectorKey $Selector) -and
                            -not (Test-RootSelector $candidateSelector) -and
                            (Test-MatchingTerminalTarget $Selector $candidateSelector) -and
                            ($definition.Important -or -not $localImportant)
                        ) {
                            [void]$possibleValues.Add([string]$definition.Value)
                        }
                    }
                }
            } elseif ($Candidates.ContainsKey($name)) {
                $entry = $Candidates[$name]
                $possibleValues = @($entry.Values)
                $mayBeAbsent = -not [bool]$entry.Guaranteed
            } else {
                $possibleValues = @()
                $mayBeAbsent = $true
            }
            if ($possibleValues.Count -eq 0) {
                $definitionState = [System.Tuple[bool,bool]]::new($false, $true)
            } else {
                $reachesFixed = $false
                $definitionInvalid = $false
                $nextSeen = @($Seen) + $name
                foreach ($possibleValue in $possibleValues) {
                    $state = Get-CssValueFixedState $possibleValue $Candidates $LocalProperties $LocalPriorities $Selector $nextSeen $Memo ($Depth + 1)
                    $reachesFixed = $reachesFixed -or $state.Item1
                    $definitionInvalid = $definitionInvalid -or $state.Item2
                    if ($reachesFixed) { break }
                }
                $definitionState = [System.Tuple[bool,bool]]::new($reachesFixed, ($mayBeAbsent -or $definitionInvalid))
            }
            $Memo[$name] = $definitionState
        }

        if ($definitionState.Item1) {
            return [System.Tuple[bool,bool]]::new($true, ($mayBeInvalid -or $definitionState.Item2))
        }
        if ($definitionState.Item2) {
            if ($null -ne $fallback) {
                $fallbackState = Get-CssValueFixedState $fallback $Candidates $LocalProperties $LocalPriorities $Selector $Seen $Memo ($Depth + 1)
                if ($fallbackState.Item1) {
                    return [System.Tuple[bool,bool]]::new($true, ($mayBeInvalid -or $fallbackState.Item2))
                }
                $mayBeInvalid = $mayBeInvalid -or $fallbackState.Item2
            } else {
                $mayBeInvalid = $true
            }
        }
    }
    return [System.Tuple[bool,bool]]::new($false, $mayBeInvalid)
}

function Find-FixedWidthDeclaration {
    param(
        [string]$Source,
        [System.Collections.Generic.Dictionary[string,object]]$Candidates,
        [System.Collections.Generic.Dictionary[string,string]]$LocalProperties = $null,
        [System.Collections.Generic.Dictionary[string,bool]]$LocalPriorities = $null,
        [string]$Selector = ''
    )
    if ($null -eq $LocalProperties) { $LocalProperties = Get-LocalCustomProperties $Source }
    $memo = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal)
    foreach ($match in [regex]::Matches($Source, $maxWidthPattern)) {
        $state = Get-CssValueFixedState $match.Groups[1].Value $Candidates $LocalProperties $LocalPriorities $Selector @() $memo
        if ($state.Item1) { return $match.Value.Trim() }
    }
    return $null
}

function Get-ReconstructedEditContent {
    param([string]$Path, [string]$OldString, [string]$NewString, [bool]$ReplaceAll)
    if ([string]::IsNullOrEmpty($OldString)) { return $null }

    $stream = $null
    try {
        $stream = [System.IO.File]::Open(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::ReadWrite
        )
        if ($stream.Length -gt $maxEditBytes) { return $null }
        $bytes = New-Object byte[] ([int]$stream.Length)
        $offset = 0
        while ($offset -lt $bytes.Length) {
            $read = $stream.Read($bytes, $offset, $bytes.Length - $offset)
            if ($read -le 0) { return $null }
            $offset += $read
        }
        $utf8 = [System.Text.UTF8Encoding]::new($false, $true)
        $source = $utf8.GetString($bytes)
    } catch {
        return $null
    } finally {
        if ($null -ne $stream) { $stream.Dispose() }
    }

    $index = $source.IndexOf($OldString, [System.StringComparison]::Ordinal)
    if ($index -lt 0) { return $null }
    if ($ReplaceAll) { return $source.Replace($OldString, $NewString) }
    return $source.Substring(0, $index) + $NewString + $source.Substring($index + $OldString.Length)
}

function Find-UnresolvedTextDeclaration {
    param([string]$Path, [string]$Source)

    $clean = [regex]::Replace($Source, '/\*.*?\*/', '', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    $cssBlocks = New-Object System.Collections.Generic.List[string]
    if ($Path -match '(?i)\.css$') {
        [void]$cssBlocks.Add($clean)
    } else {
        foreach ($match in [regex]::Matches($clean, '(?is)<style\b[^>]*>(.*?)</style\s*>')) {
            [void]$cssBlocks.Add($match.Groups[1].Value)
        }
        if ($cssBlocks.Count -eq 0 -and $clean.Contains('{') -and [regex]::IsMatch($clean, $maxWidthPattern)) {
            [void]$cssBlocks.Add($clean)
        }
    }

    foreach ($css in $cssBlocks) {
        foreach ($ruleMatch in [regex]::Matches($css, '([^{}]+)\{([^{}]*)\}', [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
            if (-not (Test-TextSelector $ruleMatch.Groups[1].Value)) { continue }
            foreach ($declaration in [regex]::Matches($ruleMatch.Groups[2].Value, $maxWidthPattern)) {
                if ([regex]::IsMatch($declaration.Groups[1].Value, $varStartPattern)) { return $declaration.Value.Trim() }
            }
        }
    }

    if ($Path -notmatch '(?i)\.css$') {
        foreach ($tagMatch in [regex]::Matches($clean, '<([a-z][a-z0-9:-]*)\b([^>]*)>', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
            $tag = $tagMatch.Groups[1].Value
            $attributes = $tagMatch.Groups[2].Value
            $style = [regex]::Match($attributes, '(?is)\bstyle\s*=\s*(["''])(.*?)\1')
            if (-not $style.Success -or -not (Test-InlineText $tag $attributes)) { continue }
            foreach ($declaration in [regex]::Matches($style.Groups[2].Value, $maxWidthPattern)) {
                if ([regex]::IsMatch($declaration.Groups[1].Value, $varStartPattern)) { return $declaration.Value.Trim() }
            }
        }
    }
    return $null
}

function Find-UnsafeCustomPropertyDeclaration {
    param([string]$Source)
    $clean = [regex]::Replace($Source, '/\*.*?\*/', '', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    foreach ($declaration in [regex]::Matches($clean, $customPropertyPattern)) {
        $value = $declaration.Groups[2].Value
        if ([regex]::IsMatch($value, $fixedUnitPattern) -or [regex]::IsMatch($value, $varStartPattern)) {
            return $declaration.Value.Trim()
        }
    }
    return $null
}

function Find-FixedTextDeclaration {
    param([string]$Path, [string]$Source)

    $clean = [regex]::Replace($Source, '/\*.*?\*/', '', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    $cssBlocks = New-Object System.Collections.Generic.List[string]
    if ($Path -match '(?i)\.css$') {
        $cssBlocks.Add($clean)
    } else {
        foreach ($match in [regex]::Matches($clean, '(?is)<style\b[^>]*>(.*?)</style\s*>')) {
            $cssBlocks.Add($match.Groups[1].Value)
        }
        if ($cssBlocks.Count -eq 0 -and $clean.Contains('{') -and [regex]::IsMatch($clean, $maxWidthPattern)) {
            $cssBlocks.Add($clean)
        }
    }

    $cssSource = [string]::Join("`n", @($cssBlocks))
    $htmlSource = if ($Path -match '(?i)\.css$') { '' } else { $clean }
    $candidates = Get-CustomPropertyCandidates $cssSource $htmlSource
    $scopedDeclarations = Get-SelectorCustomPropertyDeclarations $cssSource
    foreach ($css in $cssBlocks) {
        foreach ($ruleMatch in [regex]::Matches($css, '([^{}]+)\{([^{}]*)\}', [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
            $selector = $ruleMatch.Groups[1].Value
            $key = Get-SelectorKey $selector
            $local = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
            $localPriorities = [System.Collections.Generic.Dictionary[string,bool]]::new([System.StringComparer]::Ordinal)
            if ($scopedDeclarations.ContainsKey($key)) {
                foreach ($name in $scopedDeclarations[$key].Keys) {
                    $local[$name] = $scopedDeclarations[$key][$name].Value
                    $localPriorities[$name] = $scopedDeclarations[$key][$name].Important
                }
            }
            $declaration = Find-FixedWidthDeclaration $ruleMatch.Groups[2].Value $candidates $local $localPriorities $selector
            if ($declaration -and (Test-TextSelector $selector)) { return $declaration }
        }
    }

    if ($Path -notmatch '(?i)\.css$') {
        foreach ($tagMatch in [regex]::Matches($clean, '<([a-z][a-z0-9:-]*)\b([^>]*)>', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
            $tag = $tagMatch.Groups[1].Value
            $attributes = $tagMatch.Groups[2].Value
            $style = [regex]::Match($attributes, '(?is)\bstyle\s*=\s*(["''])(.*?)\1')
            if (-not $style.Success) { continue }
            $declaration = Find-FixedWidthDeclaration $style.Groups[2].Value $candidates
            if ($declaration -and (Test-InlineText $tag $attributes)) { return $declaration }
        }
    }
    return $null
}

$analysisContent = $content
$reconstructionFailed = $false
if (-not $hasContent) {
    $analysisContent = Get-ReconstructedEditContent $filePath $oldString $newString $replaceAll
    if ($null -eq $analysisContent) {
        $analysisContent = $newString
        $reconstructionFailed = $true
    }
}
if ([string]::IsNullOrEmpty($analysisContent)) { exit 0 }

$declaration = Find-FixedTextDeclaration $filePath $analysisContent
if ($declaration) {
    [Console]::Error.WriteLine("[html-responsive-guard] BLOCKED: $declaration in $filePath violates $rulePath.")
    [Console]::Error.WriteLine("Fixed px/ch text caps must move to a responsive container.")
    exit 2
}

if ($reconstructionFailed) {
    $unresolved = Find-UnresolvedTextDeclaration $filePath $newString
    $unsafeCustomProperty = Find-UnsafeCustomPropertyDeclaration $newString
    $riskyDeclaration = if ($unresolved) { $unresolved } else { $unsafeCustomProperty }
    if ($riskyDeclaration) {
        [Console]::Error.WriteLine("[html-responsive-guard] BLOCKED: could not reconstruct $filePath before evaluating $riskyDeclaration; verify the target file and retry. Rule: $rulePath.")
        exit 2
    }
}
exit 0
