# DevAI-Hub Universal Installer V5
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

    $logFile = "$env:TEMP\devai_install_v5.log"
    # Suppress output to keep cleaner logs
    & robocopy $Source $Destination /E /NFL /NDL /NJH /NJS | Out-Null
    
    if (-not [string]::IsNullOrEmpty($CustomMessage)) {
        Write-Item -Message $CustomMessage -Color "DarkGreen"
    }
    else {
        Write-Item -Message "✓ Installed to $Destination" -Color "DarkGreen"
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

        # Global CLAUDE.md
        Safe-Copy -Source "$RepoRoot\catalog\CLAUDE.md" -Destination "$globalClaude\CLAUDE.md" -Confirm:$true -CustomMessage "✓ Global instructions installed at: $globalClaude\CLAUDE.md"

        # Global Skills
        Safe-Folder-Copy -Source "$RepoRoot\catalog\skills" -Destination (Join-Path $globalClaude "skills") -CustomMessage "✓ Global skills catalog installed at: $(Join-Path $globalClaude "skills")"

        # Global Commands
        Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $globalClaude "commands") -CustomMessage "✓ Global commands installed at: $(Join-Path $globalClaude "commands")"
    }

    # 2. Gemini / Antigravity
    if ($platforms -contains "GEMINI") {
        Write-Header -Provider "GEMINI"
        Write-Item -Message "Installing Global Configuration..."
        $globalGeminiDir = Join-Path $env:USERPROFILE ".gemini"
        $globalAgentDir = Join-Path $env:USERPROFILE ".agent"
        
        if (-not (Test-Path $globalGeminiDir)) { New-Item -ItemType Directory -Force -Path $globalGeminiDir | Out-Null }
        if (-not (Test-Path $globalAgentDir)) { New-Item -ItemType Directory -Force -Path $globalAgentDir | Out-Null }
        
        # Global GEMINI.md
        Safe-Copy -Source "$RepoRoot\templates\ai-instructions\generic-instructions.md" -Destination "$globalGeminiDir\GEMINI.md" -Confirm:$true -CustomMessage "✓ Global instructions installed at: $globalGeminiDir\GEMINI.md"
        
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

        # --- Install Logic ---

        # 1. Claude
        if ($workspacePlatforms -contains "CLAUDE") {
            Write-Header -Provider "CLAUDE"
            Write-Item -Message "Installing Workspace Configuration..."
            $claudeDir = Join-Path $targetPath ".claude"
            
            # CLAUDE.md
            Safe-Copy -Source "$RepoRoot\catalog\CLAUDE.md" -Destination "$targetPath\CLAUDE.md" -Confirm:$true -CustomMessage "✓ Workspace instructions installed at: $targetPath\CLAUDE.md"

            # Skills
            Safe-Folder-Copy -Source "$RepoRoot\catalog\skills" -Destination (Join-Path $claudeDir "skills") -CustomMessage "✓ Workspace skills catalog installed at: $(Join-Path $claudeDir "skills")"
            
            # Commands
            Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $claudeDir "commands") -CustomMessage "✓ Workspace commands installed at: $(Join-Path $claudeDir "commands")"

            # Context & Memory
            Safe-Folder-Copy -Source "$RepoRoot\catalog\context" -Destination (Join-Path $claudeDir "context") -CustomMessage "✓ Workspace context installed at: $(Join-Path $claudeDir "context")"
            Safe-Folder-Copy -Source "$RepoRoot\catalog\memory" -Destination (Join-Path $claudeDir "memory") -CustomMessage "✓ Workspace memory installed at: $(Join-Path $claudeDir "memory")"
        }

        # 2. Gemini / Antigravity
        if ($workspacePlatforms -contains "GEMINI") {
            Write-Header -Provider "GEMINI"
            Write-Item -Message "Installing Workspace Configuration..."
            $geminiDir = Join-Path $targetPath ".gemini"
            $agentDir = Join-Path $targetPath ".agent"

            if (-not (Test-Path $geminiDir)) { New-Item -ItemType Directory -Force -Path $geminiDir | Out-Null }
            if (-not (Test-Path $agentDir)) { New-Item -ItemType Directory -Force -Path $agentDir | Out-Null }

            Safe-Copy -Source "$RepoRoot\templates\ai-instructions\generic-instructions.md" -Destination "$geminiDir\GEMINI.md" -Confirm:$true -CustomMessage "✓ Workspace instructions installed at: $geminiDir\GEMINI.md"
            
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

        # --- Prepare Rules for Copilot/Cursor ---
        $mergedContent = "# AI Coding Rules`n`n"
        foreach ($lang in $languages) {
            $langKey = $lang.ToLower()
            if ($langKey -eq "c++") { $langKey = "cpp" }
            $src = "$RepoRoot\templates\ai-instructions\coding-instructions\${langKey}.md"
            if (Test-Path $src) {
                $mergedContent += "`n`n## Rules for $lang`n" + (Get-Content $src -Raw)
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

# --- Main ---
$repoRoot = Resolve-Path "$PSScriptRoot\.."
Install-Global -RepoRoot $repoRoot
Install-Workspace -RepoRoot $repoRoot
Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkCyan
Write-Host "       Thank You For Using The DevAI-Hub Universal Installer    " -ForegroundColor DarkCyan
Write-Host "================================================================" -ForegroundColor DarkCyan
Write-Host ""
Pause
