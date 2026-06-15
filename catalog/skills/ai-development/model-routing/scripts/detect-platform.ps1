<#
.SYNOPSIS
    Detect the agentic platform currently running.

.DESCRIPTION
    PowerShell sibling of detect-platform.sh. Prints a single normalized
    platform id on stdout, one of:
        claude-code | codex | antigravity | gemini-cli | cursor | copilot |
        opencode | unknown

    Detection is best-effort and uses only environment cues that are already
    present: host-injected environment markers first, then binary-on-PATH plus
    config-dir presence as an availability fallback. Makes ZERO outbound calls
    and requires no credential.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-Binary {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-Platform {
    # 1. Host-injected environment markers (the platform you are running IN).
    if ($env:CLAUDECODE -or $env:CLAUDE_CODE_ENTRYPOINT -or $env:CLAUDE_CODE_SSE_PORT) {
        return 'claude-code'
    }
    if ($env:CODEX_HOME -or $env:CODEX_SANDBOX) {
        return 'codex'
    }
    if ($env:CURSOR_TRACE_ID -or $env:CURSOR_AGENT) {
        return 'cursor'
    }
    if ($env:COPILOT_AGENT_ID -or $env:GITHUB_COPILOT_CLI) {
        return 'copilot'
    }
    if ($env:OPENCODE -or $env:OPENCODE_BIN_PATH) {
        return 'opencode'
    }

    # 2. Binary-on-PATH + config-dir presence (availability fallback). agy
    #    (Antigravity) is checked before the generic gemini binary because both
    #    live under ~/.gemini. Each function call is wrapped in parentheses so
    #    PowerShell does not parse -or as an argument to the call.
    $userHome = $env:USERPROFILE
    if ((Test-Binary 'agy') -or (Test-Path (Join-Path $userHome '.gemini/antigravity-cli'))) {
        return 'antigravity'
    }
    if ((Test-Binary 'codex') -or (Test-Path (Join-Path $userHome '.codex'))) {
        return 'codex'
    }
    if ((Test-Binary 'gemini') -or (Test-Path (Join-Path $userHome '.gemini'))) {
        return 'gemini-cli'
    }
    if (Test-Binary 'opencode') {
        return 'opencode'
    }

    return 'unknown'
}

Write-Output (Get-Platform)
