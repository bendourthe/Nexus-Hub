<#
.SYNOPSIS
    PowerShell parity for auto-format-on-write.sh.

.DESCRIPTION
    PostToolUse hook (Write, Edit) that runs the language-appropriate formatter on
    the file that was just written. Silent and best-effort: every formatter
    invocation is optional, failures are swallowed, and the hook always exits 0.

    Formatter selection by extension (same mapping as the .sh sibling):
      js/jsx/ts/tsx/css/scss/less/json/html/htm/yaml/yml/md/mdx/vue/svelte/graphql
                                    -> prettier (or ./node_modules/.bin via npx)
      py/pyi                        -> black, else ruff format
      go                            -> gofmt -w
      rs                            -> rustfmt
      c/h/cpp/cc/cxx/hpp/hxx/m/mm   -> clang-format -i

.NOTES
    Runtime controls match the .sh sibling, including the extra `no-format`
    profile: NEXUS_DISABLED_HOOKS=auto-format-on-write,
    NEXUS_HOOK_PROFILE=minimal, or NEXUS_HOOK_PROFILE=no-format all skip it.
#>

$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "auto-format-on-write"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "no-format") { exit 0 }

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

function Test-Tool { param([string]$Name) return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

function Invoke-Quietly {
    param([string]$Exe, [string[]]$Arguments)
    try { & $Exe @Arguments *> $null } catch { }
}

$ext = ([System.IO.Path]::GetExtension($filePath)).TrimStart('.').ToLower()

switch ($ext) {
    { $_ -in @('js','jsx','ts','tsx','css','scss','less','json','html','htm',
               'yaml','yml','md','mdx','vue','svelte','graphql') } {
        if (Test-Tool prettier) {
            Invoke-Quietly prettier @('--write', $filePath)
        } elseif ((Test-Tool npx) -and (Test-Path "node_modules/.bin/prettier")) {
            Invoke-Quietly npx @('prettier', '--write', $filePath)
        }
        break
    }
    { $_ -in @('py','pyi') } {
        if (Test-Tool black) {
            Invoke-Quietly black @('--quiet', $filePath)
        } elseif (Test-Tool ruff) {
            Invoke-Quietly ruff @('format', $filePath)
        }
        break
    }
    'go' {
        if (Test-Tool gofmt) { Invoke-Quietly gofmt @('-w', $filePath) }
        break
    }
    'rs' {
        if (Test-Tool rustfmt) { Invoke-Quietly rustfmt @($filePath) }
        break
    }
    { $_ -in @('c','h','cpp','cc','cxx','hpp','hxx','m','mm') } {
        if (Test-Tool clang-format) { Invoke-Quietly clang-format @('-i', $filePath) }
        break
    }
    default { }
}

exit 0
