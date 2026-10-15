<#
.SYNOPSIS
    Apply a model + effort switch for a given agentic platform.

.DESCRIPTION
    PowerShell sibling of switch-model.sh. Behavior follows the three-tier
    switch spectrum:
      - Scriptable (codex, antigravity, gemini-cli): validate the model against
        the enumerated set, then print the exact NON-INTERACTIVE switch command
        that applies it on the next invocation. Emitting the command is the
        switch artifact: a subprocess helper cannot mutate a sibling CLI's live
        session, and silently rewriting a user config file would be a
        surprising side effect, so the deterministic, idempotent action is to
        print the documented mechanism.
      - One user action (claude-code): the main loop cannot switch its own model
        mid-session; print the exact /model (+ /effort) keystroke to type.
      - Manual only (cursor, copilot, opencode): print the model-picker step.

    Model validation: the requested model must appear in the enumerated set
    before a scriptable switch is emitted. The set is taken from
    NEXUS_ROUTING_MODELS when that env var is set (a comma/space/newline list
    the caller already enumerated for the session), otherwise from the sibling
    enumerate-models.ps1. When the set cannot be enumerated (the CLI is absent
    and no NEXUS_ROUTING_MODELS is supplied), the helper refuses rather than
    guess.

    Idempotent, zero outbound calls, no new credential. The only network surface
    in this skill is the optional Anthropic GET /v1/models inside
    enumerate-models.ps1, gated on ANTHROPIC_API_KEY already being present.

    Exit codes: 0 success; 2 usage/unknown platform; 3 model not in enumerated
    set; 4 enumeration unavailable so the model could not be validated.

.PARAMETER Platform
    A normalized platform id produced by detect-platform.ps1.

.PARAMETER Model
    A model from the platform's enumerated set.

.PARAMETER Effort
    Optional reasoning effort (low|medium|high|xhigh|max) where the platform
    exposes an effort knob; ignored otherwise.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Platform,
    [Parameter(Mandatory = $true, Position = 1)]
    [string]$Model,
    [Parameter(Mandatory = $false, Position = 2)]
    [string]$Effort = ''
)

Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-ErrorMsg { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-InfoMsg  { param([string]$Message) Write-Host "[INFO]  $Message" }

# Resolve the enumerated model set into a string array, or $null when no
# scriptable set is available.
function Get-EnumeratedModels {
    param([string]$PlatformId)

    # 1. Caller-supplied set (already enumerated for the session).
    if ($env:NEXUS_ROUTING_MODELS) {
        return ($env:NEXUS_ROUTING_MODELS -split '[,\s]+' | Where-Object { $_ -ne '' })
    }

    # 2. Enumerate via the sibling helper.
    $enumerate = Join-Path $scriptDir 'enumerate-models.ps1'
    if (-not (Test-Path $enumerate)) {
        return $null
    }
    $out = ''
    try {
        $out = (& $enumerate $PlatformId 2>$null | Out-String)
    } catch {
        return $null
    }
    if ([string]::IsNullOrWhiteSpace($out)) {
        return $null
    }
    # A picker/config sentinel carries no scriptable list -> cannot validate.
    if ($out -match '"source":"(picker|config)"') {
        return $null
    }
    # Return the raw enumeration blob as a single-element array. Different
    # platforms name the model field differently (Codex uses "slug", the
    # Anthropic API uses "id"), and the JSON also carries unrelated ids (e.g.
    # service-tier ids), so a targeted field extraction is fragile. The caller
    # validates by substring against this blob, which accepts any model id that
    # appears in the live enumeration.
    return @($out)
}

# Returns 0 if present, 3 if absent, 4 if the set cannot be determined.
function Test-ModelInSet {
    param([string]$PlatformId, [string]$ModelId)
    $set = Get-EnumeratedModels -PlatformId $PlatformId
    if ($null -eq $set) {
        return 4
    }
    foreach ($entry in $set) {
        if ($entry -eq $ModelId) { return 0 }
        if ($entry -like "*$ModelId*") { return 0 }
    }
    return 3
}

function Invoke-ScriptableSwitch {
    param([string]$PlatformId, [string]$ModelId, [string]$EffortLevel)

    $rc = Test-ModelInSet -PlatformId $PlatformId -ModelId $ModelId
    switch ($rc) {
        3 {
            Write-ErrorMsg "model '$ModelId' is not in the enumerated set for '$PlatformId'; refusing to switch."
            exit 3
        }
        4 {
            Write-ErrorMsg "cannot validate '$ModelId' for '$PlatformId': model enumeration is unavailable."
            Write-InfoMsg  "install the platform CLI, or pass the enumerated set via NEXUS_ROUTING_MODELS."
            exit 4
        }
    }

    switch ($PlatformId) {
        'codex' {
            if ($EffortLevel) {
                Write-Output "codex -c model=$ModelId -c model_reasoning_effort=$EffortLevel"
            } else {
                Write-Output "codex -c model=$ModelId"
            }
        }
        'antigravity' {
            Write-Output "agy -m $ModelId"
            if ($EffortLevel) { Write-InfoMsg "antigravity exposes no documented effort knob; effort '$EffortLevel' ignored." }
        }
        'gemini-cli' {
            Write-Output "gemini --model $ModelId"
            Write-InfoMsg "or set GEMINI_MODEL=$ModelId / settings.json model.name=$ModelId for a persistent switch."
            if ($EffortLevel) { Write-InfoMsg "gemini-cli exposes no documented effort knob; effort '$EffortLevel' ignored." }
        }
    }
    $effortNote = if ($EffortLevel) { " (effort: $EffortLevel)" } else { '' }
    Write-InfoMsg "scriptable switch for '$PlatformId' -> ${ModelId}${effortNote}: run the command above to apply on the next invocation."
    exit 0
}

switch ($Platform) {
    { $_ -in @('codex', 'antigravity', 'gemini-cli') } {
        Invoke-ScriptableSwitch -PlatformId $Platform -ModelId $Model -EffortLevel $Effort
        break
    }
    'claude-code' {
        Write-Output "Type in this session: /model $Model"
        if ($Effort) { Write-Output "Then type: /effort $Effort" }
        Write-InfoMsg "claude-code cannot switch its own model from a script; type the instruction(s) above. Delegated subagent work can be routed via the Task/Workflow model parameter."
        exit 0
    }
    { $_ -in @('cursor', 'copilot', 'opencode') } {
        Write-Output "Select `"$Model`" in the $Platform model picker."
        Write-InfoMsg "$Platform exposes no scriptable switch surface; select the model manually."
        exit 0
    }
    { $_ -in @('unknown', '') } {
        Write-ErrorMsg "platform is unknown; cannot switch. Run detect-platform.ps1 first."
        exit 2
    }
    default {
        Write-ErrorMsg "unrecognized platform '$Platform'."
        exit 2
    }
}
