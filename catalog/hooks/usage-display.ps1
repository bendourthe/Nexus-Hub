<#
.SYNOPSIS
    PowerShell parity for usage-display.sh.

.DESCRIPTION
    Stop hook that shows a compact usage-limits summary after a conversation turn.
    Reads the local OAuth credentials, fetches usage from the Anthropic OAuth API,
    caches the response for 5 minutes, and prints a one-line summary to stderr only
    when a metric exceeds the display threshold. Completely silent when usage is
    healthy or any precondition fails; always exits 0.

    Configuration (same values as the .sh sibling):
      display threshold  50%
      cache TTL          300 seconds
      credentials        ~/.claude/.credentials.json
      cache              ~/.claude/.usage-cache.json

.NOTES
    Outbound surface, stated plainly because this is the only catalog hook that
    makes a network call: it reaches exactly ONE host, api.anthropic.com, with the
    user's OWN existing OAuth token, to read that user's own usage. It introduces no
    new credential, no third-party destination, and no telemetry. The token is read
    from the local credentials file and sent only in the Authorization header; it is
    never logged, printed, or written to the cache.

    Three places this version is cleaner than the .sh sibling without changing
    behavior: no `stat` GNU/BSD probing (.NET exposes LastWriteTime), no `date`
    GNU/BSD branching for reset formatting (DateTimeOffset parses ISO 8601
    directly), and no curl/jq dependency (Invoke-RestMethod plus native JSON), so
    it works on a stock Windows host where the bash version would exit silently.

    The cache is written with BOM-less UTF-8 so it stays readable by the .sh
    sibling, which shares the same cache file.
#>

$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "usage-display"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

# --- Configuration ---
$displayThreshold = 50
$cacheTtlSeconds = 300

$claudeDir = Join-Path $HOME ".claude"
$credentialsFile = Join-Path $claudeDir ".credentials.json"
$cacheFile = Join-Path $claudeDir ".usage-cache.json"
$apiUrl = "https://api.anthropic.com/api/oauth/usage"
$betaHeader = "oauth-2025-04-20"

# --- Drain stdin (Stop hooks receive a JSON payload) ---
if ([Console]::IsInputRedirected) { $null = [Console]::In.ReadToEnd() }

function Get-PercentColor {
    <# ANSI colour matching the .sh sibling's thresholds. #>
    param([int]$Pct)
    if ($Pct -ge 90) { return "$([char]27)[0;31m" }        # red
    elseif ($Pct -ge 75) { return "$([char]27)[0;38;5;208m" } # orange
    elseif ($Pct -ge 50) { return "$([char]27)[0;33m" }     # yellow
    else { return "$([char]27)[0;32m" }                     # green
}

$reset = "$([char]27)[0m"
$gray = "$([char]27)[0;90m"

function Format-ResetTime {
    <# ISO 8601 -> "45m", "3h 20m", "Tue  4:05 PM", "any moment", or "N/A". #>
    param([string]$Iso)
    if ([string]::IsNullOrWhiteSpace($Iso) -or $Iso -eq "null") { return "N/A" }

    $resetAt = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse($Iso, [ref]$resetAt)) { return "N/A" }

    $diff = $resetAt - [DateTimeOffset]::Now
    if ($diff.TotalSeconds -le 0) { return "any moment" }

    $totalMinutes = [math]::Floor($diff.TotalMinutes)
    if ($totalMinutes -lt 60) { return "${totalMinutes}m" }

    $hours = [math]::Floor($totalMinutes / 60)
    $remainingMin = $totalMinutes % 60
    if ($hours -lt 24) {
        if ($remainingMin -gt 0) { return "${hours}h ${remainingMin}m" }
        return "${hours}h"
    }

    # More than 24 hours: show day and time, matching the .sh "%a %l:%M %p".
    try { return $resetAt.ToLocalTime().ToString("ddd h:mm tt") } catch { return "${hours}h" }
}

# --- Check cache freshness ---
$apiResponse = $null
$useCache = $false
if (Test-Path -LiteralPath $cacheFile -PathType Leaf) {
    try {
        $cacheAge = ((Get-Date) - (Get-Item -LiteralPath $cacheFile).LastWriteTime).TotalSeconds
        if ($cacheAge -lt $cacheTtlSeconds) { $useCache = $true }
    } catch { $useCache = $false }
}

if ($useCache) {
    try { $apiResponse = Get-Content -LiteralPath $cacheFile -Raw -ErrorAction Stop | ConvertFrom-Json } catch { $apiResponse = $null }
}

if (-not $apiResponse) {
    # --- Read credentials ---
    if (-not (Test-Path -LiteralPath $credentialsFile -PathType Leaf)) { exit 0 }
    try { $creds = Get-Content -LiteralPath $credentialsFile -Raw -ErrorAction Stop | ConvertFrom-Json } catch { exit 0 }

    $token = $null
    if ($creds -and $creds.claudeAiOauth) { $token = $creds.claudeAiOauth.accessToken }
    if ([string]::IsNullOrWhiteSpace($token)) { exit 0 }

    # --- Check token expiry ---
    $expiresAt = 0
    if ($creds.claudeAiOauth.PSObject.Properties.Name -contains 'expiresAt') {
        try { $expiresAt = [long]$creds.claudeAiOauth.expiresAt } catch { $expiresAt = 0 }
    }
    $nowMs = [long]([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())
    if ($expiresAt -gt 0 -and $nowMs -ge $expiresAt) { exit 0 }  # expired

    # --- Fetch from the API (3-second timeout so a slow network never blocks) ---
    $raw = $null
    try {
        $raw = Invoke-RestMethod -Uri $apiUrl -Method Get -TimeoutSec 3 -Headers @{
            "Authorization"  = "Bearer $token"
            "anthropic-beta" = $betaHeader
        } -ErrorAction Stop
    } catch {
        exit 0
    }
    if (-not $raw) { exit 0 }

    # Verify the response carries the expected shape before trusting or caching it.
    if (-not ($raw.PSObject.Properties.Name -contains 'five_hour')) { exit 0 }

    $apiResponse = $raw
    # Cache it (BOM-less, so the .sh sibling sharing this file can read it).
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($cacheFile, ($raw | ConvertTo-Json -Depth 20), $utf8NoBom)
    } catch { }
}

# --- Parse metrics (truncate toward zero, as the .sh sibling's ${VAR%.*} does) ---
function Get-Utilization {
    param($Node)
    if (-not $Node) { return 0 }
    if (-not ($Node.PSObject.Properties.Name -contains 'utilization')) { return 0 }
    try { return [int][math]::Floor([double]$Node.utilization) } catch { return 0 }
}

$session = Get-Utilization $apiResponse.five_hour
$weekly = Get-Utilization $apiResponse.seven_day
$sonnet = Get-Utilization $apiResponse.seven_day_sonnet

# --- Threshold check: stay silent when everything is healthy ---
if ($session -lt $displayThreshold -and $weekly -lt $displayThreshold -and $sonnet -lt $displayThreshold) {
    exit 0
}

# --- Find the highest metric and its reset time ---
$highestName = "Session"
$highestPct = $session
$resetIso = if ($apiResponse.five_hour) { $apiResponse.five_hour.resets_at } else { $null }

if ($weekly -gt $highestPct) {
    $highestName = "Weekly"
    $highestPct = $weekly
    $resetIso = if ($apiResponse.seven_day) { $apiResponse.seven_day.resets_at } else { $null }
}
if ($sonnet -gt $highestPct) {
    $highestName = "Sonnet"
    $highestPct = $sonnet
    $resetIso = if ($apiResponse.seven_day_sonnet) { $apiResponse.seven_day_sonnet.resets_at } else { $null }
}

$resetDisplay = Format-ResetTime $resetIso

# --- Build output ---
$out = "${gray}Usage:${reset}"
$out += " Session $(Get-PercentColor $session)$session%${reset}"
$out += " | Weekly $(Get-PercentColor $weekly)$weekly%${reset}"
$out += " | Sonnet $(Get-PercentColor $sonnet)$sonnet%${reset}"
if ($resetDisplay -and $resetDisplay -ne "N/A") {
    $out += "  ${gray}($highestName resets in $resetDisplay)${reset}"
}

# Output to stderr (Claude Code surfaces hook stderr to the user).
[Console]::Error.WriteLine($out)

exit 0
