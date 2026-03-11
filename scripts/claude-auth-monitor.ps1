# Claude Code Auth Monitor - Silent Token Refresh
# Proactively refreshes the OAuth access token before it expires so the
# Claude Code VS Code extension never shows the login page mid-session.
#
# How it works:
#   Reads ~/.claude/.credentials.json, checks expiresAt, and if the token
#   expires within $RefreshThresholdMinutes it POSTs to the Anthropic token
#   endpoint using the stored refreshToken. The updated credentials are
#   written back to the same file; the VS Code extension picks them up on
#   its next API call with no restart required.
#
# Installed to: ~/.devai-hub/scripts/claude-auth-monitor.ps1
# Launched by:  ~/.devai-hub/scripts/run-auth-monitor.vbs (wscript, truly hidden)
# Scheduled:    Windows Task Scheduler — every 2 minutes

$ErrorActionPreference = "Stop"

$CredentialsFile         = Join-Path $env:USERPROFILE ".claude\.credentials.json"
$TokenRefreshUrl         = "https://console.anthropic.com/v1/oauth/token"
$ClientId                = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
$RefreshThresholdMinutes = 30   # Refresh when fewer than this many minutes remain

# --- Helpers ---

function Send-ToastNotification {
    param([string]$Title, [string]$Message)
    $savedPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        $xmlDoc = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xmlDoc.LoadXml(@"
<?xml version="1.0"?>
<toast>
  <visual><binding template="ToastText02">
    <text id="1">$Title</text>
    <text id="2">$Message</text>
  </binding></visual>
</toast>
"@)
        $toast = New-Object Windows.UI.Notifications.ToastNotification $xmlDoc
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude Code Auth Monitor").Show($toast)
    }
    catch {
        try {
            Add-Type -AssemblyName System.Windows.Forms 2>$null
            $notify = New-Object System.Windows.Forms.NotifyIcon
            $notify.Icon = [System.Drawing.SystemIcons]::Warning
            $notify.Visible = $true
            $notify.ShowBalloonTip(8000, $Title, $Message, [System.Windows.Forms.ToolTipIcon]::Warning)
            Start-Sleep -Seconds 9
            $notify.Dispose()
        }
        catch { }
    }
    $ErrorActionPreference = $savedPref
}

function Get-OAuthCredentials {
    if (-not (Test-Path $CredentialsFile)) { return $null }
    try {
        $raw = Get-Content $CredentialsFile -Raw | ConvertFrom-Json
        return $raw.claudeAiOauth
    }
    catch { return $null }
}

function Save-OAuthCredentials {
    param(
        [string]$AccessToken,
        [string]$RefreshToken,
        [long]$ExpiresAt
    )
    try {
        $raw = Get-Content $CredentialsFile -Raw | ConvertFrom-Json
        $raw.claudeAiOauth.accessToken  = $AccessToken
        $raw.claudeAiOauth.refreshToken = $RefreshToken
        $raw.claudeAiOauth.expiresAt    = $ExpiresAt
        $raw | ConvertTo-Json -Depth 10 | Set-Content $CredentialsFile -Encoding UTF8
        return $true
    }
    catch { return $false }
}

function Invoke-TokenRefresh {
    param([string]$RefreshToken)
    $body = "grant_type=refresh_token&refresh_token=$([Uri]::EscapeDataString($RefreshToken))&client_id=$ClientId"
    $savedPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $response = Invoke-WebRequest `
            -Uri $TokenRefreshUrl `
            -Method POST `
            -Headers @{ "Content-Type" = "application/x-www-form-urlencoded" } `
            -Body $body `
            -UseBasicParsing `
            -ErrorAction SilentlyContinue
        $ErrorActionPreference = $savedPref
        if ($response -and $response.StatusCode -eq 200) {
            return $response.Content | ConvertFrom-Json
        }
        return $null
    }
    catch {
        $ErrorActionPreference = $savedPref
        return $null
    }
}

# --- Main ---

$creds = Get-OAuthCredentials
if (-not $creds) { exit 0 }
if (-not $creds.refreshToken) { exit 0 }

# Determine whether a refresh is needed
$needsRefresh = $false

if (-not $creds.accessToken) {
    $needsRefresh = $true
}
elseif ($creds.expiresAt) {
    # expiresAt is stored as milliseconds since Unix epoch
    $expiresAt = [DateTimeOffset]::FromUnixTimeMilliseconds([long]$creds.expiresAt)
    $minutesRemaining = ($expiresAt - [DateTimeOffset]::UtcNow).TotalMinutes
    if ($minutesRemaining -lt $RefreshThresholdMinutes) {
        $needsRefresh = $true
    }
}
else {
    # No expiry info — attempt a refresh to be safe
    $needsRefresh = $true
}

if (-not $needsRefresh) { exit 0 }

# Call the refresh endpoint
$tokenResponse = Invoke-TokenRefresh -RefreshToken $creds.refreshToken

if (-not $tokenResponse -or -not $tokenResponse.access_token) {
    # Refresh token may have expired — user must log in manually
    Send-ToastNotification `
        -Title "Claude Code: Sign-In Required" `
        -Message "Your session could not be refreshed automatically. Please sign in via the Claude Code extension in VS Code."
    exit 0
}

# Calculate new expiry (milliseconds since Unix epoch)
$newExpiresAt = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() + ([long]$tokenResponse.expires_in * 1000)

# Write updated credentials back to disk
$saved = Save-OAuthCredentials `
    -AccessToken  $tokenResponse.access_token `
    -RefreshToken $tokenResponse.refresh_token `
    -ExpiresAt    $newExpiresAt

# No success toast — silent refresh should be invisible to the user.
# Only surface failures (above). A log entry is enough for diagnostics.
if ($saved) {
    $logLine = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') Token refreshed silently. New expiry: $([DateTimeOffset]::FromUnixTimeMilliseconds($newExpiresAt).ToString('yyyy-MM-dd HH:mm:ss')) UTC"
    $logFile = Join-Path $env:USERPROFILE ".devai-hub\auth-monitor.log"
    try { Add-Content -Path $logFile -Value $logLine -ErrorAction SilentlyContinue } catch { }
}

exit 0
