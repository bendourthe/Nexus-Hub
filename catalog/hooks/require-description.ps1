<#
.SYNOPSIS
    PowerShell parity for require-description.sh.

.DESCRIPTION
    PreToolUse hook that BLOCKS (exit 2) a Bash tool call carrying no description.

    Accepts EITHER of these as proof that a description exists:
      1. A non-empty "description" field in the tool input JSON.
      2. A description comment on the first non-blank line of the command
         (the current "# Description: ..." prefix, the legacy bordered block, or
         the intermediate "# desc:" shape; all three are accepted for backwards
         compatibility).

    The format-bash-description.py hook runs before this one and only adds the
    prefix to commands that are NOT auto-approved; auto-approved commands carry
    their description in the "description" field instead.

.NOTES
    This is one of the few BLOCKING hooks in the catalog, so it mirrors the .sh
    sibling exactly: the same two acceptance checks, the same message text on BOTH
    stdout and stderr, and the same exit 2. Do not soften it to advisory without
    changing the .sh sibling in lockstep.
#>

$ErrorActionPreference = "Continue"

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

$description = $null
$command = $null
try {
    $payload = $raw | ConvertFrom-Json
    if ($payload -and $payload.tool_input) {
        $names = $payload.tool_input.PSObject.Properties.Name
        if ($names -contains 'description') { $description = $payload.tool_input.description }
        if ($names -contains 'command') { $command = $payload.tool_input.command }
    }
} catch {
    # Malformed payload: allow rather than block on a parsing artifact.
    exit 0
}

# --- Check 1: non-empty description field ---
if (-not [string]::IsNullOrWhiteSpace($description)) { exit 0 }

# --- Fail open when there is no command to judge ---
# Mirrors git-guardrails and the .sh sibling: if no command could be extracted,
# this is not a Bash tool call we can assess (an empty payload, a valid payload for
# a DIFFERENT tool such as Write, or a malformed one), so allow rather than block.
# Catching only the parse error is not enough: a well-formed payload carrying no
# command would otherwise fall through to the block below and refuse an unrelated
# tool call.
if ([string]::IsNullOrWhiteSpace($command)) { exit 0 }

# --- Check 2: description comment on the first non-blank line of the command ---
if (-not [string]::IsNullOrWhiteSpace($command)) {
    $firstLine = ($command -split "`n" | Where-Object { $_.Trim() -ne '' } | Select-Object -First 1)
    if ($firstLine -and ($firstLine -imatch '^\s*#.*(desc:|description)')) { exit 0 }
}

# --- Block and instruct the model to provide a description ---
$msg = @'
BLOCKED: Missing required description.

Every Bash command must include a description. Provide it as the
"description" parameter in the Bash tool call (plain text, one
sentence, <=120 chars, no newlines). The format-bash-description.py
hook formats it automatically.

Alternatively, the command may begin with a single-line description
prefix:

  # Description: Lists all agent config files under the project directory
  # ---
  find ~/.claude -type f -name '*.md'

Add a description, then retry.
'@

Write-Output $msg
[Console]::Error.WriteLine($msg)

exit 2
