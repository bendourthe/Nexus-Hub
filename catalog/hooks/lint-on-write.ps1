<#
.SYNOPSIS
    PowerShell parity for lint-on-write.sh.

.DESCRIPTION
    PostToolUse hook (Write, Edit) that runs the language-appropriate linter on the
    file that was just written and reports any output to stderr. Advisory only:
    every linter invocation is optional and the hook always exits 0.

    Linter selection by extension (same mapping as the .sh sibling):
      js/jsx/ts/tsx -> eslint (or ./node_modules/.bin via npx)
      py/pyi        -> ruff check, else pylint
      go            -> golangci-lint run
      rs            -> a cargo clippy hint (clippy needs cargo context)

.NOTES
    Reports the linter's output verbatim to stderr, prefixed with the same
    "[lint] <tool> warnings for <file>:" header the .sh sibling emits, so a reader
    cannot tell the two implementations apart from the transcript.
#>

$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "lint-on-write"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

# --- Read JSON from stdin ---
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

$filePath = $null
try {
    $payload = $raw | ConvertFrom-Json
    if ($payload -and $payload.tool_input) {
        $names = $payload.tool_input.PSObject.Properties.Name
        if ($names -contains 'file_path') { $filePath = $payload.tool_input.file_path }
        elseif ($names -contains 'path') { $filePath = $payload.tool_input.path }
    }
} catch { exit 0 }

if (-not $filePath) { exit 0 }
if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) { exit 0 }

$fileName = try { Split-Path $filePath -Leaf } catch { $filePath }

function Test-Tool { param([string]$Name) return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

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

function Report-Lint {
    <#
      Run a linter and, when it produced any output, emit the .sh sibling's header
      followed by that output verbatim. Non-zero exit codes are expected (a linter
      exits non-zero when it finds problems), so they are swallowed by design.
    #>
    param([string]$Tool, [string]$Exe, [string[]]$Arguments)
    $out = $null
    try { $out = (Invoke-Utf8Child $Exe $Arguments -MergeStderr).Lines -join [Environment]::NewLine } catch { $out = $null }
    if (-not [string]::IsNullOrWhiteSpace($out)) {
        [Console]::Error.WriteLine("[lint] $Tool warnings for ${fileName}:")
        [Console]::Error.WriteLine($out.TrimEnd())
    }
}

$ext = ([System.IO.Path]::GetExtension($filePath)).TrimStart('.').ToLower()

switch ($ext) {
    { $_ -in @('js','jsx','ts','tsx') } {
        if (Test-Tool eslint) {
            Report-Lint 'eslint' 'eslint' @('--no-error-on-unmatched-pattern', '--format', 'compact', $filePath)
        } elseif ((Test-Tool npx) -and (Test-Path "node_modules/.bin/eslint")) {
            Report-Lint 'eslint' 'npx' @('eslint', '--no-error-on-unmatched-pattern', '--format', 'compact', $filePath)
        }
        break
    }
    { $_ -in @('py','pyi') } {
        if (Test-Tool ruff) {
            Report-Lint 'ruff' 'ruff' @('check', $filePath)
        } elseif (Test-Tool pylint) {
            Report-Lint 'pylint' 'pylint' @('--output-format=text', '--score=no', $filePath)
        }
        break
    }
    'go' {
        if (Test-Tool golangci-lint) {
            Report-Lint 'golangci-lint' 'golangci-lint' @('run', $filePath)
        }
        break
    }
    'rs' {
        # Clippy requires cargo context, so provide a hint rather than running it.
        if (Test-Tool cargo) {
            [Console]::Error.WriteLine("[lint] Tip: run 'cargo clippy' to lint Rust files")
        }
        break
    }
    default { }
}

exit 0
