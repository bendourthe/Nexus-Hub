# Entry point for Windows installation.
#
# Dual-mode (v3.7.0):
#   * In-repo    - run from a cloned checkout (.\install.ps1 or via install.bat).
#                  Delegates to .\scripts\installer.ps1 exactly as before.
#   * Standalone - piped from the network:
#                      irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex
#                  Prechecks the required tools, downloads the catalog archive
#                  from the project's own GitHub, extracts it to ~/.nexus-hub/src,
#                  and runs the extracted scripts\installer.ps1. No prior clone,
#                  no unzip, no cd.
#
# The ONLY outbound call is to the project's own GitHub (github.com /
# raw.githubusercontent.com) -- the standard, audited bootstrap posture. No
# third-party data processor, credential, or new dependency is introduced.
#
# Internal testing affordances (environment variables):
#   NEXUS_HUB_REF                git ref to fetch                 (default: main)
#   NEXUS_HUB_REPO               owner/name slug      (default: bendourthe/Nexus-Hub)
#   NEXUS_HUB_TARBALL            explicit archive source (local path OR URL);
#                                bypasses URL construction (used by the CI smoke test)
#   NEXUS_HUB_SRC                extraction target      (default: ~/.nexus-hub/src)
#   NEXUS_HUB_FORCE_STANDALONE=1 force standalone mode even inside a checkout
#   NEXUS_HUB_PRECHECK_ONLY=1    run the dependency precheck then exit (no fetch)
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassThruArgs = @()
)

$ErrorActionPreference = "Stop"

$NexusHubRepoDefault = "bendourthe/Nexus-Hub"

function Write-BootstrapInfo  { param([string]$Message) Write-Host $Message }
function Write-BootstrapError { param([string]$Message) Write-Host "Error: $Message" -ForegroundColor Red }

function Get-HomeDir {
    if ($env:USERPROFILE) { return $env:USERPROFILE }
    if ($env:HOME) { return $env:HOME }
    return (Get-Location).Path
}

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# Resolve the PowerShell executable to re-invoke the core installer with. This
# must be the SAME host running this script, not a hardcoded "powershell":
# Windows PowerShell 5.1 is "powershell.exe", but PowerShell 7 is "pwsh", and on
# Linux/macOS (or a pwsh-only Windows) "powershell" does not exist at all -- so
# `& powershell` fails with "term 'powershell' is not recognized". The running
# process path covers every case (5.1 and 7, Windows and Unix).
function Get-PowerShellExe {
    try {
        $self = (Get-Process -Id $PID).Path
        if ($self) { return $self }
    } catch {}
    if ($PSVersionTable.PSVersion.Major -ge 6) { return "pwsh" }
    return "powershell"
}

# Resolve the directory this script lives in, or $null when invoked via irm|iex
# (no file on disk -> $PSScriptRoot / $PSCommandPath are empty).
function Resolve-ScriptDir {
    if ($PSScriptRoot) { return $PSScriptRoot }
    if ($PSCommandPath) { return (Split-Path -Parent $PSCommandPath) }
    return $null
}

# Required-tool precheck: PowerShell 5.1+, an extractor (tar OR Expand-Archive),
# and a Python interpreter (the core installer's own dependency). The downloader
# is the built-in Invoke-WebRequest, always present. Fails with a clear,
# actionable message and a non-zero exit on the first miss.
function Invoke-DependencyPrecheck {
    if ($PSVersionTable.PSVersion.Major -lt 5) {
        Write-BootstrapError "PowerShell 5.1 or newer is required (found $($PSVersionTable.PSVersion)). Update Windows PowerShell, or install PowerShell 7+ from https://aka.ms/powershell."
        exit 1
    }
    $hasTar = Test-CommandExists "tar"
    $hasExpand = Test-CommandExists "Expand-Archive"
    if (-not $hasTar -and -not $hasExpand) {
        Write-BootstrapError "no archive extractor found -- need 'tar' (built in on Windows 10+) or the Expand-Archive cmdlet (PowerShell 5+)."
        exit 1
    }
    if (-not (Test-CommandExists "python3") -and -not (Test-CommandExists "python") -and -not (Test-CommandExists "py")) {
        Write-BootstrapError "Python 3 is required by the installer but was not found. Install it from https://www.python.org/downloads/ or run 'winget install Python.Python.3'."
        exit 1
    }
}

# In-repo path: behave exactly as install.bat did, delegating to the core
# PowerShell installer in scripts\.
function Invoke-InRepo {
    param([string]$Dir, [string[]]$ArgList)
    $installer = Join-Path $Dir "scripts\installer.ps1"
    if (-not (Test-Path $installer)) {
        Write-BootstrapError "Installer script not found at $installer"
        exit 1
    }
    & (Get-PowerShellExe) -NoProfile -ExecutionPolicy Bypass -File $installer @ArgList
    exit $LASTEXITCODE
}

# Standalone bootstrap: precheck, fetch the catalog archive, extract it, and
# hand off to the extracted core installer.
function Invoke-Standalone {
    param([string[]]$ArgList)

    Invoke-DependencyPrecheck
    if ($env:NEXUS_HUB_PRECHECK_ONLY -eq "1") {
        Write-BootstrapInfo "[precheck] all required tools present (extractor, python)."
        exit 0
    }

    $ref = if ($env:NEXUS_HUB_REF) { $env:NEXUS_HUB_REF } else { "main" }
    $repo = if ($env:NEXUS_HUB_REPO) { $env:NEXUS_HUB_REPO } else { $NexusHubRepoDefault }
    $src = if ($env:NEXUS_HUB_SRC) { $env:NEXUS_HUB_SRC } else { Join-Path (Get-HomeDir) ".nexus-hub\src" }

    # Guard the destructive refresh below: never operate on an empty or root path.
    if ([string]::IsNullOrWhiteSpace($src) -or $src -eq "\" -or $src -eq "/") {
        Write-BootstrapError "refusing to use unsafe extraction directory: '$src'"
        exit 1
    }

    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("nexus-hub-bootstrap-" + [System.Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null

    $exitCode = 1
    try {
        $tarball = $env:NEXUS_HUB_TARBALL
        $useTar = Test-CommandExists "tar"
        $archive = $null

        if ($tarball -and (Test-Path $tarball)) {
            Write-BootstrapInfo "Using local catalog archive: $tarball"
            $archive = $tarball
            if ($tarball -match '\.zip$') { $useTar = $false }
        } else {
            $ext = if ($useTar) { "tar.gz" } else { "zip" }
            $archive = Join-Path $tmp ("nexus-hub." + $ext)
            $url = if ($tarball) { $tarball } else { "https://github.com/$repo/archive/refs/heads/$ref.$ext" }
            Write-BootstrapInfo "Downloading Nexus-Hub catalog ($repo@$ref)..."
            try {
                Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing -TimeoutSec 300
            } catch {
                Write-BootstrapError "download failed: $url -- $($_.Exception.Message)"
                exit 1
            }
        }

        Write-BootstrapInfo "Extracting catalog to $src ..."
        if (Test-Path $src) { Remove-Item -Recurse -Force $src }
        New-Item -ItemType Directory -Force -Path $src | Out-Null

        if ($useTar) {
            # The GitHub tarball wraps everything in a single top dir
            # (Nexus-Hub-<ref>/); --strip-components=1 drops it.
            & tar -xzf $archive --strip-components=1 -C $src
            if ($LASTEXITCODE -ne 0) {
                Write-BootstrapError "failed to extract catalog from $archive (tar exit $LASTEXITCODE)"
                exit 1
            }
        } else {
            # Expand-Archive has no strip option, so unpack to a staging dir and
            # flatten the single top-level folder the GitHub zipball produces.
            $unpack = Join-Path $tmp "unpack"
            New-Item -ItemType Directory -Force -Path $unpack | Out-Null
            Expand-Archive -Path $archive -DestinationPath $unpack -Force
            $top = Get-ChildItem -Path $unpack -Directory | Select-Object -First 1
            $contentRoot = if ($top) { $top.FullName } else { $unpack }
            Copy-Item -Path (Join-Path $contentRoot "*") -Destination $src -Recurse -Force
        }

        $installer = Join-Path $src "scripts\installer.ps1"
        if (-not (Test-Path $installer)) {
            Write-BootstrapError "extracted catalog has no scripts/installer.ps1 at $installer"
            exit 1
        }

        Write-BootstrapInfo "Running installer from $src ..."
        & (Get-PowerShellExe) -NoProfile -ExecutionPolicy Bypass -File $installer @ArgList
        $exitCode = $LASTEXITCODE
    } finally {
        if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue }
    }
    exit $exitCode
}

# --- Main ---
$scriptDir = Resolve-ScriptDir
$forceStandalone = ($env:NEXUS_HUB_FORCE_STANDALONE -eq "1")
if (-not $forceStandalone -and $scriptDir -and (Test-Path (Join-Path $scriptDir "scripts\installer.ps1"))) {
    Invoke-InRepo -Dir $scriptDir -ArgList $PassThruArgs
} else {
    Invoke-Standalone -ArgList $PassThruArgs
}
