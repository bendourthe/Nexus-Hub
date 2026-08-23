<#
.SYNOPSIS
    PowerShell sibling of rewrite-command.sh.

.DESCRIPTION
    PreToolUse delegate that asks `python -m nexus_context_compressor rewrite`
    and maps exit 0/1/2/3 onto allow / passthrough / deny / ask. Missing Python
    or a failed import is passthrough, never auto-allow.
#>

$ErrorActionPreference = "Continue"

if (-not [Console]::IsInputRedirected) { exit 0 }
$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }

$payload = $null
$command = $null
try {
    $payload = $raw | ConvertFrom-Json
    $inputObj = $null
    if ($payload.PSObject.Properties.Name -contains 'tool_input') {
        $inputObj = $payload.tool_input
    } elseif ($payload.PSObject.Properties.Name -contains 'toolInput') {
        $inputObj = $payload.toolInput
    }
    if ($inputObj -and ($inputObj.PSObject.Properties.Name -contains 'command')) {
        $command = [string]$inputObj.command
    }
} catch { exit 0 }

if ([string]::IsNullOrEmpty($command)) { exit 0 }

$pyBin = $null
foreach ($candidate in @('python3', 'python')) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $pyBin = $candidate; break }
}
if (-not $pyBin) { exit 0 }

try {
    & $pyBin -c "import nexus_context_compressor" *> $null
    if ($LASTEXITCODE -ne 0) { exit 0 }
} catch { exit 0 }

$hostSettings = $null
$candidates = @()
if ($env:CLAUDE_CONFIG_DIR) {
    $candidates += (Join-Path $env:CLAUDE_CONFIG_DIR 'settings.json')
}
if ($HOME) {
    $candidates += (Join-Path $HOME '.claude/settings.json')
}
$candidates += (Join-Path (Get-Location) '.claude/settings.json')
foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate)) {
        $hostSettings = $candidate
        break
    }
}

if ($hostSettings) {
    $rewrite = & $pyBin -m nexus_context_compressor rewrite --cmd $command --host-settings $hostSettings 2>$null
} else {
    $rewrite = & $pyBin -m nexus_context_compressor rewrite --cmd $command 2>$null
}
$code = $LASTEXITCODE

$decision = $null
switch ($code) {
    0 { $decision = 'allow' }
    2 { $decision = 'deny' }
    3 { $decision = 'ask' }
    default { exit 0 }
}

$updated = [ordered]@{}
if ($inputObj) {
    foreach ($prop in $inputObj.PSObject.Properties) {
        $updated[$prop.Name] = $prop.Value
    }
}
if (-not [string]::IsNullOrEmpty($rewrite)) {
    $updated['command'] = [string]$rewrite
}

$hookOut = [ordered]@{
    hookEventName      = 'PreToolUse'
    permissionDecision = $decision
}
if (-not [string]::IsNullOrEmpty($rewrite)) {
    $hookOut['updatedInput'] = $updated
}

$out = [ordered]@{ hookSpecificOutput = $hookOut }
Write-Output ($out | ConvertTo-Json -Depth 20 -Compress)
exit 0
