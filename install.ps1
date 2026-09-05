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
#   NEXUS_HUB_EXPECTED_SHA256    pin the archive SHA-256 (64 hex chars)
#   NEXUS_HUB_CHECKSUMS          path to a GNU sha256sum-format checksums.txt
#   NEXUS_HUB_SKIP_CHECKSUM=1    skip SHA-256 verification (path-traversal
#                                guard still runs). Mirrors RTK_SKIP_CHECKSUM.
#   NEXUS_HUB_RELEASE_BASE       where a TAGGED ref's published artifact set lives
#                                (URL base or a local directory holding
#                                Nexus-Hub-<version>.tar.gz and SHA256SUMS);
#                                default: the tag's GitHub Release assets
#
# Pinning (v4.7.0): `-Ref <tag-or-branch>` (consumed here, not passed on) or
# NEXUS_HUB_REF selects what to install. A release tag (vX.Y.Z) downloads the
# tarball the release workflow published and verifies it against the published
# SHA256SUMS, FAIL-CLOSED: a mismatch, a missing checksum file, or an
# unresolvable ref aborts with a non-zero exit and never installs unverified.
# A branch ref (the default, main) has no publishable digest because every
# commit changes the archive, so it keeps the pin/checksums/warning behavior
# above. A tag install writes ~/.nexus-hub/PINNED_REF; a branch install
# removes it; `nexus-hub upgrade` reads it. Lockstep with install.sh.
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

# Resolve a tar that can actually read a Windows path. GNU tar -- the one Git
# Bash / MSYS put on PATH -- parses a drive-letter path as a remote `host:path`
# spec, so extracting from `a drive-letter path` makes it try to connect to a host
# named "C" and die with "Cannot connect to C: resolve failed", followed by a
# misleading "gzip: stdin: unexpected end of file" from the gzip child. That is
# why the failure has read as a corrupt archive rather than a path-parsing bug.
# Windows ships bsdtar at System32\tar.exe (Windows 10 1803+), which handles
# drive letters correctly, so prefer it explicitly rather than trusting PATH
# order. Same class of defect as the System32 WSL `bash` stub shadowing Git Bash
# (v3.15.6 Phase 4, v3.17.6 Phase 6).
function Resolve-TarExe {
    if ($env:SystemRoot) {
        $systemTar = Join-Path $env:SystemRoot "System32\tar.exe"
        if (Test-Path -LiteralPath $systemTar) { return $systemTar }
    }
    $cmd = Get-Command "tar" -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    return $null
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
    $hasTar = [bool](Resolve-TarExe)
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

function Get-Sha256Hex {
    param([string]$Path)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::OpenRead($Path)
        try {
            $hash = $sha.ComputeHash($stream)
            return ([System.BitConverter]::ToString($hash) -replace '-', '').ToLowerInvariant()
        } finally {
            $stream.Dispose()
        }
    } finally {
        $sha.Dispose()
    }
}

function Test-UnsafeArchiveEntry {
    param([string]$Name)
    if ([string]::IsNullOrEmpty($Name)) { return $false }
    $normalized = $Name -replace '\\', '/'
    if ($normalized.StartsWith('/') -or $normalized -match '^[A-Za-z]:') { return $true }
    foreach ($part in $normalized.Split('/')) {
        if ($part -eq '..') { return $true }
    }
    return $false
}

function Get-ArchiveMemberNames {
    param([string]$ArchivePath, [bool]$UseTar, [string]$TarExe)
    $names = New-Object System.Collections.Generic.List[string]
    if ($UseTar -and $TarExe) {
        $listed = & $TarExe -tzf $ArchivePath 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "tar -tzf failed for $ArchivePath : $listed"
        }
        foreach ($line in @($listed)) {
            $n = [string]$line
            if (-not [string]::IsNullOrWhiteSpace($n)) { $names.Add($n.Trim()) }
        }
        return $names
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)
    try {
        foreach ($entry in $zip.Entries) { $names.Add($entry.FullName) }
    } finally {
        $zip.Dispose()
    }
    return $names
}

function Assert-ArchiveSafe {
    param([string]$ArchivePath, [bool]$UseTar, [string]$TarExe)
    $members = Get-ArchiveMemberNames -ArchivePath $ArchivePath -UseTar $UseTar -TarExe $TarExe
    foreach ($name in $members) {
        if (Test-UnsafeArchiveEntry -Name $name) {
            Write-BootstrapError "refusing to extract $ArchivePath : unsafe member '$name' (absolute or '..' path, CWE-22)"
            exit 1
        }
    }
}

function Get-ChecksumFromFile {
    param([string]$FilePath, [string]$ArchiveName)
    if (-not (Test-Path -LiteralPath $FilePath)) { return $null }
    foreach ($line in Get-Content -LiteralPath $FilePath) {
        $trim = $line.Trim()
        if (-not $trim -or $trim.StartsWith('#')) { continue }
        $parts = $trim -split '\s+', 2
        if ($parts.Count -lt 1) { continue }
        $hash = $parts[0].ToLowerInvariant()
        if ($parts.Count -eq 1) { return $hash }
        $fname = $parts[1].Trim().TrimStart('*')
        if ([System.IO.Path]::GetFileName($fname) -eq $ArchiveName) { return $hash }
    }
    return $null
}

function Assert-ArchiveChecksum {
    param([string]$ArchivePath, [string]$Ref, [string]$Repo)
    if ($env:NEXUS_HUB_SKIP_CHECKSUM -eq '1') {
        Write-BootstrapInfo "checksum verification skipped (NEXUS_HUB_SKIP_CHECKSUM=1)"
        return
    }
    $actual = Get-Sha256Hex -Path $ArchivePath
    $expected = $env:NEXUS_HUB_EXPECTED_SHA256
    if ($expected) { $expected = $expected.ToLowerInvariant() }
    if (-not $expected -and $env:NEXUS_HUB_CHECKSUMS) {
        $expected = Get-ChecksumFromFile -FilePath $env:NEXUS_HUB_CHECKSUMS -ArchiveName ([System.IO.Path]::GetFileName($ArchivePath))
    }
    if (-not $expected -and $Ref -match '^(v[0-9]|[0-9]+\.[0-9])') {
        $tmpSum = Join-Path ([System.IO.Path]::GetTempPath()) ("nexus-hub-checksums-" + [System.Guid]::NewGuid().ToString("N") + ".txt")
        $url = "https://raw.githubusercontent.com/$Repo/$Ref/checksums.txt"
        try {
            Invoke-WebRequest -Uri $url -OutFile $tmpSum -UseBasicParsing -TimeoutSec 30
            $expected = Get-ChecksumFromFile -FilePath $tmpSum -ArchiveName ([System.IO.Path]::GetFileName($ArchivePath))
            if (-not $expected) {
                $expected = Get-ChecksumFromFile -FilePath $tmpSum -ArchiveName ("Nexus-Hub-$Ref.tar.gz")
            }
        } catch {
            # Tagged checksums.txt is optional until the first release publishes one.
        } finally {
            if (Test-Path -LiteralPath $tmpSum) { Remove-Item -LiteralPath $tmpSum -Force -ErrorAction SilentlyContinue }
        }
    }
    if ($expected) {
        if ($actual -ne $expected) {
            Write-BootstrapError "checksum mismatch for $ArchivePath : expected $expected, got $actual"
            exit 1
        }
        Write-BootstrapInfo "checksum OK ($actual)"
        return
    }
    Write-BootstrapInfo "warning: unverified '$Ref' tarball (no published checksum). Set NEXUS_HUB_EXPECTED_SHA256 or NEXUS_HUB_CHECKSUMS, or NEXUS_HUB_SKIP_CHECKSUM=1 to skip."
}


# --- Release-tag verification (v4.7.0, fail-closed; lockstep with install.sh) ---

function Test-ReleaseTag {
    param([string]$Ref)
    return [bool]($Ref -match '^v[0-9]')
}

function Get-ReleaseAssetBase {
    param([string]$Repo, [string]$Ref)
    if ($env:NEXUS_HUB_RELEASE_BASE) { return $env:NEXUS_HUB_RELEASE_BASE }
    return "https://github.com/$Repo/releases/download/$Ref"
}

# Fetch published file $Name from $Base into $Dest. Returns "ok", "missing"
# (local directory without the file), or "failed" (network or copy failure).
function Get-ReleaseFile {
    param([string]$Base, [string]$Name, [string]$Dest)
    if (Test-Path -LiteralPath $Base -PathType Container) {
        $candidate = Join-Path $Base $Name
        if (-not (Test-Path -LiteralPath $candidate)) { return "missing" }
        try { Copy-Item -LiteralPath $candidate -Destination $Dest -Force; return "ok" } catch { return "failed" }
    }
    try {
        Invoke-WebRequest -Uri ("$Base/$Name") -OutFile $Dest -UseBasicParsing -TimeoutSec 300
        return "ok"
    } catch {
        return "failed"
    }
}

function Assert-ReleaseArchiveChecksum {
    param([string]$ArchivePath, [string]$Name, [string]$Ref, [string]$Base)
    if ($env:NEXUS_HUB_SKIP_CHECKSUM -eq '1') {
        Write-BootstrapInfo "WARNING: checksum verification skipped for release $Ref (NEXUS_HUB_SKIP_CHECKSUM=1). This install is unverified by your explicit choice."
        return
    }
    $actual = Get-Sha256Hex -Path $ArchivePath
    $expected = $env:NEXUS_HUB_EXPECTED_SHA256
    if ($expected) { $expected = $expected.ToLowerInvariant() }
    if (-not $expected -and $env:NEXUS_HUB_CHECKSUMS) {
        $expected = Get-ChecksumFromFile -FilePath $env:NEXUS_HUB_CHECKSUMS -ArchiveName $Name
    }
    if (-not $expected) {
        $sums = Join-Path (Split-Path -Parent $ArchivePath) "SHA256SUMS"
        $state = Get-ReleaseFile -Base $Base -Name "SHA256SUMS" -Dest $sums
        if ($state -eq "missing") {
            Write-BootstrapError "release $Ref carries no SHA256SUMS at $Base. Tags published before v4.7.0 have no artifact set; install a newer tag, or supply NEXUS_HUB_TARBALL plus NEXUS_HUB_EXPECTED_SHA256 for this one. Not installing unverified."
            exit 1
        }
        if ($state -ne "ok") {
            Write-BootstrapError "could not fetch SHA256SUMS for release $Ref from $Base (network failure or the asset is absent; this is NOT evidence of tampering). Check the connection or the Releases page, or supply NEXUS_HUB_EXPECTED_SHA256. Not installing unverified."
            exit 1
        }
        $expected = Get-ChecksumFromFile -FilePath $sums -ArchiveName $Name
        if (-not $expected) {
            Write-BootstrapError "SHA256SUMS for release $Ref has no entry for $Name. Not installing unverified."
            exit 1
        }
    }
    if ($actual -ne $expected) {
        Write-BootstrapError "checksum mismatch for $Name (release $Ref): expected $expected, got $actual. The download does not match what the release published; delete it and re-download, and if it repeats, treat the artifact as suspect. Not installing."
        exit 1
    }
    Write-BootstrapInfo "checksum OK ($actual)"
}

function Set-PinMarker {
    param([string]$Src, [string]$Ref)
    $pinDir = Split-Path -Parent $Src
    $marker = Join-Path $pinDir "PINNED_REF"
    try {
        if (Test-ReleaseTag -Ref $Ref) {
            New-Item -ItemType Directory -Force -Path $pinDir | Out-Null
            [System.IO.File]::WriteAllText($marker, "$Ref`n", (New-Object System.Text.UTF8Encoding($false)))
        } elseif (Test-Path -LiteralPath $marker) {
            Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue
        }
    } catch {}
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

    # Consume -Ref <value> here; everything else passes through to the core installer.
    $refFlag = $null
    $passthru = New-Object System.Collections.Generic.List[string]
    for ($i = 0; $i -lt $ArgList.Count; $i++) {
        $a = [string]$ArgList[$i]
        if ($a -eq '-Ref' -or $a -eq '--ref') {
            if ($i + 1 -ge $ArgList.Count) { Write-BootstrapError "-Ref needs a value (a tag such as v4.7.0, or a branch)"; exit 1 }
            $refFlag = [string]$ArgList[$i + 1]; $i++
        } elseif ($a -like '-Ref=*' -or $a -like '--ref=*') {
            $refFlag = $a.Substring($a.IndexOf('=') + 1)
        } else {
            $passthru.Add($a)
        }
    }
    $ArgList = $passthru.ToArray()
    $ref = if ($refFlag) { $refFlag } elseif ($env:NEXUS_HUB_REF) { $env:NEXUS_HUB_REF } else { "main" }
    if ([string]::IsNullOrWhiteSpace($ref)) { Write-BootstrapError "-Ref needs a value (a tag such as v4.7.0, or a branch)"; exit 1 }
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
        $tarExe = Resolve-TarExe
        $useTar = [bool]$tarExe
        $archive = $null

        $assetName = "Nexus-Hub-" + ($ref -replace '^v', '') + ".tar.gz"
        $assetBase = Get-ReleaseAssetBase -Repo $repo -Ref $ref
        if ($tarball -and (Test-Path $tarball)) {
            Write-BootstrapInfo "Using local catalog archive: $tarball"
            $archive = $tarball
            if ($tarball -match '\.zip$') { $useTar = $false }
        } elseif (Test-ReleaseTag -Ref $ref) {
            # A release tag installs the artifact the project PUBLISHED, not GitHub's
            # generated archive, and the download is verified fail-closed below.
            if (-not $useTar) {
                Write-BootstrapError "a pinned release install needs tar (built in on Windows 10+) to read the published .tar.gz; install tar or use the main branch."
                exit 1
            }
            $archive = Join-Path $tmp "nexus-hub.tar.gz"
            Write-BootstrapInfo "Downloading Nexus-Hub release $ref ($repo)..."
            $state = Get-ReleaseFile -Base $assetBase -Name $assetName -Dest $archive
            if ($state -ne "ok") {
                Write-BootstrapError "could not resolve release '$ref' at $assetBase : no $assetName (a typo, a tag that was never published, or a network failure). List versions at https://github.com/$repo/releases or with: gh release list -R $repo"
                exit 1
            }
        } else {
            $ext = if ($useTar) { "tar.gz" } else { "zip" }
            $archive = Join-Path $tmp ("nexus-hub." + $ext)
            $url = if ($tarball) { $tarball } else { "https://github.com/$repo/archive/refs/heads/$ref.$ext" }
            Write-BootstrapInfo "Downloading Nexus-Hub catalog ($repo@$ref)..."
            try {
                Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing -TimeoutSec 300
            } catch {
                Write-BootstrapError "could not resolve branch '$ref' in $repo (a typo or a branch that does not exist): $($_.Exception.Message). List releases at https://github.com/$repo/releases or pin one with -Ref vX.Y.Z"
                exit 1
            }
        }

        Assert-ArchiveSafe -ArchivePath $archive -UseTar $useTar -TarExe $tarExe
        if (Test-ReleaseTag -Ref $ref) {
            Assert-ReleaseArchiveChecksum -ArchivePath $archive -Name $assetName -Ref $ref -Base $assetBase
        } else {
            Assert-ArchiveChecksum -ArchivePath $archive -Ref $ref -Repo $repo
        }
        Set-PinMarker -Src $src -Ref $ref

        Write-BootstrapInfo "Extracting catalog to $src ..."
        if (Test-Path $src) { Remove-Item -Recurse -Force $src }
        New-Item -ItemType Directory -Force -Path $src | Out-Null

        if ($useTar) {
            # The GitHub tarball wraps everything in a single top dir
            # (Nexus-Hub-<ref>/); --strip-components=1 drops it.
            & $tarExe -xzf $archive --strip-components=1 -C $src
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
