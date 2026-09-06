<#
.SYNOPSIS
    PowerShell parity for compress-output.sh.

.DESCRIPTION
    PreToolUse hook (Bash) that, when explicitly enabled, rewrites the Bash command
    so its stdout flows through the local context-compressor engine, then restores
    the original exit status. Emits a PreToolUse allow decision with the rewritten
    tool_input; exits 0 and changes nothing when any precondition fails.

    Opt-in gate (default OFF): set NEXUS_CONTEXT_COMPRESS=1. Inert otherwise, so it
    never rewrites commands, and never spawns a Python import check per Bash call,
    for users who have not opted in.

.NOTES
    IMPORTANT: the command being rewritten is a BASH command, so this hook emits
    BASH syntax even though the hook itself is PowerShell. `${PIPESTATUS[0]}` is a
    bash construct and is emitted LITERALLY for the target shell to expand; it must
    not be interpolated here. The .ps1 is the hook's implementation language, not
    the shell that runs the result.

    One deliberate difference, in the safe direction: the bash version needs `jq` to
    splice the new command back into tool_input without mangling the JSON, and is
    inert without it. PowerShell handles JSON natively, so this version works with
    no external dependency.

    Fail-open discipline is preserved exactly: if no Python interpreter is present,
    or the engine does not import cleanly, the rewrite is skipped entirely so the
    command runs raw. Piping through a missing engine would swallow the command's
    output, which is worse than not compressing.
#>

$ErrorActionPreference = "Continue"

# --- Opt-in gate (default OFF) -------------------------------------------
if ($env:NEXUS_CONTEXT_COMPRESS -ne "1") { exit 0 }

# --- Read JSON from stdin and extract the command ------------------------
if (-not [Console]::IsInputRedirected) { exit 0 }
$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }

$payload = $null
$command = $null
try {
    $payload = $raw | ConvertFrom-Json
    if ($payload -and $payload.tool_input -and
        ($payload.tool_input.PSObject.Properties.Name -contains 'command')) {
        $command = $payload.tool_input.command
    }
} catch { exit 0 }

# No command (non-Bash tool, or empty): allow unchanged.
if ([string]::IsNullOrEmpty($command)) { exit 0 }

# Idempotency: never wrap a command that already routes through the compressor
# (re-entrancy, or a command the user wrote by hand).
if ($command -match 'nexus_context_compressor') { exit 0 }

# --- Resolve a Python interpreter ----------------------------------------
$pyBin = $null
foreach ($candidate in @('python3', 'python')) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $pyBin = $candidate; break }
}
if (-not $pyBin) { exit 0 }

# --- Fail-open guard: only rewrite if the engine imports cleanly ----------
try {
    & $pyBin -c "import nexus_context_compressor" *> $null
    if ($LASTEXITCODE -ne 0) { exit 0 }
} catch {
    exit 0
}

# --- Build the rewritten command -----------------------------------------
# Wrap the original command in a group so the WHOLE command's stdout (not just its
# last pipeline stage) flows through the compressor, then restore the original exit
# status. The ${PIPESTATUS[0]} below is deliberately LITERAL bash: single-quoted
# here so PowerShell does not touch it, and expanded by the target shell.
$suffix = ' ; } | ' + $pyBin + ' -m nexus_context_compressor compress; exit ${PIPESTATUS[0]}'
$new = '{ ' + $command + $suffix

# --- Emit the PreToolUse decision -----------------------------------------
# Preserve every other tool_input field and replace only .command.
$updated = [ordered]@{}
foreach ($prop in $payload.tool_input.PSObject.Properties) {
    $updated[$prop.Name] = $prop.Value
}
$updated['command'] = $new

$decision = [ordered]@{
    hookSpecificOutput = [ordered]@{
        hookEventName      = 'PreToolUse'
        permissionDecision = 'allow'
        updatedInput       = $updated
    }
}

Write-Output ($decision | ConvertTo-Json -Depth 20 -Compress)
exit 0
