# Nexus-Hub Universal Installer V10 (Windows)
# Installs AI Skills Globally OR to a Workspace with Safe Overwrite and Modern UI
#
# Supported flags (v2.2.0+):
#   -Enterprise   Opt in to the standalone Gemini CLI install path. After
#                 2026-06-18 (per the 2026-05-21 Google Developers Blog
#                 announcement), Gemini CLI stops serving free / Google AI Pro
#                 / Ultra / GitHub-installed users; this switch is the only way
#                 to keep the integration after that date (requires a paid
#                 Gemini API key). Default: the installer prints a sunset
#                 warning and skips Gemini CLI, but still installs Antigravity
#                 CLI (which covers the same functionality via the
#                 antigravity2 integration).
#   -Help         Show usage and exit.
[CmdletBinding()]
param(
    [switch]$Enterprise,
    [switch]$Help,
    [string]$PrintConfig,
    [switch]$Check,
    [string]$Branch,
    [Parameter(Position = 0)]
    [string]$Subcommand,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$SubcommandArgs
)

if ($Help) {
    @"
Usage:
  pwsh scripts/installer.ps1 [-Enterprise] [-Help]
  pwsh scripts/installer.ps1 init [-Target PATH] [-DryRun]
  pwsh scripts/installer.ps1 -PrintConfig <integration-key>
  pwsh scripts/installer.ps1 -Check
  pwsh scripts/installer.ps1 -Branch <name> [-Enterprise]

Subcommands:
  init          Bootstrap project-local surfaces (Cursor rules, Claude
                settings.json stub) from a global install. Walks every
                registered integration that defines wire_project_surfaces()
                and writes the corresponding files. Defaults Target to the
                current directory.

Read-only modes (no disk writes):
  -PrintConfig <key>  Dump the Markdown readout of what the given integration
                      would install.
  -Check              Dry-run every integration and exit non-zero if any action
                      would create / update / remove a file. Useful in CI.

Options:
  -Enterprise   Install the standalone Gemini CLI integration. Requires a paid
                Gemini API key. After 2026-06-18 (per the 2026-05-21 Google
                Developers Blog announcement), Gemini CLI stops serving free /
                Google AI Pro / Ultra / GitHub-installed users; this switch is
                the only way to keep the integration after that date.
                Default (without -Enterprise): the installer prints a sunset
                warning and skips Gemini CLI but still installs Antigravity CLI.
  -Branch <name>  Install the catalog from a pushed branch instead of the
                current checkout. Shallow-clones the repo at <name> into a
                deterministic cache directory (~/.nexus-hub/branches/<name>/),
                then runs the install from that checkout -- the user's working
                copy is never touched. Combine with -Check to print the resolved
                cache path and clone source without cloning (a probe).
  -Help         Show this help and exit.
"@ | Write-Host
    exit 0
}

$ErrorActionPreference = "Stop"

# Map an arbitrary git branch name to a filesystem-safe cache token (the
# PowerShell sibling of installer.sh's sanitize_branch_name): every character
# outside [A-Za-z0-9._-] becomes '-', parent-dir tokens are neutralized, and a
# leading dot/dash is stripped so the result is never a hidden dir or a path-
# traversal vector.
function Get-SanitizedBranchName {
    param([string]$Raw)
    $s = ($Raw -replace '[^A-Za-z0-9._-]', '-')
    $s = $s -replace '\.\.', '-'
    $s = $s -replace '^[-.]', ''
    if ([string]::IsNullOrEmpty($s)) { $s = 'branch' }
    return $s
}

# --- Version ---
# Single source of truth for the installer banner version label.
# Keep in sync with .claude-plugin/plugin.json and CHANGELOG.md.
$script:NexusHubVersion = "3.2.2"

$Host.UI.RawUI.WindowTitle = "Nexus-Hub Installer"
$script:InstallerTitle = "Nexus-Hub Installer"
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
#
# Modernized in v2.1.0: dropped the 120-char banner / dash rule style in favor
# of lightweight typographical accents that read cleanly in narrow and wide
# terminals alike. Function names are preserved so call sites and smoke tests
# do not need to change.

function Write-CenteredBanner {
    param(
        [string]$Text,
        [string]$Color = "Cyan",
        [string]$BorderChar = "-"  # accepted for backwards compat; not used
    )
    Restore-Title
    Write-Host ""
    Write-Host "▶ $Text" -ForegroundColor $Color
}

function Write-SubSectionBanner {
    param(
        [string]$Text,
        [string]$Color = "Yellow"
    )
    Restore-Title
    Write-Host ""
    Write-Host "  · $Text" -ForegroundColor $Color
}

function Get-ProviderColor {
    param([string]$Provider)
    $color = switch ($Provider) {
        # Provider-level headers (v2.1.0+)
        "ANTHROPIC"       { "DarkYellow" }
        "OPENAI"          { "DarkMagenta" }
        "GOOGLE"          { "Blue" }
        "MICROSOFT"       { "DarkCyan" }
        "ANYSPHERE"       { "Magenta" }
        "OPENCODE"        { "Cyan" }
        "NEXUS"           { "DarkBlue" }
        Default           { "White" }
    }
    return $color
}

function Write-Header {
    param([string]$Provider)
    $color = Get-ProviderColor -Provider $Provider
    Write-Host ""
    Write-Host "  ▸ $Provider" -ForegroundColor $color
}

function Write-Item {
    param(
        [string]$Message,
        [string]$Color = "White",
        [int]$Indent = 2
    )
    $spaces = " " * $Indent
    Write-Host "${spaces}$Message" -ForegroundColor $Color
}

function Read-Prompt {
    param(
        [string]$Message,
        [int]$Indent = 2
    )
    $spaces = " " * $Indent
    Write-Host "${spaces}${Message}: " -NoNewline -ForegroundColor "Yellow"
    return Read-Host
}

# --- Interaction Helpers ---

function Select-Platforms {
    param([string]$PhaseName)
    Write-Host ""
    Write-Host "Select providers to install for $PhaseName (comma separated):" -ForegroundColor White
    Write-Host "A - ALL (Recommended)"
    Write-Host "1 - Anthropic   ─ Claude Code"
    Write-Host "2 - OpenAI      ─ Codex"
    Write-Host "3 - Google      ─ Gemini, Antigravity 1.0, Antigravity 2.0, Gemini CLI"
    Write-Host "4 - Microsoft   ─ GitHub Copilot"
    Write-Host "5 - Anysphere   ─ Cursor"
    Write-Host "6 - OpenCode    ─ OpenCode"
    Write-Host "7 - Nexus       ─ Nexus-AI (Local Desktop Studio)"

    # Provider → set of internal platform keys. The 4 legacy platforms
    # (CLAUDE / GEMINI / CODEX / COPILOT) trigger the inline installer
    # blocks; the rest flow through the integration runner. GEMINI bundles
    # Gemini IDE + Antigravity 1.0 (they share one legacy block).
    $providerMap = [ordered]@{
        "1" = @("CLAUDE")
        "2" = @("CODEX")
        "3" = @("GEMINI", "ANTIGRAVITY2", "GEMINI_CLI")
        "4" = @("COPILOT")
        "5" = @("CURSOR")
        "6" = @("OPENCODE")
        "7" = @("NEXUS_AI")
    }

    $allPlatforms = @()
    foreach ($k in $providerMap.Keys) { $allPlatforms += $providerMap[$k] }

    $inputStr = Read-Prompt "Selection [A, 1-7]"
    if ([string]::IsNullOrWhiteSpace($inputStr)) { return $allPlatforms }

    $selected = @()
    $sawAll = $false

    foreach ($token in $inputStr.Split(',')) {
        $key = $token.Trim().ToUpper()
        if ($key -eq "A") {
            $sawAll = $true
        } elseif ($providerMap.Contains($key)) {
            $selected += $providerMap[$key]
        }
    }

    if ($sawAll -or $selected.Count -eq 0) { return $allPlatforms }
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

# Recursively copies an entire folder tree from $Source to $Destination via robocopy /MIR.
#
# Per-skill bundled resources (scripts/, references/, assets/) under
# catalog\skills\<cat>\<name>\ are copied recursively as part of the parent
# skill folder copy - robocopy /MIR mirrors arbitrary subdirectory depth.
# This is the auto-distribution behavior documented in AGENTS.md
# "Per-skill Bundled Resources"; no per-skill explicit-name copy step is
# needed for skill-bundled content. Lockstep parity with the bash installer's
# safe_folder_copy (rsync -a / cp -R).
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

    # compress-output.sh is the other PreToolUse Bash hook; it ships alongside
    # git-guardrails because the settings.json merge below pulls the whole
    # PreToolUse array (which now includes it). It is opt-in / default-off
    # (inert unless NEXUS_CONTEXT_COMPRESS=1), so copying the file is harmless.
    Safe-Copy -Source "$RepoRoot\catalog\hooks\compress-output.sh" -Destination (Join-Path $hooksDir "compress-output.sh") -Confirm:$true -CustomMessage "✓ $Scope output-compression hook installed at: $hooksDir"

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

    # Core defaults seeded from the template: effortLevel + model scalars, plus the
    # env.CLAUDE_CODE_EFFORT_LEVEL override. The env var is the highest-precedence
    # effort lever per the Claude Code docs, so it forces the effort past the VS
    # Code effort toggle (which otherwise resets to the model default each session).
    $content = Get-Content $settingsFile -Raw
    try {
        $existingJson = $content | ConvertFrom-Json
        $templateJson = Get-Content $templateFile -Raw | ConvertFrom-Json
        $coreKeys = @("effortLevel", "model")
        $applied = @()

        foreach ($key in $coreKeys) {
            if (-not $templateJson.PSObject.Properties[$key]) { continue }
            $templateValue = $templateJson.$key
            if ($existingJson.PSObject.Properties[$key] -and $existingJson.$key -eq $templateValue) {
                continue
            }
            if ($existingJson.PSObject.Properties[$key]) {
                $existingJson.$key = $templateValue
            } else {
                $existingJson | Add-Member -NotePropertyName $key -NotePropertyValue $templateValue
            }
            $applied += "${key}: ${templateValue}"
        }

        # Deep-merge the env effort override, preserving any sibling env vars.
        if ($templateJson.PSObject.Properties["env"] -and $templateJson.env.PSObject.Properties["CLAUDE_CODE_EFFORT_LEVEL"]) {
            $envEffort = $templateJson.env.CLAUDE_CODE_EFFORT_LEVEL
            if (-not $existingJson.PSObject.Properties["env"]) {
                $existingJson | Add-Member -NotePropertyName "env" -NotePropertyValue ([PSCustomObject]@{})
            }
            if ($existingJson.env.PSObject.Properties["CLAUDE_CODE_EFFORT_LEVEL"]) {
                if ($existingJson.env.CLAUDE_CODE_EFFORT_LEVEL -ne $envEffort) {
                    $existingJson.env.CLAUDE_CODE_EFFORT_LEVEL = $envEffort
                    $applied += "env.CLAUDE_CODE_EFFORT_LEVEL: $envEffort"
                }
            } else {
                $existingJson.env | Add-Member -NotePropertyName "CLAUDE_CODE_EFFORT_LEVEL" -NotePropertyValue $envEffort
                $applied += "env.CLAUDE_CODE_EFFORT_LEVEL: $envEffort"
            }
        }

        if ($applied.Count -eq 0) {
            Write-Item -Message "✓ Core settings (effortLevel, model, env effort) already current in settings.json" -Color "DarkGreen"
            return
        }
        $existingJson | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
        Write-Item -Message "✓ $Scope settings.json updated core settings ($($applied -join ', '))" -Color "DarkGreen"
    }
    catch {
        Write-Item -Message "Warning: Could not set core settings ($($_.Exception.Message))" -Color "Yellow"
        Write-Item -Message "  Manually copy effortLevel/model/env from $templateFile to $settingsFile" -Color "Yellow"
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

# Ensure the OpenAI Codex CLI is present before writing its config. Nexus-Hub
# configures Codex permissions on every install; when the CLI is absent the
# config is never validated until the user installs Codex later, so install it
# now (via npm) when missing. Non-fatal: a failed or skipped install only prints
# a hint and never aborts the installer.
function Ensure-CodexCli {
    if (Get-Command codex -ErrorAction SilentlyContinue) {
        Write-Item -Message "[OK] Codex CLI detected" -Color "DarkGreen"
        return
    }
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Item -Message "Codex CLI not found; installing (npm install -g @openai/codex)..." -Color "Gray"
        try {
            & npm install -g @openai/codex 2>$null | Out-Null
        } catch {}
        if (Get-Command codex -ErrorAction SilentlyContinue) {
            Write-Item -Message "[OK] Codex CLI installed" -Color "DarkGreen"
        } else {
            Write-Item -Message "Warning: could not auto-install Codex CLI. Install manually: npm install -g @openai/codex" -Color "Yellow"
        }
    } else {
        Write-Item -Message "Codex CLI not found and npm is unavailable. Install Node.js, then run: npm install -g @openai/codex" -Color "Yellow"
    }
}

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
            Ensure-CodexCli
            $configDir = Join-Path $env:USERPROFILE ".codex"
            $configFile = Join-Path $configDir "config.toml"
            $templateFile = Join-Path $permDir "codex-permissions.toml"

            if (-not (Test-Path $templateFile)) {
                Write-Item -Message "Skip: Codex permissions template not found" -Color "DarkGray"
                return
            }

            if (Test-Path $configFile) {
                $content = Get-Content $configFile -Raw

                # Repair an already-broken config: [permissions.*] present but
                # default_permissions missing -> the newer Codex CLI refuses to
                # load it. Insert the key before the FIRST table header of any
                # kind (the only valid spot for a root-level key in TOML).
                if ($content -match '(?m)^\[permissions' -and $content -notmatch 'default_permissions') {
                    Copy-Item -Path $configFile -Destination "$configFile.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')" -Force
                    # Instance .Replace(input, replacement, count) caps at one insert;
                    # [regex]::Replace(...)'s 4th arg is RegexOptions, not a count.
                    $content = ([regex]'(?m)^(\[)').Replace($content, "default_permissions = `"default`"`r`n`r`n`$1", 1)
                    # WriteAllText writes UTF-8 WITHOUT a BOM; Set-Content -Encoding UTF8
                    # on PS 5.1 prepends a BOM that breaks strict TOML parsers.
                    [System.IO.File]::WriteAllText($configFile, $content)
                    Write-Item -Message "[OK] Repaired Codex config.toml: inserted missing default_permissions" -Color "DarkGreen"
                }

                # Already fully configured (managed block complete, incl. default_permissions)?
                if ($content -match 'permissions\.default\.network' -and $content -match 'allowed_domains' -and $content -match 'default_permissions') {
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
                if ($existingContent -notmatch 'default_permissions') {
                    # Required by the newer Codex permissions system: a config with
                    # [permissions.*] but no default_permissions fails to load.
                    $sectionsToAdd = @("default_permissions = `"default`"") + $sectionsToAdd
                }
                if ($existingContent -notmatch 'approval_policy') {
                    $sectionsToAdd = @("approval_policy = `"on-request`"") + $sectionsToAdd
                }

                if ($sectionsToAdd.Count -gt 0) {
                    $appendContent = "`n`n# --- Nexus-Hub auto-approve permissions ---`n" + ($sectionsToAdd -join "`n`n")
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

    # Per-provider install blocks. The Select-Platforms menu groups by
    # organization (Anthropic / OpenAI / Google / Microsoft / Anysphere /
    # OpenCode / Nexus); the install output mirrors that grouping so each
    # provider has a single colored Write-Header line and its platforms
    # listed underneath.

    # --- Anthropic -- Claude Code ----------------------------------------
    if ($platforms -contains "CLAUDE") {
        Write-Header -Provider "ANTHROPIC"
        Write-Item -Message "Claude Code" -Color "Gray"
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
        $script:NonObviousTooling = "- (configure per project with /setup project)"
        # DF-001: the registry runner renders CLAUDE.md (marker-merged, full
        # placeholder substitution). -InstructionOnly leaves the catalog mirror
        # to the Safe-Folder-Copy block below.
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "claude" -DisplayName "CLAUDE.md (instruction file)" -InstructionOnly

        Safe-Folder-Copy -Source "$RepoRoot\catalog\skills"   -Destination (Join-Path $globalClaude "skills")   -CustomMessage "✓ Skills catalog installed at: $(Join-Path $globalClaude "skills")"
        Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $globalClaude "commands") -CustomMessage "✓ Commands installed at: $(Join-Path $globalClaude "commands")"
        Safe-Folder-Copy -Source "$RepoRoot\catalog\agents"   -Destination (Join-Path $globalClaude "agents")   -CustomMessage "✓ Agents installed at: $(Join-Path $globalClaude "agents")"
        Safe-Folder-Copy -Source "$RepoRoot\catalog\rules"    -Destination (Join-Path $globalClaude "rules")    -CustomMessage "✓ Rules installed at: $(Join-Path $globalClaude "rules")"

        $mcpConfigDest = Join-Path $globalClaude "mcp-configs"
        if (-not (Test-Path $mcpConfigDest)) { New-Item -ItemType Directory -Force -Path $mcpConfigDest | Out-Null }
        Safe-Copy -Source "$RepoRoot\catalog\mcp-configs\mcp-servers.json" -Destination (Join-Path $mcpConfigDest "mcp-servers.json") -Confirm:$false -CustomMessage "✓ MCP server config installed at: $mcpConfigDest"

        Install-GitGuardrails    -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"
        Install-UsageDisplay     -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"
        Install-RequireDescription -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"
        Install-CoreSettings     -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global"
    }

    # --- OpenAI -- Codex --------------------------------------------------
    if ($platforms -contains "CODEX") {
        Write-Header -Provider "OPENAI"
        Write-Item -Message "Codex" -Color "Gray"
        $globalCodexDir = Join-Path $env:USERPROFILE ".codex"
        if (-not (Test-Path $globalCodexDir)) { New-Item -ItemType Directory -Force -Path $globalCodexDir | Out-Null }

        Safe-Folder-Copy -Source "$RepoRoot\catalog\skills"   -Destination (Join-Path $globalCodexDir "skills")   -CustomMessage "✓ Skills catalog installed at: $(Join-Path $globalCodexDir "skills")"
        Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $globalCodexDir "prompts")  -CustomMessage "✓ Custom prompts installed at: $(Join-Path $globalCodexDir "prompts")"

        # AGENTS.md (open standard read by Codex, Jules, Cursor, Aider, OpenCode)
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "codex" -DisplayName "AGENTS.md (instruction file)" -InstructionOnly
    }

    # --- Google -- Gemini / Antigravity 1.0 + 2.0 / Gemini CLI -----------
    $googleHas = ($platforms -contains "GEMINI") -or ($platforms -contains "ANTIGRAVITY2") -or ($platforms -contains "GEMINI_CLI")
    if ($googleHas) {
        Write-Header -Provider "GOOGLE"

        if ($platforms -contains "GEMINI") {
            Write-Item -Message "Gemini IDE + Antigravity 1.0" -Color "Gray"
            $globalGeminiDir = Join-Path $env:USERPROFILE ".gemini"
            if (-not (Test-Path $globalGeminiDir)) { New-Item -ItemType Directory -Force -Path $globalGeminiDir | Out-Null }

            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "gemini" -DisplayName "GEMINI.md (instruction file)" -InstructionOnly

            # Antigravity 2.0 + CLI: the antigravity2 integration (below) owns the
            # entire Antigravity mirror -- it flattens skills to skills/<name>/SKILL.md,
            # mirrors commands to workflows/, installs the curated hooks + hooks.json,
            # and writes to BOTH the IDE global root (~/.gemini/antigravity) and the
            # CLI global root (~/.gemini/antigravity-cli). The previous verbatim
            # antigravity-cli copies buried every SKILL.md under a category folder the
            # IDE could not read. (The Gemini IDE ~/.gemini/skills mirror below and the
            # Antigravity 1.0 global_workflows mirror are separate, untouched surfaces.)
            Safe-Folder-Copy -Source "$RepoRoot\catalog\skills"   -Destination (Join-Path $globalGeminiDir "skills")    -CustomMessage "✓ Skills catalog installed at: $(Join-Path $globalGeminiDir "skills")"

            $globalAntigravityWorkflows = Join-Path $globalGeminiDir "antigravity\global_workflows"
            if (-not (Test-Path $globalAntigravityWorkflows)) { New-Item -ItemType Directory -Force -Path $globalAntigravityWorkflows | Out-Null }
            Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination $globalAntigravityWorkflows -CustomMessage "✓ Antigravity workflows installed at: $globalAntigravityWorkflows"
        }

        if ($platforms -contains "ANTIGRAVITY2") {
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "antigravity2" -DisplayName "Antigravity 2.0 + CLI"
            Write-Item -Message "Antigravity 2.0 IDE: slash commands appear only inside an OPEN project folder (its .agents/workflows/). Run a workspace/project install in your repo so the commands show; a global-only install is not scanned by the IDE for slash commands." -Color "Yellow"
        }
        if ($platforms -contains "GEMINI_CLI") {
            if ($Enterprise) {
                Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "gemini-cli" -DisplayName "Gemini CLI (enterprise)"
            }
            else {
                Write-Item -Message "Gemini CLI: skipped (sunset on 2026-06-18 for free / Google AI Pro / Ultra / GitHub-installed users). Re-run with -Enterprise to install (requires paid Gemini API key); Antigravity CLI above covers the same functionality." -Color "Yellow"
            }
        }
    }

    # --- Microsoft -- GitHub Copilot -------------------------------------
    if ($platforms -contains "COPILOT") {
        Write-Header -Provider "MICROSOFT"
        Write-Item -Message "GitHub Copilot" -Color "Gray"
        Write-Item -Message "Check skipped (no global file support on Windows)." -Color "DarkGray"
    }

    # --- Anysphere -- Cursor ---------------------------------------------
    if ($platforms -contains "CURSOR") {
        Write-Header -Provider "ANYSPHERE"
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "cursor" -DisplayName "Cursor"
    }

    # --- OpenCode --------------------------------------------------------
    if ($platforms -contains "OPENCODE") {
        Write-Header -Provider "OPENCODE"
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "opencode" -DisplayName "OpenCode"
    }

    # --- Nexus -- Nexus-AI (Local Desktop Studio) ------------------------
    if ($platforms -contains "NEXUS_AI") {
        Write-Header -Provider "NEXUS"
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "nexus-ai" -DisplayName "Nexus-AI (Local Desktop Studio)"
    }

    # --- Auto-Approve Permissions sub-section ---
    # Permissions only apply to the legacy 4 (CLAUDE / GEMINI / CODEX /
    # COPILOT); the registry-driven platforms do not ship their own
    # auto-approve configs yet. Mirrored to provider headers for visual
    # consistency with the install-skills section above.
    Write-SubSectionBanner -Text "Auto-Approve Permissions"

    if ($platforms -contains "CLAUDE") {
        Write-Header -Provider "ANTHROPIC"
        Install-Permissions -RepoRoot $RepoRoot -Platform "CLAUDE" -Scope "Global"
    }
    if ($platforms -contains "CODEX") {
        Write-Header -Provider "OPENAI"
        Install-Permissions -RepoRoot $RepoRoot -Platform "CODEX" -Scope "Global"
    }
    if ($platforms -contains "GEMINI") {
        Write-Header -Provider "GOOGLE"
        Install-Permissions -RepoRoot $RepoRoot -Platform "GEMINI" -Scope "Global"
    }
    if ($platforms -contains "COPILOT") {
        Write-Header -Provider "MICROSOFT"
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

# Render-Template was removed in v2.3.0 / Phase 7 (DF-001). Instruction-file
# rendering now flows through scripts/lib/integrations/runner.py via
# Invoke-RegistryPlatform (single renderer shared with installer.sh), which
# substitutes the same placeholder set and marker-merges the body. The detected
# script globals (ProjectName, BuildCmd, OSContext, ...) are threaded to the
# runner by Invoke-RegistryPlatform.

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

        # --- Install Logic (provider-grouped) ---

        # --- Anthropic -- Claude Code ------------------------------------
        if ($workspacePlatforms -contains "CLAUDE") {
            Write-Header -Provider "ANTHROPIC"
            Write-Item -Message "Claude Code" -Color "Gray"
            $claudeDir = Join-Path $targetPath ".claude"

            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "claude" -DisplayName "CLAUDE.md (instruction file)" -Languages ($languages -join ',') -InstructionOnly

            Safe-Folder-Copy -Source "$RepoRoot\catalog\skills"   -Destination (Join-Path $claudeDir "skills")   -CustomMessage "✓ Skills catalog installed at: $(Join-Path $claudeDir "skills")"
            Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $claudeDir "commands") -CustomMessage "✓ Commands installed at: $(Join-Path $claudeDir "commands")"
            Safe-Folder-Copy -Source "$RepoRoot\catalog\agents"   -Destination (Join-Path $claudeDir "agents")   -CustomMessage "✓ Agents installed at: $(Join-Path $claudeDir "agents")"
            Safe-Folder-Copy -Source "$RepoRoot\catalog\rules"    -Destination (Join-Path $claudeDir "rules")    -CustomMessage "✓ Rules installed at: $(Join-Path $claudeDir "rules")"

            $mcpConfigDestWs = Join-Path $claudeDir "mcp-configs"
            if (-not (Test-Path $mcpConfigDestWs)) { New-Item -ItemType Directory -Force -Path $mcpConfigDestWs | Out-Null }
            Safe-Copy -Source "$RepoRoot\catalog\mcp-configs\mcp-servers.json" -Destination (Join-Path $mcpConfigDestWs "mcp-servers.json") -Confirm:$false -CustomMessage "✓ MCP server config installed at: $mcpConfigDestWs"

            Safe-Folder-Copy -Source "$RepoRoot\catalog\context" -Destination (Join-Path $claudeDir "context") -CustomMessage "✓ Context installed at: $(Join-Path $claudeDir "context")"
            Safe-Folder-Copy -Source "$RepoRoot\catalog\memory"  -Destination (Join-Path $claudeDir "memory")  -CustomMessage "✓ Memory installed at: $(Join-Path $claudeDir "memory")"

            Install-GitGuardrails    -RepoRoot $RepoRoot -TargetClaudeDir $claudeDir -Scope "Workspace"
            Install-UsageDisplay     -RepoRoot $RepoRoot -TargetClaudeDir $claudeDir -Scope "Workspace"
            Install-RequireDescription -RepoRoot $RepoRoot -TargetClaudeDir $claudeDir -Scope "Workspace"
        }

        # --- OpenAI -- Codex ---------------------------------------------
        if ($workspacePlatforms -contains "CODEX") {
            Write-Header -Provider "OPENAI"
            Write-Item -Message "Codex" -Color "Gray"
            $codexDir = Join-Path $targetPath ".codex"
            if (-not (Test-Path $codexDir)) { New-Item -ItemType Directory -Force -Path $codexDir | Out-Null }

            Safe-Folder-Copy -Source "$RepoRoot\catalog\skills"   -Destination (Join-Path $codexDir "skills")  -CustomMessage "✓ Skills catalog installed at: $(Join-Path $codexDir "skills")"
            Safe-Folder-Copy -Source "$RepoRoot\catalog\commands" -Destination (Join-Path $codexDir "prompts") -CustomMessage "✓ Custom prompts installed at: $(Join-Path $codexDir "prompts")"

            # AGENTS.md at project root (open standard read by Codex, Jules, Cursor, Aider, OpenCode)
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "codex" -DisplayName "AGENTS.md (instruction file)" -Languages ($languages -join ',') -InstructionOnly
        }

        # --- Google -- Gemini / Antigravity 1.0 + 2.0 / Gemini CLI ------
        $googleWsHas = ($workspacePlatforms -contains "GEMINI") -or ($workspacePlatforms -contains "ANTIGRAVITY2") -or ($workspacePlatforms -contains "GEMINI_CLI")
        if ($googleWsHas) {
            Write-Header -Provider "GOOGLE"

            if ($workspacePlatforms -contains "GEMINI") {
                Write-Item -Message "Gemini IDE + Antigravity 1.0" -Color "Gray"
                $geminiDir = Join-Path $targetPath ".gemini"
                if (-not (Test-Path $geminiDir)) { New-Item -ItemType Directory -Force -Path $geminiDir | Out-Null }

                Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "gemini" -DisplayName "GEMINI.md (instruction file)" -Languages ($languages -join ',') -InstructionOnly

                # Antigravity 2.0 + CLI: the antigravity2 integration (below) owns the
                # .agents/ mirror -- it flattens skills to .agents/skills/<name>/SKILL.md,
                # mirrors commands to .agents/workflows/, and installs .agents/hooks/ +
                # .agents/hooks.json. The previous verbatim copies buried SKILL.md under a
                # category folder the IDE could not read.
            }

            if ($workspacePlatforms -contains "ANTIGRAVITY2") {
                Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "antigravity2" -DisplayName "Antigravity 2.0 + CLI"
            }
            if ($workspacePlatforms -contains "GEMINI_CLI") {
                if ($Enterprise) {
                    Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "gemini-cli" -DisplayName "Gemini CLI (enterprise)"
                }
                else {
                    Write-Item -Message "Gemini CLI: skipped (sunset on 2026-06-18 for free / Google AI Pro / Ultra / GitHub-installed users). Re-run with -Enterprise to install (requires paid Gemini API key); Antigravity CLI above covers the same functionality." -Color "Yellow"
                }
            }
        }

        # --- Prepare Copilot/Cursor instruction body (used below) -------
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

        # --- Microsoft -- GitHub Copilot --------------------------------
        if ($workspacePlatforms -contains "COPILOT") {
            Write-Header -Provider "MICROSOFT"
            Write-Item -Message "GitHub Copilot" -Color "Gray"
            $copilotDir = Join-Path $targetPath ".github"
            if (-not (Test-Path $copilotDir)) { New-Item -ItemType Directory -Force -Path $copilotDir | Out-Null }
            $copilotFile = Join-Path $copilotDir "copilot-instructions.md"

            $doWrite = $true
            if ((Test-Path $copilotFile)) {
                if ($script:OverwriteMode -eq "ALL") {
                    # Overwrite
                }
                elseif ($script:OverwriteMode -eq "NONE") {
                    Write-Item -Message "File exists: copilot-instructions.md (skipped)" -Color "DarkGray"
                    $doWrite = $false
                }
                else {
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

        # --- Anysphere -- Cursor ----------------------------------------
        if ($workspacePlatforms -contains "CURSOR") {
            Write-Header -Provider "ANYSPHERE"
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "cursor" -DisplayName "Cursor"
        }

        # --- OpenCode ---------------------------------------------------
        if ($workspacePlatforms -contains "OPENCODE") {
            Write-Header -Provider "OPENCODE"
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "opencode" -DisplayName "OpenCode"
        }

        # --- Nexus -- Nexus-AI ------------------------------------------
        if ($workspacePlatforms -contains "NEXUS_AI") {
            Write-Header -Provider "NEXUS"
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "nexus-ai" -DisplayName "Nexus-AI (Local Desktop Studio)"
        }

        Write-Host ""
}

function Resolve-PythonExecutable {
    if (Get-Command python -ErrorAction SilentlyContinue)  { return "python" }
    if (Get-Command py -ErrorAction SilentlyContinue)      { return "py" }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return "python3" }
    return $null
}

function Invoke-RegistryPlatform {
    param(
        [string]$RepoRoot,
        [string]$Scope,            # "global" or "workspace"
        [string]$TargetPath,       # used for workspace scope only
        [string]$IntegrationKey,   # registry key, e.g. "antigravity2"
        [string]$DisplayName,      # human-readable label printed as a sub-item
        [string]$Languages = "",   # csv; appends coding-snippet fragments
        [switch]$InstructionOnly   # render only the instruction file (skip catalog mirror)
    )
    $runner = Join-Path $RepoRoot "scripts\lib\integrations\runner.py"
    if (-not (Test-Path $runner)) { return }
    $py = Resolve-PythonExecutable
    if (-not $py) {
        Write-Item -Message "Python not found -- skipping $DisplayName." -Color "DarkYellow"
        return
    }

    Write-Item -Message "$DisplayName" -Color "Gray"
    $argsList = @($runner, "install", "--scope", $Scope, "--integrations", $IntegrationKey, "--quiet")
    if ($Scope -eq "workspace") {
        $argsList += @("--target", $TargetPath)
    }
    if ($script:OverwriteMode -eq "ALL") { $argsList += "--overwrite" }
    if ($InstructionOnly) { $argsList += "--instruction-only" }
    if ($Languages) { $argsList += @("--languages", $Languages) }
    # Thread the instruction-template placeholders from the detected script
    # globals so the registry renders the same instruction body the legacy
    # Render-Template produced (DF-001).
    $argsList += @("--project-name", "$($script:ProjectName)")
    $argsList += @("--var", "PRIMARY_LANGUAGE=$($script:PrimaryLanguage)")
    $argsList += @("--var", "PACKAGE_MANAGER=$($script:PackageManager)")
    $argsList += @("--var", "BUILD_TOOL=$($script:BuildTool)")
    $argsList += @("--var", "TEST_FRAMEWORK=$($script:TestFramework)")
    $argsList += @("--var", "LINT_TOOL=$($script:LintTool)")
    $argsList += @("--var", "BUILD_CMD=$($script:BuildCmd)")
    $argsList += @("--var", "TEST_CMD=$($script:TestCmd)")
    $argsList += @("--var", "LINT_CMD=$($script:LintCmd)")
    $argsList += @("--var", "NON_OBVIOUS_TOOLING=$($script:NonObviousTooling)")
    $argsList += @("--var", "OS_CONTEXT=$($script:OSContext)")

    & $py @argsList
    if ($LASTEXITCODE -ne 0) {
        Write-Item -Message "$DisplayName install reported non-zero exit; continuing." -Color "Yellow"
    } else {
        Write-Item -Message "✓ Installed ($Scope scope)" -Color "DarkGreen"
    }
}

function Install-VSCodeExtensions {
    param ($RepoRoot)
    Write-Host ""
    Write-Host "  > Claude Usage Monitor" -ForegroundColor DarkYellow

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
        & code --uninstall-extension "nexus-hub.claude-usage-monitor" 2>$null | Out-Null
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
    Write-Item -Message "Nexus-Hub can generate professional Word (.docx) and PowerPoint (.pptx)" -Color "White"
    Write-Item -Message "reports from Markdown files using the /research report command." -Color "White"
    Write-Host ""

    # Ensure global directories exist
    $nexusHome = Join-Path $env:USERPROFILE ".nexus-hub"
    $templatesDest = Join-Path $nexusHome "templates\documentation"
    $scriptsDest = Join-Path $nexusHome "scripts"

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
    # (nexus-skill-server, nexus-code-search, nexus-web-fetch). Pure-local.
    $benchmarkSource = Join-Path $RepoRoot "scripts\nexus_mcp_benchmark.py"
    if (Test-Path $benchmarkSource) {
        Safe-Copy -Source $benchmarkSource -Destination (Join-Path $scriptsDest "nexus_mcp_benchmark.py") -Confirm:$true -CustomMessage "✓ MCP benchmark installed at: $scriptsDest\nexus_mcp_benchmark.py"
    }

    # Copy skill-eval-loop dispatcher scripts (v1.2.0-wip / Phase 5 / A6 + A7).
    # Three repo-level scripts that work alongside the catalog/skills/workflow/
    # skill-eval-loop/ skill: the iteration aggregator, the browser-based
    # viewer, and the description optimizer. All three follow the v1.1.3
    # four-hook precedent for CLI dispatch (single dispatcher with --cli
    # flag, no cross-CLI fallback, parity-test enforced via pytest). Lockstep
    # with the same block in scripts/installer.sh.
    $evalAggregatorSource = Join-Path $RepoRoot "scripts\aggregate_benchmark.py"
    if (Test-Path $evalAggregatorSource) {
        Safe-Copy -Source $evalAggregatorSource -Destination (Join-Path $scriptsDest "aggregate_benchmark.py") -Confirm:$true -CustomMessage "✓ Eval-loop benchmark aggregator installed at: $scriptsDest\aggregate_benchmark.py"
    }
    $evalViewerSource = Join-Path $RepoRoot "scripts\skill_eval_viewer.py"
    if (Test-Path $evalViewerSource) {
        Safe-Copy -Source $evalViewerSource -Destination (Join-Path $scriptsDest "skill_eval_viewer.py") -Confirm:$true -CustomMessage "✓ Eval-loop browser viewer installed at: $scriptsDest\skill_eval_viewer.py"
    }
    $evalOptimizerSource = Join-Path $RepoRoot "scripts\optimize_skill_description.py"
    if (Test-Path $evalOptimizerSource) {
        Safe-Copy -Source $evalOptimizerSource -Destination (Join-Path $scriptsDest "optimize_skill_description.py") -Confirm:$true -CustomMessage "✓ Skill-description optimizer installed at: $scriptsDest\optimize_skill_description.py"
    }

    # Copy .skill packager script (v1.2.0-wip / Phase 7 / A16). Produces a
    # portable .skill ZIP archive from a catalog\skills\<cat>\<name>\ directory
    # for distribution to Claude.ai or the Anthropic API skill-upload endpoint
    # - delivery channels Nexus-Hub does not currently reach. Lockstep with
    # the same block in scripts\installer.sh.
    $skillPackagerSource = Join-Path $RepoRoot "scripts\package_skill.py"
    if (Test-Path $skillPackagerSource) {
        Safe-Copy -Source $skillPackagerSource -Destination (Join-Path $scriptsDest "package_skill.py") -Confirm:$true -CustomMessage "✓ Skill packager installed at: $scriptsDest\package_skill.py"
    }

    # Copy nexus-hub affected CLI dispatcher (v2.2.0 / codegraph Phase 5 /
    # T032). Mirror of the bash block in scripts\installer.sh. Wraps the
    # nexus-code-search code_affected_tests graph query so users can pipe
    # `git diff --name-only` into a test-impact query without booting the
    # MCP server.
    $affectedSource = Join-Path $RepoRoot "scripts\nexus_hub_affected.py"
    if (Test-Path $affectedSource) {
        Safe-Copy -Source $affectedSource -Destination (Join-Path $scriptsDest "nexus_hub_affected.py") -Confirm:$true -CustomMessage "✓ Affected-tests CLI installed at: $scriptsDest\nexus_hub_affected.py"
    }

    # Copy v2.3.0 CI validators (Phase 2 / T004-T005). Mirror of the bash
    # block in scripts\installer.sh. Four standalone static validators:
    # validate_no_personal_paths.py (leaked /Users/<name> or C:\Users\<name>
    # paths), validate_unicode_safety.py (Trojan Source + zero-width chars),
    # scan_supply_chain_iocs.py (curl-pipe-bash, lifecycle shell-outs,
    # floating GitHub Action refs, typosquats), validate_workflow_security.py
    # (pull_request_target abuse, github.event injection, write-all perms).
    $noPathsSource = Join-Path $RepoRoot "scripts\validate_no_personal_paths.py"
    if (Test-Path $noPathsSource) {
        Safe-Copy -Source $noPathsSource -Destination (Join-Path $scriptsDest "validate_no_personal_paths.py") -Confirm:$true -CustomMessage "✓ No-personal-paths validator installed at: $scriptsDest\validate_no_personal_paths.py"
    }
    $unicodeSource = Join-Path $RepoRoot "scripts\validate_unicode_safety.py"
    if (Test-Path $unicodeSource) {
        Safe-Copy -Source $unicodeSource -Destination (Join-Path $scriptsDest "validate_unicode_safety.py") -Confirm:$true -CustomMessage "✓ Unicode-safety validator installed at: $scriptsDest\validate_unicode_safety.py"
    }
    $iocsSource = Join-Path $RepoRoot "scripts\scan_supply_chain_iocs.py"
    if (Test-Path $iocsSource) {
        Safe-Copy -Source $iocsSource -Destination (Join-Path $scriptsDest "scan_supply_chain_iocs.py") -Confirm:$true -CustomMessage "✓ Supply-chain IOC scanner installed at: $scriptsDest\scan_supply_chain_iocs.py"
    }
    $workflowSource = Join-Path $RepoRoot "scripts\validate_workflow_security.py"
    if (Test-Path $workflowSource) {
        Safe-Copy -Source $workflowSource -Destination (Join-Path $scriptsDest "validate_workflow_security.py") -Confirm:$true -CustomMessage "✓ Workflow-security validator installed at: $scriptsDest\validate_workflow_security.py"
    }
    # validate_solution_frontmatter.py (v2.4.0): parser-safety linter for
    # solution-knowledge-base docs (docs/solutions). Mirror of the bash block.
    $solutionFmSource = Join-Path $RepoRoot "scripts\validate_solution_frontmatter.py"
    if (Test-Path $solutionFmSource) {
        Safe-Copy -Source $solutionFmSource -Destination (Join-Path $scriptsDest "validate_solution_frontmatter.py") -Confirm:$true -CustomMessage "✓ Solution-frontmatter validator installed at: $scriptsDest\validate_solution_frontmatter.py"
    }
    # check_version_sync.py (v3.0.0): version-drift guard. Reads the canonical
    # version from .claude-plugin\plugin.json and asserts every other
    # version-carrying surface (both installers, marketplace.json, the latest
    # CHANGELOG heading, README/AGENTS markers) matches it. Stdlib-only, so it
    # is a single cross-platform .py file with no .ps1 sibling (NI-v24-1
    # convention). Mirror of the bash block in scripts\installer.sh.
    $versionSyncSource = Join-Path $RepoRoot "scripts\check_version_sync.py"
    if (Test-Path $versionSyncSource) {
        Safe-Copy -Source $versionSyncSource -Destination (Join-Path $scriptsDest "check_version_sync.py") -Confirm:$true -CustomMessage "✓ Version-sync guard installed at: $scriptsDest\check_version_sync.py"
    }
    # scan_skill_security.py (v3.0.0): thin CLI launcher for the
    # nexus-skill-scanner static skill-security engine (extensions\nexus-skill-scanner).
    # Stdlib-only launcher; it locates the bundled package src under extensions\.
    # Single cross-platform .py file with no .ps1 sibling (NI-v24-1 convention).
    # Mirror of the bash block in scripts\installer.sh.
    $scanSkillSource = Join-Path $RepoRoot "scripts\scan_skill_security.py"
    if (Test-Path $scanSkillSource) {
        Safe-Copy -Source $scanSkillSource -Destination (Join-Path $scriptsDest "scan_skill_security.py") -Confirm:$true -CustomMessage "✓ Skill-security scanner installed at: $scriptsDest\scan_skill_security.py"
    }
    # generate_release_changelog.py / .ps1 (v2.4.0): local conventional-commit
    # release helper - computes the next semver bump + a Keep-a-Changelog
    # section from local git history. Zero-outbound (local git only); an
    # optional helper for the /update version / /update changelog flows, NOT a
    # GitHub Action. Both siblings ship. Mirror of the bash block.
    $releaseChangelogPy = Join-Path $RepoRoot "scripts\generate_release_changelog.py"
    if (Test-Path $releaseChangelogPy) {
        Safe-Copy -Source $releaseChangelogPy -Destination (Join-Path $scriptsDest "generate_release_changelog.py") -Confirm:$true -CustomMessage "✓ Release-changelog helper installed at: $scriptsDest\generate_release_changelog.py"
    }
    $releaseChangelogPs1 = Join-Path $RepoRoot "scripts\generate_release_changelog.ps1"
    if (Test-Path $releaseChangelogPs1) {
        Safe-Copy -Source $releaseChangelogPs1 -Destination (Join-Path $scriptsDest "generate_release_changelog.ps1") -Confirm:$true -CustomMessage "✓ Release-changelog helper (PowerShell) installed at: $scriptsDest\generate_release_changelog.ps1"
    }

    # Copy v2.3.0 Phase 4 lifecycle scripts (T011 consult advisor + T012
    # harness audit). Mirror of the matching block in scripts\installer.sh.
    # The doctor / repair / list-installed surface itself lives on
    # scripts\lib\integrations\runner.py and ships via the registry copy
    # step further down.
    $consultSource = Join-Path $RepoRoot "scripts\nexus_hub_consult.py"
    if (Test-Path $consultSource) {
        Safe-Copy -Source $consultSource -Destination (Join-Path $scriptsDest "nexus_hub_consult.py") -Confirm:$true -CustomMessage "✓ Consult advisor installed at: $scriptsDest\nexus_hub_consult.py"
    }
    $auditSource = Join-Path $RepoRoot "scripts\harness_audit.py"
    if (Test-Path $auditSource) {
        Safe-Copy -Source $auditSource -Destination (Join-Path $scriptsDest "harness_audit.py") -Confirm:$true -CustomMessage "✓ Harness audit installed at: $scriptsDest\harness_audit.py"
    }

    # Copy v2.3.0 Phase 6 framework-coverage generator (T017). Mirror of the
    # matching block in scripts\installer.sh. Read-only, zero-outbound: reads
    # the optional framework-mapping frontmatter fields (mitre_attack /
    # atlas_techniques / d3fend_techniques / nist_csf / nist_ai_rmf) across
    # catalog\skills\ and emits a coverage matrix (Markdown or JSON) of which
    # skills cover which MITRE/NIST controls.
    $coverageSource = Join-Path $RepoRoot "scripts\build_framework_coverage.py"
    if (Test-Path $coverageSource) {
        Safe-Copy -Source $coverageSource -Destination (Join-Path $scriptsDest "build_framework_coverage.py") -Confirm:$true -CustomMessage "✓ Framework coverage generator installed at: $scriptsDest\build_framework_coverage.py"
    }

    # Copy feature-directory bootstrap scripts (v2.1.0 / adoption-spec-kit
    # Phase 7 / G5). The two scripts resolve the next specs\<NNN>-<slug>\
    # prefix (sequential or timestamp per .specify\init-options.json),
    # create the directory, and persist .specify\feature.json so downstream
    # commands (/spec clarify, /spec analyze, /plan issues) can locate
    # the active feature directory without git-branch coupling. Lockstep
    # with the same block in scripts\installer.sh.
    $newFeatureShSource = Join-Path $RepoRoot "scripts\new-feature.sh"
    if (Test-Path $newFeatureShSource) {
        Safe-Copy -Source $newFeatureShSource -Destination (Join-Path $scriptsDest "new-feature.sh") -Confirm:$true -CustomMessage "✓ Feature directory bootstrap (bash) installed at: $scriptsDest\new-feature.sh"
    }
    $newFeaturePs1Source = Join-Path $RepoRoot "scripts\new-feature.ps1"
    if (Test-Path $newFeaturePs1Source) {
        Safe-Copy -Source $newFeaturePs1Source -Destination (Join-Path $scriptsDest "new-feature.ps1") -Confirm:$true -CustomMessage "✓ Feature directory bootstrap (PowerShell) installed at: $scriptsDest\new-feature.ps1"
    }

    # Copy integration registry module (v2.1.0+). Mirror of the bash block
    # in scripts\installer.sh. Lands the per-platform install hierarchy under
    # ~\.nexus-hub\scripts\lib\integrations\ so users can invoke the runner
    # standalone post-install.
    $integrationsSrc = Join-Path $RepoRoot "scripts\lib\integrations"
    $integrationsDest = Join-Path $scriptsDest "lib\integrations"
    if (Test-Path $integrationsSrc) {
        Safe-Folder-Copy -Source $integrationsSrc -Destination $integrationsDest -CustomMessage "✓ Integration registry installed at: $integrationsDest"
    }
    $libInit = Join-Path $scriptsDest "lib\__init__.py"
    if ((Test-Path (Split-Path $libInit -Parent)) -and -not (Test-Path $libInit)) {
        New-Item -ItemType File -Force -Path $libInit | Out-Null
    }

    # Copy style-guides (v1.0.0+). Reference content for /research compile
    # and /research report; deliberately not in catalog\commands so the files
    # do not surface as slash commands.
    $styleGuidesSrc = Join-Path $RepoRoot "catalog\style-guides"
    $styleGuidesDest = Join-Path $nexusHome "style-guides"
    if (Test-Path $styleGuidesSrc) {
        Safe-Folder-Copy -Source $styleGuidesSrc -Destination $styleGuidesDest -CustomMessage "✓ Style guides installed at: $styleGuidesDest"
    }

    # Copy opt-in git pre-commit hook sources (v1.1.2+; expanded to four
    # platform-parallel variants in v1.1.3). Each hook calls only its own
    # CLI - they are independent of each other. The hooks themselves are
    # NEVER auto-wired into a repository; users opt in by running the
    # /setup hooks slash command from inside the target
    # repo, which copies the chosen platform's script to .git\hooks\pre-commit.
    $nexusHooksDest = Join-Path $nexusHome "hooks"
    if (-not (Test-Path $nexusHooksDest)) { New-Item -ItemType Directory -Force -Path $nexusHooksDest | Out-Null }
    $diffReviewVariants = @(
        "claude-diff-review.sh",
        "gemini-diff-review.sh",
        "antigravity-cli-diff-review.sh",
        "antigravity-cli-diff-review.ps1",
        "codex-diff-review.sh",
        "opencode-diff-review.sh"
    )
    foreach ($variant in $diffReviewVariants) {
        $diffReviewSrc = Join-Path $RepoRoot "catalog\hooks\$variant"
        if (Test-Path $diffReviewSrc) {
            Safe-Copy -Source $diffReviewSrc -Destination (Join-Path $nexusHooksDest $variant) -Confirm:$true -CustomMessage "✓ Pre-commit review hook source installed at: $nexusHooksDest\$variant"
        }
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
    # `/research report` command (generic vs custom path gate). Bundled generic templates
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
    $nexusHome = Join-Path $env:USERPROFILE ".nexus-hub"
    $nexusData = Join-Path $nexusHome "data"

    if (-not (Test-Path $nexusData)) { New-Item -Path $nexusData -ItemType Directory -Force | Out-Null }

    if (Test-Path $skillIndexSrc) {
        Copy-Item -Path $skillIndexSrc -Destination (Join-Path $nexusData "SKILL_INDEX.md") -Force
        Write-Item -Message "  Skill index copied to $nexusData" -Color "DarkGreen"
    }
    else {
        Write-Item -Message "  SKILL_INDEX.md not found in data/. Run 'python infrastructure/tools/build_skills_catalog.py' first." -Color "Yellow"
    }

    # Copy skills.json and bundles.json to global data dir
    $skillsJsonSrc = Join-Path $RepoRoot "data\skills.json"
    $bundlesJsonSrc = Join-Path $RepoRoot "data\bundles.json"
    if (Test-Path $skillsJsonSrc) { Copy-Item -Path $skillsJsonSrc -Destination (Join-Path $nexusData "skills.json") -Force }
    if (Test-Path $bundlesJsonSrc) { Copy-Item -Path $bundlesJsonSrc -Destination (Join-Path $nexusData "bundles.json") -Force }

    Write-Item -Message "  Skill data installed to $nexusData" -Color "DarkGreen"

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
    $mcpServerSrc = Join-Path $RepoRoot "extensions\nexus-skill-server"
    $mcpServerDest = Join-Path $nexusHome "mcp-server"
    if (Test-Path $mcpServerDest) { Remove-Item -Path $mcpServerDest -Recurse -Force }
    Copy-Item -Path $mcpServerSrc -Destination $mcpServerDest -Recurse -Force
    Write-Item -Message "  MCP server source copied to $mcpServerDest" -Color "DarkGreen"

    # Create venv and install dependencies
    $venvPath = Join-Path $nexusHome "mcp-server-venv"
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

    # Install nexus-code-search into the same venv (v1.0.0+).
    # Local-only code-search MCP. Zero outbound calls. See AGENTS.md MCP Registry Policy.
    $codeSearchSrc = Join-Path $RepoRoot "extensions\nexus-code-search"
    $codeSearchDest = Join-Path $nexusHome "code-search"
    $ErrorActionPreference = "Continue"
    if (Test-Path $codeSearchSrc) {
        if (Test-Path $codeSearchDest) { Remove-Item -Path $codeSearchDest -Recurse -Force }
        Copy-Item -Path $codeSearchSrc -Destination $codeSearchDest -Recurse -Force
        if ($hasUv) {
            & uv pip install --python "$venvPath\Scripts\python.exe" -e $codeSearchDest 2>$null | Out-Null
        } else {
            & "$venvPath\Scripts\pip.exe" install -q -e $codeSearchDest 2>$null | Out-Null
        }
        Write-Item -Message "  nexus-code-search installed at $codeSearchDest" -Color "DarkGreen"
    }

    # Install nexus-web-fetch into the same venv (v1.0.0+).
    # Local-only web-fetch MCP (fetches user-specified URLs only). See AGENTS.md.
    $webFetchSrc = Join-Path $RepoRoot "extensions\nexus-web-fetch"
    $webFetchDest = Join-Path $nexusHome "web-fetch"
    if (Test-Path $webFetchSrc) {
        if (Test-Path $webFetchDest) { Remove-Item -Path $webFetchDest -Recurse -Force }
        Copy-Item -Path $webFetchSrc -Destination $webFetchDest -Recurse -Force
        if ($hasUv) {
            & uv pip install --python "$venvPath\Scripts\python.exe" -e $webFetchDest 2>$null | Out-Null
        } else {
            & "$venvPath\Scripts\pip.exe" install -q -e $webFetchDest 2>$null | Out-Null
        }
        Write-Item -Message "  nexus-web-fetch installed at $webFetchDest" -Color "DarkGreen"
    }

    # Install nexus-context-compressor into the same venv (v3.2.0+).
    # Local-first context-compression engine. Zero outbound by default; tiktoken
    # is the only required dependency, with an offline stdlib fallback. Installed
    # with the [mcp] extra so the Phase 4 (T013) compress/retrieve MCP server runs;
    # the server is registered in the mcpServers merge block below.
    # See AGENTS.md MCP Registry Policy.
    $contextCompressorSrc = Join-Path $RepoRoot "extensions\nexus-context-compressor"
    $contextCompressorDest = Join-Path $nexusHome "context-compressor"
    if (Test-Path $contextCompressorSrc) {
        if (Test-Path $contextCompressorDest) { Remove-Item -Path $contextCompressorDest -Recurse -Force }
        Copy-Item -Path $contextCompressorSrc -Destination $contextCompressorDest -Recurse -Force
        if ($hasUv) {
            & uv pip install --python "$venvPath\Scripts\python.exe" -e "$contextCompressorDest[mcp]" 2>$null | Out-Null
        } else {
            & "$venvPath\Scripts\pip.exe" install -q -e "$contextCompressorDest[mcp]" 2>$null | Out-Null
        }
        Write-Item -Message "  nexus-context-compressor installed at $contextCompressorDest" -Color "DarkGreen"
    }
    $ErrorActionPreference = "Stop"

    # Add or update mcpServers without touching other keys (e.g., hooks)
    $skillServerEntry = [PSCustomObject]@{
        command = "$venvPath\Scripts\python.exe"
        args    = @("-m", "nexus_skill_server")
        env     = [PSCustomObject]@{ NEXUS_HUB_ROOT = $nexusHome }
    }
    $codeSearchEntry = [PSCustomObject]@{
        command = "$venvPath\Scripts\python.exe"
        args    = @("-m", "nexus_code_search")
        env     = [PSCustomObject]@{ NEXUS_HUB_ROOT = $nexusHome }
    }
    $webFetchEntry = [PSCustomObject]@{
        command = "$venvPath\Scripts\python.exe"
        args    = @("-m", "nexus_web_fetch")
        env     = [PSCustomObject]@{ NEXUS_HUB_ROOT = $nexusHome }
    }
    $contextCompressorEntry = [PSCustomObject]@{
        command = "$venvPath\Scripts\python.exe"
        args    = @("-m", "nexus_context_compressor", "serve")
        env     = [PSCustomObject]@{ NEXUS_HUB_ROOT = $nexusHome }
    }

    if (-not $settings.PSObject.Properties["mcpServers"]) {
        $settings | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([PSCustomObject]@{})
    }

    foreach ($pair in @(
        @{ Name = "nexus-skill-server"; Entry = $skillServerEntry },
        @{ Name = "nexus-code-search"; Entry = $codeSearchEntry },
        @{ Name = "nexus-web-fetch"; Entry = $webFetchEntry },
        @{ Name = "nexus-context-compressor"; Entry = $contextCompressorEntry }
    )) {
        $name = $pair.Name
        $entry = $pair.Entry
        if ($settings.mcpServers.PSObject.Properties[$name]) {
            $settings.mcpServers.$name = $entry
        } else {
            $settings.mcpServers | Add-Member -NotePropertyName $name -NotePropertyValue $entry
        }
    }

    # Remove superseded legacy (devai-hub) MCP entries left by pre-rename installs;
    # they are replaced one-for-one by the nexus-* servers registered above.
    foreach ($legacy in @("devai-skill-server", "devai-code-search", "devai-web-fetch")) {
        if ($settings.mcpServers.PSObject.Properties[$legacy]) {
            $settings.mcpServers.PSObject.Properties.Remove($legacy)
        }
    }

    $settings | ConvertTo-Json -Depth 10 | Set-Content $claudeSettings -Encoding UTF8
    Write-Item -Message "  MCP servers registered in $claudeSettings (nexus-skill-server, nexus-code-search, nexus-web-fetch, nexus-context-compressor)" -Color "DarkGreen"
    Write-Item -Message "  Servers will auto-start with Claude Code. No manual steps needed." -Color "DarkGreen"
}

# --- Banner ---

# NEXUS-HUB wordmark. Printed at startup ahead of the welcome banner.
# The banner uses Unicode block characters for a clean wordmark; the
# `@'...'@` here-string preserves the literal glyphs verbatim. installer.ps1
# is saved as UTF-8 with BOM so PowerShell renders these characters in both
# Windows PowerShell 5.1 and PowerShell 7+. Modeled after the Claude Code
# CLI banner style.
function Write-NexusBanner {
    $banner = @'
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗      ██╗  ██╗██╗   ██╗██████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝      ██║  ██║██║   ██║██╔══██╗
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗█████╗███████║██║   ██║██████╔╝
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║╚════╝██╔══██║██║   ██║██╔══██╗
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║      ██║  ██║╚██████╔╝██████╔╝
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝      ╚═╝  ╚═╝ ╚═════╝ ╚═════╝
'@

    $bannerLines = $banner -split "`r?`n"
    Write-Host ""
    foreach ($line in $bannerLines) {
        Write-Host $line -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "  Multi-platform AI skill harness  ·  v$script:NexusHubVersion  ·  https://github.com/bendourthe/Nexus-Hub" -ForegroundColor DarkGray
    Write-Host ""
}

# Uninstalls the legacy DevAI-Hub VS Code extension if present. The
# Claude Usage Monitor was published under `devai-hub.claude-usage-monitor`
# before the rename; the current build ships as `nexus-hub.claude-usage-monitor`.
# Leaving both installed produces a duplicate entry in VS Code's Extensions
# pane and two status-bar items. Called unconditionally at startup -- the
# function silently no-ops when nothing legacy is installed, so it is safe
# (and necessary) to re-run on every install, including for users who
# migrated ~/.devai-hub/ in an earlier installer run.
function Remove-LegacyVSCodeExtensions {
    $codeCmd = Get-Command "code" -ErrorAction SilentlyContinue
    if (-not $codeCmd) { return }
    $installed = & code --list-extensions 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $installed) { return }

    $legacyIds = @("devai-hub.claude-usage-monitor")
    $emitted = $false
    foreach ($id in $legacyIds) {
        if ($installed -contains $id) {
            if (-not $emitted) { Write-Host "" }
            Write-Host "  Removing legacy VS Code extension: $id" -ForegroundColor Yellow
            & code --uninstall-extension $id 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Removed $id" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ Could not auto-remove $id (uninstall it manually from VS Code)" -ForegroundColor Yellow
            }
            $emitted = $true
        }
    }
    if ($emitted) { Write-Host "" }
}

# Detects an existing ~/.devai-hub/ install and migrates it to ~/.nexus-hub/.
# One-shot, one-way per the backward-compat decision in
# docs/archive/v2/v2.0.0/rename-decisions.md. The installer does NOT ship a symlink or
# compatibility shim. Three branches:
#   1. legacy only             -> prompt to migrate (default Y), then Move-Item.
#   2. legacy AND new co-exist -> ask user: keep-new, abort, or merge.
#   3. neither / new only      -> no-op (fresh or already-migrated install).
# When the legacy directory is detected, also uninstall the legacy VS Code
# extension (devai-hub.claude-usage-monitor) so the rename is complete.
function Invoke-LegacyInstallMigration {
    $legacy = Join-Path $env:USERPROFILE ".devai-hub"
    $current = Join-Path $env:USERPROFILE ".nexus-hub"

    $legacyExists = Test-Path $legacy
    $currentExists = Test-Path $current

    if ($legacyExists -and -not $currentExists) {
        Write-Host ""
        Write-Host "  Detected existing DevAI-Hub install at $legacy" -ForegroundColor Yellow
        $ans = Read-Host "  Migrate to Nexus-Hub ($current)? [Y/n]"
        if ([string]::IsNullOrWhiteSpace($ans)) { $ans = "Y" }
        if ($ans -match "^[Yy]") {
            Move-Item -Path $legacy -Destination $current
            Write-Host "  Migrated $legacy -> $current" -ForegroundColor Green
        }
        else {
            Write-Host "  Migration declined. Remove $legacy manually or rerun and accept." -ForegroundColor Red
            exit 1
        }
        Write-Host ""
    }
    elseif ($legacyExists -and $currentExists) {
        Write-Host ""
        Write-Host "  Both $legacy and $current exist." -ForegroundColor Yellow
        Write-Host "  Choose: [k]eep new + delete old, [a]bort + handle manually, [m]erge (best effort)"
        $ans = Read-Host "  Selection [k/a/m]"
        switch -Regex ($ans) {
            "^[Kk]" {
                Remove-Item -Path $legacy -Recurse -Force
                Write-Host "  Removed $legacy. Keeping $current." -ForegroundColor Green
            }
            "^[Mm]" {
                Copy-Item -Path (Join-Path $legacy "*") -Destination $current -Recurse -Force
                Remove-Item -Path $legacy -Recurse -Force
                Write-Host "  Merged $legacy into $current (best effort)." -ForegroundColor Green
            }
            default {
                Write-Host "  Aborted. Resolve $legacy and $current manually before rerunning." -ForegroundColor Red
                exit 1
            }
        }
        Write-Host ""
    }
}

function Show-WelcomeBanner {
    # The Nexus-Hub Universal Installer welcome line. The wordmark printed
    # by Write-NexusBanner (and Invoke-LegacyInstallMigration when active)
    # already finishes with a blank line, so this function deliberately does
    # not add its own leading blank. Title text is preserved for the
    # installer-smoke test contract.
    Restore-Title
    Write-Host "Welcome to the Nexus-Hub Universal Installer (v$script:NexusHubVersion)" -ForegroundColor Cyan
}

function Show-FarewellBanner {
    Write-Host ""
    Write-Host "✓ Nexus-Hub v$script:NexusHubVersion installed." -ForegroundColor Green
}

# --- Main ---
$repoRoot = Resolve-Path "$PSScriptRoot\.."

# --- Branch-based install (v2.4.0+) --------------------------------------
# When -Branch <name> is given, install the catalog from a shallow clone of
# that pushed branch in a deterministic cache dir, leaving the user's working
# copy untouched. NEXUS_HUB_BRANCH_RESOLVED guards against re-cloning once we
# have re-launched into the cached checkout. This block runs before the
# read-only dispatch so that -Branch + -Check is a clone-free probe.
if ($Branch -and $env:NEXUS_HUB_BRANCH_RESOLVED -ne "1") {
    $branchToken = Get-SanitizedBranchName -Raw $Branch
    $homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
    $branchCacheDir = Join-Path $homeDir ".nexus-hub/branches/$branchToken"
    $branchSrcUrl = ""
    try { $branchSrcUrl = (& git -C "$repoRoot" config --get remote.origin.url).Trim() } catch { $branchSrcUrl = "" }
    if ([string]::IsNullOrEmpty($branchSrcUrl)) { $branchSrcUrl = "$repoRoot" }

    if ($Check) {
        # Probe: print the resolution and exit without cloning or installing.
        Write-Host "nexus-hub branch install (dry-run):"
        Write-Host "  branch:    $Branch"
        Write-Host "  sanitized: $branchToken"
        Write-Host "  source:    $branchSrcUrl"
        Write-Host "  cache dir: $branchCacheDir"
        exit 0
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "git is required for -Branch installs but was not found on PATH."
        exit 2
    }

    Write-Host "Installing Nexus-Hub from branch '$Branch' (cache: $branchCacheDir)..."
    $branchParent = Split-Path $branchCacheDir -Parent
    if (-not (Test-Path $branchParent)) { New-Item -ItemType Directory -Force -Path $branchParent | Out-Null }
    if (Test-Path (Join-Path $branchCacheDir ".git")) {
        & git -C "$branchCacheDir" fetch --depth 1 origin "$Branch"
        if ($LASTEXITCODE -ne 0) { Write-Error "Failed to refresh branch cache at $branchCacheDir"; exit 2 }
        & git -C "$branchCacheDir" checkout -f FETCH_HEAD
        if ($LASTEXITCODE -ne 0) { Write-Error "Failed to checkout branch cache at $branchCacheDir"; exit 2 }
    } else {
        if (Test-Path $branchCacheDir) { Remove-Item -Recurse -Force $branchCacheDir }
        & git clone --depth 1 --branch "$Branch" "$branchSrcUrl" "$branchCacheDir"
        if ($LASTEXITCODE -ne 0) { Write-Error "Failed to clone branch '$Branch' from $branchSrcUrl"; exit 2 }
    }

    $cachedInstaller = Join-Path $branchCacheDir "scripts/installer.ps1"
    if (-not (Test-Path $cachedInstaller)) {
        Write-Error "Cached checkout has no scripts/installer.ps1 at $cachedInstaller"
        exit 2
    }
    $env:NEXUS_HUB_BRANCH_RESOLVED = "1"
    $branchPassthru = @()
    if ($Enterprise) { $branchPassthru += "-Enterprise" }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $cachedInstaller @branchPassthru
    exit $LASTEXITCODE
}

# Read-only subcommand dispatch (init / -PrintConfig / -Check) - bypass the
# interactive scope menu and proxy to the Python runner so they are pipeable /
# scriptable.
if ($Subcommand -eq "init" -or $PrintConfig -or $Check) {
    $runner = Join-Path $repoRoot "scripts\lib\integrations\runner.py"
    if (-not (Test-Path $runner)) {
        Write-Error "Runner not found at $runner"
        exit 2
    }
    $py = Resolve-PythonExecutable
    if (-not $py) {
        Write-Error "Python not found on PATH; cannot run read-only subcommand."
        exit 2
    }
    if ($Subcommand -eq "init") {
        $passthrough = @("init")
        if ($SubcommandArgs) { $passthrough += $SubcommandArgs }
        & $py $runner @passthrough
    } elseif ($PrintConfig) {
        & $py $runner print-config $PrintConfig
    } else {
        & $py $runner check
    }
    exit $LASTEXITCODE
}

Write-NexusBanner
Invoke-LegacyInstallMigration
# Idempotent cleanup -- safe to run every install. Catches the case where the
# user already migrated ~/.devai-hub/ in an earlier run (before this cleanup
# existed) but still has devai-hub.claude-usage-monitor installed in VS Code.
Remove-LegacyVSCodeExtensions
Show-WelcomeBanner

Write-Host ""
Write-Host "Where would you like to install Nexus-Hub?"
Write-Host "  [G] Global    - all projects on this machine (recommended)" -ForegroundColor Green
Write-Host "  [W] Workspace - a single project directory" -ForegroundColor Yellow
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
# Interactive custom-template import moved to /research report at use time (v0.9.7).
Install-Templates -RepoRoot $repoRoot

Write-Host ""
Write-Host "✓ Nexus-Hub v$script:NexusHubVersion installed ($scopeLabel scope)." -ForegroundColor Green
Write-Host ""
Write-Host "Restart any running AI assistant sessions (Claude Code, Cursor, Gemini CLI, Codex, Copilot, OpenCode) so they pick up the new settings, hooks, skills, and rules." -ForegroundColor Yellow

Show-FarewellBanner
Pause
