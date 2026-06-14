<#
.SYNOPSIS
    List the available models for a given agentic platform.

.DESCRIPTION
    PowerShell sibling of enumerate-models.sh. Prints the model list as JSON on
    stdout by calling that platform's OWN enumeration surface. When no
    scriptable enumeration surface exists (Cursor, Copilot, OpenCode, or a
    missing CLI), prints a picker sentinel telling the caller to read the model
    set from the platform's model picker.

    The ONLY outbound call this script can make is the Anthropic GET /v1/models
    endpoint for Claude Code, and ONLY when ANTHROPIC_API_KEY is already set in
    the environment. No other connection is opened and no new credential is
    required.

.PARAMETER Platform
    A normalized platform id produced by detect-platform.ps1.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Platform
)

Set-StrictMode -Version Latest

$pickerSentinel = '{"source":"picker","models":[],"note":"no scriptable model list; read models from the platform model picker"}'

function Test-Binary {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

switch ($Platform) {
    'codex' {
        if (Test-Binary 'codex') {
            try { & codex debug models } catch { Write-Output $pickerSentinel }
        } else {
            Write-Output $pickerSentinel
        }
        break
    }
    'antigravity' {
        if (Test-Binary 'agy') {
            try { & agy models } catch { Write-Output $pickerSentinel }
        } else {
            Write-Output $pickerSentinel
        }
        break
    }
    'gemini-cli' {
        # Gemini CLI's model set lives in its alias config rather than a stable
        # list subcommand; point the caller at the alias set.
        if (Test-Path (Join-Path $env:USERPROFILE '.gemini/settings.json')) {
            Write-Output '{"source":"config","models":[],"note":"read model aliases from ~/.gemini/settings.json"}'
        } else {
            Write-Output $pickerSentinel
        }
        break
    }
    'claude-code' {
        if ($env:ANTHROPIC_API_KEY) {
            try {
                $headers = @{
                    'x-api-key'         = $env:ANTHROPIC_API_KEY
                    'anthropic-version' = '2023-06-01'
                }
                $resp = Invoke-WebRequest -Uri 'https://api.anthropic.com/v1/models' `
                    -Headers $headers -TimeoutSec 10 -UseBasicParsing
                Write-Output $resp.Content
            } catch {
                Write-Output $pickerSentinel
            }
        } else {
            Write-Output $pickerSentinel
        }
        break
    }
    { $_ -in @('cursor', 'copilot', 'opencode', 'unknown') } {
        Write-Output $pickerSentinel
        break
    }
    default {
        Write-Error "unknown platform `"$Platform`""
        exit 2
    }
}
