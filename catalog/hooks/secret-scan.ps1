<#
.SYNOPSIS
    PowerShell parity for secret-scan.sh.

.DESCRIPTION
    PreToolUse hook (Write, Edit) that scans the content being written for
    credential-shaped material and BLOCKS (exit 2) when it finds any. Exits 0 when
    the content is clean.

    Detected patterns (same set as the .sh sibling):
      AWS access keys     (AKIA...)
      OpenAI/Stripe keys  (sk-...)
      GitHub tokens       (ghp_..., gho_..., ghs_..., ghr_...)
      Slack tokens        (xoxb-..., xoxp-..., xoxa-...)
      Private keys        (BEGIN RSA / EC / PKCS#8 / OPENSSH PRIVATE KEY)
      Generic secrets     (password/secret/token assignments with 8+ char values)

.NOTES
    This hook BLOCKS, so it mirrors the .sh sibling's contract exactly: the same
    pattern set, the same false-positive exclusions, the same stderr report shape,
    and the same exit 2. Do not soften it without changing the .sh in lockstep.

    One deliberate difference, in the safe direction: the bash version needs `jq`
    and exits 0 silently without it, so on a host with no jq it scans nothing.
    PowerShell parses JSON natively, so this version always scans. It blocks in
    strictly more cases, never fewer.

    It reports only the CATEGORY of each finding, never the matched value, so the
    hook's own output cannot become the leak.
#>

$ErrorActionPreference = "Continue"

# --- Read JSON from stdin ---
if (-not [Console]::IsInputRedirected) { exit 0 }
$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }

$filePath = $null
$content = $null
try {
    $payload = $raw | ConvertFrom-Json
    if ($payload -and $payload.tool_input) {
        $names = $payload.tool_input.PSObject.Properties.Name
        if ($names -contains 'file_path') { $filePath = $payload.tool_input.file_path }
        elseif ($names -contains 'path') { $filePath = $payload.tool_input.path }
        if ($names -contains 'content') { $content = $payload.tool_input.content }
        elseif ($names -contains 'new_string') { $content = $payload.tool_input.new_string }
    }
} catch {
    # Malformed payload: allow rather than block on a parsing artifact.
    exit 0
}

# If there is no content to scan, allow.
if ([string]::IsNullOrEmpty($content)) { exit 0 }

if (-not $filePath) { $filePath = "unknown" }
$fileName = try { Split-Path $filePath -Leaf } catch { $filePath }

# --- Secret patterns (regex -> human-readable category) ---
$secretPatterns = @(
    @{ Pattern = 'AKIA[0-9A-Z]{16}';                     Desc = 'AWS Access Key ID' }
    @{ Pattern = 'sk-[a-zA-Z0-9]{20,}';                  Desc = 'API key (OpenAI/Stripe-style sk- prefix)' }
    @{ Pattern = 'ghp_[a-zA-Z0-9]{36,}';                 Desc = 'GitHub Personal Access Token' }
    @{ Pattern = 'gho_[a-zA-Z0-9]{36,}';                 Desc = 'GitHub OAuth Token' }
    @{ Pattern = 'ghs_[a-zA-Z0-9]{36,}';                 Desc = 'GitHub Server Token' }
    @{ Pattern = 'ghr_[a-zA-Z0-9]{36,}';                 Desc = 'GitHub Refresh Token' }
    @{ Pattern = 'xoxb-[0-9a-zA-Z-]{20,}';               Desc = 'Slack Bot Token' }
    @{ Pattern = 'xoxp-[0-9a-zA-Z-]{20,}';               Desc = 'Slack User Token' }
    @{ Pattern = 'xoxa-[0-9a-zA-Z-]{20,}';               Desc = 'Slack App Token' }
    @{ Pattern = '-----BEGIN RSA PRIVATE KEY-----';      Desc = 'RSA Private Key' }
    @{ Pattern = '-----BEGIN EC PRIVATE KEY-----';       Desc = 'EC Private Key' }
    @{ Pattern = '-----BEGIN PRIVATE KEY-----';          Desc = 'Private Key (PKCS#8)' }
    @{ Pattern = '-----BEGIN OPENSSH PRIVATE KEY-----';  Desc = 'OpenSSH Private Key' }
)

$found = New-Object System.Collections.Generic.List[string]

foreach ($entry in $secretPatterns) {
    # -cmatch keeps the case sensitivity of the .sh sibling's `grep -E`.
    if ($content -cmatch $entry.Pattern) { $found.Add($entry.Desc) }
}

# --- Hardcoded password/secret/token assignments in config-like content ---
# Matches: password = "value", secret: 'value', TOKEN="value" (8+ char values).
$assignRe = '(password|secret|token|api_key|apikey|auth_token|access_token)\s*[:=]\s*["''][^"'']{8,}'
$fpRe = '(your[-_]|example|placeholder|changeme|xxx|process\.env|os\.environ|\$\{|\$\()'
if ($content -imatch $assignRe) {
    # Re-find the first matching LINE so the false-positive filter is applied to
    # the same text the .sh sibling checks, not to the whole document.
    $matchLine = ($content -split "`n" | Where-Object { $_ -imatch $assignRe } | Select-Object -First 1)
    if ($matchLine -and -not ($matchLine -imatch $fpRe)) {
        $found.Add('Hardcoded password/secret/token assignment')
    }
}

# --- Report findings ---
if ($found.Count -gt 0) {
    [Console]::Error.WriteLine("[secret-scan] BLOCKED: Potential secrets detected in ${fileName}:")
    foreach ($s in $found) { [Console]::Error.WriteLine("  - $s") }
    [Console]::Error.WriteLine("Remove secrets and use environment variables or a secrets manager instead.")
    exit 2
}

# Content is clean.
exit 0
