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
    One deliberate difference from the .sh sibling, in the safe direction: the bash
    version needs `jq` to extract multi-line content and exits 0 silently without
    it, so on a host with no jq it never warns. PowerShell parses JSON natively, so
    this version always works. It warns in strictly more cases, never fewer.

    Byte counting: the bash version pipes content through `echo`, which appends a
    newline, so its byte count is one higher than the content's own. This version
    counts the content itself. A one-byte difference against a 50KB threshold is
    immaterial, and the honest count is the more defensible number to report.
#>

# Never fail loudly - always exit 0.
$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "large-file-guard"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

# --- Configuration ---
$maxLines = if ($env:LARGE_FILE_MAX_LINES) { [int]$env:LARGE_FILE_MAX_LINES } else { 500 }
$maxBytes = if ($env:LARGE_FILE_MAX_BYTES) { [long]$env:LARGE_FILE_MAX_BYTES } else { 51200 }

# --- Read JSON from stdin ---
if (-not [Console]::IsInputRedirected) { exit 0 }
$raw = [Console]::In.ReadToEnd()
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
    [Console]::Error.WriteLine("[large-file-guard] Warning: $fileName has $lineCount lines (threshold: $maxLines). Consider splitting this file into smaller modules.")
}

# --- Check byte size ---
$byteCount = [System.Text.Encoding]::UTF8.GetByteCount($content)
if ($byteCount -gt $maxBytes) {
    $kbSize = [math]::Floor($byteCount / 1024)
    $kbThreshold = [math]::Floor($maxBytes / 1024)
    [Console]::Error.WriteLine("[large-file-guard] Warning: $fileName is ${kbSize}KB (threshold: ${kbThreshold}KB). Consider splitting this file into smaller modules.")
}

# Advisory only - never block.
exit 0
