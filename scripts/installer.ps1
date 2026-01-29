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
} catch { }

# --- Formatting Helpers ---

function Get-ProviderColor {
    param([string]$Provider)
    $color = switch ($Provider) {
        "CLAUDE"   { "DarkYellow" }
        "GEMINI"   { "Blue" }
        "WINDSURF" { "Cyan" }
        "CURSOR"   { "Magenta" }
        "COPILOT"  { "Gray" }
        Default    { "White" }
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

function Safe-Copy {
    param(
        [string]$Source,
        [string]$Destination,
        [boolean]$Confirm = $false
    )
    
    if (-not (Test-Path $Source)) {
        Write-Item -Message "Skip: Source not found ($(Split-Path $Source -Leaf))" -Color "DarkGray"
        return
    }

    if (Test-Path $Destination) {
        if ($Confirm) {
            if (-not $script:OverwriteAll) {
                Write-Item -Message "File exists: $Destination" -Color "Yellow"
                $resp = Read-Prompt "Overwrite? (Y/N/A)"
                if ($resp -match "^[Aa]") {
                    $script:OverwriteAll = $true
                } elseif ($resp -notmatch "^[Yy]") {
                    Write-Item -Message "Skipped by user." -Color "Gray"
                    return
                }
            }
        }
    }

    try {
        if (Test-Path $Destination) { Remove-Item $Destination -Force -ErrorAction Stop }
        Copy-Item -Path $Source -Destination $Destination -Force -ErrorAction Stop
        Write-Item -Message "✓ Installed to $Destination" -Color "DarkGreen"
    } catch {
        Write-Item -Message "ERROR: Could not write file. Is it open?" -Color "Red"
        Write-Item -Message $_.Exception.Message -Color "Red" -Indent 2
    }
}

function Safe-Folder-Copy {
    param(
        [string]$Source,
        [string]$Destination
    )
    if (Test-Path $Destination) {
        if (-not $script:OverwriteAll) {
            Write-Item -Message "Folder exists: $Destination" -Color "Yellow"
            $resp = Read-Prompt "Overwrite contents? (Y/N/A)"
            if ($resp -match "^[Aa]") {
                $script:OverwriteAll = $true
            } elseif ($resp -notmatch "^[Yy]") {
                Write-Item -Message "Skipped." -Color "Gray"
                return
            }
        }
    } else {
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    }

    $logFile = "$env:TEMP\devai_install_v5.log"
    # Suppress output to keep cleaner logs
    & robocopy $Source $Destination /E /NFL /NDL /NJH /NJS | Out-Null
    Write-Item -Message "✓ Folder updated." -Color "DarkGreen"
}

# --- Install Functions ---

function Install-Global {
    param ($RepoRoot)
    Clear-Host
    $script:OverwriteAll = $false
    Write-Host "================================================================" -ForegroundColor DarkCyan
    Write-Host "                   DevAI-Hub Universal Installer                " -ForegroundColor DarkCyan
    Write-Host "================================================================" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host "                  PHASE 1: Global Installation                  " -ForegroundColor Cyan
    Write-Host "----------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Checking User Profile ($env:USERPROFILE)..." -ForegroundColor Gray
    
    # 1. Claude
    Write-Header -Provider "CLAUDE"
    Write-Item -Message "Checking Global Skills..."
    $globalClaude = Join-Path $env:USERPROFILE ".claude"
    Safe-Folder-Copy -Source "$RepoRoot\claude-skills-catalog" -Destination (Join-Path $globalClaude "skills")

    # 2. Gemini
    Write-Header -Provider "GEMINI"
    Write-Item -Message "Checking Configuration & Skills..."
    $globalGeminiDir = Join-Path $env:USERPROFILE ".gemini"
    if (-not (Test-Path $globalGeminiDir)) { New-Item -ItemType Directory -Force -Path $globalGeminiDir | Out-Null }
    
    Safe-Copy -Source "$RepoRoot\templates\ai-instructions\generic-instructions.md" -Destination "$globalGeminiDir\GEMINI.md" -Confirm:$true
    
    # Mirror Skills to Gemini
    $geminiSkills = Join-Path $globalGeminiDir "skills"
    Safe-Folder-Copy -Source "$RepoRoot\claude-skills-catalog" -Destination $geminiSkills

    # 3. Copilot
    Write-Header -Provider "COPILOT" 
    Write-Item -Message "Check skipped (No global file support on Windows)." -Color "DarkGray"

    # 4. Cursor
    Write-Header -Provider "CURSOR"
    Write-Item -Message "Check skipped (No global file support on Windows)." -Color "DarkGray"
    
    # 5. Windsurf
    Write-Header -Provider "WINDSURF"
    Write-Item -Message "Checking Memories/Rules..."
    $windsurfDir = Join-Path $env:USERPROFILE ".codeium\windsurf\memories"
    if (-not (Test-Path $windsurfDir)) { New-Item -ItemType Directory -Force -Path $windsurfDir | Out-Null }
    Safe-Copy -Source "$RepoRoot\templates\ai-instructions\generic-instructions.md" -Destination "$windsurfDir\global_rules.md" -Confirm:$true
    
    Write-Host ""
    Write-Host "----------------------------------------------------------------" -ForegroundColor Green
    Write-Host "              Global Installation Phase Complete.               " -ForegroundColor Green
    Write-Host "----------------------------------------------------------------" -ForegroundColor Green
    Write-Host ""
}

function Get-LanguageSelection {
    param([array]$Detected)
    $map = @{ "1"="Python"; "2"="JavaScript"; "3"="TypeScript"; "4"="Java"; "5"="C#"; "6"="Go"; "7"="C++" }
    
    if ($Detected.Count -gt 0) {
        Write-Host "Detected languages: $($Detected -join ', ')" -ForegroundColor Yellow
        $resp = Read-Host "${spaces}└─> Use these? (Y/N)" -ForegroundColor Yellow
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
        "Python" = (Get-ChildItem $Path -Include *.py -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "JavaScript" = (Get-ChildItem $Path -Include *.js,*.jsx -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "TypeScript" = (Get-ChildItem $Path -Include *.ts,*.tsx -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "Java" = (Get-ChildItem $Path -Include *.java -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "C#" = (Get-ChildItem $Path -Include *.cs -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "Go" = (Get-ChildItem $Path -Include *.go -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        "C++" = (Get-ChildItem $Path -Include *.cpp,*.h,*.hpp -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
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
        $response = Read-Host "Select Project? (Y/N)"
        if ($response -notmatch "^[Yy]") { break }

        $targetPath = [ModernFolderPicker.FileOpenDialog]::ShowDialog()
        if ([string]::IsNullOrWhiteSpace($targetPath)) { 
            Write-Host "No folder selected." -ForegroundColor Yellow
            continue 
        }
        Write-Host "Target: $targetPath" -ForegroundColor DarkYellow

        $detected = Detect-Languages -Path $targetPath
        $languages = Get-LanguageSelection -Detected $detected
        Write-Host "Selected: $($languages -join ', ')" -ForegroundColor Yellow

        # --- Install Logic ---

        # 1. Claude
        Write-Header -Provider "CLAUDE"
        Write-Item -Message "Installing Workspace Resources..."
        $claudeDir = Join-Path $targetPath ".claude"
        New-Item -ItemType Directory -Force -Path (Join-Path $claudeDir "skills") | Out-Null
        Invoke-Expression "robocopy '$RepoRoot\claude-skills-catalog' '$targetPath\.claude\skills' /E /NFL /NDL /NJH /NJS" | Out-Null
        
        $primary = $languages[0].ToLower()
        if ($primary -eq "c++") { $primary = "cpp" }
        
        # FIX: Source is README.md, Dest is CLAUDE.md
        Safe-Copy -Source "$RepoRoot\templates\ai-instructions\claude-code\${primary}\README.md" -Destination "$targetPath\CLAUDE.md" -Confirm:$true

        # 2. Gemini
        Write-Header -Provider "GEMINI"
        Write-Item -Message "Installing Workspace Instructions..."
        $geminiDir = Join-Path $targetPath ".gemini"
        if (-not (Test-Path $geminiDir)) { New-Item -ItemType Directory -Force -Path $geminiDir | Out-Null }
        Safe-Copy -Source "$RepoRoot\templates\ai-instructions\generic-instructions.md" -Destination "$geminiDir\GEMINI.md" -Confirm:$true
        
        # Mirror Skills to Workspace Gemini
        New-Item -ItemType Directory -Force -Path (Join-Path $geminiDir "skills") | Out-Null
        $geminiCmds = Join-Path $geminiDir "commands"
        New-Item -ItemType Directory -Force -Path $geminiCmds | Out-Null
        
        Invoke-Expression "robocopy '$RepoRoot\claude-skills-catalog' '$geminiDir\skills' /E /NFL /NDL /NJH /NJS" | Out-Null
        Write-Item -Message "✓ Copied Skills & Commands structure" -Color "DarkGreen"

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

        # 3. Copilot
        Write-Header -Provider "COPILOT"
        Write-Item -Message "Installing instructions..."
        $copilotDir = Join-Path $targetPath ".github"
        if (-not (Test-Path $copilotDir)) { New-Item -ItemType Directory -Force -Path $copilotDir | Out-Null }
        $copilotFile = Join-Path $copilotDir "copilot-instructions.md"
        
        $doWrite = $true
        if ((Test-Path $copilotFile)) {
             Write-Item -Message "File exists: copilot-instructions.md" -Color "Yellow"
             $resp = Read-Prompt "Overwrite? (Y/N)"
             if ($resp -notmatch "^[Yy]") { $doWrite = $false }
        }
        if ($doWrite) {
            $mergedContent | Set-Content $copilotFile
            Write-Item -Message "✓ Updated copilot-instructions.md" -Color "DarkGreen"
        }

        # 4. Cursor
        Write-Header -Provider "CURSOR"
        Write-Item -Message "Installing .cursorrules..."
        $cursorFile = Join-Path $targetPath ".cursorrules"
        $doWrite = $true
        if ((Test-Path $cursorFile)) {
             Write-Item -Message "File exists: .cursorrules" -Color "Yellow"
             $resp = Read-Prompt "Overwrite? (Y/N)"
             if ($resp -notmatch "^[Yy]") { $doWrite = $false }
        }
        if ($doWrite) {
            $mergedContent | Set-Content $cursorFile
            Write-Item -Message "✓ Updated .cursorrules" -Color "DarkGreen"
        }

        # 5. Windsurf
        Write-Header -Provider "WINDSURF"
        Write-Item -Message "Installing Workspace Rules..."
        $windsurfDir = Join-Path $targetPath ".codeium\windsurf\memories"
        if (-not (Test-Path $windsurfDir)) { New-Item -ItemType Directory -Force -Path $windsurfDir | Out-Null }
        Safe-Copy -Source "$RepoRoot\templates\ai-instructions\generic-instructions.md" -Destination "$windsurfDir\rules.md" -Confirm:$true
        
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
Write-Host "Done."
Pause
