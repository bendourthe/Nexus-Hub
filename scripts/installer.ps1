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
    # v3.7.0 / Phase 2 -- no-prompt install controls.
    [string]$Workspace,        # install into a single project dir; default = global
    [string]$Platforms,        # comma-separated integration keys; default = all
    [switch]$Yes,              # non-interactive: never prompt, refresh managed files
    [switch]$Force,            # overwrite existing managed files without asking
    # v3.15.6 / AC5 -- opt-in hardened permission posture. Absent (the default)
    # keeps the convenience default (allow-only auto-approve, no prompts) exactly
    # as it was; present ALSO merges the deny/ask overlay from
    # configs/permissions/claude-permissions-strict.json.
    [switch]$StrictPermissions,
    # v3.16.1 -- install-selection selectors. Contract:
    # docs/releases/v3/v3.16/development/install-selection-contract.md
    # Absent (the default) installs the full catalog, exactly as before.
    # Bound as -Profile for lockstep with the Bash --profile flag, but stored in
    # $InstallProfile: $Profile is a PowerShell AUTOMATIC variable (the path to
    # the user's profile script), and a parameter of that name shadows it inside
    # the script. The alias keeps the user-facing spelling identical across both
    # installers without the shadowing.
    [Alias("Profile")]
    [string]$InstallProfile,   # one profile id
    [string]$Modules,          # comma-separated capability module ids
    [string]$Bundles,          # comma-separated role bundle ids
    [Parameter(Position = 0)]
    [string]$Subcommand,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$SubcommandArgs
)

if ($Help) {
    @"
Usage:
  pwsh scripts/installer.ps1 [-Workspace PATH] [-Platforms LIST] [-Yes]
                             [-Profile ID] [-Modules LIST] [-Bundles LIST]
                             [-Force] [-Enterprise] [-StrictPermissions] [-Help]
  pwsh scripts/installer.ps1 init [-Target PATH] [-DryRun]
  pwsh scripts/installer.ps1 -PrintConfig <integration-key>
  pwsh scripts/installer.ps1 -Check
  pwsh scripts/installer.ps1 -Branch <name> [-Enterprise]

By default the installer runs with NO prompts: a global install across ALL
supported platforms (absent platforms skip-with-note). Existing managed files
that you have customized are detected and you are asked ONCE whether to
overwrite them; with -Yes / -Force (or any non-interactive / piped run) they
are refreshed to the latest version automatically.

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
  -StrictPermissions
                Install the OPT-IN hardened Claude Code permission posture in
                addition to the read-only auto-approve list: deny/ask entries for
                the execution-trigger config surfaces (version-control hooks and
                config, interpreter paths, harness and editor config) from
                configs/permissions/claude-permissions-strict.json. Without this
                switch the install is unchanged (allow-only, no prompts). A
                deliberate posture split: convenience by default, hardened on
                request.
  -Workspace <path>  Install into a single project directory instead of the
                default global (all-projects) scope.
  -Platforms <list>  Install only the given comma-separated integration keys
                instead of all platforms. Valid keys: claude, codex, gemini,
                antigravity2, gemini-cli, copilot, cursor, opencode, nexus-ai,
                aider, windsurf, kimi, qwen, openclaw.
  -Profile <id> Install one profile instead of the whole catalog: minimal,
                core, or full. Default (no selector) is full.
  -Modules <list>  Install the given comma-separated capability modules.
  -Bundles <list>  Install the given comma-separated role bundles.
                Selectors combine by union: -Profile core -Modules ai-engineering
                installs both. -Profile full cannot be combined with others.
                Hooks, rules, templates, and settings install under EVERY
                selection; only skills and their dependent commands and agents
                are filtered. Selectors need Python; a full install does not.
  -Yes          Non-interactive: never prompt, and refresh existing managed
                files to the latest version (also implied when stdin is not a
                TTY, e.g. a piped irm|iex install).
  -Force        Overwrite existing managed files with the Nexus-Hub version
                without asking (implies -Yes for prompting).
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
$script:NexusHubVersion = "4.7.0"

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
        "AIDER"           { "Green" }
        "WINDSURF"        { "DarkGreen" }
        "KIMI"            { "Red" }
        "QWEN"            { "DarkRed" }
        "OPENCLAW"        { "Yellow" }
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

# --- Per-platform install checklist (v3.14.5 Phase 2) ---
#
# The registry runner emits a structured per-surface summary
# (runner.py --summary-json); the installer renders it as a fixed-order
# checklist so every platform reads identically, and collects platforms whose
# tool was not detected into one "NOT DETECTED" group instead of a colored
# header plus a caveat line per platform.

# Canonical surface order + display labels (matches the bash installer).
$script:ChecklistSurfaces = @(
    @{ Key = "instruction"; Label = "Core Files" },
    @{ Key = "skills";      Label = "Skills" },
    @{ Key = "commands";    Label = "Commands" },
    @{ Key = "agents";      Label = "Agents" },
    @{ Key = "rules";       Label = "Rules" },
    @{ Key = "hooks";       Label = "Hooks" },
    @{ Key = "settings";    Label = "Core Settings" }
)

# Platforms whose tool was not detected on this machine (grouped at run end).
$script:UndetectedPlatforms = @()

function Reset-UndetectedPlatforms { $script:UndetectedPlatforms = @() }

function Add-UndetectedPlatform {
    param([string]$Name, [string]$Reason = "not detected")
    $script:UndetectedPlatforms += [pscustomobject]@{ Name = $Name; Reason = $Reason }
}

function Write-ChecklistRow {
    param(
        [string]$Label,
        [string]$State,          # "ok" | "warn"
        [string]$Detail = ""
    )
    $mark = if ($State -eq "ok") { [char]0x2713 } else { "!" }
    $color = if ($State -eq "ok") { "Green" } else { "Yellow" }
    $col = ("{0}:" -f $Label).PadRight(16)
    Write-Host ("    [{0}] {1} {2}" -f $mark, $col, $Detail) -ForegroundColor $color
}

function Write-PlatformChecklist {
    # Render a registry platform's summary object as the fixed-order checklist.
    param($PlatformSummary)
    foreach ($s in $script:ChecklistSurfaces) {
        $entry = $null
        if ($PlatformSummary.surfaces -and $PlatformSummary.surfaces.PSObject.Properties[$s.Key]) {
            $entry = $PlatformSummary.surfaces.($s.Key)
        }
        if ($null -eq $entry) { continue }
        if ($entry.status -eq "installed") {
            Write-ChecklistRow -Label $s.Label -State "ok" -Detail $entry.path
        }
        else {
            Write-ChecklistRow -Label $s.Label -State "warn" -Detail "install reported an issue"
        }
    }
}

function Write-UndetectedGroup {
    # Print the single grouped section for platforms not found on this machine.
    if ($script:UndetectedPlatforms.Count -eq 0) { return }
    Write-Host ""
    Write-Host "  > NOT DETECTED (skipped)" -ForegroundColor DarkGray
    foreach ($p in $script:UndetectedPlatforms) {
        Write-Host ("    - {0} ({1})" -f $p.Name, $p.Reason) -ForegroundColor DarkGray
    }
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

# Map a user-supplied integration key (the --platforms vocabulary) to the
# internal PS platform keys the per-provider install blocks gate on. GEMINI is
# the Gemini IDE (full registry mirror as of v3.11.0); Antigravity 2.0 is a
# separate ANTIGRAVITY2 key. (Antigravity 1.0 has no reachable install block.)
$script:IntegrationKeyToPlatforms = [ordered]@{
    "claude"       = @("CLAUDE")
    "codex"        = @("CODEX")
    "gemini"       = @("GEMINI")
    "antigravity2" = @("ANTIGRAVITY2")
    "gemini-cli"   = @("GEMINI_CLI")
    "copilot"      = @("COPILOT")
    "cursor"       = @("CURSOR")
    "opencode"     = @("OPENCODE")
    "nexus-ai"     = @("NEXUS_AI")
    "aider"        = @("AIDER")
    "windsurf"     = @("WINDSURF")
    "kimi"         = @("KIMI")
    "qwen"         = @("QWEN")
    "openclaw"     = @("OPENCLAW")
}

# Resolve the set of internal platform keys to install (v3.7.0 / Phase 2). With
# no -Platforms argument every platform is selected (the no-prompt default);
# otherwise the comma-separated integration keys are validated and expanded.
# Exits non-zero on an unknown key.
function Resolve-Platforms {
    param([string]$PlatformsArg)

    $allPlatforms = @()
    foreach ($k in $script:IntegrationKeyToPlatforms.Keys) {
        $allPlatforms += $script:IntegrationKeyToPlatforms[$k]
    }

    if ([string]::IsNullOrWhiteSpace($PlatformsArg)) { return $allPlatforms }

    $selected = @()
    foreach ($token in $PlatformsArg.Split(',')) {
        $key = $token.Trim().ToLower()
        if ([string]::IsNullOrWhiteSpace($key)) { continue }
        if ($script:IntegrationKeyToPlatforms.Contains($key)) {
            $selected += $script:IntegrationKeyToPlatforms[$key]
        }
        else {
            Write-Host "Unknown platform key: '$key'" -ForegroundColor Red
            Write-Host ("Valid keys: " + ($script:IntegrationKeyToPlatforms.Keys -join ", ")) -ForegroundColor Red
            exit 2
        }
    }
    if ($selected.Count -eq 0) {
        Write-Host "-Platforms produced an empty platform set" -ForegroundColor Red
        exit 2
    }
    return $selected
}

# --- File Operations ---

# Writes an object as JSON in UTF-8 *without* a BOM. Windows PowerShell 5.1's
# Set-Content / Out-File -Encoding UTF8 prepend a BOM, which is invalid per the
# JSON spec and breaks strict JSON.parse consumers such as the Claude Code VS Code
# extension ("Unexpected token ... is not valid JSON"). .NET WriteAllText with
# UTF8Encoding($false) is BOM-less on both Windows PowerShell 5.1 and PowerShell 7+.
function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Object,
        [int]$Depth = 10
    )
    $json = $Object | ConvertTo-Json -Depth $Depth
    [System.IO.File]::WriteAllText($Path, $json, (New-Object System.Text.UTF8Encoding($false)))
}

# Copy a single managed file with conflict-only overwrite semantics (v3.7.0 /
# Phase 2). The $Confirm parameter is retained for call-site signature
# compatibility but no longer gates a prompt: conflict handling is uniform and
# driven by $script:OverwriteMode.
#
#   - source missing                -> skip-with-note
#   - destination missing           -> create
#   - destination identical to src  -> nothing to do (idempotent, silent)
#   - destination differs:
#       OverwriteMode "ALL" (refresh)        -> overwrite now
#       otherwise (interactive "CONFLICT")   -> record conflict + KEEP; the
#         single end-of-run Resolve-Conflicts prompt decides whether to overwrite
# Return the uppercase hex SHA-256 of a file, using .NET directly.
#
# This deliberately does NOT use Get-FileHash. That cmdlet lives in the
# Microsoft.PowerShell.Utility module, and on GitHub's windows-latest image a
# Windows PowerShell 5.1 session running this script raised
# CommandNotFoundException for it -- while Write-Host and the rest of Utility
# worked, and while the same script under pwsh 7 on the same image was fine.
#
# The trigger is subtle enough to be worth recording: Safe-Copy only hashes when
# the destination ALREADY exists, so on a fresh install every call short-circuits
# and the cmdlet is never invoked. The install-smoke job therefore passed for
# releases while this line was unreachable; it only fired once a job installed
# twice into the same HOME, which the v3.16.1 parity suite is the first to do.
#
# The exact cause of the missing cmdlet was not reproducible off that image
# (an empty PSModulePath and a simulated pwsh-7 PSModulePath both resolve
# Get-FileHash correctly on a local 5.1). It does not need to be: this is the
# SECOND time the cmdlet has failed on a 5.1 runner image in this repo -- see
# catalog/hooks/provenance-ledger.ps1, where v3.15.6 hit the same thing and
# reached for the same .NET stream. Two independent sightings make it a property
# of the environment, not a one-off.
#
# Since the dependency buys nothing -- .NET's SHA256 is available in every
# edition with no module resolution at all -- it is removed rather than tuned
# around. Do not reintroduce it.
function Get-FileSha256 {
    param([string]$Path)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::OpenRead($Path)
        try {
            return [System.BitConverter]::ToString($sha.ComputeHash($stream)).Replace("-", "")
        } finally {
            $stream.Dispose()
        }
    } finally {
        $sha.Dispose()
    }
}

function Safe-Copy {
    param(
        [string]$Source,
        [string]$Destination,
        [boolean]$Confirm = $false,
        [string]$CustomMessage
    )
    $null = $Confirm  # retained for call-site compatibility; intentionally unused

    if (-not (Test-Path $Source)) {
        Write-Item -Message "Skip: Source not found ($(Split-Path $Source -Leaf))" -Color "DarkGray"
        return
    }

    if (Test-Path $Destination) {
        $srcHash = Get-FileSha256 -Path $Source
        $dstHash = Get-FileSha256 -Path $Destination
        if ($srcHash -eq $dstHash) {
            # Already current -- nothing to write.
            return
        }
        if ($script:OverwriteMode -ne "ALL") {
            # Interactive conflict: a managed file the user may have customized
            # differs from the catalog version. Keep it and defer to the single
            # end-of-run confirmation in Resolve-Conflicts.
            $script:ConflictSrcs += $Source
            $script:ConflictDsts += $Destination
            Write-Item -Message "Differs (kept; pending confirmation): $Destination" -Color "Yellow"
            return
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

# Resolve any conflicts accumulated by Safe-Copy during an interactive install
# (v3.7.0 / Phase 2). Conflicts are only recorded when OverwriteMode is not
# "ALL", so this prints the list, asks ONCE, and on confirmation overwrites the
# kept files. The non-interactive / -Yes / -Force path reaches here with an
# empty list (no-op).
function Resolve-Conflicts {
    $count = $script:ConflictDsts.Count
    if ($count -eq 0) { return }

    Write-SubSectionBanner -Text "Existing customizations detected"
    Write-Item -Message "$count managed file(s) on disk differ from the Nexus-Hub version:" -Color "Yellow"
    for ($i = 0; $i -lt $count; $i++) {
        Write-Item -Message "- $($script:ConflictDsts[$i])" -Color "DarkYellow"
    }

    $resp = Read-Prompt "Overwrite these with the Nexus-Hub version? [y/N]"
    if ($resp -match "^[Yy]") {
        for ($i = 0; $i -lt $count; $i++) {
            $dst = $script:ConflictDsts[$i]
            $src = $script:ConflictSrcs[$i]
            try {
                $parent = Split-Path $dst -Parent
                if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
                Copy-Item -Path $src -Destination $dst -Force -ErrorAction Stop
                Write-Item -Message "✓ Refreshed $dst" -Color "DarkGreen"
            }
            catch {
                Write-Item -Message "ERROR: Could not write $dst. Is it open?" -Color "Red"
            }
        }
    }
    else {
        Write-Item -Message "Kept your $count customized file(s). Re-run with -Yes (or -Force) to refresh them." -Color "Gray"
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
    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    }

    # Catalog trees are Nexus-owned content meant to be refreshed on every
    # install/upgrade, so they no longer prompt (v3.7.0 / Phase 2). The resolved
    # OverwriteMode picks the sync mode:
    #   "ALL" (refresh)  -> robocopy /MIR: refresh files AND remove stale ones
    #                       (the non-interactive / -Yes / -Force / bootstrap path).
    #   otherwise        -> robocopy /E: add/update files but keep any extras the
    #                       user added (never destructive, no prompt).
    if ($script:OverwriteMode -eq "ALL") {
        Write-Item -Message "Syncing (old files not in source will be removed)..." -Color "DarkGray"
        & robocopy $Source $Destination /MIR /NFL /NDL /NJH /NJS | Out-Null
    }
    else {
        Write-Item -Message "Merging (adding/updating files, keeping extras)..." -Color "DarkGray"
        & robocopy $Source $Destination /E /NFL /NDL /NJH /NJS | Out-Null
    }
    Restore-Title

    if (-not [string]::IsNullOrEmpty($CustomMessage)) {
        Write-Item -Message $CustomMessage -Color "DarkGreen"
    }
    else {
        Write-Item -Message "✓ Installed to $Destination" -Color "DarkGreen"
    }
}

# Install the skills catalog FLATTENED to the one-level layout Claude Code
# requires. Claude discovers skills exactly one level deep
# (<dir>\skills\<name>\SKILL.md), so the catalog's <category>\ tier must be
# dropped (this honors scripts\lib\integrations\claude.py's
# flatten_skills_layout: True; Codex / Gemini already flatten via the registry
# adapter). A verbatim category-nested copy leaves every SKILL.md at
# <dir>\skills\<category>\<name>\, which Claude cannot see. We stage a flattened
# copy in a temp dir, then hand it to Safe-Folder-Copy, reusing its refresh
# (robocopy /MIR prune) and merge semantics unchanged - so a prior
# category-nested layout and any upstream-removed skill are pruned in refresh
# mode, with strict parity to the bash installer's flatten_skills_into.
function Flatten-SkillsInto {
    param(
        [string]$Source,       # catalog\skills
        [string]$Destination,  # <claude>\skills
        [string]$CustomMessage
    )
    if (-not (Test-Path $Source)) {
        Write-Item -Message "Skip: Source folder not found ($(Split-Path $Source -Leaf))" -Color "DarkGray"
        return
    }
    $staging = Join-Path ([System.IO.Path]::GetTempPath()) ("nexus-skills-" + [System.Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    try {
        Get-ChildItem -Path $Source -Directory | ForEach-Object {          # category
            Get-ChildItem -Path $_.FullName -Directory | ForEach-Object {  # skill
                Copy-Item -Path $_.FullName -Destination (Join-Path $staging $_.Name) -Recurse -Force
            }
        }
        # Drop any category directories left by a PRIOR category-nested install so
        # the undiscoverable <dir>\skills\<category>\ layout never lingers. In
        # refresh mode robocopy /MIR already prunes them; this also covers merge
        # mode (catalog category names are never skill names).
        if (Test-Path $Destination) {
            Get-ChildItem -Path $Source -Directory | ForEach-Object {
                $stale = Join-Path $Destination $_.Name
                if (Test-Path $stale) { Remove-Item -Recurse -Force -Path $stale -ErrorAction SilentlyContinue }
            }
        }
        Safe-Folder-Copy -Source $staging -Destination $Destination -CustomMessage $CustomMessage
    }
    finally {
        Remove-Item -Recurse -Force -Path $staging -ErrorAction SilentlyContinue
    }
}

# --- Hook Installation ---

function Convert-ClaudeHookCommandsForWindows {
    param(
        [string]$SettingsFile,
        [string]$RepoRoot,
        [string]$Scope
    )

    if (-not (Test-Path $SettingsFile)) { return }
    $python = Resolve-PythonExecutable
    if (-not $python) { throw "Python is required to migrate Claude hook commands for Cursor compatibility" }
    $compat = Join-Path $RepoRoot "catalog\hooks\cursor-hook-compat.py"
    & $python $compat --rewrite-settings $SettingsFile --catalog-hooks-dir (Join-Path $RepoRoot "catalog\hooks") --host windows --scope $Scope.ToLowerInvariant()
    if ($LASTEXITCODE -ne 0) { throw "Could not migrate Claude hook commands for Windows" }
}

function Install-ClaudeHookFiles {
    param(
        [string]$RepoRoot,
        [string]$TargetClaudeDir,
        [string]$Scope
    )

    $sourceDir = Join-Path $RepoRoot "catalog\hooks"
    $hooksDir = Join-Path $TargetClaudeDir "hooks"
    if (-not (Test-Path $hooksDir)) { New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null }

    foreach ($pattern in @("*.ps1", "*.py")) {
        foreach ($source in @(Get-ChildItem -LiteralPath $sourceDir -Filter $pattern -File)) {
            Safe-Copy -Source $source.FullName -Destination (Join-Path $hooksDir $source.Name) -Confirm:$true -CustomMessage "✓ $Scope hook installed: $($source.Name)"
        }
    }
}

function Get-ManagedHookStem {
    param([object]$Hook)

    if ($null -eq $Hook) { return "" }
    $commandProperty = $Hook.PSObject.Properties["command"]
    if (-not $commandProperty -or -not $commandProperty.Value) { return "" }
    $matches = [regex]::Matches(
        [string]$commandProperty.Value,
        '(?<stem>[A-Za-z0-9_-]+)\.(?:sh|ps1|py)'
    )
    if ($matches.Count -gt 0) {
        return $matches[$matches.Count - 1].Groups["stem"].Value
    }
    return [string]$commandProperty.Value
}

function Merge-ManagedClaudeHooks {
    param(
        [Parameter(Mandatory = $true)][object]$ExistingJson,
        [Parameter(Mandatory = $true)][object]$TemplateJson
    )

    $hooksProperty = $ExistingJson.PSObject.Properties["hooks"]
    if (-not $hooksProperty) {
        $ExistingJson | Add-Member -NotePropertyName "hooks" -NotePropertyValue ([pscustomobject]@{})
    }
    elseif ($null -eq $hooksProperty.Value -or -not ($hooksProperty.Value -is [pscustomobject])) {
        $hooksProperty.Value = [pscustomobject]@{}
    }

    foreach ($eventProperty in $TemplateJson.hooks.PSObject.Properties) {
        $eventName = $eventProperty.Name
        $existingEventProperty = $ExistingJson.hooks.PSObject.Properties[$eventName]
        if (-not $existingEventProperty) {
            $ExistingJson.hooks | Add-Member -NotePropertyName $eventName -NotePropertyValue @($eventProperty.Value)
            continue
        }

        $existingEntries = @($existingEventProperty.Value)
        foreach ($templateEntry in @($eventProperty.Value)) {
            $templateMatcherProperty = $templateEntry.PSObject.Properties["matcher"]
            $templateMatcher = if ($templateMatcherProperty) { [string]$templateMatcherProperty.Value } else { "" }
            foreach ($templateHook in @($templateEntry.hooks)) {
                $templateTypeProperty = $templateHook.PSObject.Properties["type"]
                $templateType = if ($templateTypeProperty) { [string]$templateTypeProperty.Value } else { "" }
                $templateStem = Get-ManagedHookStem -Hook $templateHook
                $alreadyInstalled = $false

                foreach ($existingEntry in $existingEntries) {
                    $existingMatcherProperty = $existingEntry.PSObject.Properties["matcher"]
                    $existingMatcher = if ($existingMatcherProperty) { [string]$existingMatcherProperty.Value } else { "" }
                    if ($existingMatcher -ne $templateMatcher) { continue }
                    foreach ($existingHook in @($existingEntry.hooks)) {
                        $existingTypeProperty = $existingHook.PSObject.Properties["type"]
                        $existingType = if ($existingTypeProperty) { [string]$existingTypeProperty.Value } else { "" }
                        if (
                            $existingType -eq $templateType -and
                            (Get-ManagedHookStem -Hook $existingHook) -eq $templateStem
                        ) {
                            $alreadyInstalled = $true
                            break
                        }
                    }
                    if ($alreadyInstalled) { break }
                }

                if (-not $alreadyInstalled) {
                    $newEntry = [ordered]@{}
                    foreach ($property in $templateEntry.PSObject.Properties) {
                        if ($property.Name -ne "hooks") {
                            $newEntry[$property.Name] = $property.Value
                        }
                    }
                    $newEntry["hooks"] = @($templateHook)
                    $existingEntries += [pscustomobject]$newEntry
                }
            }
        }
        $existingEventProperty.Value = $existingEntries
    }

    return $ExistingJson
}

function Install-GitGuardrails {
    param(
        [string]$RepoRoot,
        [string]$TargetClaudeDir,
        [string]$Scope  # "Global" or "Workspace"
    )

    # Copy every PowerShell/Python hook referenced by the full settings template,
    # including private helper modules sourced by registered hooks.
    Install-ClaudeHookFiles -RepoRoot $RepoRoot -TargetClaudeDir $TargetClaudeDir -Scope $Scope

    # Preserve the legacy explicit copies for compatibility with narrowly staged
    # source bundles while the full catalog copy above owns normal installations.
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

    # Global scope uses ~/.claude/ paths. The parsed template is then converted to
    # PowerShell commands so Cursor and Claude never need Bash on Windows.
    if ($Scope -eq "Global") {
        $templateRaw = $templateRaw -replace '(?<![~/.])\.claude/hooks/', '~/.claude/hooks/'
    }

    $templateJson = $templateRaw | ConvertFrom-Json

    if (Test-Path $settingsFile) {
        try {
            $existingJson = Get-Content $settingsFile -Raw | ConvertFrom-Json
            $existingJson = Merge-ManagedClaudeHooks -ExistingJson $existingJson -TemplateJson $templateJson
            Write-JsonFile -Path $settingsFile -Object $existingJson
            Convert-ClaudeHookCommandsForWindows -SettingsFile $settingsFile -RepoRoot $RepoRoot -Scope $Scope
            Write-Item -Message "✓ $Scope settings.json reconciled with managed hooks" -Color "DarkGreen"
        }
        catch {
            Write-Item -Message "Warning: Could not merge into existing settings.json ($($_.Exception.Message))" -Color "Yellow"
            Write-Item -Message "  You may need to manually add the hook config" -Color "Yellow"
        }
    }
    else {
        # No existing settings.json: write the host-converted template rather than
        # copying its POSIX commands verbatim.
        Write-JsonFile -Path $settingsFile -Object $templateJson
        Convert-ClaudeHookCommandsForWindows -SettingsFile $settingsFile -RepoRoot $RepoRoot -Scope $Scope
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

    # Global scope uses ~/.claude/ paths; convert the parsed hook commands below.
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

            Write-JsonFile -Path $settingsFile -Object $existingJson
            Convert-ClaudeHookCommandsForWindows -SettingsFile $settingsFile -RepoRoot $RepoRoot -Scope $Scope
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
                        command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$hookPath/require-description.ps1`""
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
                        command = "python $hookPath/format-powershell-description.py"
                    }
                )
            }
            $entriesToAdd += [PSCustomObject]@{
                matcher = "PowerShell"
                hooks   = @(
                    [PSCustomObject]@{
                        type    = "command"
                        command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$hookPath/require-powershell-description.ps1`""
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

            Write-JsonFile -Path $settingsFile -Object $existingJson
            $added = ($entriesToAdd | ForEach-Object { $_.matcher }) -join ", "
            Write-Item -Message "✓ $Scope settings.json updated with description hooks ($added)" -Color "DarkGreen"
        }
        Convert-ClaudeHookCommandsForWindows -SettingsFile $settingsFile -RepoRoot $RepoRoot -Scope $Scope
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

        # Treat the scalar and higher-precedence env lever as one user-owned
        # pair. If either exists, preserve the pair exactly; only a config with
        # neither effort key and an absent or object-shaped env receives both
        # defaults.
        $hasScalarEffort = [bool]$existingJson.PSObject.Properties["effortLevel"]
        $hasEnvEffort = (
            $existingJson.PSObject.Properties["env"] -and
            $existingJson.env -is [System.Management.Automation.PSCustomObject] -and
            $existingJson.env.PSObject.Properties["CLAUDE_CODE_EFFORT_LEVEL"]
        )
        $hasAnyEffort = $hasScalarEffort -or $hasEnvEffort

        foreach ($key in $coreKeys) {
            if (-not $templateJson.PSObject.Properties[$key]) { continue }
            if ($key -eq "effortLevel" -and $hasAnyEffort) { continue }
            $templateValue = $templateJson.$key
            if ($existingJson.PSObject.Properties[$key]) {
                continue
            }
            $existingJson | Add-Member -NotePropertyName $key -NotePropertyValue $templateValue
            $applied += "${key}: ${templateValue}"
        }

        # Seed the env effort override with the scalar only when the entire
        # effort pair is absent. Any existing pair shape remains user-owned.
        if (-not $hasAnyEffort -and $templateJson.PSObject.Properties["env"] -and $templateJson.env.PSObject.Properties["CLAUDE_CODE_EFFORT_LEVEL"]) {
            $envEffort = $templateJson.env.CLAUDE_CODE_EFFORT_LEVEL
            if (-not $existingJson.PSObject.Properties["env"]) {
                $existingJson | Add-Member -NotePropertyName "env" -NotePropertyValue ([PSCustomObject]@{})
            }
            if ($existingJson.env -is [System.Management.Automation.PSCustomObject] -and -not $existingJson.env.PSObject.Properties["CLAUDE_CODE_EFFORT_LEVEL"]) {
                $existingJson.env | Add-Member -NotePropertyName "CLAUDE_CODE_EFFORT_LEVEL" -NotePropertyValue $envEffort
                $applied += "env.CLAUDE_CODE_EFFORT_LEVEL: $envEffort"
            }
            elseif ($existingJson.env -isnot [System.Management.Automation.PSCustomObject]) {
                Write-Warning "existing env is not an object; preserving it and skipping env.CLAUDE_CODE_EFFORT_LEVEL"
            }
        }

        if ($applied.Count -eq 0) {
            Write-Item -Message "✓ Core settings already present; existing values preserved in settings.json" -Color "DarkGreen"
            return
        }
        Write-JsonFile -Path $settingsFile -Object $existingJson
        Write-Item -Message "✓ $Scope settings.json seeded absent core settings ($($applied -join ', ')); existing values preserved" -Color "DarkGreen"
    }
    catch {
        Write-Warning "Could not set core settings ($($_.Exception.Message))"
        Write-Warning "Manually copy effortLevel/model/env from $templateFile to $settingsFile"
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

# v3.15.6 / AC5 -- opt-in hardened deny/ask overlay. Mirrors
# merge_strict_permissions() in installer.sh.
#
# Union-merges the `deny` and `ask` arrays from claude-permissions-strict.json
# into settings.json. Three deliberate properties:
#   * ADDITIVE: a user's existing deny/ask entries are never removed.
#   * NO defaultMode: that key's documented value set is unverified in this repo
#     (the v3.16.0 autonomy plan schedules confirming it), and "default" is
#     already Claude Code's behavior, so writing it would be a schema bet on a
#     user's config file with no benefit.
#   * SEPARATE from Install-Permissions: that function returns early in its
#     allow-merge path (nothing new to add, merge failed), so calling this from
#     inside it would silently skip the overlay in the common "allow list already
#     up to date" case. It is invoked from the call site instead.
function Merge-StrictPermissions {
    param(
        [string]$SettingsFile,
        [string]$OverlayFile,
        [string]$Scope
    )

    if (-not (Test-Path $OverlayFile)) {
        Write-Item -Message "Skip: strict permissions overlay not found" -Color "DarkGray"
        return
    }
    if (-not (Test-Path $SettingsFile)) {
        Write-Item -Message "Skip: settings.json not present, cannot apply the strict overlay" -Color "DarkGray"
        return
    }

    try {
        $overlay = Get-Content $OverlayFile -Raw | ConvertFrom-Json
        $existing = Get-Content $SettingsFile -Raw | ConvertFrom-Json

        if (-not $existing.permissions) {
            $existing | Add-Member -NotePropertyName "permissions" -NotePropertyValue ([PSCustomObject]@{})
        }

        $added = 0
        foreach ($key in @("deny", "ask")) {
            $overlayEntries = @($overlay.permissions.$key)
            if ($overlayEntries.Count -eq 0) { continue }

            if (-not ($existing.permissions.PSObject.Properties.Name -contains $key)) {
                $existing.permissions | Add-Member -NotePropertyName $key -NotePropertyValue @()
            }
            $current = @($existing.permissions.$key)
            $merged = @($current + $overlayEntries | Select-Object -Unique)
            $added += ($merged.Count - $current.Count)
            $existing.permissions.$key = $merged
        }

        if ($added -eq 0) {
            Write-Item -Message "[OK] Strict deny/ask entries already up to date (0 new)" -Color "DarkGreen"
            return
        }

        $backupPath = "$SettingsFile.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item -Path $SettingsFile -Destination $backupPath -Force
        Write-Item -Message "  Backup created: $backupPath" -Color "DarkGray"

        Write-JsonFile -Path $SettingsFile -Object $existing
        Write-Item -Message "[OK] $Scope STRICT permission overlay applied ($added new deny/ask entries)" -Color "DarkGreen"
        Write-Item -Message "  Denied: version-control hook/config writes, interpreter paths, git execution-indirection commands" -Color "Gray"
        Write-Item -Message "  Ask: harness settings and hooks, editor task/launch config, editor rules" -Color "Gray"
    }
    catch {
        Write-Item -Message "Warning: Could not merge the strict permission overlay ($($_.Exception.Message))" -Color "Yellow"
    }
}

# v3.17.0 Phase 1.2 -- the single permission-merge path for BOTH installers.
#
# Delegates to scripts/merge_permissions.py, which installer.sh calls identically.
# One implementation, two thin callers.
#
# PARITY DEBT PAID: this installer previously performed its own native JSON merge.
# That merge was a pure union, so an entry DELETED from a shipped template was never
# removed from an existing user's config -- meaning the Phase 1.1 hardening reached
# macOS and Linux users on upgrade and Windows users never. Porting rather than
# re-implementing is the only correct fix: removal safety depends on the shipped-entry
# manifest at ~/.nexus-hub/permissions-manifest.json, and a second implementation of
# that bookkeeping is precisely the drift this phase exists to eliminate.
#
# Returns $true on success, $false when the sync failed.
function Merge-PermissionsViaHelper {
    param(
        [string]$RepoRoot,
        [string]$TemplateFile,
        [string]$SettingsFile,
        [string]$Key,               # permissions.allow | tools.allowed | allowedDomains
        [string]$Platform,          # manifest key: CLAUDE, GEMINI, ...
        [string]$SetTrueKey         # set ONE literal boolean key instead (Copilot)
    )

    $helper = Join-Path $RepoRoot "scripts\merge_permissions.py"
    if (-not (Test-Path $helper)) {
        Write-Item -Message "Warning: merge helper not found at $helper" -Color "Yellow"
        return $false
    }

    $py = Resolve-PythonExecutable
    if (-not $py) {
        Write-Item -Message "Warning: Python not found, cannot sync permissions automatically" -Color "Yellow"
        return $false
    }

    $settingsDir = Split-Path -Parent $SettingsFile
    if ($settingsDir -and -not (Test-Path $settingsDir)) {
        New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null
    }

    $helperArgs = @($helper, "--settings", $SettingsFile)
    if ($SetTrueKey) {
        $helperArgs += @("--set-true", $SetTrueKey)
    }
    else {
        $manifest = Join-Path (Join-Path $env:USERPROFILE ".nexus-hub") "permissions-manifest.json"
        $helperArgs += @("--template", $TemplateFile, "--key", $Key,
                         "--manifest", $manifest, "--platform", $Platform)
    }

    # Deliberately NO `2>&1` here. In Windows PowerShell 5.1 redirecting a native
    # command's stderr wraps each line in an ErrorRecord (NativeCommandError) and
    # sets $? to $false even on a clean exit, which turns a good run into a visible
    # error. The helper reports BOTH its count and its removals on stdout for exactly
    # this reason, so there is nothing to redirect; real errors reach the console
    # on their own.
    $output = & $py @helperArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Item -Message "Warning: could not sync permissions into $SettingsFile" -Color "Yellow"
        return $false
    }

    # Report each retired entry rather than removing anything silently from a file
    # the user may have hand-edited.
    foreach ($line in $output) {
        if ($line -like "removed: *" -or $line -like "set: *") {
            Write-Item -Message "  $line" -Color "DarkGray"
        }
    }
    return $true
}

# v3.17.0 Phase 1.2: the $Scope parameter is now load-bearing. It was documented as
# "Global" or "Workspace" since v0.9.x, but every call site passed "Global" and
# Install-Workspace never called this function at all, so a -Workspace install
# received no permission baseline on any operating system.
#
# Only CLAUDE is wired at workspace scope. The other three skip WITH A NOTE rather
# than guessing:
#   * GEMINI / CODEX -- no project-scoped permission path is documented well enough
#     to write. A guessed path is worse than none: it looks configured and is not.
#   * COPILOT -- its surface is .vscode\settings.json, which is COMMIT-VISIBLE. The
#     plan forbids pushing a permission grant into a user's repository history
#     without an explicit maintainer decision (same reasoning that made the v3.11.0
#     Copilot .github\skills\ surface opt-in).
function Install-Permissions {
    param(
        [string]$RepoRoot,
        [string]$Platform,          # "CLAUDE", "GEMINI", "CODEX", "COPILOT"
        [string]$Scope,             # "Global" or "Workspace"
        [string]$TargetPath         # project root; required when Scope is "Workspace"
    )

    if ($Scope -eq "Workspace") {
        if (-not $TargetPath -or -not (Test-Path $TargetPath)) {
            Write-Item -Message "Skip: workspace permissions need a valid target path" -Color "DarkGray"
            return
        }
        switch ($Platform) {
            "GEMINI" {
                Write-Item -Message "Skip: Gemini has no documented project-scoped permission path (global scope only)" -Color "DarkGray"
                return
            }
            "CODEX" {
                Write-Item -Message "Skip: Codex has no documented project-scoped permission path (global scope only)" -Color "DarkGray"
                return
            }
            "COPILOT" {
                Write-Item -Message "Skip: Copilot's only permission surface is .vscode\settings.json, which is commit-visible" -Color "DarkGray"
                Write-Item -Message "  A workspace grant there would enter your repository history; use a global install instead." -Color "Gray"
                return
            }
        }
    }

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

            if ($Scope -eq "Workspace") {
                # settings.local.json, NEVER settings.json: the latter is
                # commit-visible and would push a permission grant into the user's
                # repository history. Confirmed target (maintainer decision,
                # v3.17.0 Phase 1.2).
                $configDir = Join-Path $TargetPath ".claude"
                $settingsFile = Join-Path $configDir "settings.local.json"
            }

            # v3.17.0: one path for create AND merge, shared with installer.sh. The
            # helper creates the file when absent, unions new entries, retires entries
            # a prior Nexus-Hub version shipped and this one no longer does (never a
            # user's own entry), backs up before any change, writes atomically, and
            # strips the template's `_`-prefixed documentation keys.
            if (Merge-PermissionsViaHelper -RepoRoot $RepoRoot -TemplateFile $templateFile `
                    -SettingsFile $settingsFile -Key "permissions.allow" -Platform "CLAUDE") {
                Write-Item -Message "[OK] $Scope auto-approve permissions synced in settings.json" -Color "DarkGreen"
            }
            else {
                return
            }

            Write-Item -Message "  Auto-approved: file reads, search (Glob/Grep), web search, git read-only commands" -Color "Gray"
            Write-Item -Message "  WebFetch: scoped to trusted domains (see $settingsFile to customize)" -Color "Gray"
            Write-Item -Message "  NOT auto-approved: file writes, destructive commands, git mutations, package installs" -Color "Gray"
            Write-Item -Message "  Config: $settingsFile" -Color "Gray"

            # A workspace grant is only private if the file is actually ignored.
            # settings.local.json is Claude Code's local-only convention, but nothing
            # guarantees THIS repository ignores it, so check rather than assume.
            if ($Scope -eq "Workspace" -and (Get-Command git -ErrorAction SilentlyContinue)) {
                & git -C $TargetPath check-ignore -q $settingsFile
                if ($LASTEXITCODE -ne 0) {
                    Write-Item -Message "  Note: $settingsFile is NOT git-ignored in this project." -Color "DarkYellow"
                    Write-Item -Message "  Add '.claude/settings.local.json' to .gitignore so the grant stays local." -Color "DarkYellow"
                }
            }
        }

        "GEMINI" {
            $configDir = Join-Path $env:USERPROFILE ".gemini"
            $settingsFile = Join-Path $configDir "settings.json"
            $templateFile = Join-Path $permDir "gemini-permissions.json"

            if (-not (Test-Path $templateFile)) {
                Write-Item -Message "Skip: Gemini permissions template not found" -Color "DarkGray"
                return
            }

            # v3.17.0 amendment A3, bug 1: this branch previously gated on fixed
            # sentinels ('"ReadFileTool"' and '"allowedDomains"') to decide whether
            # permissions were already configured. That is the identical stale-marker
            # defect the CLAUDE branch was fixed for, and the bash sibling's
            # `grep -q 'run_shell_command(docker ps)'` twin: because the sentinel
            # entries are present in every existing user's settings.json, the branch
            # returned early forever and those users never received newly-shipped
            # entries -- including, critically, the v3.17.0 Phase 1.1 hardening. The
            # sentinel is replaced by the same count-and-sync helper the CLAUDE branch
            # uses, which is idempotent by construction and needs no marker.
            $geminiOk = $true
            if (-not (Merge-PermissionsViaHelper -RepoRoot $RepoRoot -TemplateFile $templateFile `
                    -SettingsFile $settingsFile -Key "tools.allowed" -Platform "GEMINI")) {
                $geminiOk = $false
            }
            if (-not (Merge-PermissionsViaHelper -RepoRoot $RepoRoot -TemplateFile $templateFile `
                    -SettingsFile $settingsFile -Key "allowedDomains" -Platform "GEMINI_DOMAINS")) {
                $geminiOk = $false
            }
            if ($geminiOk) {
                Write-Item -Message "[OK] $Scope auto-approve permissions synced in settings.json" -Color "DarkGreen"
            }
            else {
                return
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

            # v3.17.0: routed through the shared helper so both installers write this
            # key with one implementation (it takes its own timestamped backup, writes
            # atomically, and no-ops when the key is already true). The bash sibling
            # previously required `jq` here and skipped without it, which is what made
            # its Git-Bash path unreachable.
            if (Merge-PermissionsViaHelper -RepoRoot $RepoRoot -SettingsFile $vscodeSettingsFile `
                    -SetTrueKey "github.copilot.chat.codeGeneration.useInstructionFiles") {
                Write-Item -Message "[OK] $Scope VS Code settings updated with Copilot instruction file support" -Color "DarkGreen"
            }
            else {
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
    # Each main section is a "▶ UPPERCASE" banner (Write-CenteredBanner prepends
    # its own single blank line); there is no separate "Global Installation"
    # super-header - the scope is already stated in the welcome + farewell lines.
    Write-CenteredBanner -Text "SKILLS & COMMANDS"

    # Scope/platform/overwrite are resolved once at startup (v3.7.0 / Phase 2):
    # $script:OverwriteMode and $script:SelectedPlatforms are already set, so no
    # interactive Overwrite/platform prompts here.
    $platforms = $script:SelectedPlatforms
    Reset-UndetectedPlatforms
    Write-Host ""
    Write-Host "Checking User Profile ($env:USERPROFILE)..." -ForegroundColor Gray

    # Per-provider install blocks gated on the --platforms subset
    # ($platforms -contains <KEY>). The output groups by organization
    # (Anthropic / OpenAI / Google / Microsoft / Anysphere / OpenCode / Nexus);
    # each provider has a single colored Write-Header line and its platforms
    # listed underneath.

    # --- Anthropic -- Claude Code ----------------------------------------
    if ($platforms -contains "CLAUDE") {
        Write-Header -Provider "ANTHROPIC"
        $globalClaude = Join-Path $env:USERPROFILE ".claude"
        if (-not (Test-Path $globalClaude)) { New-Item -ItemType Directory -Force -Path $globalClaude | Out-Null }

        # Global CLAUDE.md (concise WHAT/WHY/HOW template).
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

        # Claude is the one bespoke (non-registry) install. Each helper below
        # prints its own progress via Write-Host; run every step quietly
        # (`6>$null` redirects PowerShell's information stream, which is where
        # Write-Host writes since PS 5.0, suppressing the "Merging..." lines and
        # per-step notices) and render ONE unified checklist afterward so Claude
        # reads identically to the registry platforms. DF-001: the registry
        # runner renders CLAUDE.md; the Safe-Folder-Copy block does the mirror.
        # v3.16.1: Get-CatalogSource returns the filtered stage when a selection
        # is active and the real catalog otherwise, so the no-selector path is
        # unchanged.
        Flatten-SkillsInto -Source (Get-CatalogSource -RepoRoot $RepoRoot -Surface "skills")   -Destination (Join-Path $globalClaude "skills")   6>$null
        Safe-Folder-Copy -Source (Get-CatalogSource -RepoRoot $RepoRoot -Surface "commands") -Destination (Join-Path $globalClaude "commands") 6>$null
        Safe-Folder-Copy -Source (Get-CatalogSource -RepoRoot $RepoRoot -Surface "agents")   -Destination (Join-Path $globalClaude "agents")   6>$null
        Safe-Folder-Copy -Source "$RepoRoot\catalog\rules"    -Destination (Join-Path $globalClaude "rules")    6>$null
        # Org rules are seeded by the registry after refresh-mode catalog pruning.
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "claude" -DisplayName "CLAUDE.md (instruction file)" -InstructionOnly 6>$null

        $mcpConfigDest = Join-Path $globalClaude "mcp-configs"
        if (-not (Test-Path $mcpConfigDest)) { New-Item -ItemType Directory -Force -Path $mcpConfigDest | Out-Null }
        Safe-Copy -Source "$RepoRoot\catalog\mcp-configs\mcp-servers.json" -Destination (Join-Path $mcpConfigDest "mcp-servers.json") -Confirm:$false 6>$null

        Install-GitGuardrails      -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global" 6>$null
        Install-UsageDisplay       -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global" 6>$null
        Install-RequireDescription -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global" 6>$null
        Install-CoreSettings       -RepoRoot $RepoRoot -TargetClaudeDir $globalClaude -Scope "Global" 6>$null

        # Unified checklist, built from the resulting on-disk state.
        Write-Item -Message "Claude Code" -Color "Gray"
        if (Test-Path (Join-Path $globalClaude "CLAUDE.md")) { Write-ChecklistRow -Label "Core Files" -State "ok" -Detail (Join-Path $globalClaude "CLAUDE.md") }
        if (Test-Path (Join-Path $globalClaude "skills"))    { Write-ChecklistRow -Label "Skills" -State "ok" -Detail (Join-Path $globalClaude "skills") }
        if (Test-Path (Join-Path $globalClaude "commands"))  { Write-ChecklistRow -Label "Commands" -State "ok" -Detail (Join-Path $globalClaude "commands") }
        if (Test-Path (Join-Path $globalClaude "agents"))    { Write-ChecklistRow -Label "Agents" -State "ok" -Detail (Join-Path $globalClaude "agents") }
        if (Test-Path (Join-Path $globalClaude "rules"))     { Write-ChecklistRow -Label "Rules" -State "ok" -Detail (Join-Path $globalClaude "rules") }
        if (Test-Path (Join-Path $globalClaude "settings.json")) {
            Write-ChecklistRow -Label "Hooks" -State "ok" -Detail "git-guardrails, usage, require-description, compress-output"
            Write-ChecklistRow -Label "Core Settings" -State "ok" -Detail "settings.json retained; existing values preserved (see warnings above)"
        }
    }

    # --- OpenAI -- Codex --------------------------------------------------
    if ($platforms -contains "CODEX") {
        $globalCodexDir = Join-Path $env:USERPROFILE ".codex"
        if (-not (Test-Path $globalCodexDir)) { New-Item -ItemType Directory -Force -Path $globalCodexDir | Out-Null }
        # The codex integration flattens skills to ~/.codex/skills AND
        # ~/.agents/skills, emits every command as a skill plus a legacy prompt,
        # and renders ~/.codex/AGENTS.md. Since v3.15.8 it also writes
        # ~/.codex/agents/*.toml (custom agents) and merges ~/.codex/hooks.json +
        # ~/.codex/hooks/, enabling [features] hooks in ~/.codex/config.toml (see
        # docs/policy/platform-read-contracts.md). Each hook registration carries
        # Codex's commandWindows override, so a Windows user runs the .ps1 sibling
        # of the same guardrail rather than getting no hook at all.
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "codex" -DisplayName "Codex" -Provider "OPENAI"
    }

    # --- Google -- Gemini / Antigravity 2.0 / Gemini CLI ----------------
    # The GOOGLE header is shared by up to three platforms, so it prints eagerly
    # only when a platform that always renders (Gemini IDE / Antigravity 2.0) is
    # selected. Gemini CLI (non-enterprise) is a deliberate skip -> the group.
    $googleRenders = ($platforms -contains "GEMINI") -or ($platforms -contains "ANTIGRAVITY2")
    if ($googleRenders) { Write-Header -Provider "GOOGLE" }
    if ($platforms -contains "GEMINI") {
        $globalGeminiDir = Join-Path $env:USERPROFILE ".gemini"
        if (-not (Test-Path $globalGeminiDir)) { New-Item -ItemType Directory -Force -Path $globalGeminiDir | Out-Null }
        # Renders GEMINI.md and mirrors the catalog to ~/.gemini/{skills,workflows,agents,rules}.
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "gemini" -DisplayName "Gemini IDE"
    }
    if ($platforms -contains "ANTIGRAVITY2") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "antigravity2" -DisplayName "Antigravity 2.0 + CLI"
    }
    if ($platforms -contains "GEMINI_CLI") {
        if ($Enterprise) {
            # GEMINI.md + skills + TOML commands + agents + rules + native hooks
            # merged into ~/.gemini/settings.json (v3.15.8 Phase 6). Gemini CLI has
            # no commandWindows slot, so running from PowerShell registers the .ps1
            # siblings and the PowerShell-flavored guardrails; both siblings ship.
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "gemini-cli" -DisplayName "Gemini CLI" -Provider "GOOGLE"
        }
        else {
            Add-UndetectedPlatform -Name "Gemini CLI" -Reason "enterprise-only; re-run with -Enterprise"
        }
    }

    # --- Microsoft -- GitHub Copilot -------------------------------------
    # VS Code user-profile prompt files (slash commands) + custom agents at
    # ~/.copilot/agents (v3.15.8 Phase 8, verbatim catalog Markdown). Hooks are
    # NOT written: Copilot's default hook locations include ~/.claude/settings.json,
    # which the Claude block above already populates, so they are inherited.
    if ($platforms -contains "COPILOT") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "copilot" -DisplayName "GitHub Copilot" -Provider "MICROSOFT"
    }

    # --- Anysphere -- Cursor ---------------------------------------------
    if ($platforms -contains "CURSOR") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "cursor" -DisplayName "Cursor" -Provider "ANYSPHERE"
    }

    # --- OpenCode --------------------------------------------------------
    if ($platforms -contains "OPENCODE") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "opencode" -DisplayName "OpenCode" -Provider "OPENCODE"
    }

    # --- Aider -----------------------------------------------------------
    if ($platforms -contains "AIDER") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "aider" -DisplayName "Aider" -Provider "AIDER"
    }

    # --- Windsurf --------------------------------------------------------
    if ($platforms -contains "WINDSURF") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "windsurf" -DisplayName "Windsurf" -Provider "WINDSURF"
    }

    # --- Kimi ------------------------------------------------------------
    # AGENTS.md + skills + custom agents (verbatim catalog Markdown) + native
    # hooks as a marker-managed [[hooks]] block in ~/.kimi-code/config.toml
    # (v3.15.8 Phase 7). A PowerShell install registers the .ps1 siblings.
    if ($platforms -contains "KIMI") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "kimi" -DisplayName "Kimi Code CLI" -Provider "KIMI"
    }

    # --- Qwen ------------------------------------------------------------
    # QWEN.md + skills + Markdown commands + agents + native hooks merged into
    # ~/.qwen/settings.json (v3.15.8 Phase 6). A PowerShell install registers the
    # .ps1 siblings and sets Qwen's own shell field to "powershell" to match.
    if ($platforms -contains "QWEN") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "qwen" -DisplayName "Qwen Code" -Provider "QWEN"
    }

    # --- OpenClaw --------------------------------------------------------
    if ($platforms -contains "OPENCLAW") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "openclaw" -DisplayName "OpenClaw" -Provider "OPENCLAW"
    }

    # --- Nexus -- Nexus-AI (Local Desktop Studio) ------------------------
    if ($platforms -contains "NEXUS_AI") {
        Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "global" -IntegrationKey "nexus-ai" -DisplayName "Nexus-AI" -Provider "NEXUS"
    }

    # Platforms whose tool was not detected on this machine (or a scope with no
    # surface, e.g. Aider at global) were collected above; print them once here.
    Write-UndetectedGroup

    # --- Auto-Approve Permissions sub-section ---
    # Permissions only apply to the legacy 4 (CLAUDE / GEMINI / CODEX /
    # COPILOT); the registry-driven platforms do not ship their own
    # auto-approve configs yet. Mirrored to provider headers for visual
    # consistency with the install-skills section above.
    Write-CenteredBanner -Text "AUTO-APPROVE PERMISSIONS"

    if ($platforms -contains "CLAUDE") {
        Write-Header -Provider "ANTHROPIC"
        Install-Permissions -RepoRoot $RepoRoot -Platform "CLAUDE" -Scope "Global"
        # v3.15.6 / AC5: opt-in only. Without -StrictPermissions this is a no-op
        # and the install stays exactly as it was (allow-only, no prompts).
        # Invoked here rather than inside Install-Permissions because that
        # function returns early in its allow-merge path; see the note on
        # Merge-StrictPermissions.
        if ($StrictPermissions) {
            Merge-StrictPermissions `
                -SettingsFile (Join-Path (Join-Path $env:USERPROFILE ".claude") "settings.json") `
                -OverlayFile (Join-Path (Join-Path $RepoRoot "configs\permissions") "claude-permissions-strict.json") `
                -Scope "Global"
        }
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

    # --- Usage Monitor Extensions section (VS Code + Cursor hosts) ---
    Write-CenteredBanner -Text "USAGE MONITOR EXTENSIONS"
    Install-VSCodeExtensions -RepoRoot $RepoRoot

    # --- Cross-Platform Tools: capabilities that apply to every platform, grouped
    # under one section. Skill discovery + the git hook run here; Install-Templates
    # (next in the main flow) adds its own "· Report templates" subsection under
    # this same header.
    Write-CenteredBanner -Text "CROSS-PLATFORM TOOLS"

    Write-SubSectionBanner -Text "Skill discovery"
    Install-SkillDiscovery -RepoRoot $RepoRoot

    Write-SubSectionBanner -Text "Git commit-msg hook"
    Write-Host ""
    Install-GitCommitMsgHook -RepoRoot $RepoRoot
}

function Get-LanguageSelection {
    param([array]$Detected)
    $map = @{ "1" = "Python"; "2" = "JavaScript"; "3" = "TypeScript"; "4" = "Java"; "5" = "C#"; "6" = "Go"; "7" = "C++" }

    # Non-interactive (-Yes / -Force / piped / CI): auto-accept the detected
    # languages with no prompt; fall back to Python when nothing was detected.
    # Keeps a -Workspace install promptless (v3.7.0 / Phase 2).
    if ($script:AssumeYes) {
        if ($Detected.Count -gt 0) { return $Detected }
        return @("Python")
    }

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
    # Main-section banner; no separate "Workspace Installation" super-header - the
    # scope is already stated in the welcome + farewell lines.
    Write-CenteredBanner -Text "SKILLS & COMMANDS"

    if ([string]::IsNullOrWhiteSpace($TargetPath) -or -not (Test-Path $TargetPath)) {
        Write-Host "Invalid target path: $TargetPath" -ForegroundColor Red
        return
    }

    # Single-pass workspace install. To install into multiple workspaces, re-run the installer.
    $targetPath = $TargetPath
    Write-Host ""
    Write-Host "Target: $targetPath" -ForegroundColor DarkYellow

    # Scope/platform/overwrite are resolved once at startup (v3.7.0 / Phase 2):
    # $script:OverwriteMode and $script:SelectedPlatforms are already set, so no
    # interactive Overwrite/platform prompts here.
    Write-Host ""

        $workspacePlatforms = $script:SelectedPlatforms

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

            Flatten-SkillsInto -Source (Get-CatalogSource -RepoRoot $RepoRoot -Surface "skills")   -Destination (Join-Path $claudeDir "skills")   -CustomMessage "✓ Skills catalog installed (flattened) at: $(Join-Path $claudeDir "skills")"
            Safe-Folder-Copy -Source (Get-CatalogSource -RepoRoot $RepoRoot -Surface "commands") -Destination (Join-Path $claudeDir "commands") -CustomMessage "✓ Commands installed at: $(Join-Path $claudeDir "commands")"
            Safe-Folder-Copy -Source (Get-CatalogSource -RepoRoot $RepoRoot -Surface "agents")   -Destination (Join-Path $claudeDir "agents")   -CustomMessage "✓ Agents installed at: $(Join-Path $claudeDir "agents")"
            Safe-Folder-Copy -Source "$RepoRoot\catalog\rules"    -Destination (Join-Path $claudeDir "rules")    -CustomMessage "✓ Rules installed at: $(Join-Path $claudeDir "rules")"
            # Org rules are seeded by the registry after refresh-mode catalog pruning.
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "claude" -DisplayName "CLAUDE.md (instruction file)" -Languages ($languages -join ',') -InstructionOnly

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

            # Full registry mirror (v3.12.0): see the global Codex block. Workspace
            # scope writes .codex/{skills,prompts,agents,hooks}, .codex/hooks.json,
            # .agents/skills (flattened + command skills), and a repo-root AGENTS.md.
            # The [features] hooks switch is user-global, so a workspace install
            # advises rather than editing ~/.codex/config.toml.
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "codex" -DisplayName "Codex (AGENTS.md + skills + commands + agents + hooks)" -Languages ($languages -join ',')
        }

        # --- Google -- Gemini / Antigravity 1.0 + 2.0 / Gemini CLI ------
        $googleWsHas = ($workspacePlatforms -contains "GEMINI") -or ($workspacePlatforms -contains "ANTIGRAVITY2") -or ($workspacePlatforms -contains "GEMINI_CLI")
        if ($googleWsHas) {
            Write-Header -Provider "GOOGLE"

            if ($workspacePlatforms -contains "GEMINI") {
                Write-Item -Message "Gemini IDE" -Color "Gray"
                $geminiDir = Join-Path $targetPath ".gemini"
                if (-not (Test-Path $geminiDir)) { New-Item -ItemType Directory -Force -Path $geminiDir | Out-Null }

                # Full registry mirror (v3.11.0): GEMINI.md + .gemini/{skills,workflows,agents,rules}.
                Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "gemini" -DisplayName "Gemini IDE (GEMINI.md + catalog mirror)" -Languages ($languages -join ',')

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
                    # Project .gemini/ surfaces plus hooks in .gemini/settings.json;
                    # commands resolve via $env:GEMINI_PROJECT_DIR on Windows.
                    Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "gemini-cli" -DisplayName "Gemini CLI (enterprise)"
                }
                else {
                    Write-Item -Message "Gemini CLI: skipped (sunset on 2026-06-18 for free / Google AI Pro / Ultra / GitHub-installed users). Re-run with -Enterprise to install (requires paid Gemini API key); Antigravity CLI above covers the same functionality." -Color "Yellow"
                }
            }
        }

        # --- Microsoft -- GitHub Copilot --------------------------------
        if ($workspacePlatforms -contains "COPILOT") {
            Write-Header -Provider "MICROSOFT"
            # Render .github/copilot-instructions.md via the registry so it carries the
            # {{SKILL_INDEX}} block (from base-codex.md) and is marker-merged, preserving
            # user content above and below the managed block. Fixes C6: the prior
            # hand-built body dropped the skill index and full-overwrote the file
            # (v3.11.0 Phase 7 read-contract audit).
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "copilot" -DisplayName "GitHub Copilot (.github/copilot-instructions.md)" -Languages ($languages -join ',')
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

        # --- Aider ------------------------------------------------------
        if ($workspacePlatforms -contains "AIDER") {
            Write-Header -Provider "AIDER"
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "aider" -DisplayName "Aider (CONVENTIONS.md)" -Languages ($languages -join ',')
        }

        # --- Windsurf ---------------------------------------------------
        if ($workspacePlatforms -contains "WINDSURF") {
            Write-Header -Provider "WINDSURF"
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "windsurf" -DisplayName "Windsurf (.windsurfrules)" -Languages ($languages -join ',')
        }

        # --- Kimi -------------------------------------------------------
        # Project .kimi-code/ AGENTS.md + skills + custom agents. NO hooks at
        # workspace scope: Kimi's project config is local.toml and documents only
        # a [workspace] table, so there is no project hook path to write.
        if ($workspacePlatforms -contains "KIMI") {
            Write-Header -Provider "KIMI"
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "kimi" -DisplayName "Kimi Code CLI (.kimi-code/)" -Languages ($languages -join ',')
        }

        # --- Qwen -------------------------------------------------------
        # Project QWEN.md + .qwen/ surfaces plus hooks in .qwen/settings.json,
        # resolved via $env:QWEN_PROJECT_DIR on Windows (v3.15.8 Phase 6).
        if ($workspacePlatforms -contains "QWEN") {
            Write-Header -Provider "QWEN"
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "qwen" -DisplayName "Qwen Code (QWEN.md)" -Languages ($languages -join ',')
        }

        # --- OpenClaw ---------------------------------------------------
        if ($workspacePlatforms -contains "OPENCLAW") {
            Write-Header -Provider "OPENCLAW"
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "openclaw" -DisplayName "OpenClaw (.openclaw/ SOUL+AGENTS+IDENTITY)" -Languages ($languages -join ',')
        }

        # --- Nexus -- Nexus-AI ------------------------------------------
        if ($workspacePlatforms -contains "NEXUS_AI") {
            Write-Header -Provider "NEXUS"
            Invoke-RegistryPlatform -RepoRoot $RepoRoot -Scope "workspace" -TargetPath $targetPath -IntegrationKey "nexus-ai" -DisplayName "Nexus-AI (Local Desktop Studio)"
        }

        # --- Auto-Approve Permissions sub-section ---
        # v3.17.0 Phase 1.2: previously absent entirely, so a -Workspace install
        # received no permission baseline on any operating system while the $Scope
        # parameter of Install-Permissions sat decorative. Only CLAUDE has a
        # confirmed project-scoped target (.claude\settings.local.json); the other
        # three skip with a note stating why. Gated on the same -Platforms subset
        # as the global block.
        Write-CenteredBanner -Text "AUTO-APPROVE PERMISSIONS"

        if ($workspacePlatforms -contains "CLAUDE") {
            Write-Header -Provider "ANTHROPIC"
            Install-Permissions -RepoRoot $RepoRoot -Platform "CLAUDE" -Scope "Workspace" -TargetPath $targetPath
        }
        if ($workspacePlatforms -contains "CODEX") {
            Write-Header -Provider "OPENAI"
            Install-Permissions -RepoRoot $RepoRoot -Platform "CODEX" -Scope "Workspace" -TargetPath $targetPath
        }
        if ($workspacePlatforms -contains "GEMINI") {
            Write-Header -Provider "GOOGLE"
            Install-Permissions -RepoRoot $RepoRoot -Platform "GEMINI" -Scope "Workspace" -TargetPath $targetPath
        }
        if ($workspacePlatforms -contains "COPILOT") {
            Write-Header -Provider "MICROSOFT"
            Install-Permissions -RepoRoot $RepoRoot -Platform "COPILOT" -Scope "Workspace" -TargetPath $targetPath
        }

        Write-Host ""
}

function Resolve-PythonExecutable {
    if (Get-Command python -ErrorAction SilentlyContinue)  { return "python" }
    if (Get-Command py -ErrorAction SilentlyContinue)      { return "py" }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return "python3" }
    return $null
}

# ---------------------------------------------------------------------------
# Install selection (v3.16.1 Phase 6.2) -- lockstep with the Bash implementation
# in scripts/installer.sh.
#
# Contract: docs/releases/v3/v3.16/development/install-selection-contract.md
#
# Resolution delegates to scripts/lib/installer/selection.py rather than being
# reimplemented in PowerShell, matching the Bash decision and for the same
# reason: one tested implementation of a hashed contract beats several. What the
# plan's "no Python dependency" wording protects is preserved exactly -- these
# functions are only reached when a selector was supplied, so a no-selector full
# install still needs neither Python nor jq.
#
# Filtering is applied by STAGING: a filtered copy of catalog\skills,
# catalog\commands, and catalog\agents is built once and every downstream copy
# reads it via Get-CatalogSource. Only those three surfaces are ever filtered;
# hooks, rules, context, memory, style-guides, and mcp-configs are policy
# infrastructure and always install in full.
# ---------------------------------------------------------------------------

$script:SelectionActive     = $false
$script:SelectionStage      = $null
$script:SelectionHash       = ""
$script:SelectionSkillCount = 0
$script:SelectionCmdCount   = 0
$script:SelectionAgentCount = 0

function Test-SelectionRequested {
    return ($InstallProfile -or $Modules -or $Bundles)
}

function Get-CatalogSource {
    param([string]$RepoRoot, [string]$Surface)
    if ($script:SelectionActive) {
        $staged = Join-Path $script:SelectionStage $Surface
        if (Test-Path $staged) { return $staged }
    }
    return (Join-Path $RepoRoot "catalog\$Surface")
}

function Resolve-Selection {
    param([string]$RepoRoot)

    if (-not (Test-SelectionRequested)) { return }

    $py = Resolve-PythonExecutable
    if (-not $py) {
        Write-Host ""
        Write-Host "ERROR: -Profile / -Modules / -Bundles need Python to resolve." -ForegroundColor Red
        Write-Host "       Install Python 3, or re-run without a selector for a full install" -ForegroundColor Red
        Write-Host "       (a full install requires neither Python nor jq)." -ForegroundColor Red
        exit 2
    }

    $resolver = Join-Path $RepoRoot "scripts\lib\installer\selection.py"
    if (-not (Test-Path $resolver)) {
        Write-Host "ERROR: selection resolver not found at $resolver" -ForegroundColor Red
        exit 3
    }

    $resolverArgs = @($resolver, "--repo-root", $RepoRoot, "--emit", "lines")
    if ($InstallProfile) { $resolverArgs += @("--profile", $InstallProfile) }
    if ($Modules) { $resolverArgs += @("--modules", $Modules) }
    if ($Bundles) { $resolverArgs += @("--bundles", $Bundles) }

    # Deliberately NO `2>&1` here. In Windows PowerShell 5.1 redirecting a native
    # command's stderr wraps each line in an ErrorRecord (NativeCommandError) and
    # sets $? to $false even on a clean exit, which turns a good run into a
    # visible error. The resolver's own stderr already reaches the console, so
    # the user still sees which selector was wrong; we only need the exit code.
    $output = & $py @resolverArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    $script:SelectionStage = Join-Path ([System.IO.Path]::GetTempPath()) ("nexus-selection-" + [System.Guid]::NewGuid().ToString("N"))
    foreach ($surface in @("skills", "commands", "agents")) {
        New-Item -ItemType Directory -Force -Path (Join-Path $script:SelectionStage $surface) | Out-Null
    }

    foreach ($line in $output) {
        $text = [string]$line
        if (-not $text) { continue }
        $parts = $text -split "`t", 2
        if ($parts.Count -lt 2) { continue }
        $kind  = $parts[0].Trim()
        $value = $parts[1].Trim()
        switch ($kind) {
            "HASH" { $script:SelectionHash = $value }
            "SKILL" {
                # Skills live under catalog\skills\<category>\<name>; the stage
                # keeps the category level so a nested-layout copy still works.
                $src = Get-ChildItem -Path (Join-Path $RepoRoot "catalog\skills") -Directory -Recurse -Depth 1 -ErrorAction SilentlyContinue |
                       Where-Object { $_.Name -eq $value -and $_.Parent.Parent.Name -eq "skills" } |
                       Select-Object -First 1
                if ($src) {
                    $destCategory = Join-Path (Join-Path $script:SelectionStage "skills") $src.Parent.Name
                    New-Item -ItemType Directory -Force -Path $destCategory | Out-Null
                    Copy-Item -Path $src.FullName -Destination $destCategory -Recurse -Force
                    $script:SelectionSkillCount++
                }
            }
            "COMMAND" {
                $src = Join-Path $RepoRoot "catalog\commands\$value.md"
                if (Test-Path $src) {
                    Copy-Item -Path $src -Destination (Join-Path $script:SelectionStage "commands") -Force
                    $script:SelectionCmdCount++
                }
            }
            "AGENT" {
                $src = Join-Path $RepoRoot "catalog\agents\$value.md"
                if (Test-Path $src) {
                    Copy-Item -Path $src -Destination (Join-Path $script:SelectionStage "agents") -Force
                    $script:SelectionAgentCount++
                }
            }
            "WARN" {
                Write-Host "WARNING: selection resolved to the entire catalog; '-Profile full' says this directly." -ForegroundColor Yellow
            }
        }
    }

    $script:SelectionActive = $true
}

function Remove-SelectionStage {
    if ($script:SelectionStage -and (Test-Path $script:SelectionStage)) {
        Remove-Item -Path $script:SelectionStage -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-RegistryPlatform {
    param(
        [string]$RepoRoot,
        [string]$Scope,            # "global" or "workspace"
        [string]$TargetPath,       # used for workspace scope only
        [string]$IntegrationKey,   # registry key, e.g. "antigravity2"
        [string]$DisplayName,      # product label printed above the checklist
        [string]$Languages = "",   # csv; appends coding-snippet fragments
        [switch]$InstructionOnly,  # render only the instruction file (skip catalog mirror)
        [string]$Provider = ""     # vendor header; printed lazily only when the platform delivers
    )
    $runner = Join-Path $RepoRoot "scripts\lib\integrations\runner.py"
    if (-not (Test-Path $runner)) { return }
    $py = Resolve-PythonExecutable
    if (-not $py) {
        Write-Item -Message "Python not found -- skipping $DisplayName." -Color "DarkYellow"
        return
    }

    $summaryFile = Join-Path ([System.IO.Path]::GetTempPath()) ("nexus-summary-" + [System.Guid]::NewGuid().ToString('N') + ".json")
    $argsList = @($runner, "install", "--scope", $Scope, "--integrations", $IntegrationKey, "--quiet", "--summary-json", $summaryFile)
    if ($Scope -eq "workspace") {
        $argsList += @("--target", $TargetPath)
    }
    if ($script:OverwriteMode -eq "ALL") { $argsList += "--overwrite" }
    if ($InstructionOnly) { $argsList += "--instruction-only" }
    # v3.16.1 Phase 6.2: forward the selectors so the registry resolves the same
    # plan this script did. Appended as discrete array elements, never
    # interpolated into a command string, so a selector value cannot inject an
    # argument.
    if ($InstallProfile) { $argsList += @("--profile", $InstallProfile) }
    if ($Modules) { $argsList += @("--modules", $Modules) }
    if ($Bundles) { $argsList += @("--bundles", $Bundles) }
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
    $exitCode = $LASTEXITCODE

    # Parse the structured per-surface summary the runner just wrote.
    $platformSummary = $null
    try {
        if (Test-Path $summaryFile) {
            $summary = Get-Content $summaryFile -Raw | ConvertFrom-Json
            $platformSummary = $summary.platforms | Where-Object { $_.platform -eq $IntegrationKey } | Select-Object -First 1
        }
    }
    catch { $platformSummary = $null }
    Remove-Item $summaryFile -Force -ErrorAction SilentlyContinue

    if ($exitCode -ne 0) {
        if ($Provider) { Write-Header -Provider $Provider }
        Write-Item -Message "$DisplayName" -Color "Gray"
        Write-Item -Message "install reported a non-zero exit; continuing." -Color "Yellow"
        return
    }

    # Did the platform actually deliver any surface here?
    $surfaceCount = 0
    if ($platformSummary -and $platformSummary.surfaces) {
        $surfaceCount = @($platformSummary.surfaces.PSObject.Properties).Count
    }
    if ($surfaceCount -eq 0) {
        # Not delivered here (undetected tool, or no surface at this scope).
        $reason = "not detected"
        if ($platformSummary -and $platformSummary.notes -and (@($platformSummary.notes).Count -gt 0) -and -not ($platformSummary.detected -eq $false)) {
            $reason = "no surface at this scope"
        }
        if ($Provider) {
            # Global install: collect into the single grouped section rather than
            # printing a colored header with nothing under it.
            Add-UndetectedPlatform -Name $DisplayName -Reason $reason
        }
        else {
            # Workspace / caller-managed header: keep an inline note so nothing vanishes.
            Write-Item -Message "$DisplayName" -Color "Gray"
            Write-Item -Message "($reason)" -Color "DarkGray" -Indent 4
        }
        return
    }

    # Delivered: lazy vendor header, product label, then the fixed-order checklist.
    if ($Provider) { Write-Header -Provider $Provider }
    Write-Item -Message "$DisplayName" -Color "Gray"
    Write-PlatformChecklist -PlatformSummary $platformSummary
}

function Install-VSCodeExtensions {
    param ($RepoRoot)
    Write-Item -Message "Usage Monitor extensions show Claude Code, Codex (ChatGPT), GitHub, and" -Color "White"
    Write-Item -Message "Cursor usage in the status bar. Claude/Codex/GitHub install into VS Code only;" -Color "White"
    Write-Item -Message "Cursor Usage Monitor installs into Cursor only. Never cross-installed." -Color "White"
    Write-Host ""

    # Check for Node.js (shared by every extension)
    $nodeCmd = Get-Command "node" -ErrorAction SilentlyContinue
    if (-not $nodeCmd) {
        Write-Item -Message "Node.js is not installed (required to build the extensions)." -Color "DarkYellow"
        # A non-interactive run (the piped one-command bootstrap, -Yes, or CI) installs
        # without asking so every dependency is present in one pass; interactive prompts.
        if ($script:AssumeYes) { $installResp = "y" } else { $installResp = Read-Prompt "Install Node.js LTS via winget? [Y]es / [N]o" }
        if ($installResp -match "^[Yy]") {
            # Check for winget
            $wingetCmd = Get-Command "winget" -ErrorAction SilentlyContinue
            if (-not $wingetCmd) {
                Write-Item -Message "winget is not available. Please install Node.js manually from https://nodejs.org" -Color "Red"
                Write-Item -Message "After installing Node.js, re-run this installer to build the extensions." -Color "Yellow"
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
            Write-Item -Message "Skipped. Install Node.js from https://nodejs.org and re-run to build the extensions." -Color "Gray"
            return
        }
    }
    else {
        $nodeVersion = & node --version
        Write-Item -Message "Found Node.js $nodeVersion" -Color "DarkGreen"
    }

    # Check for npm (shared)
    $npmCmd = Get-Command "npm" -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        Write-Item -Message "npm not found. Please ensure Node.js is properly installed." -Color "Red"
        return
    }

    # Suspend strict error mode for native CLI tools (npm/npx write warnings to stderr
    # which PowerShell converts to terminating errors under $ErrorActionPreference = "Stop").
    # Shared across every extension build; restored once at the end.
    $savedErrorPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    # Dual-host resolution (v3.15.9 Phase 6): VS Code CLI and Cursor CLI are
    # discovered independently. Cursor must NEVER be a fallback for the VS Code
    # monitors, and VS Code must NEVER receive the Cursor monitor.
    $vscodeCli = $null
    $vscodeLabel = "VS Code"
    if (Get-Command "code" -ErrorAction SilentlyContinue) {
        $vscodeCli = "code"
    }
    else {
        # Empty env vars collapse to non-existent paths that Test-Path rejects safely.
        $vscodeCandidates = @(
            "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd",
            "$env:ProgramFiles\Microsoft VS Code\bin\code.cmd",
            "${env:ProgramFiles(x86)}\Microsoft VS Code\bin\code.cmd",
            "$env:LOCALAPPDATA\Programs\Microsoft VS Code Insiders\bin\code-insiders.cmd"
        )
        foreach ($candidate in $vscodeCandidates) {
            if ($candidate -and (Test-Path $candidate)) {
                $vscodeCli = $candidate
                break
            }
        }
    }

    $cursorCli = $null
    $cursorLabel = "Cursor"
    if (Get-Command "cursor" -ErrorAction SilentlyContinue) {
        $cursorCli = "cursor"
    }
    else {
        $cursorCandidates = @(
            "$env:LOCALAPPDATA\Programs\cursor\resources\app\bin\cursor.cmd",
            "$env:LOCALAPPDATA\Programs\Cursor\resources\app\bin\cursor.cmd"
        )
        foreach ($candidate in $cursorCandidates) {
            if ($candidate -and (Test-Path $candidate)) {
                $cursorCli = $candidate
                break
            }
        }
    }

    # Build each extension under its own vendor header. VS Code monitors install
    # only via $vscodeCli; the Cursor monitor installs only via $cursorCli. The
    # vendor order (Anthropic, OpenAI, Anysphere) is asserted by the
    # installer smoke test and must match scripts/installer.sh.
    Write-Header -Provider "ANTHROPIC"
    Build-And-Install-One-Extension -ExtensionDir (Join-Path $RepoRoot "extensions\claude-usage-monitor") -ExtensionId "nexus-hub.claude-usage-monitor" -DisplayName "Claude Usage Monitor" -StatusHint "Claude: --%" -CodeCli $vscodeCli -CodeLabel $vscodeLabel

    Write-Header -Provider "OPENAI"
    Build-And-Install-One-Extension -ExtensionDir (Join-Path $RepoRoot "extensions\codex-usage-monitor") -ExtensionId "nexus-hub.codex-usage-monitor" -DisplayName "Codex Usage Monitor" -StatusHint "Codex: --%" -CodeCli $vscodeCli -CodeLabel $vscodeLabel

    Write-Header -Provider "ANYSPHERE"
    Build-And-Install-One-Extension -ExtensionDir (Join-Path $RepoRoot "extensions\cursor-usage-monitor") -ExtensionId "nexus-hub.cursor-usage-monitor" -DisplayName "Cursor Usage Monitor" -StatusHint "Cursor: --%" -CodeCli $cursorCli -CodeLabel $cursorLabel

    # Restore strict error mode
    $ErrorActionPreference = $savedErrorPref
}

# Build, package, and install one VS Code usage-monitor extension. Shared by
# Install-VSCodeExtensions so every monitor installs identically.
function Build-And-Install-One-Extension {
    # $AlsoCodeCli is an optional SECOND host. One VSIX, installed into two editors:
    # Cursor is a separate application with its own extension directory, so an
    # extension installed into VS Code is simply absent there.
    param ($ExtensionDir, $ExtensionId, $DisplayName, $StatusHint, $CodeCli, $CodeLabel, $AlsoCodeCli, $AlsoCodeLabel)

    Write-Host ""
    Write-Host "  > $DisplayName" -ForegroundColor DarkYellow

    if (-not (Test-Path $ExtensionDir)) {
        Write-Item -Message "Extension source not found at: $ExtensionDir" -Color "Red"
        return
    }

    # Build the extension
    Write-Item -Message "Building $DisplayName extension..." -Color "White"
    Push-Location $ExtensionDir

    # Clean compiled output so deleted source files don't linger as stale JS
    $outDir = Join-Path $ExtensionDir "out"
    if (Test-Path $outDir) {
        Remove-Item -Path $outDir -Recurse -Force
    }

    # A node_modules tree copied in from another OS leaves bin shims the current
    # shell cannot exec, so the build fails with a confusing error. Removing it
    # forces a clean, OS-correct dependency tree (mirrors installer.sh).
    $nmDir = Join-Path $ExtensionDir "node_modules"
    if (Test-Path $nmDir) {
        Remove-Item -Path $nmDir -Recurse -Force
    }

    Write-Item -Message "  Installing dependencies..." -Color "Gray"
    $npmOutput = & npm install --silent 2>&1
    Restore-Title
    if ($LASTEXITCODE -ne 0) {
        Write-Item -Message "Build failed: npm install failed" -Color "Red"
        if ($npmOutput) { $npmOutput | Select-Object -Last 20 | ForEach-Object { Write-Item -Message "    $_" -Color "Gray" } }
        Pop-Location
        return
    }

    Write-Item -Message "  Compiling TypeScript..." -Color "Gray"
    $compileOutput = & npm run compile 2>&1
    Restore-Title
    if ($LASTEXITCODE -ne 0) {
        Write-Item -Message "Build failed: TypeScript compilation failed" -Color "Red"
        if ($compileOutput) { $compileOutput | Select-Object -Last 30 | ForEach-Object { Write-Item -Message "    $_" -Color "Gray" } }
        Pop-Location
        return
    }

    Write-Item -Message "✓ Extension built successfully." -Color "DarkGreen"
    Pop-Location

    # Package as VSIX (uses locally installed @vscode/vsce from devDependencies)
    Write-Item -Message "Packaging extension as VSIX..." -Color "White"
    Push-Location $ExtensionDir
    # Capture stdout + stderr so failures surface the real vsce diagnostic
    # (previously swallowed by 2>$null | Out-Null, leaving operators with no clue).
    # The bundled LICENSE removes vsce's only packaging warning, so it no longer
    # shows its interactive "Do you want to continue? [y/N]" prompt; piping "y" is
    # belt-and-suspenders for any future warning on an unattended run.
    $vsceOutput = "y" | & npx vsce package --no-dependencies 2>&1
    Restore-Title
    $vsixExitCode = $LASTEXITCODE
    Pop-Location

    $vsixFile = Get-ChildItem $ExtensionDir -Filter "*.vsix" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if (($vsixExitCode -ne 0) -or (-not $vsixFile)) {
        Write-Item -Message "Packaging failed (exit code: $vsixExitCode)." -Color "Red"
        if ($vsceOutput) {
            Write-Item -Message "vsce output:" -Color "Gray"
            $vsceOutput | ForEach-Object { Write-Item -Message "    $_" -Color "Gray" }
        }
        Write-Item -Message "You can still use the extension in development mode (F5 in VS Code)." -Color "Yellow"
        return
    }

    Write-Item -Message "✓ Packaged: $($vsixFile.Name)" -Color "DarkGreen"

    # Install into the detected editor
    if ($CodeCli) {
        # Uninstall any existing version first so the editor does not skip the reinstall
        & $CodeCli --uninstall-extension $ExtensionId 2>$null | Out-Null
        Restore-Title
        # --force ensures reinstall even when the version number has not changed
        & $CodeCli --install-extension $vsixFile.FullName --force 2>$null | Out-Null
        Restore-Title
        if ($LASTEXITCODE -eq 0) {
            Write-Item -Message "✓ $DisplayName extension installed in $CodeLabel!" -Color "DarkGreen"
            Write-Item -Message "  Restart $CodeLabel to activate. Look for '$StatusHint' in the status bar." -Color "White"
        }
        else {
            Write-Item -Message "$CodeLabel install failed. You can install manually:" -Color "Yellow"
            Write-Item -Message "  `"$CodeCli`" --install-extension `"$($vsixFile.FullName)`"" -Color "White"
        }
    }
    else {
        Write-Item -Message "$CodeLabel CLI not found in PATH or standard install locations." -Color "Yellow"
        Write-Item -Message "VSIX saved at: $($vsixFile.FullName)" -Color "White"
        Write-Item -Message "Install manually via ${CodeLabel}: Extensions > ... > Install from VSIX" -Color "Gray"
    }

    # The second host, when one was requested AND detected. Silent when Cursor is
    # not installed: a missing optional editor is not a failure to report.
    if ($AlsoCodeCli) {
        & $AlsoCodeCli --uninstall-extension $ExtensionId 2>$null | Out-Null
        Restore-Title
        & $AlsoCodeCli --install-extension $vsixFile.FullName --force 2>$null | Out-Null
        Restore-Title
        if ($LASTEXITCODE -eq 0) {
            Write-Item -Message "OK: $DisplayName extension installed in $AlsoCodeLabel!" -Color "DarkGreen"
            Write-Item -Message "  Restart $AlsoCodeLabel to activate. Look for '$StatusHint' in the status bar." -Color "White"
        }
        else {
            Write-Item -Message "$AlsoCodeLabel install failed. You can install manually:" -Color "Yellow"
            Write-Item -Message "  `"$AlsoCodeCli`" --install-extension `"$($vsixFile.FullName)`"" -Color "White"
        }
    }
}

# --- Template & Script Installation ---

function Install-Templates {
    param ($RepoRoot)
    # A "· subsection" under the CROSS-PLATFORM TOOLS section opened in Install-Global.
    Write-SubSectionBanner -Text "Report templates & generator"
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
    # Copy the behavioral-eval schema converter (v3.15.2 / A4). Mirror of the bash
    # block in scripts\installer.sh. Bidirectional, lossless converter between the
    # eval-loop's internal evals.json and the interoperable behavioral-eval schema.
    # Stdlib-only single .py (cross-platform, no .ps1 sibling).
    $evalConvertSource = Join-Path $RepoRoot "scripts\skill_eval_convert.py"
    if (Test-Path $evalConvertSource) {
        Safe-Copy -Source $evalConvertSource -Destination (Join-Path $scriptsDest "skill_eval_convert.py") -Confirm:$true -CustomMessage "✓ Eval-loop schema converter installed at: $scriptsDest\skill_eval_convert.py"
    }

    # Copy the trigger-and-routing eval (v3.15.2 / A1). Mirror of the bash block
    # in scripts\installer.sh. A stdlib-only, model-free detector that flags
    # skill-description trigger-vocabulary near-collisions across the whole
    # catalog, plus its intentional-neighbor allowlist. The runner reads the
    # allowlist from the file beside it, so both must land together under
    # scripts\.
    $triggerEvalsSource = Join-Path $RepoRoot "scripts\run_trigger_evals.py"
    if (Test-Path $triggerEvalsSource) {
        Safe-Copy -Source $triggerEvalsSource -Destination (Join-Path $scriptsDest "run_trigger_evals.py") -Confirm:$true -CustomMessage "✓ Trigger-and-routing eval installed at: $scriptsDest\run_trigger_evals.py"
    }
    # v3.17.0 Phase 1: permission-baseline tooling. Registered in lockstep with
    # scripts/installer.sh -- merge_permissions.py is the single merge implementation
    # BOTH installers call, so a divergence here reintroduces the exact drift that
    # phase repaired. validate_permission_baseline.py guards the read-only baseline.
    $mergePermissionsSource = Join-Path $RepoRoot "scripts\merge_permissions.py"
    if (Test-Path $mergePermissionsSource) {
        Safe-Copy -Source $mergePermissionsSource -Destination (Join-Path $scriptsDest "merge_permissions.py") -Confirm:$true -CustomMessage "✓ Permission merge helper installed at: $scriptsDest\merge_permissions.py"
    }
    $validateBaselineSource = Join-Path $RepoRoot "scripts\validate_permission_baseline.py"
    if (Test-Path $validateBaselineSource) {
        Safe-Copy -Source $validateBaselineSource -Destination (Join-Path $scriptsDest "validate_permission_baseline.py") -Confirm:$true -CustomMessage "✓ Permission-baseline validator installed at: $scriptsDest\validate_permission_baseline.py"
    }

    $triggerEvalsAllowlistSource = Join-Path $RepoRoot "scripts\run_trigger_evals.allowlist.json"
    if (Test-Path $triggerEvalsAllowlistSource) {
        Safe-Copy -Source $triggerEvalsAllowlistSource -Destination (Join-Path $scriptsDest "run_trigger_evals.allowlist.json") -Confirm:$true -CustomMessage "✓ Trigger-eval allowlist installed at: $scriptsDest\run_trigger_evals.allowlist.json"
    }

    # Copy the per-model prompting profile-layer scripts (v3.15.5 Phase 1). Mirror
    # of the bash block in scripts\installer.sh. The structural schema gate for the
    # model-prompting-research skill's profile layer, plus the ADVISORY
    # roster-staleness checker. Both stdlib-only, no outbound call. They must land
    # together: the freshness checker imports the bundle discovery and the
    # canonical roster-hash definition from the validator beside it. The skill
    # bundle itself auto-copies via the recursive skill-folder copy.
    $profileSchemaSource = Join-Path $RepoRoot "scripts\verify_model_prompting_profiles.py"
    if (Test-Path $profileSchemaSource) {
        Safe-Copy -Source $profileSchemaSource -Destination (Join-Path $scriptsDest "verify_model_prompting_profiles.py") -Confirm:$true -CustomMessage "✓ Prompting-profile schema validator installed at: $scriptsDest\verify_model_prompting_profiles.py"
    }
    $profileFreshnessSource = Join-Path $RepoRoot "scripts\check_model_prompting_freshness.py"
    if (Test-Path $profileFreshnessSource) {
        Safe-Copy -Source $profileFreshnessSource -Destination (Join-Path $scriptsDest "check_model_prompting_freshness.py") -Confirm:$true -CustomMessage "✓ Prompting-profile freshness checker installed at: $scriptsDest\check_model_prompting_freshness.py"
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

    # Copy the /skills import hygiene gate (v3.6.0 Phase 4 / N6). Mirror of the
    # bash block in scripts\installer.sh. Hardens the LOCAL import path with
    # HTTPS-only source validation, an install_allowed discovery-only flag, and
    # hash-on-import (hashing reuses scripts\lib\integrations\manifest.py,
    # copied separately under lib\). No outbound call or credential; additive
    # to the pre-install skill-security scan.
    $importHygieneSource = Join-Path $RepoRoot "scripts\import_skills.py"
    if (Test-Path $importHygieneSource) {
        Safe-Copy -Source $importHygieneSource -Destination (Join-Path $scriptsDest "import_skills.py") -Confirm:$true -CustomMessage "✓ Skill-import hygiene gate installed at: $scriptsDest\import_skills.py"
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

    # Copy the nexus-hub CLI core (v3.7.0 Phase 3). The logic behind the
    # `nexus-hub` launcher on PATH: `nexus-hub --version` and `nexus-hub
    # upgrade`. Stdlib-only, cross-platform single .py (NI-v24-1), so no .ps1
    # sibling. The launcher itself + the VERSION file are installed by
    # Install-CliLauncher below. Mirror of the same block in scripts\installer.sh.
    $cliSource = Join-Path $RepoRoot "scripts\nexus_hub_cli.py"
    if (Test-Path $cliSource) {
        Safe-Copy -Source $cliSource -Destination (Join-Path $scriptsDest "nexus_hub_cli.py") -Confirm:$true -CustomMessage "✓ nexus-hub CLI installed at: $scriptsDest\nexus_hub_cli.py"
    }

    # Copy the supply-chain manifest tooling (v3.10.0). generate_manifest.py
    # writes a SHA-256 MANIFEST.sha256 over the distributed catalog tree at
    # release time; verify_install.py powers `nexus-hub verify`, which recomputes
    # those hashes against the installed tree and reports OK/MODIFIED/MISSING/
    # EXTRA with zero outbound call. Both are stdlib-only single .py files
    # (NI-v24-1, no .ps1 sibling -- the nexus-hub.cmd launcher already covers
    # Windows via nexus_hub_cli.py). The MANIFEST.sha256 (committed at the repo
    # root by the release flow) is copied to the install root as a known-location
    # convenience; `nexus-hub verify` primarily reads the copy that rides inside
    # the materialized source tree (~\.nexus-hub\src\MANIFEST.sha256). Mirror of
    # the same block in scripts\installer.sh.
    $genManifestSource = Join-Path $RepoRoot "scripts\generate_manifest.py"
    if (Test-Path $genManifestSource) {
        Safe-Copy -Source $genManifestSource -Destination (Join-Path $scriptsDest "generate_manifest.py") -Confirm:$true -CustomMessage "✓ Manifest generator installed at: $scriptsDest\generate_manifest.py"
    }
    $verifySource = Join-Path $RepoRoot "scripts\verify_install.py"
    if (Test-Path $verifySource) {
        Safe-Copy -Source $verifySource -Destination (Join-Path $scriptsDest "verify_install.py") -Confirm:$true -CustomMessage "✓ Install verifier installed at: $scriptsDest\verify_install.py"
    }
    # setup_media_keys.py powers `nexus-hub setup-media`, the opt-in guided
    # bring-your-own-key helper for optional stock-media API keys (Pexels, for
    # stock video). Stdlib-only single .py (NI-v24-1, no .ps1 sibling -- the
    # nexus-hub.cmd launcher covers Windows via nexus_hub_cli.py, where the
    # setup-media subcommand is dispatched). Mirror of scripts\installer.sh.
    $mediaSetupSource = Join-Path $RepoRoot "scripts\setup_media_keys.py"
    if (Test-Path $mediaSetupSource) {
        Safe-Copy -Source $mediaSetupSource -Destination (Join-Path $scriptsDest "setup_media_keys.py") -Confirm:$true -CustomMessage "✓ Media-key setup helper installed at: $scriptsDest\setup_media_keys.py"
    }
    $manifestSource = Join-Path $RepoRoot "MANIFEST.sha256"
    if (Test-Path $manifestSource) {
        Safe-Copy -Source $manifestSource -Destination (Join-Path $nexusHome "MANIFEST.sha256") -Confirm:$true -CustomMessage "✓ Supply-chain manifest installed at: $nexusHome\MANIFEST.sha256"
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
    # check_release_preconditions.py (v3.17.6): release-flow guard. --pre-tag
    # refuses to tag unless HEAD is the expected release branch AND matches its
    # remote (the v3.17.5 mis-tag: a checkout failed on a locked directory and
    # the tag was created on the wrong commit). --branches and --repo-settings
    # report merged remote branches and delete_branch_on_merge, advisory only,
    # deleting nothing. Stdlib-only, so it is a single cross-platform .py file
    # with no .ps1 sibling (NI-v24-1 convention). Distributed because
    # /update release ships to users and must not describe a check they lack.
    # Mirror of the bash block in scripts\installer.sh.
    $releasePrecondSource = Join-Path $RepoRoot "scripts\check_release_preconditions.py"
    if (Test-Path $releasePrecondSource) {
        Safe-Copy -Source $releasePrecondSource -Destination (Join-Path $scriptsDest "check_release_preconditions.py") -Confirm:$true -CustomMessage "✓ Release-preconditions guard installed at: $scriptsDest\check_release_preconditions.py"
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
    # v3.16.1 (NI-3): copy the WHOLE scripts\lib tree, not just integrations\.
    # Six integration modules import from scripts\lib\installer\ (three at module
    # top level), so copying only integrations\ produced an installed tree that
    # looked importable and was not. Lockstep with the bash block.
    $libSrc = Join-Path $RepoRoot "scripts\lib"
    $libDest = Join-Path $scriptsDest "lib"
    if (Test-Path $libSrc) {
        Safe-Folder-Copy -Source $libSrc -Destination $libDest -CustomMessage "✓ Integration registry installed at: $(Join-Path $libDest 'integrations')"
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

        # v3.16.0 Phase 3: optional seeding dependencies. Platform install-time
        # behavioral defaults (configs/platform-defaults.json) are seeded into each
        # platform's own config. JSON targets use the stdlib; TOML targets need
        # tomlkit (which round-trips a user's comments and layout rather than
        # rewriting them) and YAML targets need PyYAML. Both are OPTIONAL: without
        # them the affected platforms simply skip seeding with a one-line hint, so
        # a missing library never breaks an install.
        $savedErrorPref = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & python -c "import tomlkit; import yaml" 2>$null | Out-Null
        $seedDepCheck = $LASTEXITCODE
        $ErrorActionPreference = $savedErrorPref

        if ($seedDepCheck -ne 0) {
            Write-Item -Message "Note: Install platform-defaults seeding deps with: pip install tomlkit PyYAML" -Color "Yellow"
            Write-Item -Message "      (without them, TOML/YAML platform defaults are skipped; JSON platforms are unaffected)" -Color "Yellow"
        }
        else {
            Write-Item -Message "✓ Python dependencies (tomlkit, PyYAML) are available" -Color "DarkGreen"
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
    # No trailing blank: the next section banner prepends its own single blank.
}


# --- nexus-hub CLI launcher (v3.7.0 Phase 3) ---

# Writes the installed-version marker and drops the nexus-hub.cmd launcher on
# PATH (~\.nexus-hub\bin\nexus-hub.cmd). The launcher is a thin shim over the CLI
# core (scripts\nexus_hub_cli.py, copied by Install-Templates) that powers
# `nexus-hub --version` and `nexus-hub upgrade`. upgrade's only outbound call is
# to the project's own GitHub. PATH wiring is best-effort: a clear hint is
# printed and PATH is NEVER auto-edited (a no-prompt install must not silently
# mutate the user's environment). Mirror of install_cli_launcher in
# scripts\installer.sh.
function Install-CliLauncher {
    param ($RepoRoot)

    $nexusHome = Join-Path $env:USERPROFILE ".nexus-hub"
    $binDest = Join-Path $nexusHome "bin"

    Write-CenteredBanner -Text "NEXUS-HUB CLI"
    Write-Host ""

    # Installed-version marker (read by the CLI's --version and upgrade).
    # Written from the canonical $script:NexusHubVersion as ASCII (no BOM), so it
    # is deliberately NOT a check_version_sync surface (never hand-edited).
    $versionFile = Join-Path $nexusHome "VERSION"
    if (-not (Test-Path $nexusHome)) { New-Item -ItemType Directory -Force -Path $nexusHome | Out-Null }
    Set-Content -Path $versionFile -Value $script:NexusHubVersion -Encoding ascii -NoNewline
    Write-Item -Message "✓ Version marker written: $versionFile ($script:NexusHubVersion)" -Color "DarkGreen"

    if (-not (Test-Path $binDest)) { New-Item -ItemType Directory -Force -Path $binDest | Out-Null }
    $launcherSource = Join-Path $RepoRoot "scripts\nexus-hub.cmd"
    if (Test-Path $launcherSource) {
        Safe-Copy -Source $launcherSource -Destination (Join-Path $binDest "nexus-hub.cmd") -Confirm:$true -CustomMessage "✓ nexus-hub launcher installed at: $binDest\nexus-hub.cmd"
    }

    # PATH hint (best-effort; never auto-edits the user's PATH).
    $pathEntries = @($env:PATH -split ';')
    if ($pathEntries -contains $binDest) {
        Write-Item -Message "✓ $binDest is already on your PATH -- run: nexus-hub --version" -Color "DarkGreen"
    }
    else {
        Write-Item -Message "To use the 'nexus-hub' command, add its bin directory to your PATH." -Color "Yellow"
        Write-Item -Message "  Run this once in PowerShell (appends to your user PATH), then reopen your terminal:" -Color "White"
        Write-Item -Message "    [Environment]::SetEnvironmentVariable('PATH', `"`$([Environment]::GetEnvironmentVariable('PATH','User'));$binDest`", 'User')" -Color "Cyan"
        Write-Item -Message "  Until then, run it directly: $binDest\nexus-hub.cmd --version" -Color "Gray"
    }
}


# --- Project auto-seed + on-open hook (v3.11.0 Phase 7.3) ---
#
# Lockstep with install_project_autoseed in scripts\installer.sh. Ships the opt-in
# "seed on project open" hook and, on a global install run from inside a git work
# tree, seeds the current repo's project surfaces (Antigravity .agents/, Cursor,
# Claude stub). Per the no-auto-rc-edit policy the hook is installed and its enable
# line printed; the current-repo seed is automatic. Opt out with
# $env:NEXUS_HUB_NO_AUTOSEED = "1".
function Install-ProjectAutoseed {
    param ($RepoRoot, $ScopeLabel)

    $nexusHome = Join-Path $env:USERPROFILE ".nexus-hub"
    $hooksDest = Join-Path $nexusHome "hooks"
    $runner = Join-Path $RepoRoot "scripts\lib\integrations\runner.py"

    # A "· subsection" folded under the INSTALL VERIFICATION section: it is the
    # project-scoped follow-up to any NEEDS-ACTION hints the verify step printed.
    Write-SubSectionBanner -Text "Project seeding (this repo + other projects)"
    Write-Host ""

    # Ship the on-open hook script regardless of scope.
    if (-not (Test-Path $hooksDest)) { New-Item -ItemType Directory -Force -Path $hooksDest | Out-Null }
    $hookSrc = Join-Path $RepoRoot "scripts\nexus-hub-autoseed.ps1"
    if (Test-Path $hookSrc) {
        Safe-Copy -Source $hookSrc -Destination (Join-Path $hooksDest "nexus-hub-autoseed.ps1") -Confirm:$true -CustomMessage "✓ on-open hook installed at: $(Join-Path $hooksDest "nexus-hub-autoseed.ps1")"
    }

    # Auto-seed the current repo on a GLOBAL install run from inside a git work tree
    # (a workspace install already seeded its target). Skips the source cache and
    # honors the opt-out.
    if ($ScopeLabel -eq "Global" -and $env:NEXUS_HUB_NO_AUTOSEED -ne "1") {
        $py = $null
        foreach ($c in @("python", "py", "python3")) {
            if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break }
        }
        if ($py -and (Test-Path $runner)) {
            $cwd = (Get-Location).Path
            if (-not ($cwd -eq $nexusHome -or $cwd.StartsWith($nexusHome))) {
                $inRepo = $false
                try { $null = (& git -C $cwd rev-parse --is-inside-work-tree 2>$null); if ($LASTEXITCODE -eq 0) { $inRepo = $true } } catch { }
                if ($inRepo) {
                    Write-Item -Message "Seeding project surfaces in the current repo: $cwd" -Color "Gray"
                    if ($py -eq "py") { & $py -3 $runner init --target $cwd --quiet *> $null } else { & $py $runner init --target $cwd --quiet *> $null }
                    Write-Item -Message "✓ Current repo seeded (Antigravity .agents/, Cursor rules, Claude stub)." -Color "DarkGreen"
                }
            }
        }
    }

    Write-Item -Message "To surface Nexus-Hub in another project, run inside it:  nexus-hub init" -Color "Yellow"
    Write-Item -Message "Optional 'seed on project open' hook (opt-in; the installer never edits your profile):" -Color "White"
    Write-Item -Message '  Add to $PROFILE:  . "$HOME\.nexus-hub\hooks\nexus-hub-autoseed.ps1"' -Color "Cyan"
    Write-Item -Message '  Disable auto-seed anytime with: $env:NEXUS_HUB_NO_AUTOSEED = "1"' -Color "Gray"
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
    $detectPython310 = {
        foreach ($cmd in @("python", "python3")) {
            try {
                $ver = & $cmd --version 2>&1
                if ($ver -match "Python\s+3\.(\d+)") {
                    if ([int]$Matches[1] -ge 10) { return $cmd }
                }
            }
            catch {}
        }
        return $null
    }
    $pythonCmd = & $detectPython310

    # Offer to auto-install Python when it is missing or too old, mirroring the
    # Node.js auto-install flow so every dependency is handled in a single run. A
    # non-interactive run (the piped one-command bootstrap, -Yes, or CI) installs
    # without asking. Only fires when no usable Python exists, so it never shadows
    # an existing conda/pyenv interpreter.
    if (-not $pythonCmd) {
        $wingetCmd = Get-Command "winget" -ErrorAction SilentlyContinue
        if ($wingetCmd) {
            if ($script:AssumeYes) { $pyResp = "y" } else { $pyResp = Read-Prompt "Python 3.10+ not found. Install it via winget? [Y]es / [N]o" }
            if ($pyResp -match "^[Yy]") {
                Write-Item -Message "  Installing Python via winget..." -Color "White"
                try {
                    & winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
                    # Refresh PATH for the current session so the new python resolves.
                    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                    $pythonCmd = & $detectPython310
                }
                catch {}
            }
        }
    }
    $ErrorActionPreference = "Stop"

    if (-not $pythonCmd) {
        Write-Item -Message "  Python 3.10+ not found. MCP server requires Python 3.10 or newer." -Color "Yellow"
        Write-Item -Message "  Install Python from https://python.org (or: winget install Python.Python.3.12) and re-run." -Color "Yellow"
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
        # Repository-only measurement evidence must not reach user machines.
        $codeSearchBenchmarks = Join-Path $codeSearchDest "benchmarks"
        if (Test-Path $codeSearchBenchmarks) { Remove-Item -Path $codeSearchBenchmarks -Recurse -Force }
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

    # Install nexus-memory into the same venv (v3.19.1+). Local persistent
    # agent-memory CLI. Stdlib only, zero outbound, not an MCP server. Dest
    # is $nexusHome\nexus-memory so it does not collide with the default
    # store root $nexusHome\memory.
    $memorySrc = Join-Path $RepoRoot "extensions\nexus-memory"
    $memoryDest = Join-Path $nexusHome "nexus-memory"
    if (Test-Path $memorySrc) {
        if (Test-Path $memoryDest) { Remove-Item -Path $memoryDest -Recurse -Force }
        Copy-Item -Path $memorySrc -Destination $memoryDest -Recurse -Force
        if ($hasUv) {
            & uv pip install --python "$venvPath\Scripts\python.exe" -e "$memoryDest" 2>$null | Out-Null
        } else {
            & "$venvPath\Scripts\pip.exe" install -q -e "$memoryDest" 2>$null | Out-Null
        }
        Write-Item -Message "  nexus-memory installed at $memoryDest" -Color "DarkGreen"
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

    Write-JsonFile -Path $claudeSettings -Object $settings
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
    # nexus-hub.github-usage-monitor was WITHDRAWN in v3.18.2. It reconstructed the
    # included-usage meter from data GitHub does not publish, and could report a
    # confident 0% against an exhausted allowance. Leaving it installed keeps that
    # wrong number on a user's status bar forever, so it is actively uninstalled
    # rather than merely unshipped.
    $legacyIds = @("devai-hub.claude-usage-monitor", "nexus-hub.github-usage-monitor")

    # Both hosts, not just VS Code. The GitHub monitor was the one dual-host
    # monitor, installed to Cursor as well, so a VS Code-only sweep would leave the
    # Cursor copy running.
    $emitted = $false
    foreach ($cli in @("code", "cursor")) {
        $cliCmd = Get-Command $cli -ErrorAction SilentlyContinue
        if (-not $cliCmd) { continue }
        $installed = & $cli --list-extensions 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $installed) { continue }
        foreach ($id in $legacyIds) {
            if ($installed -contains $id) {
                if (-not $emitted) { Write-Host "" }
                Write-Host "  Removing retired extension from ${cli}: $id" -ForegroundColor Yellow
                & $cli --uninstall-extension $id 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  [OK] Removed $id from $cli" -ForegroundColor Green
                } else {
                    Write-Host "  [!] Could not auto-remove $id (uninstall it manually from $cli)" -ForegroundColor Yellow
                }
                $emitted = $true
            }
        }
    }
    if ($emitted) { Write-Host "" }
}

# Detects an existing ~/.devai-hub/ install and migrates it to ~/.nexus-hub/.
# One-shot, one-way per the backward-compat decision in
# docs/archive/v2/v2.0/rename-decisions.md. The installer does NOT ship a symlink or
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
    if ($Workspace) { $branchPassthru += @("-Workspace", $Workspace) }
    if ($Platforms) { $branchPassthru += @("-Platforms", $Platforms) }
    if ($Yes) { $branchPassthru += "-Yes" }
    if ($Force) { $branchPassthru += "-Force" }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $cachedInstaller @branchPassthru
    exit $LASTEXITCODE
}

# --- nexus-hub doctor (v3.16.2 Phase 5) ---------------------------------
#
# Sibling of run_doctor() in installer.sh. Behavior and EXIT CODES must match
# the Bash version for the same machine state; that parity is asserted by test
# (tests/installer/test_doctor_parity.py), not assumed from this file existing.
# Both backfilled incidents in docs/incidents/ are about exactly this class of
# change, and their durable fixes are requirements here.
#
# Native equivalents rather than emulated shell mechanics: ConvertFrom-Json
# instead of a jq dependency, and [System.IO.File]::ReadAllText for the
# contains-check. Nothing is written, so the UTF8Encoding/BOM hazard that
# produced the v3.15.6 divergence cannot arise here -- a read-only command has
# no encoding surface.
#
# NETWORK: none. Do not add one; it is what keeps this `re-full` under the MCP
# Registry Policy.
#
# Exit codes: 0 every detected platform complete, 1 at least one incomplete,
# 2 the contract could not be read or parsed (never a false CLEAR).
function Resolve-DoctorContractPath {
    # NEXUS_DOCTOR_CONTRACT pins the contract explicitly, mirroring the Bash
    # override. When set it is used even if absent, so the fail-loud path stays
    # testable.
    if ($env:NEXUS_DOCTOR_CONTRACT) { return $env:NEXUS_DOCTOR_CONTRACT }
    $candidates = @(
        (Join-Path $repoRoot "docs\policy\platform-read-contracts.json"),
        (Join-Path $HOME ".nexus-hub\src\docs\policy\platform-read-contracts.json"),
        (Join-Path $HOME ".nexus-hub\docs\policy\platform-read-contracts.json")
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c -PathType Leaf) { return $c }
    }
    return $null
}

function Resolve-DoctorPath {
    param([string]$Spec, [string]$TargetRoot)
    if ($Spec.StartsWith("~/")) { return (Join-Path $HOME $Spec.Substring(2)) }
    if ($Spec.StartsWith("{project}/")) { return (Join-Path $TargetRoot $Spec.Substring(10)) }
    return $Spec
}

function Test-DoctorSurface {
    param([string]$Kind, [string]$Path, [string]$Needle)
    switch ($Kind) {
        "nonempty_dir" {
            if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return $false }
            # An existing but EMPTY directory is a failed surface: it surfaces
            # nothing to the platform that reads it.
            $entries = @(Get-ChildItem -LiteralPath $Path -Force -ErrorAction SilentlyContinue)
            return ($entries.Count -gt 0)
        }
        "is_file" { return (Test-Path -LiteralPath $Path -PathType Leaf) }
        "file_contains" {
            if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
            try { $text = [System.IO.File]::ReadAllText($Path) } catch { return $false }
            return $text.Contains($Needle)
        }
        default {
            # An unknown kind is a contract this doctor does not understand.
            # Fail it, so a contract addition cannot silently widen CLEAR.
            return $false
        }
    }
}

function Invoke-NexusDoctor {
    param([string[]]$DoctorArgs)

    $targetRoot = (Get-Location).Path
    $showRepair = $false
    for ($i = 0; $i -lt $DoctorArgs.Count; $i++) {
        $a = $DoctorArgs[$i]
        if ($a -eq "--target") { $targetRoot = $DoctorArgs[$i + 1]; $i++ }
        elseif ($a -like "--target=*") { $targetRoot = $a.Substring(9) }
        elseif ($a -eq "--repair") { $showRepair = $true }
        else {
            [Console]::Error.WriteLine("doctor: unknown argument: $a")
            return 2
        }
    }

    $json = Resolve-DoctorContractPath
    if (-not $json) {
        [Console]::Error.WriteLine("[doctor] FATAL: platform read-contract not found.")
        [Console]::Error.WriteLine("         Looked in the repo checkout and ~/.nexus-hub/.")
        [Console]::Error.WriteLine("         Refusing to report a result without the contract.")
        return 2
    }
    if (-not (Test-Path -LiteralPath $json -PathType Leaf)) {
        [Console]::Error.WriteLine("[doctor] FATAL: could not parse $json")
        [Console]::Error.WriteLine("         Refusing to report CLEAR on an unreadable contract.")
        return 2
    }
    try {
        $data = [System.IO.File]::ReadAllText($json) | ConvertFrom-Json
    } catch {
        [Console]::Error.WriteLine("[doctor] FATAL: could not parse $json")
        [Console]::Error.WriteLine("         Refusing to report CLEAR on an unreadable contract.")
        return 2
    }
    $entries = $data.install_verify
    if (-not $entries -or @($entries).Count -eq 0) {
        [Console]::Error.WriteLine("[doctor] FATAL: install_verify block is empty or missing in $json")
        return 2
    }

    Write-Host "[doctor] contract: $json"
    Write-Host "[doctor] project:  $targetRoot"
    Write-Host ""

    $nPass = 0; $nFail = 0; $nSkip = 0
    $repairLines = @()

    foreach ($entry in @($entries)) {
        $label = [string]$entry.label
        $detected = $false
        foreach ($d in @($entry.detect)) {
            if (-not $d) { continue }
            if (Test-Path -LiteralPath (Resolve-DoctorPath -Spec ([string]$d) -TargetRoot $targetRoot)) {
                $detected = $true
                break
            }
        }
        if (-not $detected) {
            Write-Host ("  SKIP  {0,-38} not installed on this machine" -f $label)
            $nSkip++
            continue
        }
        $parts = @()
        $anyMissing = $false
        foreach ($s in @($entry.surfaces)) {
            $resolved = Resolve-DoctorPath -Spec ([string]$s.path) -TargetRoot $targetRoot
            $needle = if ($null -ne $s.needle) { [string]$s.needle } else { "" }
            $ok = Test-DoctorSurface -Kind ([string]$s.kind) -Path $resolved -Needle $needle
            if ($ok) { $parts += ("{0}:ok" -f $s.label) }
            else { $parts += ("{0}:MISSING" -f $s.label); $anyMissing = $true }
        }
        $detail = ($parts -join ", ")
        if ($anyMissing) {
            Write-Host ("  FAIL  {0,-38} {1}" -f $label, $detail)
            if ($entry.remediation) {
                Write-Host ("        -> {0}" -f $entry.remediation)
                $repairLines += ("{0}: {1}" -f $label, $entry.remediation)
            }
            $nFail++
        } else {
            Write-Host ("  PASS  {0,-38} {1}" -f $label, $detail)
            $nPass++
        }
    }

    Write-Host ""
    Write-Host "[doctor] $nPass complete, $nFail incomplete, $nSkip not installed."

    if ($nFail -gt 0) {
        if ($showRepair) {
            Write-Host ""
            Write-Host "[doctor] --repair: the following would fix the failures above."
            Write-Host "[doctor] NOTHING WAS CHANGED. Run these yourself:"
            foreach ($line in $repairLines) { Write-Host ("         {0}" -f $line) }
        } else {
            Write-Host "[doctor] re-run with --repair to print the remediation commands."
        }
        return 1
    }
    Write-Host "[doctor] every detected platform surfaces the catalog."
    return 0
}

# `doctor` is self-contained: it reads the contract and evaluates every surface
# in this script, so it runs even where the Python runner is unavailable.
if ($Subcommand -eq "doctor") {
    $doctorArgs = @()
    if ($SubcommandArgs) { $doctorArgs = $SubcommandArgs }
    exit (Invoke-NexusDoctor -DoctorArgs $doctorArgs)
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
        # v3.15.6 / HO-2: declare installer-owned intent for the
        # escalation-trigger carve-out, which suppresses the sensitive-path
        # advisory for the project surfaces `init` legitimately writes
        # (.claude/settings.json, .cursor/rules, .agents/, .github/skills).
        # Mirrors the bash installer.
        #
        # Scope this honestly. Claude Code's PreToolUse Write/Edit hooks observe
        # the AGENT's tool calls, not this process, so `init`'s own writes never
        # reach that hook and were never going to warn. What this buys is an
        # explicit intent marker for any hook chain that DOES wrap the installer,
        # and lockstep with installer.sh. The carve-out's practical consumer is an
        # operator setting the same variable for a deliberate setup pass.
        #
        # It is NOT a security control: an agent can set this variable itself, so
        # it is self-asserted. That is acceptable only because the hook is
        # advisory, so the carve-out suppresses a warning and never grants a
        # capability. Do not promote it to a boundary.
        $env:NEXUS_HUB_INIT = "1"
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

# --- Resolve no-prompt install configuration (v3.7.0 / Phase 2) ----------
# Conflict accumulators (interactive mode only) + temp files for deferred writes.
$script:ConflictSrcs = @()
$script:ConflictDsts = @()
$script:TempFiles = @()

# Validate -Platforms into the internal platform-key set (empty/absent = all).
$script:SelectedPlatforms = Resolve-Platforms -PlatformsArg $Platforms

# --- Resolve the install selection (v3.16.1 Phase 6.2) -------------------
# Deliberately beside the -Platforms validation above and BEFORE any write: an
# invalid selector must never leave a half-installed tree. A run with no
# selector returns immediately and takes the identical path it always did.
Resolve-Selection -RepoRoot $repoRoot
if ($script:SelectionActive) {
    Write-Host ""
    Write-Host "Selection: $($script:SelectionSkillCount) skills, $($script:SelectionCmdCount) commands, $($script:SelectionAgentCount) agents"
    Write-Host "           $($script:SelectionHash)"
}

# Resolve the assume-yes / overwrite decision. -Yes or -Force force it; a
# non-interactive stdin (piped irm|iex, CI) also implies it. In that case
# existing managed files are refreshed silently (OverwriteMode "ALL");
# otherwise interactive conflicts are collected and resolved once.
$script:AssumeYes = $Yes -or $Force -or [Console]::IsInputRedirected -or (-not [Environment]::UserInteractive)
if ($script:AssumeYes) {
    $script:OverwriteMode = "ALL"
}
else {
    $script:OverwriteMode = "CONFLICT"
}

Write-NexusBanner
Invoke-LegacyInstallMigration
# Idempotent cleanup -- safe to run every install. Catches the case where the
# user already migrated ~/.devai-hub/ in an earlier run (before this cleanup
# existed) but still has devai-hub.claude-usage-monitor installed in VS Code.
Remove-LegacyVSCodeExtensions
Show-WelcomeBanner

# Scope is resolved from -Workspace (no interactive scope/platform prompt).
# Default = global install across all platforms.
$scopeLabel = "Global"
if (-not [string]::IsNullOrWhiteSpace($Workspace)) {
    $scopeLabel = "Workspace"
    $workspaceTarget = $Workspace
    if (-not (Test-Path $workspaceTarget)) {
        Write-Host "Workspace path not found: $workspaceTarget" -ForegroundColor Red
        exit 2
    }
    Install-Workspace -RepoRoot $repoRoot -TargetPath $workspaceTarget
}
else {
    Install-Global -RepoRoot $repoRoot
}

# CROSS-PLATFORM TOOLS: for a global install this header (plus the skill-discovery
# and git-hook subsections) was already opened inside Install-Global; a workspace
# install skips those global-only tools, so open the header here so the report
# templates below still render under a section rather than orphaned.
if ($scopeLabel -eq "Workspace") { Write-CenteredBanner -Text "CROSS-PLATFORM TOOLS" }

# Bundled report-generator templates + scripts are user-scope and always install silently.
# Interactive custom-template import moved to /research report at use time (v0.9.7).
Install-Templates -RepoRoot $repoRoot

# Install the nexus-hub CLI launcher + version marker (v3.7.0 Phase 3).
Install-CliLauncher -RepoRoot $repoRoot

# --- INSTALL VERIFICATION (with project seeding folded in) ---
# Post-install per-platform verification (v3.11.0 Phase 7.4): report PASS /
# NEEDS-ACTION per detected platform against its real read-path (advisory).
Write-CenteredBanner -Text "INSTALL VERIFICATION"
$verifyRunner = Join-Path $repoRoot "scripts\lib\integrations\runner.py"
$pyVerify = $null
foreach ($c in @("python", "py", "python3")) { if (Get-Command $c -ErrorAction SilentlyContinue) { $pyVerify = $c; break } }
if ($pyVerify -and (Test-Path $verifyRunner)) {
    if ($pyVerify -eq "py") { & $pyVerify -3 $verifyRunner verify --target (Get-Location).Path 2>$null }
    else { & $pyVerify $verifyRunner verify --target (Get-Location).Path 2>$null }
}

# Project seeding (v3.11.0 Phase 7.3): seed the current repo on a global install
# run from inside it, ship the opt-in on-open hook, and surface `nexus-hub init`
# for other projects. Folded under INSTALL VERIFICATION as the project-scoped
# follow-up to any NEEDS-ACTION hints above.
Install-ProjectAutoseed -RepoRoot $repoRoot -ScopeLabel $scopeLabel

# Resolve any managed-file conflicts collected during an interactive install
# (single end-of-run prompt). No-op on the non-interactive / -Yes / -Force path.
Resolve-Conflicts

# Clean up temp files created for deferred writes (e.g. the Copilot body).
foreach ($tf in $script:TempFiles) {
    if ($tf -and (Test-Path $tf)) { Remove-Item $tf -Force -ErrorAction SilentlyContinue }
}

Write-Host ""
Write-Host "✓ Nexus-Hub v$script:NexusHubVersion installed ($scopeLabel scope)." -ForegroundColor Green
Write-Host ""
Write-Host "Restart any running AI assistant sessions (Claude Code, Cursor, Gemini CLI, Codex, Copilot, OpenCode) so they pick up the new settings, hooks, skills, and rules." -ForegroundColor Yellow

# v3.16.1: remove the filtered-selection staging tree. Bash does this with
# `trap cleanup_selection_stage EXIT`; PowerShell has no script-scope equivalent,
# so it is called on the normal completion path. Without it the stage leaked a
# full copy of the selected skills into %TEMP% on every focused install.
#
# A `Register-EngineEvent PowerShell.Exiting` handler was considered to cover the
# early-`exit` paths and deliberately NOT shipped: engine-event actions run in a
# separate scope where the `$script:`-scoped stage path is not reliably visible,
# and an unverifiable cleanup is worse than a documented gap.
#
# The residual is real but bounded, and measured rather than assumed: an `exit`
# that happens AFTER Resolve-Selection leaves one stage behind. The workspace
# validation ("Workspace path not found") is one such path, observed leaking a
# stage during v3.16.1 testing. The stage lives under %TEMP%, which the OS
# reclaims, and the normal completion path below cleans up (verified: stage
# count unchanged across a successful focused install).
Remove-SelectionStage

Show-FarewellBanner
# Pause is itself a prompt -- skip it on the non-interactive / -Yes / -Force /
# piped path so a no-prompt install never blocks (v3.7.0 / Phase 2).
if (-not $script:AssumeYes) { Pause }
