# DevAI-Hub Universal Installer V8 (v0.6.3)
# Installs AI Skills Globally and to Workspaces with Safe Overwrite and Modern UI
$ErrorActionPreference = "Stop"

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
    Write-Host ""
    Write-Host "  [ ---------- $Provider ---------- ]" -ForegroundColor $color
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

    $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json

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

    $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json

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

# --- Install Functions ---

function Install-Global {
    param ($RepoRoot)
    Clear-Host
    Write-Host "================================================================" -ForegroundColor DarkCyan
    Write-Host "           Welcome to the DevAI-Hub Universal Installer         " -ForegroundColor DarkCyan
    Write-Host "================================================================" -ForegroundColor DarkCyan
    Write-Host ""
    
    # Global Overwrite Preference
    $script:OverwriteMode = Get-Overwrite-Preference
    Write-Host ""

    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host "                  PHASE 1: Global Installation                  " -ForegroundColor Cyan
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
    
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

        # Git Guardrails Hook
        Install-GitGuardrails -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"

        # Usage Display Hook
        Install-UsageDisplay -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"
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
        
        # Global Commands
        Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $globalCodexDir "commands") -CustomMessage "✓ Global commands installed at: $(Join-Path $globalCodexDir "commands")"
    }

    # 4. Microsoft - Github Copilot
    if ($platforms -contains "COPILOT") {
        Write-Header -Provider "COPILOT" 
        Write-Item -Message "Check skipped (No global file support on Windows)." -Color "DarkGray"
    }
 
    Write-Host ""
    Write-Host "----------------------------------------------------------------" -ForegroundColor Green
    Write-Host "              Global Installation Phase Complete.               " -ForegroundColor Green
    Write-Host "----------------------------------------------------------------" -ForegroundColor Green
    Write-Host ""
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
    param ($RepoRoot)
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host "                PHASE 2: Workspace Installation                 " -ForegroundColor Cyan
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
    
    while ($true) {
        Write-Host ""
        Write-Host "Do you want to configure a specific local project/repository?" -ForegroundColor White
        $response = Read-Host "Select Project? [Y]es / [N]o"
        if ($response -notmatch "^[Yy]") { break }

        $targetPath = [ModernFolderPicker.FileOpenDialog]::ShowDialog()
        if ([string]::IsNullOrWhiteSpace($targetPath)) { 
            Write-Host "No folder selected." -ForegroundColor Yellow
            continue 
        }
        Write-Host "Target: $targetPath" -ForegroundColor DarkYellow
        
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

            # Context & Memory
            Safe-Folder-Copy -Source "$RepoRoot\catalog\context" -Destination (Join-Path $claudeDir "context") -CustomMessage "✓ Workspace context installed at: $(Join-Path $claudeDir "context")"
            Safe-Folder-Copy -Source "$RepoRoot\catalog\memory" -Destination (Join-Path $claudeDir "memory") -CustomMessage "✓ Workspace memory installed at: $(Join-Path $claudeDir "memory")"

            # Git Guardrails Hook
            Install-GitGuardrails -RepoRoot $RepoRoot -TargetClaudeDir $claudeDir -Scope "Workspace"

            # Usage Display Hook
            Install-UsageDisplay -RepoRoot $RepoRoot -TargetClaudeDir $claudeDir -Scope "Workspace"
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
            
            # Commands
            Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $codexDir "commands") -CustomMessage "✓ Workspace commands installed at: $(Join-Path $codexDir "commands")"
        }

        # --- Prepare Rules for Copilot/Cursor (using concise snippets) ---
        $mergedContent = "# $($script:ProjectName) - Copilot Instructions`n`n"
        $mergedContent += "## Tech Stack`n"
        $mergedContent += "- **Language**: $($script:PrimaryLanguage)`n"
        $mergedContent += "- **Package Manager**: $($script:PackageManager)`n"
        $mergedContent += "- **Test**: $($script:TestFramework)`n"
        $mergedContent += "- **Lint**: $($script:LintTool)`n`n"
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
        Write-Host "----------------------------------------------------------------" -ForegroundColor Green
        Write-Host "      Project $(Split-Path $targetPath -Leaf) Configured!       " -ForegroundColor Green
        Write-Host "----------------------------------------------------------------" -ForegroundColor Green
    }
}

function Install-VSCodeExtensions {
    param ($RepoRoot)
    Write-Host ""
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host "        PHASE 3: Claude Code Usage Monitor Installation          " -ForegroundColor Cyan
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host ""

    Write-Item -Message "The Claude Usage Monitor is a VS Code extension that displays your Claude" -Color "White"
    Write-Item -Message "Code usage limits in the status bar and recommends when to switch models" -Color "White"
    Write-Item -Message "(e.g., Opus to Sonnet) to stay within your session and weekly limits." -Color "White"
    Write-Host ""

    $response = Read-Prompt "Install the Claude Usage Monitor VS Code extension? [Y]es / [N]o"
    if ($response -notmatch "^[Yy]") {
        Write-Item -Message "Skipped VS Code extension installation." -Color "Gray"
        return
    }

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

    Write-Item -Message "  Installing dependencies..." -Color "Gray"
    & npm install --silent 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Item -Message "Build failed: npm install failed" -Color "Red"
        Pop-Location
        $ErrorActionPreference = $savedErrorPref
        return
    }

    Write-Item -Message "  Compiling TypeScript..." -Color "Gray"
    & npm run compile 2>$null | Out-Null
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
    & npx vsce package --no-dependencies 2>$null | Out-Null
    $vsixExitCode = $LASTEXITCODE
    Pop-Location

    $vsixFile = Get-ChildItem $extensionDir -Filter "*.vsix" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if (($vsixExitCode -ne 0) -or (-not $vsixFile)) {
        Write-Item -Message "Packaging failed (exit code: $vsixExitCode)." -Color "Red"
        Write-Item -Message "You can still use the extension in development mode (F5 in VS Code)." -Color "Yellow"
        $ErrorActionPreference = $savedErrorPref
        return
    }

    Write-Item -Message "✓ Packaged: $($vsixFile.Name)" -Color "DarkGreen"

    # Install into VS Code
    $codeCmd = Get-Command "code" -ErrorAction SilentlyContinue
    if ($codeCmd) {
        & code --install-extension $vsixFile.FullName 2>$null | Out-Null
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
    Write-Host "----------------------------------------------------------------" -ForegroundColor Green
    Write-Host "           VS Code Extension Phase Complete.                    " -ForegroundColor Green
    Write-Host "----------------------------------------------------------------" -ForegroundColor Green
}

# --- Template & Script Installation ---

function Install-Templates {
    param ($RepoRoot)
    Write-Host ""
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host "     PHASE 4: Templates & Report Generator Installation         " -ForegroundColor Cyan
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
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

    Write-Host ""

    # Custom template import
    $response = Read-Prompt "Import custom Word/PowerPoint templates? [Y]es / [N]o"
    if ($response -notmatch "^[Yy]") {
        Write-Item -Message "Skipped custom template import." -Color "Gray"
        Write-Host ""
        Write-Host "----------------------------------------------------------------" -ForegroundColor Green
        Write-Host "        Templates & Scripts Installation Complete.               " -ForegroundColor Green
        Write-Host "----------------------------------------------------------------" -ForegroundColor Green
        return
    }

    # Load Windows Forms for the file picker dialog
    Add-Type -AssemblyName System.Windows.Forms

    while ($true) {
        Write-Item -Message "Opening file picker..." -Color "White"

        $dialog = New-Object System.Windows.Forms.OpenFileDialog
        $dialog.Multiselect = $true
        $dialog.Filter = "Document Templates (*.docx;*.pptx)|*.docx;*.pptx|Word Templates (*.docx)|*.docx|PowerPoint Templates (*.pptx)|*.pptx|All files (*.*)|*.*"
        $dialog.Title = "Select Document Templates to Import"

        $result = $dialog.ShowDialog()

        if ($result -ne [System.Windows.Forms.DialogResult]::OK -or $dialog.FileNames.Count -eq 0) {
            Write-Item -Message "No files selected." -Color "Gray"
            break
        }

        foreach ($filePath in $dialog.FileNames) {
            $fileName = Split-Path $filePath -Leaf
            $ext = [System.IO.Path]::GetExtension($filePath).ToLower()

            if ($ext -notin @(".docx", ".pptx")) {
                Write-Item -Message "Skipped: $fileName (only .docx and .pptx are supported)" -Color "Yellow"
                continue
            }

            Safe-Copy -Source $filePath -Destination (Join-Path $templatesDest $fileName) -Confirm:$true -CustomMessage "✓ Template imported: $fileName"
        }

        Write-Host ""
        $more = Read-Prompt "Import more templates? [Y]es / [N]o"
        if ($more -notmatch "^[Yy]") { break }
    }

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
    Write-Host "----------------------------------------------------------------" -ForegroundColor Green
    Write-Host "        Templates & Scripts Installation Complete.               " -ForegroundColor Green
    Write-Host "----------------------------------------------------------------" -ForegroundColor Green
}

# --- Main ---
$repoRoot = Resolve-Path "$PSScriptRoot\.."
Install-Global -RepoRoot $repoRoot
Install-Workspace -RepoRoot $repoRoot
Install-VSCodeExtensions -RepoRoot $repoRoot
Install-Templates -RepoRoot $repoRoot
Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkCyan
Write-Host "       Thank You For Using The DevAI-Hub Universal Installer    " -ForegroundColor DarkCyan
Write-Host "================================================================" -ForegroundColor DarkCyan
Write-Host ""
Pause
