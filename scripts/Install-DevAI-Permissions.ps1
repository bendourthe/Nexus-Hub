<#
.SYNOPSIS
    Install, update, or remove DevAI-Hub auto-approve permission configs for AI coding platforms.

.DESCRIPTION
    Detects which AI coding tools are installed (Claude Code, OpenAI Codex CLI,
    Google Gemini CLI, GitHub Copilot) and merges safe, read-only auto-approve
    permissions into each tool's user-level config.

    Auto-approved operations: file reads, glob/grep search, web search,
    web fetch (trusted domains only), git read-only commands.

    NOT auto-approved: file writes, edits, destructive commands, git mutations,
    package installs.

.PARAMETER DryRun
    Show what would change without writing any files. Maps to -WhatIf.

.PARAMETER Uninstall
    Remove DevAI-Hub permission entries from each platform's config.
    Restores from the most recent backup if available.

.PARAMETER Platforms
    Specify which platforms to target. Defaults to all four.
    Valid values: CLAUDE, GEMINI, CODEX, COPILOT

.EXAMPLE
    .\Install-DevAI-Permissions.ps1 -DryRun

.EXAMPLE
    .\Install-DevAI-Permissions.ps1 -Platforms CLAUDE,GEMINI

.EXAMPLE
    .\Install-DevAI-Permissions.ps1 -Uninstall
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$DryRun,
    [switch]$Uninstall,
    [ValidateSet("CLAUDE", "GEMINI", "CODEX", "COPILOT")]
    [string[]]$Platforms = @("CLAUDE", "GEMINI", "CODEX", "COPILOT")
)

# Map -DryRun to -WhatIf
if ($DryRun) { $WhatIfPreference = $true }

$ErrorActionPreference = "Stop"

# Resolve repo root (script is in scripts/)
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PermDir = Join-Path $RepoRoot "configs\permissions"

# --- Helper Functions ---

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-ToolInstalled {
    param([string]$Platform)
    switch ($Platform) {
        "CLAUDE"  { return (Get-Command "claude" -ErrorAction SilentlyContinue) -ne $null }
        "GEMINI"  { return (Get-Command "gemini" -ErrorAction SilentlyContinue) -ne $null }
        "CODEX"   { return (Get-Command "codex" -ErrorAction SilentlyContinue) -ne $null }
        "COPILOT" { return (Get-Command "gh" -ErrorAction SilentlyContinue) -ne $null }
        default   { return $false }
    }
}

function Get-PlatformConfigPath {
    param([string]$Platform)
    switch ($Platform) {
        "CLAUDE"  { return Join-Path $env:USERPROFILE ".claude\settings.json" }
        "GEMINI"  { return Join-Path $env:USERPROFILE ".gemini\settings.json" }
        "CODEX"   { return Join-Path $env:USERPROFILE ".codex\config.toml" }
        "COPILOT" { return Join-Path $env:APPDATA "Code\User\settings.json" }
    }
}

function Backup-Config {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        $backupPath = "$FilePath.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        if ($PSCmdlet.ShouldProcess($FilePath, "Create backup at $backupPath")) {
            Copy-Item -Path $FilePath -Destination $backupPath -Force
            Write-Status "  Backup: $backupPath" "DarkGray"
        }
        return $backupPath
    }
    return $null
}

function Get-LatestBackup {
    param([string]$FilePath)
    $dir = Split-Path $FilePath
    $name = Split-Path $FilePath -Leaf
    $backups = Get-ChildItem -Path $dir -Filter "$name.bak.*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($backups.Count -gt 0) { return $backups[0].FullName }
    return $null
}

# --- Install Logic ---

function Install-ClaudePermissions {
    $settingsFile = Get-PlatformConfigPath "CLAUDE"
    $templateFile = Join-Path $PermDir "claude-permissions.json"

    if (-not (Test-Path $templateFile)) {
        Write-Status "  Template not found: $templateFile" "Yellow"
        return
    }

    $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json
    $newEntries = @($templateJson.permissions.allow)

    if (Test-Path $settingsFile) {
        # Counting new entries BEFORE merging avoids the stale-sentinel bug
        # where a single fixed marker (e.g. WebFetch github.com) made the
        # installer skip merging entries that were added in later versions
        # of the template.
        $existingJson = Get-Content $settingsFile -Raw | ConvertFrom-Json

        if (-not $existingJson.permissions) {
            $existingJson | Add-Member -NotePropertyName "permissions" -NotePropertyValue ([PSCustomObject]@{ allow = @() })
        }
        elseif (-not $existingJson.permissions.allow) {
            $existingJson.permissions | Add-Member -NotePropertyName "allow" -NotePropertyValue @()
        }

        $existing = @($existingJson.permissions.allow)
        $merged = @($existing + $newEntries | Select-Object -Unique)
        $addedCount = $merged.Count - $existing.Count

        if ($addedCount -eq 0) {
            Write-Status "  Up to date (0 new entries)." "DarkGreen"
            return
        }

        if ($PSCmdlet.ShouldProcess($settingsFile, "Add $addedCount permission entries")) {
            Backup-Config $settingsFile | Out-Null
            $existingJson.permissions.allow = $merged
            $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            Write-Status "  Added $addedCount entries to permissions.allow" "Green"
        }
    }
    else {
        $configDir = Split-Path $settingsFile
        if ($PSCmdlet.ShouldProcess($settingsFile, "Create with $($newEntries.Count) permission entries")) {
            if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Force -Path $configDir | Out-Null }
            $newJson = [PSCustomObject]@{ permissions = [PSCustomObject]@{ allow = $newEntries } }
            $newJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            Write-Status "  Created $settingsFile with $($newEntries.Count) entries" "Green"
        }
    }
}

function Install-GeminiPermissions {
    $settingsFile = Get-PlatformConfigPath "GEMINI"
    $templateFile = Join-Path $PermDir "gemini-permissions.json"

    if (-not (Test-Path $templateFile)) {
        Write-Status "  Template not found: $templateFile" "Yellow"
        return
    }

    $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json
    $newTools = @($templateJson.tools.allowed)
    $newDomains = @($templateJson.allowedDomains)

    if (Test-Path $settingsFile) {
        $content = Get-Content $settingsFile -Raw
        if ($content -match '"ReadFileTool"' -and $content -match '"allowedDomains"') {
            Write-Status "  Already configured. Skipping." "DarkGreen"
            return
        }

        $existingJson = $content | ConvertFrom-Json
        Backup-Config $settingsFile | Out-Null

        if (-not $existingJson.tools) {
            $existingJson | Add-Member -NotePropertyName "tools" -NotePropertyValue ([PSCustomObject]@{ allowed = @() })
        }
        elseif (-not $existingJson.tools.allowed) {
            $existingJson.tools | Add-Member -NotePropertyName "allowed" -NotePropertyValue @()
        }
        if (-not $existingJson.allowedDomains) {
            $existingJson | Add-Member -NotePropertyName "allowedDomains" -NotePropertyValue @()
        }

        $mergedTools = @(@($existingJson.tools.allowed) + $newTools | Select-Object -Unique)
        $mergedDomains = @(@($existingJson.allowedDomains) + $newDomains | Select-Object -Unique)

        if ($PSCmdlet.ShouldProcess($settingsFile, "Merge tools.allowed and allowedDomains")) {
            $existingJson.tools.allowed = $mergedTools
            $existingJson.allowedDomains = $mergedDomains
            $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            Write-Status "  Merged tools and domains into settings.json" "Green"
        }
    }
    else {
        $configDir = Split-Path $settingsFile
        if ($PSCmdlet.ShouldProcess($settingsFile, "Create with tools and domain allowlists")) {
            if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Force -Path $configDir | Out-Null }
            $newJson = [PSCustomObject]@{
                tools = [PSCustomObject]@{ allowed = $newTools }
                allowedDomains = $newDomains
            }
            $newJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            Write-Status "  Created $settingsFile" "Green"
        }
    }
}

function Install-CodexPermissions {
    $configFile = Get-PlatformConfigPath "CODEX"
    $templateFile = Join-Path $PermDir "codex-permissions.toml"

    if (-not (Test-Path $templateFile)) {
        Write-Status "  Template not found: $templateFile" "Yellow"
        return
    }

    if (Test-Path $configFile) {
        $content = Get-Content $configFile -Raw
        if ($content -match 'permissions\.default\.network' -and $content -match 'allowed_domains') {
            Write-Status "  Already configured. Skipping." "DarkGreen"
            return
        }

        Backup-Config $configFile | Out-Null

        $templateContent = Get-Content $templateFile -Raw
        $sectionsToAdd = @()

        if ($content -notmatch 'approval_policy') {
            $sectionsToAdd += 'approval_policy = "on-request"'
        }
        if ($content -notmatch '\[permissions\.default\.filesystem\]') {
            $match = [regex]::Match($templateContent, '(?s)\[permissions\.default\.filesystem\].*?(?=\[|$)')
            if ($match.Success) { $sectionsToAdd += $match.Value.Trim() }
        }
        if ($content -notmatch '\[permissions\.default\.network\]') {
            $idx = $templateContent.IndexOf('[permissions.default.network]')
            if ($idx -ge 0) { $sectionsToAdd += $templateContent.Substring($idx).Trim() }
        }

        if ($sectionsToAdd.Count -gt 0) {
            $appendContent = "`n`n# --- DevAI-Hub auto-approve permissions ---`n" + ($sectionsToAdd -join "`n`n")
            if ($PSCmdlet.ShouldProcess($configFile, "Append permission sections")) {
                Add-Content -Path $configFile -Value $appendContent -Encoding UTF8
                Write-Status "  Updated config.toml with permissions" "Green"
            }
        }
    }
    else {
        $configDir = Split-Path $configFile
        if ($PSCmdlet.ShouldProcess($configFile, "Create from template")) {
            if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Force -Path $configDir | Out-Null }
            Copy-Item -Path $templateFile -Destination $configFile -Force
            Write-Status "  Created $configFile" "Green"
        }
    }
}

function Install-CopilotPermissions {
    $settingsFile = Get-PlatformConfigPath "COPILOT"

    if (-not (Test-Path $settingsFile)) {
        Write-Status "  VS Code settings.json not found at $settingsFile" "Yellow"
        Write-Status "  Copilot permissions require VS Code." "Gray"
        return
    }

    $content = Get-Content $settingsFile -Raw
    if ($content -match 'useInstructionFiles.*true') {
        Write-Status "  Already configured. Skipping." "DarkGreen"
        return
    }

    $existingJson = $content | ConvertFrom-Json
    Backup-Config $settingsFile | Out-Null

    $key = "github.copilot.chat.codeGeneration.useInstructionFiles"
    if ($PSCmdlet.ShouldProcess($settingsFile, "Set $key = true")) {
        if (-not ($existingJson.PSObject.Properties.Name -contains $key)) {
            $existingJson | Add-Member -NotePropertyName $key -NotePropertyValue $true
        }
        else {
            $existingJson.$key = $true
        }
        $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
        Write-Status "  Enabled useInstructionFiles in VS Code settings" "Green"
    }
}

# --- Uninstall Logic ---

function Uninstall-ClaudePermissions {
    $settingsFile = Get-PlatformConfigPath "CLAUDE"
    if (-not (Test-Path $settingsFile)) {
        Write-Status "  No settings.json found. Nothing to remove." "DarkGray"
        return
    }

    $templateFile = Join-Path $PermDir "claude-permissions.json"
    if (-not (Test-Path $templateFile)) {
        Write-Status "  Template not found; cannot determine which entries to remove." "Yellow"
        return
    }

    $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json
    $entriesToRemove = @($templateJson.permissions.allow)
    $existingJson = Get-Content $settingsFile -Raw | ConvertFrom-Json

    if ($existingJson.permissions -and $existingJson.permissions.allow) {
        Backup-Config $settingsFile | Out-Null
        $filtered = @($existingJson.permissions.allow | Where-Object { $_ -notin $entriesToRemove })
        $removedCount = $existingJson.permissions.allow.Count - $filtered.Count

        if ($PSCmdlet.ShouldProcess($settingsFile, "Remove $removedCount DevAI-Hub permission entries")) {
            $existingJson.permissions.allow = $filtered
            $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            Write-Status "  Removed $removedCount entries from permissions.allow" "Green"
        }
    }
    else {
        Write-Status "  No permissions.allow found. Nothing to remove." "DarkGray"
    }
}

function Uninstall-GeminiPermissions {
    $settingsFile = Get-PlatformConfigPath "GEMINI"
    if (-not (Test-Path $settingsFile)) {
        Write-Status "  No settings.json found. Nothing to remove." "DarkGray"
        return
    }

    $templateFile = Join-Path $PermDir "gemini-permissions.json"
    if (-not (Test-Path $templateFile)) { return }

    $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json
    $existingJson = Get-Content $settingsFile -Raw | ConvertFrom-Json

    Backup-Config $settingsFile | Out-Null

    if ($existingJson.tools -and $existingJson.tools.allowed) {
        $toolsToRemove = @($templateJson.tools.allowed)
        $filtered = @($existingJson.tools.allowed | Where-Object { $_ -notin $toolsToRemove })
        if ($PSCmdlet.ShouldProcess($settingsFile, "Remove DevAI-Hub tool entries")) {
            $existingJson.tools.allowed = $filtered
        }
    }

    if ($existingJson.allowedDomains) {
        $domainsToRemove = @($templateJson.allowedDomains)
        $filtered = @($existingJson.allowedDomains | Where-Object { $_ -notin $domainsToRemove })
        if ($PSCmdlet.ShouldProcess($settingsFile, "Remove DevAI-Hub domain entries")) {
            $existingJson.allowedDomains = $filtered
        }
    }

    if ($PSCmdlet.ShouldProcess($settingsFile, "Write cleaned settings")) {
        $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
        Write-Status "  Removed DevAI-Hub entries from settings.json" "Green"
    }
}

function Uninstall-CodexPermissions {
    $configFile = Get-PlatformConfigPath "CODEX"
    if (-not (Test-Path $configFile)) {
        Write-Status "  No config.toml found. Nothing to remove." "DarkGray"
        return
    }

    # Restore from latest backup if available
    $backup = Get-LatestBackup $configFile
    if ($backup) {
        if ($PSCmdlet.ShouldProcess($configFile, "Restore from backup $backup")) {
            Copy-Item -Path $backup -Destination $configFile -Force
            Write-Status "  Restored from backup: $backup" "Green"
        }
    }
    else {
        Write-Status "  No backup found. Remove DevAI-Hub sections from $configFile manually." "Yellow"
    }
}

function Uninstall-CopilotPermissions {
    $settingsFile = Get-PlatformConfigPath "COPILOT"
    if (-not (Test-Path $settingsFile)) {
        Write-Status "  No VS Code settings.json found. Nothing to remove." "DarkGray"
        return
    }

    $existingJson = Get-Content $settingsFile -Raw | ConvertFrom-Json
    $key = "github.copilot.chat.codeGeneration.useInstructionFiles"

    if ($existingJson.PSObject.Properties.Name -contains $key) {
        Backup-Config $settingsFile | Out-Null
        if ($PSCmdlet.ShouldProcess($settingsFile, "Remove $key")) {
            $existingJson.PSObject.Properties.Remove($key)
            $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            Write-Status "  Removed $key from VS Code settings" "Green"
        }
    }
    else {
        Write-Status "  $key not found. Nothing to remove." "DarkGray"
    }
}

# --- Main ---

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "       DevAI-Hub Auto-Approve Permissions Manager" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

if ($WhatIfPreference) {
    Write-Host "[DRY RUN] No files will be modified." -ForegroundColor Yellow
    Write-Host ""
}

if ($Uninstall) {
    Write-Host "Mode: UNINSTALL (removing DevAI-Hub permission entries)" -ForegroundColor Yellow
    Write-Host ""
}
else {
    Write-Host "Mode: INSTALL (merging safe read-only permissions)" -ForegroundColor White
    Write-Host ""
}

foreach ($platform in $Platforms) {
    $installed = Test-ToolInstalled $platform
    $configPath = Get-PlatformConfigPath $platform

    Write-Host "--- $platform ---" -ForegroundColor Cyan

    if (-not $installed) {
        Write-Status "  Not detected in PATH. Skipping." "DarkGray"
        switch ($platform) {
            "CLAUDE"  { Write-Status "  Install: https://docs.claude.com/en/docs/install" "Gray" }
            "GEMINI"  { Write-Status "  Install: npm install -g @anthropic-ai/gemini-cli" "Gray" }
            "CODEX"   { Write-Status "  Install: npm install -g @openai/codex" "Gray" }
            "COPILOT" { Write-Status "  Install: https://github.com/features/copilot" "Gray" }
        }
        Write-Host ""
        continue
    }

    Write-Status "  Detected. Config: $configPath" "White"

    if ($Uninstall) {
        switch ($platform) {
            "CLAUDE"  { Uninstall-ClaudePermissions }
            "GEMINI"  { Uninstall-GeminiPermissions }
            "CODEX"   { Uninstall-CodexPermissions }
            "COPILOT" { Uninstall-CopilotPermissions }
        }
    }
    else {
        switch ($platform) {
            "CLAUDE"  { Install-ClaudePermissions }
            "GEMINI"  { Install-GeminiPermissions }
            "CODEX"   { Install-CodexPermissions }
            "COPILOT" { Install-CopilotPermissions }
        }
    }

    Write-Host ""
}

Write-Host "================================================================" -ForegroundColor Green
Write-Host "  Done." -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
