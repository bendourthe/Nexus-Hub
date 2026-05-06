# DevAI-Hub Universal Installer V10 (Windows)
# Installs AI Skills Globally OR to a Workspace with Safe Overwrite and Modern UI
$ErrorActionPreference = "Stop"

# --- Version ---
# Single source of truth for the installer banner version label.
# Keep in sync with .claude-plugin/plugin.json and CHANGELOG.md.
$script:DevAIHubVersion = "1.1.1"

$Host.UI.RawUI.WindowTitle = "DevAI-Hub Installer"
$script:InstallerTitle = "DevAI-Hub Installer"
function Restore-Title { $Host.UI.RawUI.WindowTitle = $script:InstallerTitle }

# --- Modern Folder Picker (C# P-Invoke) ---
$folderPickerCode = @'
using System;
using System.Runtime.InteropServices;
using System.Runtime.CompilerServices;

namespace ModernFolderPicker
{
    public class FileOpenDialog
    {
        [DllImport("shell32.dll")]
        private static extern int SHCreateItemFromParsingName([MarshalAs(UnmanagedType.LPWStr)] string pszPath, IntPtr pbc, [MarshalAs(UnmanagedType.LPStruct)] Guid riid, out IShellItem ppv);

        [DllImport("user32.dll")]
        private static extern IntPtr GetActiveWindow();

        private const uint FOS_PICKFOLDERS = 0x00000020;
        private const uint FOS_FORCEFILESYSTEM = 0x00000040;

        public static string ShowDialog()
        {
            var dialog = (IFileOpenDialog)new FileOpenDialogImpl();
            dialog.SetOptions(FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM);

            try
            {
                dialog.Show(GetActiveWindow());
                IShellItem item;
                dialog.GetResult(out item);
                string path;
                item.GetDisplayName(SIGDN.SIGDN_FILESYSPATH, out path);
                return path;
            }
            catch { return null; }
        }

        [ComImport, Guid("DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7")]
        private class FileOpenDialogImpl { }

        [ComImport, Guid("d57c7288-d4ad-4768-be02-9d969532d960"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
        private interface IFileOpenDialog
        {
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void Show([In] IntPtr parent);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void SetFileTypes([In] uint cFileTypes, [In] IntPtr rgFilter);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void SetFileTypeIndex([In] uint iFileType);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void GetFileTypeIndex(out uint piFileType);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void Advise([In] IntPtr pfde, out uint pdwCookie);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void Unadvise([In] uint dwCookie);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void SetOptions([In] uint fos);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void GetOptions(out uint fos);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void SetDefaultFolder([In] IShellItem psi);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void SetFolder([In] IShellItem psi);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void GetFolder(out IShellItem ppsi);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void GetCurrentSelection(out IShellItem ppsi);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void SetFileName([In, MarshalAs(UnmanagedType.LPWStr)] string pszName);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void GetFileName([MarshalAs(UnmanagedType.LPWStr)] out string pszName);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void SetTitle([In, MarshalAs(UnmanagedType.LPWStr)] string pszTitle);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void SetOkButtonLabel([In, MarshalAs(UnmanagedType.LPWStr)] string pszText);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void SetFileNameLabel([In, MarshalAs(UnmanagedType.LPWStr)] string pszLabel);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void GetResult(out IShellItem ppsi);
        }

        [ComImport, Guid("43826d1e-e718-42ee-bc55-a1e261c37bfe"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
        private interface IShellItem
        {
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void BindToHandler([In] IntPtr pbc, [In] ref Guid bhid, [In] ref Guid riid, out IntPtr ppv);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void GetParent(out IShellItem ppsi);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void GetDisplayName([In] SIGDN sigdnName, [MarshalAs(UnmanagedType.LPWStr)] out string ppszName);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void GetAttributes([In] uint sfgaoMask, out uint psfgaoAttribs);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime)]
            void Compare([In] IShellItem psi, [In] uint hint, out int piOrder);
        }

        private enum SIGDN : uint
        {
            SIGDN_FILESYSPATH = 0x80058000,
        }
    }
}
'@

try {
    Add-Type -TypeDefinition $folderPickerCode
}
catch { }

# --- Formatting Helpers ---

function Write-CenteredBanner {
    param(
        [string]$Text,
        [string]$Color = "Cyan",
        [string]$BorderChar = "-"
    )
    Restore-Title
    $width = [Math]::Max($Host.UI.RawUI.WindowSize.Width, 40)
    $border = $BorderChar * $width
    $pad = [Math]::Max(0, [Math]::Floor(($width - $Text.Length) / 2))
    $centered = (" " * $pad) + $Text
    Write-Host $border -ForegroundColor $Color
    Write-Host $centered -ForegroundColor $Color
    Write-Host $border -ForegroundColor $Color
}

function Write-SubSectionBanner {
    param(
        [string]$Text,
        [string]$Color = "Yellow"
    )
    Restore-Title
    $width = [Math]::Max($Host.UI.RawUI.WindowSize.Width, 40)
    $textLen = $Text.Length + 2  # space on each side
    $totalDashes = $width - $textLen
    $leftDashes = [Math]::Floor($totalDashes / 2)
    $rightDashes = $totalDashes - $leftDashes
    $line = ("-" * $leftDashes) + " $Text " + ("-" * $rightDashes)
    Write-Host ""
    Write-Host $line -ForegroundColor $Color
}

function Get-ProviderColor {
    param([string]$Provider)
    $color = switch ($Provider) {
        "CLAUDE" { "DarkYellow" }
        "GEMINI" { "Blue" }
        "CODEX" { "DarkMagenta" }
        "COPILOT" { "Gray" }
        Default { "White" }
    }
    return $color
}

function Write-Header {
    param([string]$Provider)
    $color = Get-ProviderColor -Provider $Provider
    $text = "[ ---------- $Provider ---------- ]"
    Write-Host ""
    Write-Host "  $text" -ForegroundColor $color
}

function Write-Item {
    param(
        [string]$Message,
        [string]$Color = "White",
        [int]$Indent = 1
    )
    $spaces = " " * ($Indent * 2)
    Write-Host "${spaces}$Message" -ForegroundColor $Color
}

function Read-Prompt {
    param(
        [string]$Message,
        [int]$Indent = 1
    )
    $spaces = " " * ($Indent * 2)
    Write-Host "${spaces}└─> $Message" -NoNewline -ForegroundColor "Yellow"
    return Read-Host " "
}

# --- Interaction Helpers ---

function Select-Platforms {
    param([string]$PhaseName)
    Write-Host ""
    Write-Host "Select platforms to install for $PhaseName (comma separated):" -ForegroundColor White
    Write-Host "A - ALL (Recommended)"
    Write-Host "1 - Claude Code (Anthropic)"
    Write-Host "2 - Gemini (Google)"
    Write-Host "3 - Codex (OpenAI)"
    Write-Host "4 - GitHub Copilot (Microsoft)"

    $inputStr = Read-Prompt "Selection [A, 1-4]"
    if ([string]::IsNullOrWhiteSpace($inputStr)) { return @("CLAUDE", "GEMINI", "CODEX", "COPILOT") }

    $map = @{ "1" = "CLAUDE"; "2" = "GEMINI"; "3" = "CODEX"; "4" = "COPILOT"; "A" = "ALL" }
    $selected = @()

    $inputStr.Split(',') | ForEach-Object {
        $key = $_.Trim()
        if ($map.ContainsKey($key)) {
            if ($map[$key] -eq "ALL") {
                return @("CLAUDE", "GEMINI", "CODEX", "COPILOT")
            }
            $selected += $map[$key]
        }
    }

    if ($selected.Count -eq 0) { return @("CLAUDE", "GEMINI", "CODEX", "COPILOT") }
    return $selected
}

function Get-Overwrite-Preference {
    Write-Host "How should we handle existing installations?" -ForegroundColor White
    Write-Host "[O]verwrite All     - Replace everything without asking"
    Write-Host "[S]kip All          - Keep existing files without asking"
    Write-Host "[A]sk (Recommended) - Prompt for each conflict"

    $resp = Read-Prompt "Selection [O/S/A]"

    if ($resp -match "^[Oo]") { return "ALL" }
    if ($resp -match "^[Ss]") { return "NONE" }
    return "ASK"
}

# --- File Operations ---

function Safe-Copy {
    param(
        [string]$Source,
        [string]$Destination,
        [boolean]$Confirm = $false,
        [string]$CustomMessage
    )

    if (-not (Test-Path $Source)) {
        Write-Item -Message "Skip: Source not found ($(Split-Path $Source -Leaf))" -Color "DarkGray"
        return
    }

    if (Test-Path $Destination) {
        # Check global overwrite preference
        if ($script:OverwriteMode -eq "ALL") {
            # Proceed to overwrite
        }
        elseif ($script:OverwriteMode -eq "NONE") {
            Write-Item -Message "Skip: File exists ($Destination)" -Color "DarkGray"
            return
        }
        else {
            # ASK mode
            if ($Confirm) {
                Write-Item -Message "File exists: $Destination" -Color "Yellow"
                $resp = Read-Prompt "Overwrite? [Y]es / [N]o / [A]ll"
                if ($resp -match "^[Aa]") {
                    $script:OverwriteMode = "ALL"
                }
                elseif ($resp -notmatch "^[Yy]") {
                    Write-Item -Message "Skipped by user." -Color "Gray"
                    return
                }
            }
        }
    }

    try {
        if (Test-Path $Destination) { Remove-Item $Destination -Force -ErrorAction Stop }
        Copy-Item -Path $Source -Destination $Destination -Force -ErrorAction Stop

        if (-not [string]::IsNullOrEmpty($CustomMessage)) {
            Write-Item -Message $CustomMessage -Color "DarkGreen"
        }
        else {
            Write-Item -Message "✓ Installed to $Destination" -Color "DarkGreen"
        }
    }
    catch {
        Write-Item -Message "ERROR: Could not write file. Is it open?" -Color "Red"
        Write-Item -Message $_.Exception.Message -Color "Red" -Indent 2
    }
}

function Safe-Folder-Copy {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$CustomMessage
    )
    if (-not (Test-Path $Source)) {
        Write-Item -Message "Skip: Source folder not found ($(Split-Path $Source -Leaf))" -Color "DarkGray"
        return
    }
    if (Test-Path $Destination) {
        if ($script:OverwriteMode -eq "ALL") {
            # Proceed
        }
        elseif ($script:OverwriteMode -eq "NONE") {
            Write-Item -Message "Skip: Folder exists ($Destination)" -Color "DarkGray"
            return
        }
        else {
            # ASK
            Write-Item -Message "Folder exists: $Destination" -Color "Yellow"
            $resp = Read-Prompt "Overwrite contents? [Y]es / [N]o / [A]ll"
            if ($resp -match "^[Aa]") {
                $script:OverwriteMode = "ALL"
            }
            elseif ($resp -notmatch "^[Yy]") {
                Write-Item -Message "Skipped." -Color "Gray"
                return
            }
        }
    }
    else {
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    }

    if (Test-Path $Destination) {
        Write-Item -Message "Syncing (old files not in source will be removed)..." -Color "DarkGray"
    }
    & robocopy $Source $Destination /MIR /NFL /NDL /NJH /NJS | Out-Null
    Restore-Title

    if (-not [string]::IsNullOrEmpty($CustomMessage)) {
        Write-Item -Message $CustomMessage -Color "DarkGreen"
    }
    else {
        Write-Item -Message "✓ Installed to $Destination" -Color "DarkGreen"
    }
}

# --- Hook Installation ---

function Install-GitGuardrails {
    param(
        [string]$RepoRoot,
        [string]$TargetClaudeDir,
        [string]$Scope  # "Global" or "Workspace"
    )

    # Copy hook script
    $hooksDir = Join-Path $TargetClaudeDir "hooks"
    if (-not (Test-Path $hooksDir)) { New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null }
    Safe-Copy -Source "$RepoRoot\catalog\hooks\git-guardrails.sh" -Destination (Join-Path $hooksDir "git-guardrails.sh") -Confirm:$true -CustomMessage "✓ $Scope git guardrails hook installed at: $hooksDir"

    # Merge hook config into settings.json
    $settingsFile = Join-Path $TargetClaudeDir "settings.json"
    $templateFile = "$RepoRoot\catalog\hooks\settings.json"

    if (-not (Test-Path $templateFile)) {
        Write-Item -Message "Skip: Hook template not found" -Color "DarkGray"
        return
    }

    $templateRaw = Get-Content $templateFile -Raw

    # Windows uses "python" not "python3"; global scope uses ~/.claude/ paths
    $templateRaw = $templateRaw -replace 'python3 ', 'python '
    if ($Scope -eq "Global") {
        $templateRaw = $templateRaw -replace '(?<![~/.])\.claude/hooks/', '~/.claude/hooks/'
    }

    $templateJson = $templateRaw | ConvertFrom-Json

    if (Test-Path $settingsFile) {
        try {
            $existingJson = Get-Content $settingsFile -Raw | ConvertFrom-Json

            # Check if hooks.PreToolUse already has our guardrail
            $alreadyInstalled = $false
            if ($existingJson.hooks -and $existingJson.hooks.PreToolUse) {
                foreach ($hookEntry in $existingJson.hooks.PreToolUse) {
                    foreach ($h in $hookEntry.hooks) {
                        if ($h.command -and $h.command -like "*git-guardrails*") {
                            $alreadyInstalled = $true
                            break
                        }
                    }
                }
            }

            if ($alreadyInstalled) {
                Write-Item -Message "✓ Git guardrails hook already configured in settings.json" -Color "DarkGreen"
            }
            else {
                # Add hooks key if missing
                if (-not $existingJson.hooks) {
                    $existingJson | Add-Member -NotePropertyName "hooks" -NotePropertyValue $templateJson.hooks
                }
                else {
                    if (-not $existingJson.hooks.PreToolUse) {
                        $existingJson.hooks | Add-Member -NotePropertyName "PreToolUse" -NotePropertyValue $templateJson.hooks.PreToolUse
                    }
                    else {
                        # Append our hook entry to existing PreToolUse array
                        $existingArray = @($existingJson.hooks.PreToolUse)
                        $existingArray += $templateJson.hooks.PreToolUse
                        $existingJson.hooks.PreToolUse = $existingArray
                    }
                }

                $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
                Write-Item -Message "✓ $Scope settings.json updated with git guardrails hook" -Color "DarkGreen"
            }
        }
        catch {
            Write-Item -Message "Warning: Could not merge into existing settings.json ($($_.Exception.Message))" -Color "Yellow"
            Write-Item -Message "  You may need to manually add the hook config" -Color "Yellow"
        }
    }
    else {
        # No existing settings.json, copy template
        Copy-Item -Path $templateFile -Destination $settingsFile -Force
        Write-Item -Message "✓ $Scope settings.json created with git guardrails hook" -Color "DarkGreen"
    }
}

function Install-UsageDisplay {
    param(
        [string]$RepoRoot,
        [string]$TargetClaudeDir,
        [string]$Scope  # "Global" or "Workspace"
    )

    # Copy hook script
    $hooksDir = Join-Path $TargetClaudeDir "hooks"
    if (-not (Test-Path $hooksDir)) { New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null }
    Safe-Copy -Source "$RepoRoot\catalog\hooks\usage-display.sh" -Destination (Join-Path $hooksDir "usage-display.sh") -Confirm:$true -CustomMessage "✓ $Scope usage display hook installed at: $hooksDir"

    # Merge Stop hook config into settings.json
    $settingsFile = Join-Path $TargetClaudeDir "settings.json"
    $templateFile = "$RepoRoot\catalog\hooks\settings.json"

    if (-not (Test-Path $templateFile)) {
        Write-Item -Message "Skip: Hook template not found" -Color "DarkGray"
        return
    }

    if (-not (Test-Path $settingsFile)) {
        # No existing settings.json; install_git_guardrails will create it from the
        # template (which now includes both PreToolUse and Stop hooks).
        return
    }

    $templateRaw = Get-Content $templateFile -Raw

    # Windows uses "python" not "python3"; global scope uses ~/.claude/ paths
    $templateRaw = $templateRaw -replace 'python3 ', 'python '
    if ($Scope -eq "Global") {
        $templateRaw = $templateRaw -replace '(?<![~/.])\.claude/hooks/', '~/.claude/hooks/'
    }

    $templateJson = $templateRaw | ConvertFrom-Json

    try {
        $existingJson = Get-Content $settingsFile -Raw | ConvertFrom-Json

        # Check if usage-display already installed
        $alreadyInstalled = $false
        if ($existingJson.hooks -and $existingJson.hooks.Stop) {
            foreach ($hookEntry in $existingJson.hooks.Stop) {
                foreach ($h in $hookEntry.hooks) {
                    if ($h.command -and $h.command -like "*usage-display*") {
                        $alreadyInstalled = $true
                        break
                    }
                }
            }
        }

        if ($alreadyInstalled) {
            Write-Item -Message "✓ Usage display hook already configured in settings.json" -Color "DarkGreen"
        }
        else {
            # Add hooks key if missing
            if (-not $existingJson.hooks) {
                $existingJson | Add-Member -NotePropertyName "hooks" -NotePropertyValue ([PSCustomObject]@{ Stop = $templateJson.hooks.Stop })
            }
            else {
                if (-not $existingJson.hooks.Stop) {
                    $existingJson.hooks | Add-Member -NotePropertyName "Stop" -NotePropertyValue $templateJson.hooks.Stop
                }
                else {
                    # Append our hook entry to existing Stop array
                    $existingArray = @($existingJson.hooks.Stop)
                    $existingArray += $templateJson.hooks.Stop
                    $existingJson.hooks.Stop = $existingArray
                }
            }

            $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            Write-Item -Message "✓ $Scope settings.json updated with usage display hook" -Color "DarkGreen"
        }
    }
    catch {
        Write-Item -Message "Warning: Could not merge usage display hook into settings.json ($($_.Exception.Message))" -Color "Yellow"
        Write-Item -Message "  You may need to manually add the Stop hook config" -Color "Yellow"
    }
}

function Install-RequireDescription {
    param(
        [string]$RepoRoot,
        [string]$TargetClaudeDir,
        [string]$Scope  # "Global" or "Workspace"
    )

    # Copy hook scripts
    $hooksDir = Join-Path $TargetClaudeDir "hooks"
    if (-not (Test-Path $hooksDir)) { New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null }
    Safe-Copy -Source "$RepoRoot\catalog\hooks\require-description.sh" -Destination (Join-Path $hooksDir "require-description.sh") -Confirm:$true -CustomMessage "✓ $Scope require-description hook installed at: $hooksDir"
    Safe-Copy -Source "$RepoRoot\catalog\hooks\format-bash-description.py" -Destination (Join-Path $hooksDir "format-bash-description.py") -Confirm:$true -CustomMessage "✓ $Scope format-bash-description hook installed at: $hooksDir"
    Safe-Copy -Source "$RepoRoot\catalog\hooks\require-powershell-description.sh" -Destination (Join-Path $hooksDir "require-powershell-description.sh") -Confirm:$true -CustomMessage "✓ $Scope require-powershell-description hook installed at: $hooksDir"
    Safe-Copy -Source "$RepoRoot\catalog\hooks\format-powershell-description.py" -Destination (Join-Path $hooksDir "format-powershell-description.py") -Confirm:$true -CustomMessage "✓ $Scope format-powershell-description hook installed at: $hooksDir"

    # Merge hook config into settings.json
    $settingsFile = Join-Path $TargetClaudeDir "settings.json"

    if (-not (Test-Path $settingsFile)) {
        # Install-GitGuardrails will create it from the template (which includes both Bash and PowerShell description hooks)
        return
    }

    try {
        $existingJson = Get-Content $settingsFile -Raw | ConvertFrom-Json

        # Check Bash and PowerShell hooks separately so that an existing
        # install with only the Bash hook still picks up the PowerShell pair.
        $bashInstalled = $false
        $powershellInstalled = $false
        if ($existingJson.hooks -and $existingJson.hooks.PreToolUse) {
            foreach ($hookEntry in $existingJson.hooks.PreToolUse) {
                foreach ($h in $hookEntry.hooks) {
                    if ($h.command) {
                        if ($h.command -like "*require-powershell-description*") {
                            $powershellInstalled = $true
                        }
                        elseif ($h.command -like "*require-description*") {
                            $bashInstalled = $true
                        }
                    }
                }
            }
        }

        $hookPath = if ($Scope -eq "Global") { "~/.claude/hooks" } else { ".claude/hooks" }
        $entriesToAdd = @()

        if ($bashInstalled) {
            Write-Item -Message "✓ Require-description (Bash) hook already configured in settings.json" -Color "DarkGreen"
        }
        else {
            $entriesToAdd += [PSCustomObject]@{
                matcher = "Bash"
                hooks   = @(
                    [PSCustomObject]@{
                        type    = "command"
                        command = "bash $hookPath/require-description.sh"
                    }
                )
            }
        }

        if ($powershellInstalled) {
            Write-Item -Message "✓ Description hooks (PowerShell) already configured in settings.json" -Color "DarkGreen"
        }
        else {
            $entriesToAdd += [PSCustomObject]@{
                matcher = "PowerShell"
                hooks   = @(
                    [PSCustomObject]@{
                        type    = "command"
                        command = "python3 $hookPath/format-powershell-description.py"
                    }
                )
            }
            $entriesToAdd += [PSCustomObject]@{
                matcher = "PowerShell"
                hooks   = @(
                    [PSCustomObject]@{
                        type    = "command"
                        command = "bash $hookPath/require-powershell-description.sh"
                    }
                )
            }
        }

        if ($entriesToAdd.Count -gt 0) {
            if (-not $existingJson.hooks) {
                $existingJson | Add-Member -NotePropertyName "hooks" -NotePropertyValue ([PSCustomObject]@{ PreToolUse = @($entriesToAdd) })
            }
            else {
                if (-not $existingJson.hooks.PreToolUse) {
                    $existingJson.hooks | Add-Member -NotePropertyName "PreToolUse" -NotePropertyValue @($entriesToAdd)
                }
                else {
                    $existingArray = @($existingJson.hooks.PreToolUse)
                    $existingArray += $entriesToAdd
                    $existingJson.hooks.PreToolUse = $existingArray
                }
            }

            $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
            $added = ($entriesToAdd | ForEach-Object { $_.matcher }) -join ", "
            Write-Item -Message "✓ $Scope settings.json updated with description hooks ($added)" -Color "DarkGreen"
        }
    }
    catch {
        Write-Item -Message "Warning: Could not merge description hooks into settings.json ($($_.Exception.Message))" -Color "Yellow"
        Write-Item -Message "  You may need to manually add the Bash and PowerShell PreToolUse hooks for require-description.sh, format-powershell-description.py, and require-powershell-description.sh" -Color "Yellow"
    }
}

function Install-CoreSettings {
    param(
        [string]$RepoRoot,
        [string]$TargetClaudeDir,
        [string]$Scope  # "Global" or "Workspace"
    )

    $settingsFile = Join-Path $TargetClaudeDir "settings.json"
    $templateFile = "$RepoRoot\catalog\hooks\settings.json"

    if (-not (Test-Path $settingsFile)) {
        Write-Item -Message "Skip: settings.json not found, will be created by hook installer" -Color "DarkGray"
        return
    }

    # Idempotency: skip if effortLevel already matches the template value
    $content = Get-Content $settingsFile -Raw
    try {
        $existingJson = $content | ConvertFrom-Json
        $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json
        $templateEffort = $templateJson.effortLevel

        if ($existingJson.PSObject.Properties["effortLevel"] -and $existingJson.effortLevel -eq $templateEffort) {
            Write-Item -Message "✓ effortLevel already set to $templateEffort in settings.json" -Color "DarkGreen"
            return
        }

        if ($existingJson.PSObject.Properties["effortLevel"]) {
            $existingJson.effortLevel = $templateEffort
        } else {
            $existingJson | Add-Member -NotePropertyName "effortLevel" -NotePropertyValue $templateEffort
        }
        $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
        Write-Item -Message "✓ $Scope settings.json updated with effortLevel: $templateEffort" -Color "DarkGreen"
    }
    catch {
        Write-Item -Message "Warning: Could not set effortLevel ($($_.Exception.Message))" -Color "Yellow"
        Write-Item -Message "  Manually add: `"effortLevel`": `"xhigh`" to $settingsFile" -Color "Yellow"
    }
}

# --- Git Commit-Msg Hook ---

function Install-GitCommitMsgHook {
    param([string]$RepoRoot)

    $hookSrc = Join-Path $RepoRoot "catalog\hooks\commit-msg"
    $templateHooksDir = Join-Path $env:USERPROFILE ".git-templates\hooks"

    if (-not (Test-Path $hookSrc)) {
        Write-Item -Message "Skip: catalog/hooks/commit-msg not found" -Color "DarkGray"
        return
    }

    if (-not (Test-Path $templateHooksDir)) {
        New-Item -ItemType Directory -Force -Path $templateHooksDir | Out-Null
    }

    Copy-Item -Path $hookSrc -Destination (Join-Path $templateHooksDir "commit-msg") -Force
    Write-Item -Message "[OK] Git commit-msg hook installed at: $templateHooksDir\commit-msg" -Color "Green"

    # Register the template directory so all future repos inherit the hook
    git config --global init.templateDir "~/.git-templates" 2>$null
    Write-Item -Message "[OK] git config --global init.templateDir set to ~/.git-templates" -Color "Green"
    Write-Item -Message "  Note: run 'git init' in existing repos to apply the hook there too" -Color "DarkGray"
}

# --- Permission Installation ---

function Install-Permissions {
    param(
        [string]$RepoRoot,
        [string]$Platform,          # "CLAUDE", "GEMINI", "CODEX", "COPILOT"
        [string]$Scope              # "Global" or "Workspace"
    )

    $permDir = Join-Path $RepoRoot "configs\permissions"

    switch ($Platform) {
        "CLAUDE" {
            $configDir = Join-Path $env:USERPROFILE ".claude"
            $settingsFile = Join-Path $configDir "settings.json"
            $templateFile = Join-Path $permDir "claude-permissions.json"

            if (-not (Test-Path $templateFile)) {
                Write-Item -Message "Skip: Claude permissions template not found" -Color "DarkGray"
                return
            }

            $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json
            $newEntries = @($templateJson.permissions.allow)

            if (Test-Path $settingsFile) {
                # Counting new entries BEFORE merging avoids the stale-sentinel
                # bug where a single fixed marker (e.g. WebFetch api.github.com)
                # made the installer think permissions were "already installed"
                # and skip merging new entries shipped in later versions.
                try {
                    $existingJson = Get-Content $settingsFile -Raw | ConvertFrom-Json

                    # Ensure permissions.allow exists
                    if (-not $existingJson.permissions) {
                        $existingJson | Add-Member -NotePropertyName "permissions" -NotePropertyValue ([PSCustomObject]@{ allow = @() })
                    }
                    elseif (-not $existingJson.permissions.allow) {
                        $existingJson.permissions | Add-Member -NotePropertyName "allow" -NotePropertyValue @()
                    }

                    # Union merge (deduplicate). Only write the file (and create
                    # a backup) if the merge actually adds something new.
                    $existing = @($existingJson.permissions.allow)
                    $merged = @($existing + $newEntries | Select-Object -Unique)
                    $addedCount = $merged.Count - $existing.Count

                    if ($addedCount -eq 0) {
                        Write-Item -Message "✓ Auto-approve permissions up to date in settings.json (0 new entries)" -Color "DarkGreen"
                        return
                    }

                    # Backup before modifying
                    $backupPath = "$settingsFile.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
                    Copy-Item -Path $settingsFile -Destination $backupPath -Force
                    Write-Item -Message "  Backup created: $backupPath" -Color "DarkGray"

                    $existingJson.permissions.allow = $merged
                    $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
                    Write-Item -Message "✓ $Scope auto-approve permissions added to settings.json ($addedCount new entries)" -Color "DarkGreen"
                }
                catch {
                    Write-Item -Message "Warning: Could not merge permissions into settings.json ($($_.Exception.Message))" -Color "Yellow"
                    return
                }
            }
            else {
                # No existing settings.json; create with permissions only
                $newJson = [PSCustomObject]@{ permissions = [PSCustomObject]@{ allow = $newEntries } }
                if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Force -Path $configDir | Out-Null }
                $newJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
                Write-Item -Message "✓ $Scope settings.json created with auto-approve permissions" -Color "DarkGreen"
            }

            Write-Item -Message "  Auto-approved: file reads, search (Glob/Grep), web search, git read-only commands" -Color "Gray"
            Write-Item -Message "  WebFetch: scoped to trusted domains (see $settingsFile to customize)" -Color "Gray"
            Write-Item -Message "  NOT auto-approved: file writes, destructive commands, git mutations, package installs" -Color "Gray"
            Write-Item -Message "  Config: $settingsFile" -Color "Gray"
        }

        "GEMINI" {
            $configDir = Join-Path $env:USERPROFILE ".gemini"
            $settingsFile = Join-Path $configDir "settings.json"
            $templateFile = Join-Path $permDir "gemini-permissions.json"

            if (-not (Test-Path $templateFile)) {
                Write-Item -Message "Skip: Gemini permissions template not found" -Color "DarkGray"
                return
            }

            $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json
            $newTools = @($templateJson.tools.allowed)
            $newDomains = @($templateJson.allowedDomains)

            if (Test-Path $settingsFile) {
                $content = Get-Content $settingsFile -Raw
                if ($content -match '"ReadFileTool"' -and $content -match '"allowedDomains"') {
                    Write-Item -Message "✓ Auto-approve permissions already configured in settings.json" -Color "DarkGreen"
                    return
                }

                try {
                    $existingJson = $content | ConvertFrom-Json

                    $backupPath = "$settingsFile.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
                    Copy-Item -Path $settingsFile -Destination $backupPath -Force
                    Write-Item -Message "  Backup created: $backupPath" -Color "DarkGray"

                    # Merge tools.allowed
                    if (-not $existingJson.tools) {
                        $existingJson | Add-Member -NotePropertyName "tools" -NotePropertyValue ([PSCustomObject]@{ allowed = @() })
                    }
                    elseif (-not $existingJson.tools.allowed) {
                        $existingJson.tools | Add-Member -NotePropertyName "allowed" -NotePropertyValue @()
                    }
                    $existingTools = @($existingJson.tools.allowed)
                    $existingJson.tools.allowed = @($existingTools + $newTools | Select-Object -Unique)

                    # Merge allowedDomains
                    if (-not $existingJson.allowedDomains) {
                        $existingJson | Add-Member -NotePropertyName "allowedDomains" -NotePropertyValue @()
                    }
                    $existingDomains = @($existingJson.allowedDomains)
                    $existingJson.allowedDomains = @($existingDomains + $newDomains | Select-Object -Unique)

                    $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
                    Write-Item -Message "✓ $Scope auto-approve permissions added to settings.json" -Color "DarkGreen"
                }
                catch {
                    Write-Item -Message "Warning: Could not merge permissions into Gemini settings.json ($($_.Exception.Message))" -Color "Yellow"
                    return
                }
            }
            else {
                if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Force -Path $configDir | Out-Null }
                $newJson = [PSCustomObject]@{
                    tools = [PSCustomObject]@{ allowed = $newTools }
                    allowedDomains = $newDomains
                }
                $newJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
                Write-Item -Message "✓ $Scope settings.json created with auto-approve permissions" -Color "DarkGreen"
            }

            Write-Item -Message "  Auto-approved: file reads, search, web search, git read-only shell commands" -Color "Gray"
            Write-Item -Message "  Domains: scoped to trusted list (see $settingsFile to customize)" -Color "Gray"
            Write-Item -Message "  Limitation: piped commands bypass allowlists (upstream issue)" -Color "Gray"
            Write-Item -Message "  Config: $settingsFile" -Color "Gray"
        }

        "CODEX" {
            $configDir = Join-Path $env:USERPROFILE ".codex"
            $configFile = Join-Path $configDir "config.toml"
            $templateFile = Join-Path $permDir "codex-permissions.toml"

            if (-not (Test-Path $templateFile)) {
                Write-Item -Message "Skip: Codex permissions template not found" -Color "DarkGray"
                return
            }

            if (Test-Path $configFile) {
                $content = Get-Content $configFile -Raw
                if ($content -match 'permissions\.default\.network' -and $content -match 'allowed_domains') {
                    Write-Item -Message "✓ Auto-approve permissions already configured in config.toml" -Color "DarkGreen"
                    return
                }

                # Backup before modifying
                $backupPath = "$configFile.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
                Copy-Item -Path $configFile -Destination $backupPath -Force
                Write-Item -Message "  Backup created: $backupPath" -Color "DarkGray"
            }

            # For TOML, use Python to merge if existing file, or copy template if new
            if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Force -Path $configDir | Out-Null }

            if (-not (Test-Path $configFile)) {
                Copy-Item -Path $templateFile -Destination $configFile -Force
                Write-Item -Message "✓ $Scope config.toml created with auto-approve permissions" -Color "DarkGreen"
            }
            else {
                # Append permission sections if not present
                $templateContent = Get-Content $templateFile -Raw
                $existingContent = Get-Content $configFile -Raw

                # Extract and append missing sections
                $sectionsToAdd = @()
                if ($existingContent -notmatch '\[permissions\.default\.filesystem\]') {
                    $sectionsToAdd += ($templateContent | Select-String -Pattern '(?s)\[permissions\.default\.filesystem\].*?(?=\[|$)' -AllMatches).Matches.Value
                }
                if ($existingContent -notmatch '\[permissions\.default\.network\]') {
                    $sectionsToAdd += ($templateContent | Select-String -Pattern '(?s)\[permissions\.default\.network\].*' -AllMatches).Matches.Value
                }
                if ($existingContent -notmatch 'approval_policy') {
                    $sectionsToAdd = @("approval_policy = `"on-request`"") + $sectionsToAdd
                }

                if ($sectionsToAdd.Count -gt 0) {
                    $appendContent = "`n`n# --- DevAI-Hub auto-approve permissions ---`n" + ($sectionsToAdd -join "`n`n")
                    Add-Content -Path $configFile -Value $appendContent -Encoding UTF8
                    Write-Item -Message "✓ $Scope config.toml updated with auto-approve permissions" -Color "DarkGreen"
                }
                else {
                    Write-Item -Message "✓ Auto-approve permissions already present in config.toml" -Color "DarkGreen"
                }
            }

            Write-Item -Message "  Auto-approved: filesystem read access to project roots, network access to trusted domains" -Color "Gray"
            Write-Item -Message "  NOT auto-approved: file writes, arbitrary network access" -Color "Gray"
            Write-Item -Message "  Note: Codex does not support per-command Bash allowlisting" -Color "Gray"
            Write-Item -Message "  Config: $configFile" -Color "Gray"
        }

        "COPILOT" {
            $templateFile = Join-Path $permDir "copilot-permissions.json"

            if (-not (Test-Path $templateFile)) {
                Write-Item -Message "Skip: Copilot permissions template not found" -Color "DarkGray"
                return
            }

            # Locate VS Code settings.json
            $vscodeSettingsFile = Join-Path $env:APPDATA "Code\User\settings.json"
            if (-not (Test-Path $vscodeSettingsFile)) {
                Write-Item -Message "Skip: VS Code settings.json not found at $vscodeSettingsFile" -Color "DarkGray"
                Write-Item -Message "  Copilot permissions require VS Code. Install VS Code and retry." -Color "Gray"
                return
            }

            try {
                $content = Get-Content $vscodeSettingsFile -Raw
                if ($content -match 'useInstructionFiles.*true') {
                    Write-Item -Message "✓ Copilot useInstructionFiles already enabled in VS Code settings" -Color "DarkGreen"
                    return
                }

                $existingJson = $content | ConvertFrom-Json

                $backupPath = "$vscodeSettingsFile.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
                Copy-Item -Path $vscodeSettingsFile -Destination $backupPath -Force
                Write-Item -Message "  Backup created: $backupPath" -Color "DarkGray"

                $key = "github.copilot.chat.codeGeneration.useInstructionFiles"
                if (-not ($existingJson.PSObject.Properties.Name -contains $key)) {
                    $existingJson | Add-Member -NotePropertyName $key -NotePropertyValue $true
                }
                else {
                    $existingJson.$key = $true
                }

                $existingJson | ConvertTo-Json -Depth 10 | Set-Content $vscodeSettingsFile -Encoding UTF8
                Write-Item -Message "✓ $Scope VS Code settings updated with Copilot instruction file support" -Color "DarkGreen"
            }
            catch {
                Write-Item -Message "Warning: Could not merge Copilot settings into VS Code settings.json ($($_.Exception.Message))" -Color "Yellow"
                return
            }

            Write-Item -Message "  Limitation: Copilot lacks per-command/per-domain auto-approve" -Color "Gray"
            Write-Item -Message "  Only useInstructionFiles is enabled (behavioral guardrails via .github/copilot-instructions.md)" -Color "Gray"
            Write-Item -Message "  Blanket auto-approve is NOT set (cannot distinguish reads from writes)" -Color "Gray"
            Write-Item -Message "  Config: $vscodeSettingsFile" -Color "Gray"
        }
    }
}

# --- Install Functions ---

function Install-Global {
    param ($RepoRoot)
    Restore-Title
    Write-Host ""
    Write-CenteredBanner -Text "Global Installation" -Color "Cyan"
    # Write-SubSectionBanner below prepends its own blank line; no explicit Write-Host "" needed.

    # Global Overwrite Preference
    Write-SubSectionBanner -Text "Overwrite Request"
    Write-Host ""
    $script:OverwriteMode = Get-Overwrite-Preference
    # Write-SubSectionBanner below prepends its own blank line; no explicit Write-Host "" needed.

    Write-SubSectionBanner -Text "Skills & Commands"

    $platforms = Select-Platforms -PhaseName "Global Phase"
    Write-Host ""
    Write-Host "Checking User Profile ($env:USERPROFILE)..." -ForegroundColor Gray

    # 1. Claude
    if ($platforms -contains "CLAUDE") {
        Write-Header -Provider "CLAUDE"
        Write-Item -Message "Installing Global Configuration..."
        $globalClaude = Join-Path $env:USERPROFILE ".claude"
        if (-not (Test-Path $globalClaude)) { New-Item -ItemType Directory -Force -Path $globalClaude | Out-Null }

        # Global CLAUDE.md (new concise template with WHAT/WHY/HOW structure)
        $script:ProjectName = "Global"
        $script:OSContext = "I am a Windows user. Ensure shell commands are PowerShell-compatible."
        $script:PrimaryLanguage = ""
        $script:PackageManager = ""
        $script:BuildTool = ""
        $script:TestFramework = ""
        $script:LintTool = ""
        $script:BuildCmd = "# specify build command"
        $script:TestCmd = "# specify test command"
        $script:LintCmd = "# specify lint command"
        $script:NonObviousTooling = "- (configure per project with /setup-project)"
        Render-Template -Template "$RepoRoot\templates\ai-instructions\base-claude.md" -Output "$globalClaude\CLAUDE.md" -RepoRoot $RepoRoot -Languages @()

        # Global Skills
        Safe-Folder-Copy -Source "$RepoRoot\catalog\skills" -Destination (Join-Path $globalClaude "skills") -CustomMessage "✓ Global skills catalog installed at: $(Join-Path $globalClaude "skills")"

        # Global Commands
        Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $globalClaude "commands") -CustomMessage "✓ Global commands installed at: $(Join-Path $globalClaude "commands")"

        # Global Agents
        Safe-Folder-Copy -Source "$RepoRoot\catalog\agents" -Destination (Join-Path $globalClaude "agents") -CustomMessage "✓ Global agents installed at: $(Join-Path $globalClaude "agents")"

        # Global Rules
        Safe-Folder-Copy -Source "$RepoRoot\catalog\rules" -Destination (Join-Path $globalClaude "rules") -CustomMessage "✓ Global rules installed at: $(Join-Path $globalClaude "rules")"

        # Global MCP Server Config
        $mcpConfigDest = Join-Path $globalClaude "mcp-configs"
        if (-not (Test-Path $mcpConfigDest)) { New-Item -ItemType Directory -Force -Path $mcpConfigDest | Out-Null }
        Safe-Copy -Source "$RepoRoot\catalog\mcp-configs\mcp-servers.json" -Destination (Join-Path $mcpConfigDest "mcp-servers.json") -Confirm:$false -CustomMessage "✓ MCP server config installed at: $mcpConfigDest"

        # Git Guardrails Hook
        Install-GitGuardrails -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"

        # Usage Display Hook
        Install-UsageDisplay -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"

        # Require Description Hook
        Install-RequireDescription -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"

        # Core Settings (effortLevel)
        Install-CoreSettings -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"
    }

    # 2. Gemini / Antigravity
    if ($platforms -contains "GEMINI") {
        Write-Header -Provider "GEMINI"
        Write-Item -Message "Installing Global Configuration..."
        $globalGeminiDir = Join-Path $env:USERPROFILE ".gemini"
        $globalAgentDir = Join-Path $env:USERPROFILE ".agent"

        if (-not (Test-Path $globalGeminiDir)) { New-Item -ItemType Directory -Force -Path $globalGeminiDir | Out-Null }
        if (-not (Test-Path $globalAgentDir)) { New-Item -ItemType Directory -Force -Path $globalAgentDir | Out-Null }

        # Global GEMINI.md (concise template without Claude-specific concepts)
        Render-Template -Template "$RepoRoot\templates\ai-instructions\base-gemini.md" -Output "$globalGeminiDir\GEMINI.md" -RepoRoot $RepoRoot -Languages @()

        # Mirror Skills to Agent (Antigravity)
        Safe-Folder-Copy -Source "$RepoRoot\catalog\skills" -Destination (Join-Path $globalAgentDir "skills") -CustomMessage "✓ Global skills catalog installed at: $(Join-Path $globalAgentDir "skills")"

        # Mirror Commands to Agent Workflows
        Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $globalAgentDir "workflows") -CustomMessage "✓ Global workflows installed at: $(Join-Path $globalAgentDir "workflows")"

        # Mirror to .gemini (For Antigravity Global Context)
        Safe-Folder-Copy -Source "$RepoRoot\catalog\skills" -Destination (Join-Path $globalGeminiDir "skills") -CustomMessage "✓ Global skills catalog installed at: $(Join-Path $globalGeminiDir "skills")"

        # Correct path for Antigravity Global Workflows
        $globalAntigravityWorkflows = Join-Path $globalGeminiDir "antigravity\global_workflows"
        if (-not (Test-Path $globalAntigravityWorkflows)) { New-Item -ItemType Directory -Force -Path $globalAntigravityWorkflows | Out-Null }
        Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination $globalAntigravityWorkflows -CustomMessage "✓ Global workflows installed at: $globalAntigravityWorkflows"
    }

    # 3. OpenAI Codex
    if ($platforms -contains "CODEX") {
        Write-Header -Provider "CODEX"
        Write-Item -Message "Installing Global Configuration..."
        $globalCodexDir = Join-Path $env:USERPROFILE ".codex"

        if (-not (Test-Path $globalCodexDir)) { New-Item -ItemType Directory -Force -Path $globalCodexDir | Out-Null }

        # Global Skills
        Safe-Folder-Copy -Source "$RepoRoot\catalog\skills" -Destination (Join-Path $globalCodexDir "skills") -CustomMessage "✓ Global skills catalog installed at: $(Join-Path $globalCodexDir "skills")"

        # Global Custom Prompts (Codex equivalent of commands)
        Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $globalCodexDir "prompts") -CustomMessage "✓ Global custom prompts installed at: $(Join-Path $globalCodexDir "prompts")"

        # Global AGENTS.md (open standard instruction file for Codex, Jules, Cursor, Aider)
        Render-Template -Template "$RepoRoot\templates\ai-instructions\base-codex.md" -Output "$globalCodexDir\AGENTS.md" -RepoRoot $RepoRoot -Languages @()
    }

    # 4. Microsoft - Github Copilot
    if ($platforms -contains "COPILOT") {
        Write-Header -Provider "COPILOT"
        Write-Item -Message "Check skipped (No global file support on Windows)." -Color "DarkGray"
    }

    # --- Auto-Approve Permissions sub-section ---
    Write-SubSectionBanner -Text "Auto-Approve Permissions"

    if ($platforms -contains "CLAUDE") {
        Write-Header -Provider "CLAUDE"
        Install-Permissions -RepoRoot $RepoRoot -Platform "CLAUDE" -Scope "Global"
    }
    if ($platforms -contains "GEMINI") {
        Write-Header -Provider "GEMINI"
        Install-Permissions -RepoRoot $RepoRoot -Platform "GEMINI" -Scope "Global"
    }
    if ($platforms -contains "CODEX") {
        Write-Header -Provider "CODEX"
        Install-Permissions -RepoRoot $RepoRoot -Platform "CODEX" -Scope "Global"
    }
    if ($platforms -contains "COPILOT") {
        Write-Header -Provider "COPILOT"
        Install-Permissions -RepoRoot $RepoRoot -Platform "COPILOT" -Scope "Global"
    }

    # --- Claude Code Utilities sub-section ---
    Write-SubSectionBanner -Text "Claude Code Utilities"
    Install-VSCodeExtensions -RepoRoot $RepoRoot

    # --- Skill Discovery sub-section ---
    Write-SubSectionBanner -Text "Skill Discovery (All Platforms)"
    Install-SkillDiscovery -RepoRoot $RepoRoot

    # --- Git Commit-Msg Hook sub-section ---
    Write-SubSectionBanner -Text "Git Commit-Msg Hook (All Platforms)"
    Write-Host ""
    Install-GitCommitMsgHook -RepoRoot $RepoRoot
    # Install-Templates below calls Write-SubSectionBanner which prepends its own blank;
    # no trailing Write-Host "" needed here.
}

function Get-LanguageSelection {
    param([array]$Detected)
    $map = @{ "1" = "Python"; "2" = "JavaScript"; "3" = "TypeScript"; "4" = "Java"; "5" = "C#"; "6" = "Go"; "7" = "C++" }

    if ($Detected.Count -gt 0) {
        Write-Host "Detected languages: $($Detected -join ', ')" -ForegroundColor Yellow
        $resp = Read-Host "└─> Use these? [Y]es / [N]o"
        if ($resp -match "^[Yy]") { return $Detected }
    }

    Write-Host "Select languages (comma separated):" -ForegroundColor White
    Write-Host "1. Python  2. JS  3. TS  4. Java  5. C#  6. Go  7. C++"
    $inputStr = Read-Host "> "
    $selected = @()
    $inputStr.Split(',') | ForEach-Object {
        $key = $_.Trim()
        if ($map.ContainsKey($key)) { $selected += $map[$key] }
    }
    if ($selected.Count -eq 0) { return @("Python") }
    return $selected
}

function Detect-Languages {
    param([string]$Path)
    $counts = @{
        "Python"     = (Get-ChildItem $Path -Include *.py -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "JavaScript" = (Get-ChildItem $Path -Include *.js, *.jsx -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "TypeScript" = (Get-ChildItem $Path -Include *.ts, *.tsx -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "Java"       = (Get-ChildItem $Path -Include *.java -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "C#"         = (Get-ChildItem $Path -Include *.cs -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "Go"         = (Get-ChildItem $Path -Include *.go -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "C++"        = (Get-ChildItem $Path -Include *.cpp, *.h, *.hpp -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
    }
    return ($counts.GetEnumerator() | Where-Object { $_.Value -gt 0 } | Sort-Object Value -Descending).Name
}

function Detect-ProjectMetadata {
    param(
        [string]$TargetPath,
        [string[]]$Languages
    )

    $script:ProjectName = Split-Path $TargetPath -Leaf
    $script:OSContext = "I am a Windows user. Ensure shell commands are PowerShell-compatible."
    $script:PrimaryLanguage = if ($Languages.Count -gt 0) { $Languages[0] } else { "" }
    $script:PackageManager = ""
    $script:BuildTool = ""
    $script:TestFramework = ""
    $script:LintTool = ""
    $script:BuildCmd = "# specify build command"
    $script:TestCmd = "# specify test command"
    $script:LintCmd = "# specify lint command"
    $script:NonObviousTooling = "- (add project-specific tooling notes here)"

    if (Test-Path (Join-Path $TargetPath "pyproject.toml")) {
        $script:PackageManager = "uv (or pip with venv)"
        $script:BuildTool = "uv"
        $script:TestFramework = "pytest"
        $script:LintTool = "ruff"
        $script:BuildCmd = "uv run python src/main.py"
        $script:TestCmd = "uv run pytest tests/"
        $script:LintCmd = "uv run ruff check . && uv run ruff format ."
        $script:NonObviousTooling = "- Use ``uv`` not ``pip`` for Python package management (10-100x faster)"
    }
    elseif (Test-Path (Join-Path $TargetPath "requirements.txt")) {
        $script:PackageManager = "pip with venv"
        $script:BuildTool = "pip"
        $script:TestFramework = "pytest"
        $script:LintTool = "ruff"
        $script:BuildCmd = "python src/main.py"
        $script:TestCmd = "pytest tests/"
        $script:LintCmd = "ruff check . && ruff format ."
    }

    if (Test-Path (Join-Path $TargetPath "package.json")) {
        $script:PackageManager = "npm"
        if (Test-Path (Join-Path $TargetPath "yarn.lock")) { $script:PackageManager = "yarn" }
        if (Test-Path (Join-Path $TargetPath "pnpm-lock.yaml")) { $script:PackageManager = "pnpm" }
        if (Test-Path (Join-Path $TargetPath "bun.lockb")) {
            $script:PackageManager = "bun"
            $script:NonObviousTooling = "- Use ``bun`` not ``npm`` for package management and script execution"
        }
        $script:BuildTool = $script:PackageManager
        $script:TestFramework = "jest"
        $script:LintTool = "eslint + prettier"
        $script:BuildCmd = "$($script:PackageManager) run build"
        $script:TestCmd = "$($script:PackageManager) test"
        $script:LintCmd = "$($script:PackageManager) run lint"
    }

    if (Test-Path (Join-Path $TargetPath "go.mod")) {
        $script:PackageManager = "go mod"
        $script:BuildTool = "go"
        $script:TestFramework = "go test"
        $script:LintTool = "golangci-lint"
        $script:BuildCmd = "go build ./..."
        $script:TestCmd = "go test ./..."
        $script:LintCmd = "golangci-lint run"
    }

    if (Test-Path (Join-Path $TargetPath "pom.xml")) {
        $script:PackageManager = "Maven"
        $script:BuildTool = "mvn"
        $script:TestFramework = "JUnit 5"
        $script:LintTool = "Checkstyle"
        $script:BuildCmd = "mvn compile"
        $script:TestCmd = "mvn test"
        $script:LintCmd = "mvn checkstyle:check"
    }
    elseif ((Test-Path (Join-Path $TargetPath "build.gradle")) -or (Test-Path (Join-Path $TargetPath "build.gradle.kts"))) {
        $script:PackageManager = "Gradle"
        $script:BuildTool = "gradle"
        $script:TestFramework = "JUnit 5"
        $script:LintTool = "Checkstyle"
        $script:BuildCmd = "./gradlew build"
        $script:TestCmd = "./gradlew test"
        $script:LintCmd = "./gradlew checkstyleMain"
    }

    if ((Get-ChildItem $TargetPath -Filter *.csproj -ErrorAction SilentlyContinue) -or (Get-ChildItem $TargetPath -Filter *.sln -ErrorAction SilentlyContinue)) {
        $script:PackageManager = "NuGet (dotnet)"
        $script:BuildTool = "dotnet"
        $script:TestFramework = "xUnit"
        $script:LintTool = "dotnet format"
        $script:BuildCmd = "dotnet build"
        $script:TestCmd = "dotnet test"
        $script:LintCmd = "dotnet format"
    }

    if (Test-Path (Join-Path $TargetPath "CMakeLists.txt")) {
        $script:PackageManager = "CMake"
        $script:BuildTool = "cmake"
        $script:TestFramework = "GoogleTest"
        $script:LintTool = "clang-format"
        $script:BuildCmd = "cmake --build build"
        $script:TestCmd = "ctest --test-dir build"
        $script:LintCmd = "clang-format -i src/*.cpp include/*.h"
    }

    # Set defaults for unfilled values
    if ([string]::IsNullOrEmpty($script:PackageManager)) { $script:PackageManager = "(detect or specify)" }
    if ([string]::IsNullOrEmpty($script:BuildTool)) { $script:BuildTool = "(detect or specify)" }
    if ([string]::IsNullOrEmpty($script:TestFramework)) { $script:TestFramework = "(detect or specify)" }
    if ([string]::IsNullOrEmpty($script:LintTool)) { $script:LintTool = "(detect or specify)" }
}

function Render-Template {
    param(
        [string]$Template,
        [string]$Output,
        [string]$RepoRoot,
        [string[]]$Languages
    )

    if (-not (Test-Path $Template)) {
        Write-Item -Message "Skip: Template not found ($(Split-Path $Template -Leaf))" -Color "DarkGray"
        return
    }

    # Check for existing file (reuse overwrite logic)
    $doWrite = $true
    if (Test-Path $Output) {
        if ($script:OverwriteMode -eq "ALL") {
            # Proceed
        }
        elseif ($script:OverwriteMode -eq "NONE") {
            Write-Item -Message "File exists: $Output (Skipped)" -Color "DarkGray"
            $doWrite = $false
        }
        else {
            Write-Item -Message "File exists: $Output" -Color "Yellow"
            $resp = Read-Prompt "Overwrite? [Y]es / [N]o / [A]ll"
            if ($resp -match "^[Aa]") { $script:OverwriteMode = "ALL" }
            elseif ($resp -notmatch "^[Yy]") { $doWrite = $false }
        }
    }

    if ($doWrite) {
        $parentDir = Split-Path $Output -Parent
        if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Force -Path $parentDir | Out-Null }

        # Read template and replace placeholders
        $content = Get-Content $Template -Raw
        $content = $content.Replace("{{PROJECT_NAME}}", $script:ProjectName)
        $content = $content.Replace("{{PROJECT_DESCRIPTION}}", "(Add a 2-3 sentence project description here, or run /setup-project)")
        $content = $content.Replace("{{PRIMARY_LANGUAGE}}", $script:PrimaryLanguage)
        $content = $content.Replace("{{LANGUAGE_VERSION}}", "")
        $content = $content.Replace("{{PACKAGE_MANAGER}}", $script:PackageManager)
        $content = $content.Replace("{{BUILD_TOOL}}", $script:BuildTool)
        $content = $content.Replace("{{TEST_FRAMEWORK}}", $script:TestFramework)
        $content = $content.Replace("{{LINT_TOOL}}", $script:LintTool)
        $content = $content.Replace("{{PROJECT_STRUCTURE_BRIEF}}", "(Run /setup-project to generate project layout)")
        $content = $content.Replace("{{BUILD_CMD}}", $script:BuildCmd)
        $content = $content.Replace("{{TEST_CMD}}", $script:TestCmd)
        $content = $content.Replace("{{LINT_CMD}}", $script:LintCmd)
        $content = $content.Replace("{{NON_OBVIOUS_TOOLING}}", $script:NonObviousTooling)
        $content = $content.Replace("{{LANGUAGE_CONVENTIONS}}", "(See coding-snippets or run /setup-project)")
        $content = $content.Replace("{{OS_CONTEXT}}", $script:OSContext)

        # Replace {{SKILL_INDEX}} with actual skill index content (if available)
        $skillIndexPath = Join-Path $RepoRoot "data\SKILL_INDEX.md"
        if (Test-Path $skillIndexPath) {
            $skillIndexContent = Get-Content $skillIndexPath -Raw
            $content = $content.Replace("{{SKILL_INDEX}}", $skillIndexContent)
        }
        else {
            $content = $content.Replace("{{SKILL_INDEX}}", "<!-- Skill index not available. Run the DevAI-Hub installer to generate it. -->")
        }

        # Append language-specific snippets
        if ($Languages -and $Languages.Count -gt 0) {
            foreach ($lang in $Languages) {
                $langKey = $lang.ToLower()
                if ($langKey -eq "c++") { $langKey = "cpp" }
                if ($langKey -eq "c#") { $langKey = "csharp" }
                $snippet = Join-Path $RepoRoot "templates\ai-instructions\coding-snippets\${langKey}.md"
                if (Test-Path $snippet) {
                    $content += "`n`n" + (Get-Content $snippet -Raw)
                }
            }
        }

        $content | Set-Content $Output -Encoding UTF8
        Write-Item -Message "✓ Installed to $Output" -Color "DarkGreen"
    }
}

function Install-Workspace {
    param (
        $RepoRoot,
        $TargetPath  # pre-validated by main (v0.9.7+)
    )
    Write-Host ""
    Write-CenteredBanner -Text "Workspace Installation" -Color "Cyan"
    # Write-SubSectionBanner below prepends its own blank; no explicit Write-Host "" needed here.

    if ([string]::IsNullOrWhiteSpace($TargetPath) -or -not (Test-Path $TargetPath)) {
        Write-Host "Invalid target path: $TargetPath" -ForegroundColor Red
        return
    }

    # Single-pass workspace install. To install into multiple workspaces, re-run the installer.
    $targetPath = $TargetPath
    Write-Host ""
    Write-Host "Target: $targetPath" -ForegroundColor DarkYellow

    # Workspace Overwrite Preference (mirrors Install-Global UX)
    Write-SubSectionBanner -Text "Overwrite Request"
    Write-Host ""
    $script:OverwriteMode = Get-Overwrite-Preference
    # Next line is Select-Platforms (plain content); one blank line via Write-Host "" for separation.
    Write-Host ""

        $workspacePlatforms = Select-Platforms -PhaseName "Workspace Phase"

        $detected = Detect-Languages -Path $targetPath
        $languages = Get-LanguageSelection -Detected $detected
        Write-Host "Selected Languages: $($languages -join ', ')" -ForegroundColor Yellow

        # Auto-detect project metadata for template rendering
        Detect-ProjectMetadata -TargetPath $targetPath -Languages $languages

        # --- Install Logic ---

        # 1. Claude
        if ($workspacePlatforms -contains "CLAUDE") {
            Write-Header -Provider "CLAUDE"
            Write-Item -Message "Installing Workspace Configuration..."
            $claudeDir = Join-Path $targetPath ".claude"

            # CLAUDE.md (rendered from template with detected project metadata)
            Render-Template -Template "$RepoRoot\templates\ai-instructions\base-claude.md" -Output "$targetPath\CLAUDE.md" -RepoRoot $RepoRoot -Languages $languages

            # Skills
            Safe-Folder-Copy -Source "$RepoRoot\catalog\skills" -Destination (Join-Path $claudeDir "skills") -CustomMessage "✓ Workspace skills catalog installed at: $(Join-Path $claudeDir "skills")"

            # Commands
            Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $claudeDir "commands") -CustomMessage "✓ Workspace commands installed at: $(Join-Path $claudeDir "commands")"

            # Agents
            Safe-Folder-Copy -Source "$RepoRoot\catalog\agents" -Destination (Join-Path $claudeDir "agents") -CustomMessage "✓ Workspace agents installed at: $(Join-Path $claudeDir "agents")"

            # Rules
            Safe-Folder-Copy -Source "$RepoRoot\catalog\rules" -Destination (Join-Path $claudeDir "rules") -CustomMessage "✓ Workspace rules installed at: $(Join-Path $claudeDir "rules")"

            # MCP Server Config
            $mcpConfigDestWs = Join-Path $claudeDir "mcp-configs"
            if (-not (Test-Path $mcpConfigDestWs)) { New-Item -ItemType Directory -Force -Path $mcpConfigDestWs | Out-Null }
            Safe-Copy -Source "$RepoRoot\catalog\mcp-configs\mcp-servers.json" -Destination (Join-Path $mcpConfigDestWs "mcp-servers.json") -Confirm:$false -CustomMessage "✓ MCP server config installed at: $mcpConfigDestWs"

            # Context & Memory
            Safe-Folder-Copy -Source "$RepoRoot\catalog\context" -Destination (Join-Path $claudeDir "context") -CustomMessage "✓ Workspace context installed at: $(Join-Path $claudeDir "context")"
            Safe-Folder-Copy -Source "$RepoRoot\catalog\memory" -Destination (Join-Path $claudeDir "memory") -CustomMessage "✓ Workspace memory installed at: $(Join-Path $claudeDir "memory")"

            # Git Guardrails Hook
            Install-GitGuardrails -RepoRoot $RepoRoot -TargetClaudeDir $claudeDir -Scope "Workspace"

            # Usage Display Hook
            Install-UsageDisplay -RepoRoot $RepoRoot -TargetClaudeDir $claudeDir -Scope "Workspace"

            # Require Description Hook
            Install-RequireDescription -RepoRoot $RepoRoot -TargetClaudeDir $claudeDir -Scope "Workspace"
        }

        # 2. Gemini / Antigravity
        if ($workspacePlatforms -contains "GEMINI") {
            Write-Header -Provider "GEMINI"
            Write-Item -Message "Installing Workspace Configuration..."
            $geminiDir = Join-Path $targetPath ".gemini"
            $agentDir = Join-Path $targetPath ".agent"

            if (-not (Test-Path $geminiDir)) { New-Item -ItemType Directory -Force -Path $geminiDir | Out-Null }
            if (-not (Test-Path $agentDir)) { New-Item -ItemType Directory -Force -Path $agentDir | Out-Null }

            # GEMINI.md (rendered from template without Claude-specific concepts)
            Render-Template -Template "$RepoRoot\templates\ai-instructions\base-gemini.md" -Output "$geminiDir\GEMINI.md" -RepoRoot $RepoRoot -Languages $languages

            # Mirror Skills to Agent
            Safe-Folder-Copy -Source "$RepoRoot\catalog\skills" -Destination (Join-Path $agentDir "skills") -CustomMessage "✓ Workspace skills catalog installed at: $(Join-Path $agentDir "skills")"

            # Mirror Commands to Agent Workflows
            Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $agentDir "workflows") -CustomMessage "✓ Workspace workflows installed at: $(Join-Path $agentDir "workflows")"

            Write-Item -Message "✓ Copied Skills & Workflows structure" -Color "DarkGreen"
        }

        # 3. OpenAI Codex
        if ($workspacePlatforms -contains "CODEX") {
            Write-Header -Provider "CODEX"
            Write-Item -Message "Installing Workspace Configuration..."
            $codexDir = Join-Path $targetPath ".codex"

            if (-not (Test-Path $codexDir)) { New-Item -ItemType Directory -Force -Path $codexDir | Out-Null }

            # Skills
            Safe-Folder-Copy -Source "$RepoRoot\catalog\skills" -Destination (Join-Path $codexDir "skills") -CustomMessage "✓ Workspace skills catalog installed at: $(Join-Path $codexDir "skills")"

            # Custom Prompts (Codex equivalent of commands)
            Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $codexDir "prompts") -CustomMessage "✓ Workspace custom prompts installed at: $(Join-Path $codexDir "prompts")"

            # AGENTS.md at project root (open standard for Codex, Jules, Cursor, Aider)
            Render-Template -Template "$RepoRoot\templates\ai-instructions\base-codex.md" -Output "$targetPath\AGENTS.md" -RepoRoot $RepoRoot -Languages $languages
        }

        # --- Prepare Rules for Copilot/Cursor (using concise snippets) ---
        $mergedContent = "# $($script:ProjectName) - Copilot Instructions`n`n"
        $mergedContent += "## Tech Stack`n"
        $mergedContent += "- **Language**: $($script:PrimaryLanguage)`n"
        $mergedContent += "- **Package Manager**: $($script:PackageManager)`n"
        $mergedContent += "- **Test**: $($script:TestFramework)`n"
        $mergedContent += "- **Lint**: $($script:LintTool)`n`n"
        $mergedContent += "## Working Conventions`n"
        $mergedContent += "- Destructive git commands require explicit user confirmation before running`n"
        $mergedContent += "- Never add ``Co-Authored-By`` lines, AI attribution footers, or AI-generated signatures to commit messages`n"
        $mergedContent += "- **MANDATORY: Every Bash/shell command approval MUST be preceded by a one-sentence plain-language explanation** of what the command does and what its impact will be. This applies to ALL commands regardless of complexity. No exceptions.`n"
        $mergedContent += "- Ask clarifying questions before coding if requirements are ambiguous`n`n"
        foreach ($lang in $languages) {
            $langKey = $lang.ToLower()
            if ($langKey -eq "c++") { $langKey = "cpp" }
            if ($langKey -eq "c#") { $langKey = "csharp" }
            $src = "$RepoRoot\templates\ai-instructions\coding-snippets\${langKey}.md"
            if (Test-Path $src) {
                $mergedContent += "`n" + (Get-Content $src -Raw) + "`n"
            }
        }

        # 4. Microsoft - Github Copilot
        if ($workspacePlatforms -contains "COPILOT") {
            Write-Header -Provider "COPILOT"
            Write-Item -Message "Installing Workspace Configuration..."
            $copilotDir = Join-Path $targetPath ".github"
            if (-not (Test-Path $copilotDir)) { New-Item -ItemType Directory -Force -Path $copilotDir | Out-Null }
            $copilotFile = Join-Path $copilotDir "copilot-instructions.md"

            $doWrite = $true
            if ((Test-Path $copilotFile)) {
                if ($script:OverwriteMode -eq "ALL") {
                    # Overwrite
                }
                elseif ($script:OverwriteMode -eq "NONE") {
                    Write-Item -Message "File exists: copilot-instructions.md (Skipped)" -Color "DarkGray"
                    $doWrite = $false
                }
                else {
                    # ASK
                    Write-Item -Message "File exists: copilot-instructions.md" -Color "Yellow"
                    $resp = Read-Prompt "Overwrite? [Y]es / [N]o / [A]ll"
                    if ($resp -match "^[Aa]") {
                        $script:OverwriteMode = "ALL"
                    }
                    elseif ($resp -notmatch "^[Yy]") {
                        $doWrite = $false
                    }
                }
            }
            if ($doWrite) {
                $mergedContent | Set-Content $copilotFile
                Write-Item -Message "✓ Workspace instructions installed at: $copilotFile" -Color "DarkGreen"
            }
        }
        Write-Host ""
}

function Install-VSCodeExtensions {
    param ($RepoRoot)
    Write-Host ""
    Write-Host "[ ---------- CLAUDE USAGE MONITOR ---------- ]" -ForegroundColor DarkYellow
    Write-Host ""

    Write-Item -Message "The Claude Usage Monitor is a VS Code extension that displays your Claude" -Color "White"
    Write-Item -Message "Code usage limits in the status bar and recommends when to switch models" -Color "White"
    Write-Item -Message "(e.g., Opus to Sonnet) to stay within your session and weekly limits." -Color "White"
    Write-Host ""

    $extensionDir = Join-Path $RepoRoot "extensions\claude-usage-monitor"

    if (-not (Test-Path $extensionDir)) {
        Write-Item -Message "Extension source not found at: $extensionDir" -Color "Red"
        return
    }

    # Check for Node.js
    $nodeCmd = Get-Command "node" -ErrorAction SilentlyContinue
    if (-not $nodeCmd) {
        Write-Item -Message "Node.js is not installed (required to build the extension)." -Color "DarkYellow"
        $installResp = Read-Prompt "Install Node.js LTS via winget? [Y]es / [N]o"
        if ($installResp -match "^[Yy]") {
            # Check for winget
            $wingetCmd = Get-Command "winget" -ErrorAction SilentlyContinue
            if (-not $wingetCmd) {
                Write-Item -Message "winget is not available. Please install Node.js manually from https://nodejs.org" -Color "Red"
                Write-Item -Message "After installing Node.js, re-run this installer to build the extension." -Color "Yellow"
                return
            }

            Write-Item -Message "Installing Node.js LTS via winget..." -Color "White"
            try {
                & winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
                # Refresh PATH for current session
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

                $nodeCmd = Get-Command "node" -ErrorAction SilentlyContinue
                if (-not $nodeCmd) {
                    Write-Item -Message "Node.js was installed but is not yet available in this session." -Color "Yellow"
                    Write-Item -Message "Please close this terminal, open a new one, and re-run the installer." -Color "Yellow"
                    return
                }
                Write-Item -Message "✓ Node.js installed successfully." -Color "DarkGreen"
            }
            catch {
                Write-Item -Message "Failed to install Node.js: $($_.Exception.Message)" -Color "Red"
                Write-Item -Message "Please install Node.js manually from https://nodejs.org" -Color "Yellow"
                return
            }
        }
        else {
            Write-Item -Message "Skipped. Install Node.js from https://nodejs.org and re-run to build the extension." -Color "Gray"
            return
        }
    }
    else {
        $nodeVersion = & node --version
        Write-Item -Message "Found Node.js $nodeVersion" -Color "DarkGreen"
    }

    # Check for npm
    $npmCmd = Get-Command "npm" -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        Write-Item -Message "npm not found. Please ensure Node.js is properly installed." -Color "Red"
        return
    }

    # Suspend strict error mode for native CLI tools (npm/npx write warnings to stderr
    # which PowerShell converts to terminating errors under $ErrorActionPreference = "Stop")
    $savedErrorPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    # Build the extension
    Write-Item -Message "Building Claude Usage Monitor extension..." -Color "White"
    Push-Location $extensionDir

    # Clean compiled output so deleted source files don't linger as stale JS
    $outDir = Join-Path $extensionDir "out"
    if (Test-Path $outDir) {
        Remove-Item -Path $outDir -Recurse -Force
    }

    Write-Item -Message "  Installing dependencies..." -Color "Gray"
    & npm install --silent 2>$null | Out-Null
    Restore-Title
    if ($LASTEXITCODE -ne 0) {
        Write-Item -Message "Build failed: npm install failed" -Color "Red"
        Pop-Location
        $ErrorActionPreference = $savedErrorPref
        return
    }

    Write-Item -Message "  Compiling TypeScript..." -Color "Gray"
    & npm run compile 2>$null | Out-Null
    Restore-Title
    if ($LASTEXITCODE -ne 0) {
        Write-Item -Message "Build failed: TypeScript compilation failed" -Color "Red"
        Pop-Location
        $ErrorActionPreference = $savedErrorPref
        return
    }

    Write-Item -Message "✓ Extension built successfully." -Color "DarkGreen"
    Pop-Location

    # Package as VSIX (uses locally installed @vscode/vsce from devDependencies)
    Write-Item -Message "Packaging extension as VSIX..." -Color "White"
    Push-Location $extensionDir
    # Capture stdout + stderr so failures surface the real vsce diagnostic
    # (previously swallowed by 2>$null | Out-Null, leaving operators with no clue).
    $vsceOutput = & npx vsce package --no-dependencies 2>&1
    Restore-Title
    $vsixExitCode = $LASTEXITCODE
    Pop-Location

    $vsixFile = Get-ChildItem $extensionDir -Filter "*.vsix" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if (($vsixExitCode -ne 0) -or (-not $vsixFile)) {
        Write-Item -Message "Packaging failed (exit code: $vsixExitCode)." -Color "Red"
        if ($vsceOutput) {
            Write-Item -Message "vsce output:" -Color "Gray"
            $vsceOutput | ForEach-Object { Write-Item -Message "    $_" -Color "Gray" }
        }
        Write-Item -Message "You can still use the extension in development mode (F5 in VS Code)." -Color "Yellow"
        $ErrorActionPreference = $savedErrorPref
        return
    }

    Write-Item -Message "✓ Packaged: $($vsixFile.Name)" -Color "DarkGreen"

    # Install into VS Code
    $codeCmd = Get-Command "code" -ErrorAction SilentlyContinue
    if ($codeCmd) {
        # Uninstall any existing version first so VS Code does not skip the reinstall
        & code --uninstall-extension "devai-hub.claude-usage-monitor" 2>$null | Out-Null
        Restore-Title
        # --force ensures reinstall even when the version number has not changed
        & code --install-extension $vsixFile.FullName --force 2>$null | Out-Null
        Restore-Title
        if ($LASTEXITCODE -eq 0) {
            Write-Item -Message "✓ Claude Usage Monitor extension installed in VS Code!" -Color "DarkGreen"
            Write-Item -Message "  Restart VS Code to activate. Look for 'Claude: --%' in the status bar." -Color "White"
        }
        else {
            Write-Item -Message "VS Code install failed. You can install manually:" -Color "Yellow"
            Write-Item -Message "  code --install-extension `"$($vsixFile.FullName)`"" -Color "White"
        }
    }
    else {
        Write-Item -Message "VS Code CLI ('code') not found in PATH." -Color "Yellow"
        Write-Item -Message "VSIX saved at: $($vsixFile.FullName)" -Color "White"
        Write-Item -Message "Install manually via VS Code: Extensions > ... > Install from VSIX" -Color "Gray"
    }

    # Restore strict error mode
    $ErrorActionPreference = $savedErrorPref

    Write-Host ""
    Write-Host "  ✓ Claude Usage Monitor Installation Complete." -ForegroundColor Green
}

# --- Template & Script Installation ---

function Install-Templates {
    param ($RepoRoot)
    # Write-SubSectionBanner prepends its own blank line; no leading Write-Host "" needed.
    Write-SubSectionBanner -Text "Templates & Report Generator Installation"
    Write-Host ""
    Write-Item -Message "DevAI-Hub can generate professional Word (.docx) and PowerPoint (.pptx)" -Color "White"
    Write-Item -Message "reports from Markdown files using the /generate-report command." -Color "White"
    Write-Host ""

    # Ensure global directories exist
    $devaiHome = Join-Path $env:USERPROFILE ".devai-hub"
    $templatesDest = Join-Path $devaiHome "templates\documentation"
    $scriptsDest = Join-Path $devaiHome "scripts"

    if (-not (Test-Path $templatesDest)) { New-Item -ItemType Directory -Force -Path $templatesDest | Out-Null }
    if (-not (Test-Path $scriptsDest)) { New-Item -ItemType Directory -Force -Path $scriptsDest | Out-Null }

    # Copy bundled templates from repo
    $builtinTemplates = Join-Path $RepoRoot "templates\documentation"
    if (Test-Path $builtinTemplates) {
        Safe-Folder-Copy -Source $builtinTemplates -Destination $templatesDest -CustomMessage "✓ Built-in templates installed at: $templatesDest"
    }

    # Copy report generator script
    $scriptSource = Join-Path $RepoRoot "scripts\generate_report.py"
    if (Test-Path $scriptSource) {
        Safe-Copy -Source $scriptSource -Destination (Join-Path $scriptsDest "generate_report.py") -Confirm:$true -CustomMessage "✓ Report generator installed at: $scriptsDest\generate_report.py"
    }

    # Copy MCP benchmark script (v1.0.0+). Benchmarks the three internal MCPs
    # (devai-skill-server, devai-code-search, devai-web-fetch). Pure-local.
    $benchmarkSource = Join-Path $RepoRoot "scripts\devai_mcp_benchmark.py"
    if (Test-Path $benchmarkSource) {
        Safe-Copy -Source $benchmarkSource -Destination (Join-Path $scriptsDest "devai_mcp_benchmark.py") -Confirm:$true -CustomMessage "✓ MCP benchmark installed at: $scriptsDest\devai_mcp_benchmark.py"
    }

    # Copy style-guides (v1.0.0+). Reference content for /compile-deep-research
    # and /generate-report; deliberately not in catalog\commands so the files
    # do not surface as slash commands.
    $styleGuidesSrc = Join-Path $RepoRoot "catalog\style-guides"
    $styleGuidesDest = Join-Path $devaiHome "style-guides"
    if (Test-Path $styleGuidesSrc) {
        Safe-Folder-Copy -Source $styleGuidesSrc -Destination $styleGuidesDest -CustomMessage "✓ Style guides installed at: $styleGuidesDest"
    }

    # Check Python availability
    $pythonCmd = Get-Command "python" -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-Item -Message "Note: Python 3 is required to generate reports." -Color "Yellow"
        Write-Item -Message "Install from https://www.python.org/downloads/ or via: winget install Python.Python.3.12" -Color "Yellow"
    }
    else {
        # Check for python-docx and python-pptx
        $savedErrorPref = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & python -c "import docx; import pptx" 2>$null | Out-Null
        $depCheck = $LASTEXITCODE
        $ErrorActionPreference = $savedErrorPref

        if ($depCheck -ne 0) {
            Write-Item -Message "Note: Install report dependencies with: pip install python-docx python-pptx" -Color "Yellow"
        }
        else {
            Write-Item -Message "✓ Python dependencies (python-docx, python-pptx) are available" -Color "DarkGreen"
        }
    }

    # v0.9.7: The interactive "Import custom Word/PowerPoint templates?" prompt has been
    # removed. Custom template selection is now handled at report-generation time by the
    # `/generate-report` command (generic vs custom path gate). Bundled generic templates
    # are still copied silently above so the command has a default to offer.

    # List installed templates
    Write-Host ""
    Write-Item -Message "Installed templates:" -Color "White"
    $installed = Get-ChildItem $templatesDest -Include *.docx, *.pptx -Recurse -ErrorAction SilentlyContinue
    if ($installed) {
        foreach ($t in $installed) {
            Write-Item -Message "  $($t.Name)" -Color "DarkGreen"
        }
    }
    else {
        Write-Item -Message "  (none)" -Color "Gray"
    }
    Write-Host ""
}


# --- MCP Skill Server & Skill Index ---

function Install-SkillDiscovery {
    param ($RepoRoot)

    # --- Skill Index (all platforms) ---
    Write-Host ""
    Write-Item -Message "Installing skill index for all platforms..." -Color "White"

    $skillIndexSrc = Join-Path $RepoRoot "data\SKILL_INDEX.md"
    $devaiHome = Join-Path $env:USERPROFILE ".devai-hub"
    $devaiData = Join-Path $devaiHome "data"

    if (-not (Test-Path $devaiData)) { New-Item -Path $devaiData -ItemType Directory -Force | Out-Null }

    if (Test-Path $skillIndexSrc) {
        Copy-Item -Path $skillIndexSrc -Destination (Join-Path $devaiData "SKILL_INDEX.md") -Force
        Write-Item -Message "  Skill index copied to $devaiData" -Color "DarkGreen"
    }
    else {
        Write-Item -Message "  SKILL_INDEX.md not found in data/. Run 'python infrastructure/tools/build_skills_catalog.py' first." -Color "Yellow"
    }

    # Copy skills.json and bundles.json to global data dir
    $skillsJsonSrc = Join-Path $RepoRoot "data\skills.json"
    $bundlesJsonSrc = Join-Path $RepoRoot "data\bundles.json"
    if (Test-Path $skillsJsonSrc) { Copy-Item -Path $skillsJsonSrc -Destination (Join-Path $devaiData "skills.json") -Force }
    if (Test-Path $bundlesJsonSrc) { Copy-Item -Path $bundlesJsonSrc -Destination (Join-Path $devaiData "bundles.json") -Force }

    Write-Item -Message "  Skill data installed to $devaiData" -Color "DarkGreen"

    # --- MCP Skill Server (Claude Code only) ---
    Write-Host ""
    Write-Item -Message "MCP Skill Server (Claude Code integration)" -Color "White"

    # Check Python >= 3.10
    $ErrorActionPreference = "Continue"
    $pythonCmd = $null
    foreach ($cmd in @("python", "python3")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python\s+3\.(\d+)") {
                $minor = [int]$Matches[1]
                if ($minor -ge 10) {
                    $pythonCmd = $cmd
                    break
                }
            }
        }
        catch {}
    }
    $ErrorActionPreference = "Stop"

    if (-not $pythonCmd) {
        Write-Item -Message "  Python 3.10+ not found. MCP server requires Python 3.10 or newer." -Color "Yellow"
        Write-Item -Message "  Install Python from https://python.org and re-run the installer." -Color "Yellow"
        return
    }

    Write-Item -Message "  Found $pythonCmd" -Color "DarkGreen"

    # Copy MCP server source
    $mcpServerSrc = Join-Path $RepoRoot "extensions\devai-skill-server"
    $mcpServerDest = Join-Path $devaiHome "mcp-server"
    if (Test-Path $mcpServerDest) { Remove-Item -Path $mcpServerDest -Recurse -Force }
    Copy-Item -Path $mcpServerSrc -Destination $mcpServerDest -Recurse -Force
    Write-Item -Message "  MCP server source copied to $mcpServerDest" -Color "DarkGreen"

    # Create venv and install dependencies
    $venvPath = Join-Path $devaiHome "mcp-server-venv"
    $ErrorActionPreference = "Continue"

    # Check for uv
    $hasUv = $null -ne (Get-Command "uv" -ErrorAction SilentlyContinue)

    if ($hasUv) {
        Write-Item -Message "  Creating venv with uv..." -Color "White"
        & uv venv $venvPath 2>$null | Out-Null
        & uv pip install --python "$venvPath\Scripts\python.exe" -e $mcpServerDest 2>$null | Out-Null
    }
    else {
        Write-Item -Message "  Creating venv with $pythonCmd..." -Color "White"
        & $pythonCmd -m venv $venvPath 2>$null | Out-Null
        & "$venvPath\Scripts\pip.exe" install -q -e $mcpServerDest 2>$null | Out-Null
    }
    $ErrorActionPreference = "Stop"

    Write-Item -Message "  MCP server venv created at $venvPath" -Color "DarkGreen"

    # Register MCP server in ~/.claude/settings.json
    $claudeSettingsDir = Join-Path $env:USERPROFILE ".claude"
    $claudeSettings = Join-Path $claudeSettingsDir "settings.json"

    if (-not (Test-Path $claudeSettingsDir)) { New-Item -Path $claudeSettingsDir -ItemType Directory -Force | Out-Null }

    # Read existing settings as PSCustomObject (NOT hashtable) to preserve
    # nested structures like hooks arrays during the round-trip
    $settings = $null
    if (Test-Path $claudeSettings) {
        try { $settings = Get-Content $claudeSettings -Raw -Encoding UTF8 | ConvertFrom-Json }
        catch { Write-Item -Message "  Warning: Could not parse existing settings.json, merging carefully" -Color "Yellow" }
    }

    if ($null -eq $settings) {
        $settings = [PSCustomObject]@{}
    }

    # Install devai-code-search into the same venv (v1.0.0+).
    # Local-only code-search MCP. Zero outbound calls. See AGENTS.md MCP Registry Policy.
    $codeSearchSrc = Join-Path $RepoRoot "extensions\devai-code-search"
    $codeSearchDest = Join-Path $devaiHome "code-search"
    $ErrorActionPreference = "Continue"
    if (Test-Path $codeSearchSrc) {
        if (Test-Path $codeSearchDest) { Remove-Item -Path $codeSearchDest -Recurse -Force }
        Copy-Item -Path $codeSearchSrc -Destination $codeSearchDest -Recurse -Force
        if ($hasUv) {
            & uv pip install --python "$venvPath\Scripts\python.exe" -e $codeSearchDest 2>$null | Out-Null
        } else {
            & "$venvPath\Scripts\pip.exe" install -q -e $codeSearchDest 2>$null | Out-Null
        }
        Write-Item -Message "  devai-code-search installed at $codeSearchDest" -Color "DarkGreen"
    }

    # Install devai-web-fetch into the same venv (v1.0.0+).
    # Local-only web-fetch MCP (fetches user-specified URLs only). See AGENTS.md.
    $webFetchSrc = Join-Path $RepoRoot "extensions\devai-web-fetch"
    $webFetchDest = Join-Path $devaiHome "web-fetch"
    if (Test-Path $webFetchSrc) {
        if (Test-Path $webFetchDest) { Remove-Item -Path $webFetchDest -Recurse -Force }
        Copy-Item -Path $webFetchSrc -Destination $webFetchDest -Recurse -Force
        if ($hasUv) {
            & uv pip install --python "$venvPath\Scripts\python.exe" -e $webFetchDest 2>$null | Out-Null
        } else {
            & "$venvPath\Scripts\pip.exe" install -q -e $webFetchDest 2>$null | Out-Null
        }
        Write-Item -Message "  devai-web-fetch installed at $webFetchDest" -Color "DarkGreen"
    }
    $ErrorActionPreference = "Stop"

    # Add or update mcpServers without touching other keys (e.g., hooks)
    $skillServerEntry = [PSCustomObject]@{
        command = "$venvPath\Scripts\python.exe"
        args    = @("-m", "devai_skill_server")
        env     = [PSCustomObject]@{ DEVAI_HUB_ROOT = $devaiHome }
    }
    $codeSearchEntry = [PSCustomObject]@{
        command = "$venvPath\Scripts\python.exe"
        args    = @("-m", "devai_code_search")
        env     = [PSCustomObject]@{ DEVAI_HUB_ROOT = $devaiHome }
    }
    $webFetchEntry = [PSCustomObject]@{
        command = "$venvPath\Scripts\python.exe"
        args    = @("-m", "devai_web_fetch")
        env     = [PSCustomObject]@{ DEVAI_HUB_ROOT = $devaiHome }
    }

    if (-not $settings.PSObject.Properties["mcpServers"]) {
        $settings | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([PSCustomObject]@{})
    }

    foreach ($pair in @(
        @{ Name = "devai-skill-server"; Entry = $skillServerEntry },
        @{ Name = "devai-code-search"; Entry = $codeSearchEntry },
        @{ Name = "devai-web-fetch"; Entry = $webFetchEntry }
    )) {
        $name = $pair.Name
        $entry = $pair.Entry
        if ($settings.mcpServers.PSObject.Properties[$name]) {
            $settings.mcpServers.$name = $entry
        } else {
            $settings.mcpServers | Add-Member -NotePropertyName $name -NotePropertyValue $entry
        }
    }

    $settings | ConvertTo-Json -Depth 10 | Set-Content $claudeSettings -Encoding UTF8
    Write-Item -Message "  MCP servers registered in $claudeSettings (devai-skill-server, devai-code-search, devai-web-fetch)" -Color "DarkGreen"
    Write-Item -Message "  Servers will auto-start with Claude Code. No manual steps needed." -Color "DarkGreen"
}

# --- Banner ---

function Show-WelcomeBanner {
    $banner = "=" * 120
    Write-Host ""
    Write-Host $banner -ForegroundColor DarkCyan
    Write-Host "                                      Welcome to the DevAI-Hub Universal Installer" -ForegroundColor DarkCyan
    Write-Host "                                                     (version $script:DevAIHubVersion)" -ForegroundColor DarkCyan
    Write-Host $banner -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-FarewellBanner {
    $banner = "=" * 120
    Write-Host ""
    Write-Host $banner -ForegroundColor DarkCyan
    Write-Host "                              Thank You For Using The DevAI-Hub Universal Installer" -ForegroundColor DarkCyan
    Write-Host "                                                     (version $script:DevAIHubVersion)" -ForegroundColor DarkCyan
    Write-Host $banner -ForegroundColor DarkCyan
    Write-Host ""
}

# --- Main ---
$repoRoot = Resolve-Path "$PSScriptRoot\.."

Show-WelcomeBanner

# Ask whether to install globally (recommended, user-scope) or to a specific workspace.
Write-Host "Where would you like to install DevAI-Hub?"
Write-Host "  [G] Global (recommended) - applies to all projects on this machine (~/.claude/, ~/.gemini/, ~/.codex/, ~/.devai-hub/)" -ForegroundColor Green
Write-Host "  [W] Workspace            - scoped to a specific project directory" -ForegroundColor Yellow
Write-Host ""
$scopeChoice = Read-Host "Select [G/W]"

$scopeLabel = "Global"
if ($scopeChoice -match "^[Ww]") {
    $scopeLabel = "Workspace"
    # Workspace install: prompt for project path via folder picker, then run the workspace phase once.
    do {
        $workspaceTarget = [ModernFolderPicker.FileOpenDialog]::ShowDialog()
        if ([string]::IsNullOrWhiteSpace($workspaceTarget)) {
            Write-Host "No folder selected. Please choose a workspace directory." -ForegroundColor Yellow
        }
    } while ([string]::IsNullOrWhiteSpace($workspaceTarget))
    Install-Workspace -RepoRoot $repoRoot -TargetPath $workspaceTarget
}
else {
    # Default + explicit [Gg] both route here.
    Install-Global -RepoRoot $repoRoot
}

# Bundled report-generator templates + scripts are user-scope and always install silently.
# Interactive custom-template import moved to /generate-report at use time (v0.9.7).
Install-Templates -RepoRoot $repoRoot

Write-CenteredBanner -Text "$scopeLabel Installation Complete." -Color "Green"

Write-Host ""
Write-Host "IMPORTANT: Restart any running Claude Code, Cursor, Gemini CLI, Codex, or Copilot sessions." -ForegroundColor Yellow
Write-Host "  Settings files (settings.json, AGENTS.md, .cursor/rules/) are read at session start and not hot-reloaded." -ForegroundColor Yellow
Write-Host "  New hooks, commands, skills, and permission entries will not take effect in already-running sessions until they restart." -ForegroundColor Yellow

Show-FarewellBanner
Pause
