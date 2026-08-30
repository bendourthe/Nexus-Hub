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
$content = if ($names -contains 'content') { $payload.tool_input.content }
           elseif ($names -contains 'new_string') { $payload.tool_input.new_string }
           else { $null }

if ([string]::IsNullOrEmpty($filePath) -or [string]::IsNullOrEmpty($content)) { exit 0 }
if ($filePath -notmatch '(?i)\.(html?|xhtml|css)$') { exit 0 }

$rulePath = 'catalog/rules/html/responsive-layout.md'
$declarationPattern = '(?i)\bmax-width\s*:\s*-?(?:\d+(?:\.\d+)?|\.\d+)\s*(?:px|ch)\b'
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
        if ($cssBlocks.Count -eq 0 -and $clean.Contains('{') -and [regex]::IsMatch($clean, $declarationPattern)) {
            $cssBlocks.Add($clean)
        }
    }

    foreach ($css in $cssBlocks) {
        foreach ($ruleMatch in [regex]::Matches($css, '([^{}]+)\{([^{}]*)\}', [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
            $selector = $ruleMatch.Groups[1].Value
            $declaration = [regex]::Match($ruleMatch.Groups[2].Value, $declarationPattern)
            if ($declaration.Success -and (Test-TextSelector $selector)) { return $declaration.Value }
        }
    }

    if ($Path -notmatch '(?i)\.css$') {
        foreach ($tagMatch in [regex]::Matches($clean, '<([a-z][a-z0-9:-]*)\b([^>]*)>', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
            $tag = $tagMatch.Groups[1].Value
            $attributes = $tagMatch.Groups[2].Value
            $style = [regex]::Match($attributes, '(?is)\bstyle\s*=\s*(["''])(.*?)\1')
            if (-not $style.Success) { continue }
            $declaration = [regex]::Match($style.Groups[2].Value, $declarationPattern)
            if ($declaration.Success -and (Test-InlineText $tag $attributes)) { return $declaration.Value }
        }
    }
    return $null
}

$declaration = Find-FixedTextDeclaration $filePath $content
if (-not $declaration) { exit 0 }

[Console]::Error.WriteLine("[html-responsive-guard] BLOCKED: $declaration in $filePath violates $rulePath.")
[Console]::Error.WriteLine("Fixed px/ch text caps must move to a responsive container.")
exit 2
