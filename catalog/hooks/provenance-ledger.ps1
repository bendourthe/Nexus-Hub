<#
.SYNOPSIS
    PowerShell parity for provenance-ledger.sh.

.DESCRIPTION
    PostToolUse hook (Write, Edit, Bash) that maintains a best-effort
    file-provenance / trust-seam ledger: it records which paths the agent wrote,
    then flags a later command that references one of them.

    What it records, and what it never records: only a timestamp, a content hash,
    and a path -- one tab-separated line per agent write. It NEVER records file
    contents, diffs, environment values, or secret material, per the
    egress-redaction discipline. The hash exists so a later reader can tell
    whether the file still holds what the agent wrote, without the ledger holding
    the bytes.

    This script mirrors the .sh implementation so Windows users who run hooks
    through PowerShell get the same ledger.

.NOTES
    HONEST BOUNDARY: a hook observes the tool calls of the harness it is installed
    in. It CANNOT instrument an editor extension, a language server, a
    version-control integration, or any other trusted executor running in a
    different process, so it cannot see the execution half of most real escapes.
    Correlating an agent write with a later command IN THE SAME SESSION is what
    ships here; full cross-executor instrumentation is not locally achievable and
    is explicitly out of scope. This is the reverse-engineered `re-partial`
    capability: a local audit trail and a same-session tripwire, not an endpoint
    detection agent.

    Advisory only: always exits 0 and never blocks. Disable per-session with
    $env:NEXUS_DISABLED_HOOKS = 'provenance-ledger', or skip all advisory hooks
    with $env:NEXUS_HOOK_PROFILE = 'minimal'.

    Configuration mirrors the .sh sibling: NEXUS_PROVENANCE_DIR,
    NEXUS_PROVENANCE_MAX, NEXUS_PROVENANCE_HASH_MAX_BYTES.
#>

# Never fail loudly on internal errors - this hook is advisory only.
$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "provenance-ledger"
if ($env:NEXUS_DISABLED_HOOKS -and ($env:NEXUS_DISABLED_HOOKS.Split(',') -contains $hookName)) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }

$ledgerDir = if ($env:NEXUS_PROVENANCE_DIR) { $env:NEXUS_PROVENANCE_DIR }
             else { Join-Path (Join-Path $HOME ".nexus-hub") "cache\provenance" }
$maxLines = if ($env:NEXUS_PROVENANCE_MAX) { [int]$env:NEXUS_PROVENANCE_MAX } else { 500 }
$hashMaxBytes = if ($env:NEXUS_PROVENANCE_HASH_MAX_BYTES) { [long]$env:NEXUS_PROVENANCE_HASH_MAX_BYTES } else { 10485760 }

# --- Read the PostToolUse payload ---
if (-not [Console]::IsInputRedirected) { exit 0 }
$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }

try { $payload = $raw | ConvertFrom-Json } catch { exit 0 }
if (-not $payload) { exit 0 }

$toolName = $payload.tool_name
$sessionId = $payload.session_id
$filePath = $null
$command = $null
if ($payload.tool_input) {
    $names = $payload.tool_input.PSObject.Properties.Name
    if ($names -contains 'file_path') { $filePath = $payload.tool_input.file_path }
    elseif ($names -contains 'path')  { $filePath = $payload.tool_input.path }
    if ($names -contains 'command')   { $command = $payload.tool_input.command }
}

# Decide which branch to run. Prefer the explicit tool name over guessing from
# which field is present: a payload carrying BOTH a path and a command would
# otherwise be ambiguous. Fall back to field presence so a harness that omits
# tool_name still works.
$isWrite = $false
$isCommand = $false
switch ($toolName) {
    { $_ -in @('Write', 'Edit', 'MultiEdit', 'NotebookEdit') } { $isWrite = $true; break }
    'Bash' { $isCommand = $true; break }
    default {
        if ($filePath) { $isWrite = $true }
        if ($command)  { $isCommand = $true }
    }
}

# Session scoping: the ledger is per-session by design, so correlation cannot
# reach across unrelated sessions. Without a session id, fall back to a stable
# per-day file rather than a global one.
if (-not $sessionId) { $sessionId = "nosession-" + (Get-Date -Format 'yyyyMMdd') }
$safeSession = ($sessionId -replace '[^A-Za-z0-9._-]', '_')
$ledger = Join-Path $ledgerDir "$safeSession.tsv"

function Get-LedgerHash {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return "NOFILE" }
    $stream = $null
    $sha256 = $null
    try {
        $len = (Get-Item -LiteralPath $Path).Length
        if ($len -gt $hashMaxBytes) { return "SKIPPED-LARGE" }
        # Use the .NET stream directly. Get-FileHash has returned NOHASH on some
        # Windows PowerShell 5.1 runner images even when Test-Path and Get-Item
        # succeed for the same file.
        $stream = [System.IO.File]::OpenRead($Path)
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        $bytes = $sha256.ComputeHash($stream)
        # Lowercased so the value is byte-identical to the .sh sibling's sha256sum.
        return ([System.BitConverter]::ToString($bytes) -replace '-', '').ToLowerInvariant()
    } catch {
        return "NOHASH"
    } finally {
        if ($stream) { $stream.Dispose() }
        if ($sha256) { $sha256.Dispose() }
    }
}

# --- Branch 1: a write. Append one path+hash line. ---
if ($isWrite -and $filePath) {
    try {
        if (-not (Test-Path $ledgerDir)) { New-Item -ItemType Directory -Force -Path $ledgerDir | Out-Null }
        $normPath = $filePath -replace '\\', '/'
        $hash = Get-LedgerHash -Path $filePath
        $epoch = [int][double]::Parse((Get-Date -UFormat %s))

        # BOM-less UTF-8, deliberately. Add-Content -Encoding utf8 emits a BOM on
        # Windows PowerShell 5.1, which would (a) make the first field unparseable
        # as an integer and (b) break format parity with the .sh sibling, which
        # matters because both implementations can append to the SAME ledger file.
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::AppendAllText(
            $ledger, ("{0}`t{1}`t{2}`n" -f $epoch, $hash, $normPath), $utf8NoBom)

        # Bound growth: keep only the most recent $maxLines entries.
        $lines = @(Get-Content -LiteralPath $ledger -ErrorAction SilentlyContinue)
        if ($lines.Count -gt $maxLines) {
            $kept = $lines[($lines.Count - $maxLines)..($lines.Count - 1)]
            [System.IO.File]::WriteAllText(
                $ledger, (($kept -join "`n") + "`n"), $utf8NoBom)
        }
    } catch { }
    exit 0
}

# --- Branch 2: a command. Flag it if it references a recently written path. ---
# Heuristic, stated plainly: this matches the path or its basename anywhere in the
# command string. It therefore over-reports (a path merely mentioned as an
# argument reads the same as one being executed) and under-reports (a path reached
# through a variable, an alias, or a wrapper is invisible). It is a tripwire that
# says "look at this", not a determination that execution occurred.
if ($isCommand -and $command -and (Test-Path -LiteralPath $ledger -PathType Leaf)) {
    $hits = New-Object System.Collections.Generic.List[string]
    $now = [int][double]::Parse((Get-Date -UFormat %s))
    foreach ($line in @(Get-Content -LiteralPath $ledger -ErrorAction SilentlyContinue)) {
        $parts = $line -split "`t"
        if ($parts.Count -lt 3) { continue }
        $ts = $parts[0]
        $hash = $parts[1]
        $path = $parts[2]
        if (-not $path) { continue }
        $base = Split-Path $path -Leaf
        # Ignore very short basenames: they collide with ordinary words.
        if ($base.Length -lt 4) { continue }
        if ($command.Contains($path) -or $command.Contains($base)) {
            $shortHash = if ($hash.Length -ge 12) { $hash.Substring(0, 12) } else { $hash }
            # Report the age: "written 2s ago" reads very differently from
            # "written 40 minutes ago" when judging whether this is the agent
            # closing a loop it just opened.
            $age = "unknown"
            $parsed = 0
            if ([int]::TryParse($ts, [ref]$parsed)) { $age = "$($now - $parsed)s" }
            $hits.Add("  - $path (agent-written $age ago, hash $shortHash)")
        }
    }

    if ($hits.Count -gt 0) {
        [Console]::Error.WriteLine("[provenance-ledger] TRUST SEAM: this command references a path the agent wrote in this session:")
        foreach ($h in $hits) { [Console]::Error.WriteLine($h) }
        [Console]::Error.WriteLine("  A write the agent made is now reaching an executor. Confirm the command is running what you intend.")
        [Console]::Error.WriteLine("  Advisory only. See the Limits section of the agentic-endpoint-hardening skill: a local hook cannot observe executors in other processes.")
    }
}

exit 0
