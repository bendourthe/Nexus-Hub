<#
.SYNOPSIS
    PowerShell parity for workflow-phase-notice.sh.

.DESCRIPTION
    PostToolUse hook (Write, Edit) that emits an advisory marker when the written
    file is a workflow-phase artifact (a plan, spec, tasks, or release file), as a
    reminder that the post-phase docs and commit sequence follows. Silent for every
    other path; always exits 0 and never blocks a phase.

    This is the runnable example behind the "Workflow-phase automation recipe" in
    guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md: it approximates
    "run automation at a workflow-phase boundary" on the existing PreToolUse /
    PostToolUse surface by keying on the tool call that marks the boundary and
    inspecting the tool input, rather than inventing new harness event types.

.NOTES
    Classification order matters and matches the .sh sibling: a plans-directory
    match wins over a bare plan.md basename.

    One deliberate difference, in the safe direction: the bash version needs `jq`
    and exits 0 silently without it. PowerShell parses JSON natively, so this
    version always classifies. It notices in strictly more cases, never fewer.
#>

$ErrorActionPreference = "Continue"

# --- Runtime controls ---
$hookName = "workflow-phase-notice"
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

# --- Classify the workflow phase by path / basename ---
# Order matters: a plans-directory match wins over a bare plan.md basename.
$phase = ""
if ($normPath -match '(^|/)docs/.*/plans/[^/]+\.md$') {
    $phase = "plan"
} elseif ($baseName -eq "spec.md") {
    $phase = "spec"
} elseif ($baseName -eq "tasks.md") {
    $phase = "tasks"
} elseif ($baseName -eq "CHANGELOG.md") {
    $phase = "release"
}

# Silent for any non-workflow artifact.
if (-not $phase) { exit 0 }

# --- Emit advisory marker ---
[Console]::Error.WriteLine("[workflow-phase-notice] $phase-phase artifact written: $normPath. Remember the post-phase docs + commit sequence.")
exit 0
