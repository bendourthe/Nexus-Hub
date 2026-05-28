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

try {
    Add-Content -Path $obsPath -Value $line -Encoding utf8
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
        $allLines = Get-Content -Path $obsPath -Encoding utf8
        if ($allLines.Count -gt 1) {
            $keep = [int]([math]::Floor($allLines.Count / 2))
            if ($keep -lt 1) { $keep = 1 }
            $tail = $allLines[-$keep..-1]
            $tmp = "$obsPath.trim.$PID"
            $tail | Out-File -FilePath $tmp -Encoding utf8
            Move-Item -Path $tmp -Destination $obsPath -Force
        }
    }
} catch {}

exit 0
