<#
.SYNOPSIS
    PowerShell parity for test-gap-notice.sh.

.DESCRIPTION
    PostToolUse hook (Write, Edit) that emits an advisory marker when a source file
    is written with no conventional companion test nearby. Advisory only: always
    exits 0, never blocks.

    The filters exist to keep the advisory low-noise, and each one matters:
      * Only source extensions with a strong FILE-BASED test convention are
        considered. Languages that favor inline tests (Rust #[cfg(test)], C/C++)
        are excluded, because "no companion test file" is not a gap there.
      * Files that are themselves tests are skipped.
      * Common entrypoint / aggregator files (__init__.py, index.ts, setup.py) are
        skipped, since they rarely carry a dedicated unit test.
      * Files inside test / build / vendor directories are skipped.

.NOTES
    The companion-test search is deliberately BOUNDED to a small set of nearby
    directories rather than walking the repo: an advisory hook runs on every write,
    so a full-tree scan would be a per-write cost nobody asked for.

    Runs as an event-driven hook, not a background daemon, for the same reason
    described in dependency-staleness-notice.ps1.
#>

$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "test-gap-notice"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

# --- Read JSON from stdin ---
if (-not [Console]::IsInputRedirected) { exit 0 }
$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }

$filePath = $null
try {
    $payload = $raw | ConvertFrom-Json
    if ($payload -and $payload.tool_input) {
        $names = $payload.tool_input.PSObject.Properties.Name
        if ($names -contains 'file_path') { $filePath = $payload.tool_input.file_path }
        elseif ($names -contains 'path') { $filePath = $payload.tool_input.path }
    }
} catch { exit 0 }

if (-not $filePath) { exit 0 }

# Normalize separators (Windows paths -> POSIX) before pattern matching.
$normPath = $filePath -replace '\\', '/'
$baseName = Split-Path $normPath -Leaf
$dirName = Split-Path $normPath -Parent
if (-not $dirName) { $dirName = "." }

$ext = ([System.IO.Path]::GetExtension($baseName)).TrimStart('.')
$stem = [System.IO.Path]::GetFileNameWithoutExtension($baseName)

# --- Only source extensions with a strong file-based test convention ---
if ($ext -notin @('py','js','jsx','ts','tsx','go','rb','java','cs','php')) { exit 0 }

# --- Skip files that are themselves tests ---
$testSelfPatterns = @(
    'test_*.py', '*_test.py', '*_test.go',
    '*.test.js', '*.test.jsx', '*.test.ts', '*.test.tsx',
    '*.spec.js', '*.spec.jsx', '*.spec.ts', '*.spec.tsx',
    '*Test.java', '*Tests.cs', '*_spec.rb', '*Test.php'
)
foreach ($p in $testSelfPatterns) { if ($baseName -like $p) { exit 0 } }

# --- Skip common entrypoint / aggregator files ---
if ($baseName -in @('__init__.py','conftest.py','setup.py','index.js','index.ts','index.jsx','index.tsx')) { exit 0 }

# --- Skip files inside test / build / vendor directories ---
$guarded = "/$normPath/"
foreach ($skip in @('/test/', '/tests/', '/__tests__/', '/spec/', '/node_modules/',
                    '/vendor/', '/dist/', '/build/', '/.venv/', '/site-packages/')) {
    if ($guarded -like "*$skip*") { exit 0 }
}

# --- Look for a conventional companion test in a bounded set of nearby dirs ---
function Test-HasCompanionTest {
    param([string]$Dir, [string]$Stem)

    $candidateDirs = @(
        $Dir,
        (Join-Path $Dir 'tests'), (Join-Path $Dir 'test'),
        (Join-Path $Dir '__tests__'), (Join-Path $Dir 'spec'),
        (Join-Path $Dir '../tests'), (Join-Path $Dir '../test'),
        (Join-Path $Dir '../__tests__'), (Join-Path $Dir '../spec')
    )
    $namePatterns = @('test_*', '*_test.*', '*.test.*', '*.spec.*', '*_spec.*', '*Test.*', '*Tests.*')

    foreach ($d in $candidateDirs) {
        if (-not (Test-Path -LiteralPath $d -PathType Container)) { continue }
        $matches = Get-ChildItem -LiteralPath $d -Filter "*$Stem*" -File -ErrorAction SilentlyContinue
        foreach ($f in $matches) {
            foreach ($p in $namePatterns) {
                if ($f.Name -like $p) { return $true }
            }
        }
    }
    return $false
}

if (Test-HasCompanionTest -Dir $dirName -Stem $stem) { exit 0 }

# --- Emit advisory marker ---
[Console]::Error.WriteLine("[test-gap-notice] No companion test found near $normPath. Consider adding one (see the unit-tests / test-driven-development skills, or run /test).")
exit 0
