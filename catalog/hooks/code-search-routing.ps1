<#
.SYNOPSIS
    PowerShell parity for code-search-routing.sh.

.DESCRIPTION
    PreToolUse advisory hook for Grep, Glob, and conservative Bash search
    patterns. It recommends the local nexus-code-search index, always allows by
    default, and blocks only when NEXUS_CODE_SEARCH_ROUTING=block is explicit.
    Read is always excluded. The hook performs local string inspection only.
#>

$ErrorActionPreference = "Continue"

$hookName = "code-search-routing"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

function Write-DebugLog {
    param([string]$Message)
    if ($env:NEXUS_CODE_SEARCH_ROUTING_DEBUG -eq "1") {
        [Console]::Error.WriteLine("[code-search-routing debug] $Message")
    }
}

if (-not [Console]::IsInputRedirected) {
    Write-DebugLog "stdin is not redirected; allowing"
    exit 0
}

$raw = [Console]::In.ReadToEnd()
if (-not $raw) {
    Write-DebugLog "empty stdin; allowing"
    exit 0
}

try {
    $payload = $raw | ConvertFrom-Json
} catch {
    Write-DebugLog "malformed payload; allowing"
    exit 0
}

$toolName = if ($payload -and $payload.tool_name) { [string]$payload.tool_name } else { "" }
$command = if ($payload -and $payload.tool_input -and $payload.tool_input.command) { [string]$payload.tool_input.command } else { "" }

if (-not $toolName) {
    Write-DebugLog "incomplete payload; allowing"
    exit 0
}

if ($toolName -eq "Read") {
    Write-DebugLog "Read is explicitly excluded"
    exit 0
}

$indexedTool = ""
$hint = ""
switch ($toolName) {
    "Grep" {
        $indexedTool = "search_code"
        $hint = 'search_code(root="<repo>", query="<pattern>")'
    }
    "Glob" {
        $indexedTool = "code_search"
        $hint = 'code_search(root="<repo>", query="<file-or-symbol>")'
    }
    "Bash" {
        $lowerCommand = $command.ToLowerInvariant()
        if ($lowerCommand -match '(^|[|;&]\s*)(grep|rg)(\s|$)') {
            $indexedTool = "search_code"
            $hint = 'search_code(root="<repo>", query="<pattern>")'
        } elseif (
            $lowerCommand -match '(^|[|;&]\s*)find(\s|$)' -and
            $lowerCommand -match '\s-(name|iname|path|regex)\s' -and
            $lowerCommand -notmatch '\s-(delete|exec|execdir)(\s|$)'
        ) {
            $indexedTool = "code_search"
            $hint = 'code_search(root="<repo>", query="<file-or-symbol>")'
        }
    }
    default {
        Write-DebugLog "tool $toolName is outside the routing surface"
        exit 0
    }
}

if (-not $indexedTool) {
    Write-DebugLog "no conservative match for $toolName"
    exit 0
}

$message = "[code-search-routing] Prefer the local nexus-code-search index for this search: $hint. Native search remains available if the index is absent or the query needs raw filesystem semantics."
[Console]::Error.WriteLine($message)

if ($env:NEXUS_CODE_SEARCH_ROUTING -eq "block") {
    [Console]::Error.WriteLine("[code-search-routing] Blocked by NEXUS_CODE_SEARCH_ROUTING=block; unset it or use 'soft' to continue.")
    exit 2
}

exit 0
