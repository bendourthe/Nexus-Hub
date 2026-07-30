<#
.SYNOPSIS
    PowerShell parity for dependency-staleness-notice.sh.

.DESCRIPTION
    PostToolUse hook (Write, Edit) that emits an advisory marker when a declared
    dependency manifest changes, naming the matching ecosystem audit command.
    Advisory only: always exits 0, never blocks.

    Recognizes DECLARED-dependency manifests, not generated lockfiles, and skips
    manifests inside vendor / build directories that are not the user's own.

.NOTES
    Runs as an event-driven hook, deliberately NOT a background daemon: the check
    idea was adopted from an external always-on worker catalog, but a timer-driven
    daemon inverts this catalog's zero-runtime posture, so it fires on the tool
    event instead and exits immediately.

    One deliberate difference, in the safe direction: the bash version needs `jq`
    and exits 0 silently without it. PowerShell parses JSON natively, so this
    version always classifies. It notices in strictly more cases, never fewer.
#>

$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "dependency-staleness-notice"
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

# --- Skip manifests inside vendor / build directories (not the user's own) ---
$guarded = "/$normPath/"
foreach ($skip in @('/node_modules/', '/vendor/', '/dist/', '/build/', '/.venv/', '/site-packages/')) {
    if ($guarded -like "*$skip*") { exit 0 }
}

# --- Recognize declared-dependency manifests and map each to its audit command ---
$hint = ""
switch -Wildcard ($baseName) {
    'package.json'        { $hint = 'npm audit (or pnpm audit / yarn audit)'; break }
    'requirements.txt'    { $hint = 'pip-audit (or safety check)'; break }
    'requirements-*.txt'  { $hint = 'pip-audit (or safety check)'; break }
    'pyproject.toml'      { $hint = 'pip-audit (or safety check)'; break }
    'Pipfile'             { $hint = 'pip-audit (or safety check)'; break }
    'setup.cfg'           { $hint = 'pip-audit (or safety check)'; break }
    'go.mod'              { $hint = 'govulncheck ./...'; break }
    'Cargo.toml'          { $hint = 'cargo audit'; break }
    'Gemfile'             { $hint = 'bundle audit'; break }
    'composer.json'       { $hint = 'composer audit'; break }
    'pom.xml'             { $hint = "the OWASP dependency-check or your build's audit task"; break }
    'build.gradle'        { $hint = "the OWASP dependency-check or your build's audit task"; break }
    'build.gradle.kts'    { $hint = "the OWASP dependency-check or your build's audit task"; break }
    '*.csproj'            { $hint = 'dotnet list package --vulnerable'; break }
    default               { exit 0 }
}

# --- Emit advisory marker ---
[Console]::Error.WriteLine("[dependency-staleness-notice] Dependency manifest changed: $normPath. Consider auditing for stale / vulnerable deps (run: $hint; see the dependency-security-audit / dependency-manager skills).")
exit 0
