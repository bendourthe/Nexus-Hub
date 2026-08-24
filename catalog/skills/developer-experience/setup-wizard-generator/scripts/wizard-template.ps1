<#
.SYNOPSIS
    Interactive, resumable wizard template (PowerShell 5.1-safe sibling).

.DESCRIPTION
    Matching behavior for wizard-template.sh: one step at a time, confirmation,
    observable checks, resume via a state file of completed step ids.
    Adapt step ids, titles, and checks to the human-only sequence.
    Never echo secrets. Never use Invoke-Expression on user input.

.NOTES
    State file format is identical to the bash sibling: one completed step id
    per line, lines starting with # ignored. Override with WIZARD_STATE_FILE.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-WizardStateFile {
    if ($env:WIZARD_STATE_FILE -and $env:WIZARD_STATE_FILE.Trim()) {
        return $env:WIZARD_STATE_FILE
    }
    return ".wizard-state"
}

function Test-StepDone {
    param([Parameter(Mandatory = $true)][string]$Id)
    $stateFile = Get-WizardStateFile
    if (-not (Test-Path -LiteralPath $stateFile)) { return $false }
    $lines = [System.IO.File]::ReadAllLines((Resolve-Path -LiteralPath $stateFile))
    foreach ($line in $lines) {
        if ($line -like "#*") { continue }
        if ($line -eq $Id) { return $true }
    }
    return $false
}

function Set-StepDone {
    param([Parameter(Mandatory = $true)][string]$Id)
    $stateFile = Get-WizardStateFile
    $dir = Split-Path -Parent $stateFile
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    if (Test-Path -LiteralPath $stateFile) {
        $existing = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $stateFile), $utf8)
        if ($existing.Length -gt 0 -and -not $existing.EndsWith("`n")) {
            $existing += "`n"
        }
        [System.IO.File]::WriteAllText($stateFile, $existing + $Id + "`n", $utf8)
    } else {
        [System.IO.File]::WriteAllText($stateFile, $Id + "`n", $utf8)
    }
}

function Confirm-WizardStep {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    $reply = Read-Host $Prompt
    if ([string]::IsNullOrWhiteSpace($reply) -or $reply -match '^(y|yes)$') {
        return
    }
    throw "aborted at confirmation"
}

function Test-FileExists {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Test-Path -LiteralPath $Path)
}

function Invoke-StepWelcome {
    $id = "welcome"
    if (Test-StepDone -Id $id) {
        Write-Host "skip $id (already completed)"
        return
    }
    Write-Host ""
    Write-Host "== $id =="
    Write-Host "This wizard walks human-only setup. The agent that generated it must not run privileged steps for you."
    Write-Host "Why: a resumable script beats a half-remembered checklist."
    Confirm-WizardStep -Prompt "Press Enter to start (or type n to abort)"
    Set-StepDone -Id $id
}

function Invoke-StepExampleObservable {
    $id = "example-observable"
    $marker = ".wizard-example-marker"
    if ($env:WIZARD_EXAMPLE_MARKER -and $env:WIZARD_EXAMPLE_MARKER.Trim()) {
        $marker = $env:WIZARD_EXAMPLE_MARKER
    }
    if (Test-StepDone -Id $id) {
        Write-Host "skip $id (already completed)"
        return
    }
    Write-Host ""
    Write-Host "== $id =="
    Write-Host "Do: create the marker file the check expects."
    Write-Host "Why: the next steps assume this observable exists."
    Write-Host "Expected: a file at $marker"
    Write-Host "Create it yourself (the wizard will not write secrets or privileged files)."
    Confirm-WizardStep -Prompt "Press Enter after the file exists"
    if (-not (Test-FileExists -Path $marker)) {
        throw "expected file missing: $marker (step not marked complete; re-run to retry)"
    }
    Set-StepDone -Id $id
}

function Invoke-StepComplete {
    $id = "complete"
    if (Test-StepDone -Id $id) {
        Write-Host "skip $id (already completed)"
        return
    }
    Write-Host ""
    Write-Host "== $id =="
    Write-Host ("All adapted steps finished. State file: {0}" -f (Get-WizardStateFile))
    Set-StepDone -Id $id
}

Invoke-StepWelcome
Invoke-StepExampleObservable
Invoke-StepComplete
Write-Host "wizard finished"
