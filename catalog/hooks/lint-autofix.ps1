#!/usr/bin/env pwsh
# Lint Autofix - PreToolUse Hook for Claude Code (OPT-IN, file-mutating).
# PowerShell sibling of lint-autofix.sh; see that file for the full contract.
#
# On a `git commit` Bash tool call, runs available formatters' native --fix on
# the STAGED files that have NO unstaged changes, then re-stages them. The
# LLM-judgment half is the lint-repair-loop skill (run by the agent on its own
# session model); this hook makes no LLM call.
#
# Opt-in and fail-open:
#   - Inert unless NEXUS_ENABLE_LINT_AUTOFIX=1 (it mutates files).
#   - Opt-out via NEXUS_DISABLED_HOOKS=lint-autofix or NEXUS_HOOK_PROFILE=minimal.
#   - Never touches a file with unstaged changes (staged-clean files only).
#   - Always exits 0; never blocks a commit. No network, no LLM call.

$ErrorActionPreference = 'SilentlyContinue'

# --- Opt-in gate (this hook mutates files) ---
if ($env:NEXUS_ENABLE_LINT_AUTOFIX -ne '1') { exit 0 }

# --- Opt-out overrides ---
if (",$($env:NEXUS_DISABLED_HOOKS)," -like '*,lint-autofix,*') { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq 'minimal') { exit 0 }

try {
    $raw = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }

    $command = ($raw | ConvertFrom-Json).tool_input.command
    if ([string]::IsNullOrWhiteSpace($command)) { exit 0 }

    # Only act on a `git commit` invocation.
    if ($command -notmatch '(^|[;&|]|\s)git\s+commit(\s|$)') { exit 0 }

    & git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) { exit 0 }

    $staged = @(& git diff --cached --name-only --diff-filter=ACM)
    if (-not $staged -or $staged.Count -eq 0) { exit 0 }
    $unstaged = @(& git diff --name-only)
    $unstagedSet = @{}
    foreach ($u in $unstaged) { if ($u) { $unstagedSet[$u] = $true } }

    $fixed = @()
    $skipped = @()

    foreach ($f in $staged) {
        if (-not $f) { continue }
        if ($unstagedSet.ContainsKey($f)) { $skipped += $f; continue }
        if (-not (Test-Path -LiteralPath $f)) { continue }

        $ext = [System.IO.Path]::GetExtension($f).ToLowerInvariant()
        $did = $false
        switch ($ext) {
            '.py' {
                if (Get-Command ruff -ErrorAction SilentlyContinue) {
                    & ruff check --fix -- $f *> $null
                    & ruff format -- $f *> $null
                    $did = $true
                }
            }
            { $_ -in '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs' } {
                if (Get-Command prettier -ErrorAction SilentlyContinue) {
                    & prettier --write -- $f *> $null
                    $did = $true
                }
            }
            '.go' {
                if (Get-Command gofmt -ErrorAction SilentlyContinue) {
                    & gofmt -w -- $f *> $null
                    $did = $true
                }
            }
            '.sh' {
                if (Get-Command shfmt -ErrorAction SilentlyContinue) {
                    & shfmt -w -- $f *> $null
                    $did = $true
                }
            }
        }
        if ($did) { & git add -- $f *> $null; $fixed += $f }
    }

    if ($fixed.Count -gt 0) { [Console]::Error.WriteLine("[lint-autofix] formatted and re-staged: $($fixed -join ' ')") }
    if ($skipped.Count -gt 0) { [Console]::Error.WriteLine("[lint-autofix] skipped (unstaged changes present): $($skipped -join ' ')") }
}
catch { }

exit 0
