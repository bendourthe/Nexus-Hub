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
# Hook payloads are UTF-8 whatever the console code page is (WN-37): decode the raw
# handle and reply through UTF-8 writers rather than calling SetConsoleCP.
$hookUtf8 = New-Object System.Text.UTF8Encoding($false)
$raw = (New-Object System.IO.StreamReader([Console]::OpenStandardInput(), $hookUtf8, $true)).ReadToEnd()
# Windows PowerShell 5.1 without a console drains the raw handle into [Console]::In.
if (-not $raw) { $raw = [Console]::In.ReadToEnd() }
$utf8Writer = New-Object System.IO.StreamWriter([Console]::OpenStandardOutput(), $hookUtf8); $utf8Writer.AutoFlush = $true; [Console]::SetOut($utf8Writer)
$utf8Writer = New-Object System.IO.StreamWriter([Console]::OpenStandardError(), $hookUtf8); $utf8Writer.AutoFlush = $true; [Console]::SetError($utf8Writer)
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

function Invoke-Utf8Child {
    # Run a program and decode its output as UTF-8, not the console code page (WN-45),
    # without SetConsoleCP. A .cmd/.bat shim runs through cmd.exe; PYTHONUTF8 and
    # PYTHONIOENCODING reach the child only. ExitCode is -1 when it cannot start.
    # cmd.exe re-parses its whole command line and no quoting carries arbitrary text
    # through it (AF-1, AF-2): when an argument or the shim path holds a cmd
    # metacharacter, a double quote or a line break, a same-named .exe/.com later on
    # PATH runs instead, and with none the child is not started (ExitCode -1).
    param([string]$Exe, [string[]]$Arguments, [switch]$MergeStderr)
    $result = [pscustomobject]@{ Lines = @(); ExitCode = -1 }
    $onWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
    $found = @(Get-Command $Exe -CommandType Application -ErrorAction SilentlyContinue |
        Where-Object { -not $onWindows -or $_.Extension -match '^\.(exe|com|cmd|bat)$' })
    if ($found.Count -eq 0) { return $result }
    $cmd = $found[0]
    if ($onWindows -and $cmd.Extension -match '^\.(cmd|bat)$') {
        $unsafe = @(@($Arguments) + @($cmd.Source) | Where-Object { [string]$_ -match '[&|<>^%!"\r\n]' })
        if ($unsafe.Count -gt 0) {
            $cmd = $found | Where-Object { $_.Extension -match '^\.(exe|com)$' } | Select-Object -First 1
            if (-not $cmd) { return $result }
        }
    }
    $argLine = (@($Arguments) | ForEach-Object {
        if ($_ -and $_ -notmatch '[\s"]') { $_ } else { '"' + (([string]$_ -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"' }
    }) -join ' '
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    if ($onWindows -and $cmd.Extension -match '^\.(cmd|bat)$') {
        $psi.FileName = if ($env:ComSpec) { $env:ComSpec } else { 'cmd.exe' }
        $psi.Arguments = '/d /s /c ""' + $cmd.Source + '" ' + $argLine + '"'
    } else { $psi.FileName = $cmd.Source; $psi.Arguments = $argLine }
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $psi.StandardErrorEncoding = New-Object System.Text.UTF8Encoding($false)
    $psi.EnvironmentVariables['PYTHONUTF8'] = '1'; $psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    try { $proc = [System.Diagnostics.Process]::Start($psi) } catch { return $result }
    $errTask = $proc.StandardError.ReadToEndAsync()
    $text = $proc.StandardOutput.ReadToEnd()
    $proc.WaitForExit()
    if ($MergeStderr) { $text += $errTask.Result }
    $result.ExitCode = $proc.ExitCode
    if ($text) { $result.Lines = @($text.TrimEnd("`r", "`n") -split "`r?`n") }
    return $result
}

$rewriteArgs = @('-m', 'nexus_context_compressor', 'rewrite', '--cmd', $command)
if ($hostSettings) { $rewriteArgs += @('--host-settings', $hostSettings) }
$child = Invoke-Utf8Child $pyBin $rewriteArgs
# One line stays a string and several stay an array, as `& ...` captured them.
$rewrite = foreach ($line in $child.Lines) { $line }
$code = $child.ExitCode

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
