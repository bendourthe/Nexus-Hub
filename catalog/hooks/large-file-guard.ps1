<#
.SYNOPSIS
    PowerShell parity for large-file-guard.sh.

.DESCRIPTION
    PreToolUse hook (Write) that warns when the content being written exceeds a
    line-count or byte-size threshold. Advisory only: always exits 0.

    Thresholds (same environment variables as the .sh sibling):
      LARGE_FILE_MAX_LINES  (default 500)
      LARGE_FILE_MAX_BYTES  (default 51200 = 50KB)

.NOTES
    PowerShell parses JSON natively. The Bash sibling uses jq when available and
    falls back to Python 3, so both implementations warn on hosts without jq.

    Byte counting: the bash version pipes content through `echo`, which appends a
    newline, so its byte count is one higher than the content's own. This version
    counts the content itself. A one-byte difference against a 50KB threshold is
    immaterial, and the honest count is the more defensible number to report.
#>

# Never fail loudly - always exit 0.
$ErrorActionPreference = "Continue"

# Read Settings on every invocation. Only an exact JSON false disables a guard.
function Test-NexusGuardrailDisabled {
    param([string]$Key)
    $guardHome = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
    if (-not $guardHome) { return $false }
    try {
        $guardFile = Join-Path $guardHome '.nexus-hub/guardrails.json'
        if (-not (Test-Path -LiteralPath $guardFile -PathType Leaf)) { return $false }
        # PowerShell 7 unwraps a one-element JSON array into its object, so require a top-level object first.
        $guardText = (Get-Content -LiteralPath $guardFile -Raw -ErrorAction Stop).TrimStart([char]0xFEFF, ' ', "`t", "`r", "`n")
        if (-not $guardText.StartsWith('{')) { return $false }
        $guardSettings = $guardText | ConvertFrom-Json -ErrorAction Stop
        if ($guardSettings -isnot [pscustomobject]) { return $false }
        $guardProperty = $guardSettings.PSObject.Properties | Where-Object { $_.Name -ceq $Key } | Select-Object -First 1
        return ($null -ne $guardProperty -and $guardProperty.Value -is [bool] -and -not $guardProperty.Value)
    } catch { return $false }
}
if (Test-NexusGuardrailDisabled -Key "warn_large_files") { exit 0 }

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
$script:NexusTag = "[Nexus-Hub: large-file-guard]"
# Make CR, LF, ESC and the other C0 control characters in an echoed value
# visible, so a file name or command cannot start a forged tagged line.
function ConvertTo-NexusVisible {
    param([string]$Value)
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in "$Value".ToCharArray()) {
        $code = [int]$ch
        if ($code -eq 9) { [void]$sb.Append('\t') }
        elseif ($code -eq 10) { [void]$sb.Append('\n') }
        elseif ($code -eq 13) { [void]$sb.Append('\r') }
        elseif ($code -lt 32 -or $code -eq 127) { [void]$sb.Append(('\x{0:x2}' -f $code)) }
        else { [void]$sb.Append($ch) }
    }
    return $sb.ToString()
}
# Print the tag and the message to stderr; every further line is printed as is.
function Write-NexusMessage {
    param([string]$Message, [string[]]$More = @())
    [Console]::Error.WriteLine("$script:NexusTag $Message")
    foreach ($line in $More) { [Console]::Error.WriteLine($line) }
}

# --- Runtime controls ---
$hookName = "large-file-guard"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

# --- Configuration ---
$maxLines = if ($env:LARGE_FILE_MAX_LINES) { [int]$env:LARGE_FILE_MAX_LINES } else { 500 }
$maxBytes = if ($env:LARGE_FILE_MAX_BYTES) { [long]$env:LARGE_FILE_MAX_BYTES } else { 51200 }

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

try { $payload = $raw | ConvertFrom-Json } catch { exit 0 }
if (-not $payload -or -not $payload.tool_input) { exit 0 }

$names = $payload.tool_input.PSObject.Properties.Name
$filePath = if ($names -contains 'file_path') { $payload.tool_input.file_path }
            elseif ($names -contains 'path') { $payload.tool_input.path }
            else { $null }
$content = if ($names -contains 'content') { $payload.tool_input.content } else { $null }

if (-not $content) { exit 0 }
if (-not $filePath) { exit 0 }

$fileName = try { Split-Path $filePath -Leaf } catch { $filePath }

# --- Check line count ---
$lineCount = ($content -split "`n").Count
if ($lineCount -gt $maxLines) {
    Write-NexusMessage "Warning: $(ConvertTo-NexusVisible $fileName) has $lineCount lines (threshold: $maxLines). Consider splitting this file into smaller modules."
}

# --- Check byte size ---
$byteCount = [System.Text.Encoding]::UTF8.GetByteCount($content)
if ($byteCount -gt $maxBytes) {
    $kbSize = [math]::Floor($byteCount / 1024)
    $kbThreshold = [math]::Floor($maxBytes / 1024)
    Write-NexusMessage "Warning: $(ConvertTo-NexusVisible $fileName) is ${kbSize}KB (threshold: ${kbThreshold}KB). Consider splitting this file into smaller modules."
}

# Advisory only - never block.
exit 0
