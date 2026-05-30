<#
.SYNOPSIS
    Bisect a test suite to find the file that pollutes shared state. PowerShell
    sibling of find-polluter.sh.

.DESCRIPTION
    Runs each test file in isolation, cleaning a watched artifact (a file or
    directory a well-behaved run should never leave behind) before each run, and
    reports the first test file whose isolated run re-creates that artifact. Use
    it when a suite is order-dependent because one test leaks filesystem or
    global state into the others.

    Project-agnostic: you supply the watched artifact, a glob for the test files
    to bisect, and your own test-runner command. It hardcodes no language or
    framework and makes NO network calls. The only thing it writes is the
    removal of the watched artifact between runs (guarded against unsafe paths).

.PARAMETER Watch
    Path or wildcard of the pollution artifact to watch for. Removed before each
    isolated run; its reappearance identifies the polluter.

.PARAMETER Tests
    Wildcard selecting the test files to bisect, e.g. "tests\*.test.js" or
    "tests/test_*.py". Expanded inside the script.

.PARAMETER TestCommand
    Your test command as a single string. Use {} as the placeholder for the
    current test file; if {} is absent the file is appended as the final
    argument. The command is split on whitespace into an executable plus
    arguments, then invoked with the call operator (no Invoke-Expression). The
    {} token is replaced as a single argument, so a file path with spaces stays
    intact; only the template's own arguments must be whitespace-separable.

.EXAMPLE
    .\find-polluter.ps1 -Watch "tmp/leaked.lock" -Tests "tests/*.test.js" -TestCommand "node --test {}"

.EXAMPLE
    .\find-polluter.ps1 -Watch ".cache/state" -Tests "tests/test_*.py" -TestCommand "pytest -p no:randomly {}"

.NOTES
    Exit code: 0 when the scan ran (whether or not a polluter was found - this
    is a diagnostic aid, not a gate); 2 on a usage or IO error.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Watch,

    [Parameter(Mandatory = $true)]
    [string]$Tests,

    [Parameter(Mandatory = $true)]
    [string]$TestCommand
)

$ErrorActionPreference = 'Stop'

function Write-InfoLine  { param([string]$Message) Write-Host "[INFO]  $Message" }
function Write-ErrorLine { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

# Guard: refuse obviously catastrophic watch patterns.
$unsafe = @('', '/', '\', '.', '..', '*', '/*', '~', $HOME, $PWD.Path)
if ($unsafe -contains $Watch) {
    Write-ErrorLine "refusing to use an unsafe -Watch pattern: '$Watch'"
    exit 2
}

# Return $true if at least one path currently matches the watched artifact
# pattern. Test-Path honors wildcards and works for both files and directories.
function Test-ArtifactExists {
    return [bool](Test-Path -Path $Watch)
}

# Remove every match of the watched artifact pattern, re-checking each resolved
# item against the unsafe-path guard before removal.
function Remove-Artifact {
    if (-not (Test-Path -Path $Watch)) {
        return
    }
    foreach ($item in @(Get-Item -Path $Watch -Force -ErrorAction SilentlyContinue)) {
        $full = $item.FullName
        if ($full -eq $HOME -or $full -eq $PWD.Path -or [string]::IsNullOrEmpty($full)) {
            Write-ErrorLine "refusing to remove unsafe path: '$full'"
            exit 2
        }
    }
    Remove-Item -Path $Watch -Recurse -Force -ErrorAction SilentlyContinue
}

# Run the user's test command for a single file, substituting {} (or appending
# the file when no placeholder is present). A failing test must NOT abort the
# bisection - only pollution matters - so the exit status is swallowed.
function Invoke-OneTest {
    param([string]$TestFile)

    $parts = $TestCommand -split '\s+' | Where-Object { $_ -ne '' }
    $cmdParts = @()
    $substituted = $false
    foreach ($p in $parts) {
        if ($p -eq '{}') {
            $cmdParts += $TestFile
            $substituted = $true
        }
        else {
            $cmdParts += $p
        }
    }
    if (-not $substituted) {
        $cmdParts += $TestFile
    }

    $exe = $cmdParts[0]
    $rest = @()
    if ($cmdParts.Count -gt 1) {
        $rest = $cmdParts[1..($cmdParts.Count - 1)]
    }

    try {
        & $exe @rest *> $null
    }
    catch {
        # Test failures and missing runners are tolerated; only pollution counts.
    }
}

# Expand the test glob into a sorted file list.
$files = @(Get-ChildItem -Path $Tests -File -ErrorAction SilentlyContinue | Sort-Object FullName)
if ($files.Count -lt 1) {
    Write-ErrorLine "no test files matched: $Tests"
    exit 2
}

Write-InfoLine "Watching artifact: $Watch"
Write-InfoLine "Bisecting $($files.Count) test file(s) from: $Tests"

# Start clean so a pre-existing artifact does not produce a false positive.
if (Test-ArtifactExists) {
    Write-InfoLine "Watched artifact already present at start; removing for a clean baseline."
    Remove-Artifact
}

$polluter = $null
foreach ($file in $files) {
    Remove-Artifact
    Write-InfoLine "Running in isolation: $($file.FullName)"
    Invoke-OneTest -TestFile $file.FullName
    if (Test-ArtifactExists) {
        $polluter = $file.FullName
        break
    }
}

if ($polluter) {
    Write-Host ""
    Write-Host "[RESULT] Polluter found: $polluter"
    # The polluter path goes to the output stream so the result is scriptable.
    Write-Output $polluter
    Write-InfoLine "This file re-created '$Watch' when run in isolation."
}
else {
    Write-Host ""
    Write-Host "[RESULT] No polluter found among $($files.Count) file(s)."
    Write-InfoLine "None of the bisected files re-created '$Watch' in isolation."
}

exit 0
