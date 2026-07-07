<#
Nexus-Hub "seed on project open" hook (v3.11.0 Phase 7.3). PowerShell sibling of
nexus-hub-autoseed.sh. Dot-source from your PowerShell profile to auto-seed a
repo's project surfaces (Antigravity .agents/, Cursor rules, Claude settings
stub) the first time you enter it.

  Enable:  add to $PROFILE:  . "$HOME\.nexus-hub\hooks\nexus-hub-autoseed.ps1"
  Disable: $env:NEXUS_HUB_NO_AUTOSEED = "1"

Design: fail-open (a hook error never disrupts the prompt), idempotent (a
.nexus-hub/seeded marker prevents re-seeding), opt-out via the env var. The
installer NEVER auto-edits your profile; enabling this hook is your explicit
opt-in.
#>

function global:Invoke-NexusHubAutoseed {
    if ($env:NEXUS_HUB_NO_AUTOSEED -eq "1") { return }
    if (-not (Get-Command nexus-hub -ErrorAction SilentlyContinue)) { return }
    try {
        $top = (& git rev-parse --show-toplevel 2>$null)
        if (-not $top) { return }
        $top = $top.Trim()
        $nexusHome = Join-Path $HOME ".nexus-hub"
        if ($top -eq $nexusHome -or $top.StartsWith($nexusHome)) { return }
        $marker = Join-Path $top ".nexus-hub/seeded"
        if (Test-Path $marker) { return }
        & nexus-hub init --target $top --quiet *> $null
        New-Item -ItemType Directory -Force -Path (Join-Path $top ".nexus-hub") *> $null
        New-Item -ItemType File -Force -Path $marker *> $null
    } catch { }  # fail-open: never disrupt the prompt
}

# Wrap the prompt so the seed check runs on each directory context. Guarded so
# re-sourcing does not stack wrappers.
if (-not $global:__NexusHubAutoseedHooked) {
    $global:__NexusHubAutoseedPrevPrompt = $function:prompt
    function global:prompt {
        Invoke-NexusHubAutoseed
        if ($global:__NexusHubAutoseedPrevPrompt) { & $global:__NexusHubAutoseedPrevPrompt }
        else { "PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) " }
    }
    $global:__NexusHubAutoseedHooked = $true
}
