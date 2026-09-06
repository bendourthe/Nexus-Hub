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
$raw = [Console]::In.ReadToEnd()
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

function Report-Lint {
    <#
      Run a linter and, when it produced any output, emit the .sh sibling's header
      followed by that output verbatim. Non-zero exit codes are expected (a linter
      exits non-zero when it finds problems), so they are swallowed by design.
    #>
    param([string]$Tool, [string]$Exe, [string[]]$Arguments)
    $out = $null
    try { $out = (& $Exe @Arguments 2>&1 | Out-String) } catch { $out = $null }
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
