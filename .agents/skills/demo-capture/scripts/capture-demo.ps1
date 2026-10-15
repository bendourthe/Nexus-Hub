<#
.SYNOPSIS
    capture-demo.ps1 - Local visual PR-evidence capture (zero-outbound).

.DESCRIPTION
    PowerShell sibling of capture-demo.py, kept in lockstep behavior parity per
    the AGENTS.md cross-platform rule. Detects locally-installed capture tools
    and the project type, then either reports a capture plan (-Mode probe, the
    default) or drives a local capture (-Mode capture), writing artifacts to a
    local docs/demos/ directory.

    It NEVER uploads, hosts, or shares anything: the upstream upload / approval /
    hosting surface is deliberately dropped. When a required tool is absent the
    script reports which tool to install and exits 0 (graceful degradation)
    rather than failing hard. Zero-outbound: no network call, no connection.

.PARAMETER Mode
    'probe' (default) prints the capture plan as JSON; 'capture' drives a local capture.
.PARAMETER Type
    Project type: auto (default) / cli / tui / web / api / generic.
.PARAMETER Root
    Project root (defaults to CWD).
.PARAMETER Out
    Local output dir relative to Root (default docs/demos).
.PARAMETER Name
    Artifact slug (default: <type>-demo-<timestamp>).
.PARAMETER Url
    URL for the web screenshot tier (default http://localhost:3000).
.PARAMETER Cmd
    Command to record for the terminal tier.
.PARAMETER Browser
    Override the browser binary.
.PARAMETER Recorder
    Override the terminal recorder binary.
#>
[CmdletBinding()]
param(
    [ValidateSet("probe", "capture")]
    [string]$Mode = "probe",
    [ValidateSet("auto", "cli", "tui", "web", "api", "generic")]
    [string]$Type = "auto",
    [string]$Root = ".",
    [string]$Out = "docs/demos",
    [string]$Name,
    [string]$Url = "http://localhost:3000",
    [string]$Cmd,
    [string]$Browser,
    [string]$Recorder
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Recorders = @("asciinema", "termtosvg")
$GifTools  = @("agg", "ffmpeg")
$Browsers  = @("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome", "msedge")

$InstallHints = [ordered]@{
    recorder = "Install a terminal recorder: 'asciinema' (pip install asciinema / brew install asciinema) or 'termtosvg'."
    gif      = "Install a GIF tool: 'agg' (asciinema gif generator) or 'ffmpeg'."
    browser  = "Install a Chromium-family browser (chromium / google-chrome / msedge) for headless screenshots."
}

function Test-Tool($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Get-Tools() {
    return [ordered]@{
        recorder = @($Recorders | Where-Object { Test-Tool $_ })
        gif      = @($GifTools | Where-Object { Test-Tool $_ })
        browser  = @($Browsers | Where-Object { Test-Tool $_ })
    }
}

function Read-Text($path) {
    try { return [System.IO.File]::ReadAllText($path) } catch { return "" }
}

function Get-ProjectType($rootPath) {
    $pkg = Join-Path $rootPath "package.json"
    if (Test-Path -LiteralPath $pkg -PathType Leaf) {
        $text = (Read-Text $pkg).ToLowerInvariant()
        $webMarkers = @("react", "vue", "svelte", "next", "astro", "vite", '"dev"', '"start"')
        foreach ($m in $webMarkers) { if ($text.Contains($m)) { return "web" } }
        if ($text.Contains('"bin"')) { return "cli" }
    }
    foreach ($c in @("index.html", "public/index.html", "src/index.html")) {
        if (Test-Path -LiteralPath (Join-Path $rootPath $c) -PathType Leaf) { return "web" }
    }
    $pyproject = Join-Path $rootPath "pyproject.toml"
    if (Test-Path -LiteralPath $pyproject -PathType Leaf) {
        $text = (Read-Text $pyproject).ToLowerInvariant()
        if ($text.Contains("[project.scripts]") -or $text.Contains("console_scripts")) { return "cli" }
        foreach ($m in @("fastapi", "flask", "django")) { if ($text.Contains($m)) { return "api" } }
    }
    $cargo = Join-Path $rootPath "Cargo.toml"
    if ((Test-Path -LiteralPath $cargo -PathType Leaf) -and (Read-Text $cargo).Contains("[[bin]]")) { return "cli" }
    if (Test-Path -LiteralPath (Join-Path $rootPath "go.mod") -PathType Leaf) { return "cli" }
    if (Test-Path -LiteralPath (Join-Path $rootPath "bin") -PathType Container) { return "cli" }
    return "generic"
}

function Get-Tier($projectType) {
    if ($projectType -eq "web") { return @("browser-screenshots", "browser") }
    return @("terminal-recording", "recorder")
}

function Build-Plan($rootPath, $outDir, $projectType) {
    $tools = Get-Tools
    $tier = Get-Tier $projectType
    $missing = @(@("recorder", "gif", "browser") | Where-Object { $tools[$_].Count -eq 0 })
    $needed = $tier[1]
    $blocking = @()
    if ($tools[$needed].Count -eq 0) { $blocking = @($needed) }
    $available = [ordered]@{}
    foreach ($k in $tools.Keys) { if ($tools[$k].Count -gt 0) { $available[$k] = $tools[$k] } }
    $hints = [ordered]@{}
    foreach ($cap in $missing) { $hints[$cap] = $InstallHints[$cap] }
    return [ordered]@{
        project_type          = $projectType
        recommended_tier      = $tier[0]
        needed_capability     = $needed
        available_tools       = $available
        missing_capabilities  = $missing
        blocking_capabilities = $blocking
        install_hints         = $hints
        out_dir               = "$outDir"
        upload                = "disabled (local-only by design; no upload/host/share step exists)"
    }
}

function Get-Slug($name, $projectType) {
    if ($name) {
        return (($name.ToCharArray() | ForEach-Object {
            if (($_ -match '[a-zA-Z0-9]') -or ($_ -eq '-') -or ($_ -eq '_')) { $_ } else { '-' }
        }) -join '')
    }
    $stamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
    return "$projectType-demo-$stamp"
}

function Invoke-Capture($cmd, $result, $artifact) {
    try {
        $proc = & $cmd[0] @($cmd[1..($cmd.Count - 1)]) 2>&1
        if (($LASTEXITCODE -eq 0) -and (Test-Path -LiteralPath $artifact -PathType Leaf)) {
            [void]$result.captured.Add([ordered]@{ artifact = "$artifact"; tool = $cmd[0] })
        } else {
            $reason = ("$proc").Trim()
            if ($reason.Length -gt 200) { $reason = $reason.Substring(0, 200) }
            if (-not $reason) { $reason = "non-zero exit" }
            [void]$result.skipped.Add([ordered]@{ capability = $cmd[0]; reason = $reason })
        }
    } catch {
        [void]$result.skipped.Add([ordered]@{ capability = $cmd[0]; reason = "$($_.Exception.Message)" })
    }
}

# --- Resolve paths -----------------------------------------------------------
$rootResolved = [System.IO.Path]::GetFullPath($Root)
$outDir = [System.IO.Path]::GetFullPath((Join-Path $rootResolved $Out))
$projectType = if ($Type -ne "auto") { $Type } else { Get-ProjectType $rootResolved }

if ($Mode -eq "probe") {
    Write-Output ((Build-Plan $rootResolved $outDir $projectType) | ConvertTo-Json -Depth 8)
    exit 0
}

# --- Capture mode ------------------------------------------------------------
[void](New-Item -ItemType Directory -Force -Path $outDir)
$tools = Get-Tools
$plan = Build-Plan $rootResolved $outDir $projectType
$slug = Get-Slug $Name $projectType
$result = [ordered]@{
    plan     = $plan
    captured = New-Object System.Collections.ArrayList
    skipped  = New-Object System.Collections.ArrayList
}

if ($plan.recommended_tier -eq "browser-screenshots") {
    $br = if ($Browser) { $Browser } elseif ($tools.browser.Count -gt 0) { $tools.browser[0] } else { $null }
    if (-not $br -or -not (Test-Tool $br)) {
        [void]$result.skipped.Add([ordered]@{ capability = "browser"; reason = "no Chromium-family browser found"; hint = $InstallHints.browser })
    } else {
        $outPng = Join-Path $outDir "$slug.png"
        $cmd = @($br, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--screenshot=$outPng", "--window-size=1280,800", $Url)
        Invoke-Capture $cmd $result $outPng
    }
} else {
    $rec = if ($Recorder) { $Recorder } elseif ($tools.recorder.Count -gt 0) { $tools.recorder[0] } else { $null }
    if (-not $rec -or -not (Test-Tool $rec)) {
        [void]$result.skipped.Add([ordered]@{ capability = "recorder"; reason = "no terminal recorder found"; hint = $InstallHints.recorder })
    } elseif ($rec -ne "asciinema") {
        [void]$result.skipped.Add([ordered]@{ capability = "recorder"; reason = "$rec capture not automated; run it manually"; hint = $InstallHints.recorder })
    } else {
        $outCast = Join-Path $outDir "$slug.cast"
        $cmd = @("asciinema", "rec", "--overwrite")
        if ($Cmd) { $cmd += @("--command", $Cmd) }
        $cmd += "$outCast"
        Invoke-Capture $cmd $result $outCast
        if ((Test-Path -LiteralPath $outCast -PathType Leaf) -and ($tools.gif.Count -gt 0) -and ($tools.gif[0] -eq "agg")) {
            $outGif = Join-Path $outDir "$slug.gif"
            Invoke-Capture @("agg", "$outCast", "$outGif") $result $outGif
        }
    }
}

Write-Output ($result | ConvertTo-Json -Depth 8)
exit 0
