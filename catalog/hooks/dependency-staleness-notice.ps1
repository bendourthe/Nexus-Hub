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

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
$script:NexusTag = "[Nexus-Hub: dependency-staleness-notice]"
# Make CR, LF, ESC and the other C0 control characters in an echoed value
# visible, so a file name or command cannot start a forged tagged line.
function ConvertTo-NexusVisible {
    param([string]$Value)
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in "$Value".ToCharArray()) {
        $code = [int]$ch
        if ($code -eq 9) { [void]$sb.Append('\t') }
        elseif ($code -eq 10) { [void]$sb.Append('\n') }
        elseif ($code -eq 13) { [void]$sb.Append('\r') }
        elseif ($code -lt 32 -or $code -eq 127) { [void]$sb.Append(('\x{0:x2}' -f $code)) }
        else { [void]$sb.Append($ch) }
    }
    return $sb.ToString()
}
# Print the tag and the message to stderr; every further line is printed as is.
function Write-NexusMessage {
    param([string]$Message, [string[]]$More = @())
    [Console]::Error.WriteLine("$script:NexusTag $Message")
    foreach ($line in $More) { [Console]::Error.WriteLine($line) }
}

# --- Runtime controls ---
$hookName = "dependency-staleness-notice"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

# --- Read JSON from stdin ---
if (-not [Console]::IsInputRedirected) { exit 0 }
# Hook payloads are UTF-8 whatever the console code page is (WN-37): decode the raw
# handle and reply through UTF-8 writers rather than calling SetConsoleCP.
$hookUtf8 = New-Object System.Text.UTF8Encoding($false)
$raw = (New-Object System.IO.StreamReader([Console]::OpenStandardInput(), $hookUtf8, $true)).ReadToEnd()
# Windows PowerShell 5.1 without a console drains the raw handle into [Console]::In.
if (-not $raw) { $raw = [Console]::In.ReadToEnd() }
$utf8Writer = New-Object System.IO.StreamWriter([Console]::OpenStandardOutput(), $hookUtf8); $utf8Writer.AutoFlush = $true; [Console]::SetOut($utf8Writer)
$utf8Writer = New-Object System.IO.StreamWriter([Console]::OpenStandardError(), $hookUtf8); $utf8Writer.AutoFlush = $true; [Console]::SetError($utf8Writer)
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
Write-NexusMessage "Dependency manifest changed: $(ConvertTo-NexusVisible $normPath). Consider auditing for stale / vulnerable deps (run: $hint; see the dependency-security-audit / dependency-manager skills)."
exit 0
