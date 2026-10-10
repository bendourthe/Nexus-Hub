<#
.SYNOPSIS
    PowerShell parity for learning-capture.sh.

.DESCRIPTION
    Reads a Claude Code hook payload from stdin and appends a single JSON line
    to `.nexus/observations.jsonl` under the project root. The continuous-learning
    skill (catalog/skills/workflow/continuous-learning/SKILL.md) reads that file
    in-session.

    Hard constraints: no network calls, no external observer model, project-scoped.

.NOTES
    Runtime controls:
      $env:NEXUS_DISABLED_HOOKS  = 'learning-capture'  skip this hook entirely
      $env:NEXUS_HOOK_PROFILE    = 'minimal'           skip this hook entirely
      $env:NEXUS_LEARNING_CAPTURE = 'off'              skip writes (default 'on')
      $env:NEXUS_LEARNING_PATH    = '<path>'           override observations file
      $env:NEXUS_LEARNING_MAX_BYTES = '<int>'          truncate file when exceeded
                                                       (default 1048576 = 1 MiB)
#>

$ErrorActionPreference = "Continue"

$hookName = "learning-capture"
$disabled = $env:NEXUS_DISABLED_HOOKS
if ($disabled -and $disabled.Split(',') -contains $hookName) { exit 0 }
if ($env:NEXUS_HOOK_PROFILE -eq "minimal") { exit 0 }
if ($env:NEXUS_LEARNING_CAPTURE -eq "off") { exit 0 }

# --- Read payload ---
$stdin = [Console]::In.ReadToEnd()
if (-not $stdin) { exit 0 }

# --- Locate project root ---
$projectRoot = (Get-Location).Path
try {
    $gitTop = (git rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -eq 0 -and $gitTop) { $projectRoot = $gitTop }
} catch {}

$obsRel = if ($env:NEXUS_LEARNING_PATH) { $env:NEXUS_LEARNING_PATH } else { ".nexus/observations.jsonl" }
$obsPath = Join-Path $projectRoot $obsRel
$obsDir = Split-Path $obsPath -Parent

try {
    if (-not (Test-Path $obsDir)) {
        New-Item -ItemType Directory -Path $obsDir -Force | Out-Null
    }
} catch { exit 0 }

# --- Parse payload ---
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$event = "unknown"
$tool = ""
$promptSample = ""

try {
    $payload = $stdin | ConvertFrom-Json -ErrorAction Stop
    foreach ($name in @('hook_event_name', 'event', 'type')) {
        if ($payload.PSObject.Properties.Name -contains $name -and $payload.$name) {
            $event = "$($payload.$name)"
            break
        }
    }
    foreach ($name in @('tool_name', 'tool')) {
        if ($payload.PSObject.Properties.Name -contains $name -and $payload.$name) {
            $tool = "$($payload.$name)"
            break
        }
    }
    foreach ($name in @('prompt', 'user_prompt')) {
        if ($payload.PSObject.Properties.Name -contains $name -and $payload.$name) {
            $promptRaw = "$($payload.$name)"
            if ($promptRaw.Length -gt 400) {
                $promptSample = $promptRaw.Substring(0, 400)
            } else {
                $promptSample = $promptRaw
            }
            break
        }
    }
} catch {}

# Event and tool are display fields; keep each bounded and valid UTF-16.
foreach ($name in @('event', 'tool')) {
    $value = Get-Variable -Name $name -ValueOnly
    if ($value.Length -gt 128) {
        $end = if ([char]::IsHighSurrogate($value[127])) { 127 } else { 128 }
        Set-Variable -Name $name -Value $value.Substring(0, $end)
    }
}

# --- Compose JSON record ---
$record = [ordered]@{
    ts            = $timestamp
    event         = $event
    tool          = $tool
    prompt_sample = $promptSample
}
try {
    $line = $record | ConvertTo-Json -Compress -Depth 3
} catch { exit 0 }

# Serialize append and rotation together so parallel PowerShell writers cannot
# drop an append on a sharing violation or replace one another's newer records.
$mutex = $null
$locked = $false
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $destination = [System.IO.Path]::GetFullPath($obsPath).ToUpperInvariant()
        $lockHash = [System.BitConverter]::ToString($sha256.ComputeHash($utf8NoBom.GetBytes($destination))).Replace("-", "")
    } finally { $sha256.Dispose() }
    $mutex = New-Object System.Threading.Mutex($false, ("Local\NexusHubLearningCapture-" + $lockHash))
    try { $locked = $mutex.WaitOne(5000) }
    catch [System.Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) { exit 0 }

    try {
        [System.IO.File]::AppendAllText($obsPath, $line + "`n", $utf8NoBom)
    } catch { exit 0 }

    # --- Truncate when the file exceeds the cap ---
    $maxRaw = if ($env:NEXUS_LEARNING_MAX_BYTES) { $env:NEXUS_LEARNING_MAX_BYTES } else { "1048576" }
    $maxBytes = 0
    if (-not [int]::TryParse($maxRaw, [ref]$maxBytes) -or $maxBytes -le 0) {
        $maxBytes = 1048576
    }

    try {
        $size = (Get-Item $obsPath).Length
        if ($size -gt $maxBytes) {
            $allLines = [System.IO.File]::ReadAllLines($obsPath, $utf8NoBom)
            $kept = New-Object System.Collections.Generic.List[string]
            $total = 0
            for ($i = $allLines.Count - 1; $i -ge 0; $i--) {
                $bytes = $utf8NoBom.GetByteCount($allLines[$i] + "`n")
                if ($total + $bytes -gt $maxBytes) { break }
                $kept.Insert(0, $allLines[$i])
                $total += $bytes
            }
            $tmp = "$obsPath.trim.$PID"
            $body = if ($kept.Count) { ($kept -join "`n") + "`n" } else { "" }
            [System.IO.File]::WriteAllText($tmp, $body, $utf8NoBom)
            Move-Item -LiteralPath $tmp -Destination $obsPath -Force
        }
    } catch {}
} catch {
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    if ($mutex) { $mutex.Dispose() }
}

exit 0
