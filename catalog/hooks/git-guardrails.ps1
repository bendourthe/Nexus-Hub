<#
.SYNOPSIS
    PowerShell parity for git-guardrails.sh.

.DESCRIPTION
    PreToolUse hook (Bash) that reads a Claude Code JSON payload from stdin,
    extracts tool_input.command, and blocks (exit 2) when the command matches a
    dangerous git pattern. Allows (exit 0) otherwise.

    Covers three classes:
      1. Destructive history / working-tree operations (force push, hard reset,
         clean -f, branch -D, stash drop/clear, rm -rf .git).
      2. Git execution indirection (core.hooksPath / core.fsmonitor), both the
         inline `git -c key=value` form and the persistent `git config` form.
         This is group B of the canonical execution-trigger surface list.
      3. An opt-in protected-branch commit guard (NEXUS_PROTECTED_BRANCHES).

    This script mirrors the .sh implementation so Windows users who run hooks
    through PowerShell get the same guardrail.

.NOTES
    Limitation (read this before trusting it): these are fixed regexes matched
    against the RAW command string, not an argv decomposition. Quoting, unusual
    spacing, environment indirection, and equivalent alternate flags can all
    evade them, and a flag nobody listed will pass silently. This hook is
    defense-in-depth, NOT a boundary. See the "Limits and Honest Boundaries"
    section of catalog/skills/security-operations/agentic-endpoint-hardening/SKILL.md.

    Regex note: .NET regex is case-sensitive by default, matching the behavior of
    `grep -E` in the .sh sibling.
#>

# Never fail loudly on internal errors.
$ErrorActionPreference = "Continue"

# --- Dangerous patterns ---
# Each entry: @{ Pattern = '<regex>'; Desc = '<human-readable>' }
$dangerousPatterns = @(
    @{ Pattern = 'git\s+push\s+.*--force';            Desc = 'Force push overwrites remote history' }
    @{ Pattern = 'git\s+push\s+-[a-zA-Z]*f';          Desc = 'Force push overwrites remote history' }
    @{ Pattern = 'git\s+push\s+.*--force-with-lease'; Desc = 'Force-with-lease push overwrites remote history' }
    @{ Pattern = 'git\s+reset\s+--hard';              Desc = 'Hard reset discards all uncommitted work' }
    @{ Pattern = 'git\s+clean\s+-[a-zA-Z]*f';         Desc = 'Clean -f permanently deletes untracked files' }
    @{ Pattern = 'git\s+branch\s+-D';                 Desc = 'Force-delete branch without merge check' }
    @{ Pattern = 'git\s+checkout\s+\.';               Desc = 'Discards all working tree changes' }
    @{ Pattern = 'git\s+checkout\s+--\s+\.';          Desc = 'Discards all working tree changes' }
    @{ Pattern = 'git\s+restore\s+\.';                Desc = 'Discards all working tree changes' }
    @{ Pattern = 'git\s+stash\s+drop';                Desc = 'Permanently loses stashed work' }
    @{ Pattern = 'git\s+stash\s+clear';               Desc = 'Permanently loses all stashed work' }
    @{ Pattern = 'rm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+\.git'; Desc = 'Destroys the entire repository' }

    # Execution indirection via git metadata (group B of the canonical
    # execution-trigger surface list). Both settings name something git EXECUTES
    # on ordinary operations, so writing either turns a routine git command into
    # arbitrary code execution. The leading `(-c\s+\S+\s+)*` tolerates other -c
    # options appearing first, so interleaving them is not an evasion.
    @{ Pattern = 'git\s+(-c\s+\S+\s+)*-c\s*core\.hooksPath\s*=';
       Desc = 'Redirects git hooks to an agent-chosen directory, so a later git operation executes it' }
    @{ Pattern = 'git\s+(-c\s+\S+\s+)*-c\s*core\.fsmonitor\s*=';
       Desc = 'Sets the filesystem-monitor command git runs on ordinary operations, which is arbitrary execution' }
)

# --- Read JSON from stdin ---
if (-not [Console]::IsInputRedirected) { exit 0 }
$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }

$command = $null
try {
    $payload = $raw | ConvertFrom-Json
    if ($payload.tool_input -and
        ($payload.tool_input.PSObject.Properties.Name -contains 'command')) {
        $command = $payload.tool_input.command
    }
} catch {
    exit 0
}

# If we couldn't extract a command, allow (don't block non-Bash tools).
if (-not $command) { exit 0 }

# --- Heredoc-body separation (parity with strip_heredoc_bodies in the .sh) ---
# A command that WRITES a file (cat > doc.md <<'EOF' ... EOF) carries the file's
# text inside the same raw string the patterns are matched against, so prose that
# merely NAMES a destructive command reads as an attempt to RUN one.
#
# Bodies are removed from the BLOCKING scan, but a pattern found only inside a
# body still warns on stderr rather than vanishing, so the guard never silently
# matches less. See the longer rationale in the .sh sibling.
function Remove-HeredocBodies {
    param([string] $Text)
    $delimRe = '<<-?\s*["'']?([A-Za-z_][A-Za-z0-9_]*)["'']?'
    $kept = New-Object System.Collections.Generic.List[string]
    $delim = $null
    $inBody = $false
    foreach ($line in ($Text -split "`r?`n")) {
        if ($inBody) {
            if ($line.Trim() -ceq $delim) { $inBody = $false }
            continue
        }
        $m = [regex]::Match($line, $delimRe)
        if ($m.Success) {
            $delim = $m.Groups[1].Value
            $inBody = $true
        }
        $kept.Add($line) | Out-Null
    }
    return ($kept -join "`n")
}

# $scan drives every block decision below; $command is kept for reporting and for
# the written-content warning.
$scan = Remove-HeredocBodies -Text $command

# --- Check command against each pattern ---
foreach ($entry in $dangerousPatterns) {
    if ($scan -cmatch $entry.Pattern) {
        [Console]::Error.WriteLine("BLOCKED: '$command' matches dangerous git pattern. $($entry.Desc). The user has prevented you from doing this.")
        exit 2
    }
    if ($command -cmatch $entry.Pattern) {
        [Console]::Error.WriteLine("NOTE: a dangerous git pattern ($($entry.Desc)) appears inside written file content, not as a command. Allowing the write.")
    }
}

# --- Persistent execution-indirection guard (group B, `git config` form) ---
# core.hooksPath and core.fsmonitor are reachable two ways: inline for a single
# invocation (`git -c key=value ...`, caught above) and PERSISTENTLY via
# `git config`, which writes the value into .git/config so it applies to every
# later operation. The persistent form needs its own check because a read of the
# same key is harmless: `git config --get core.hooksPath` only inspects, so
# matching the key alone would false-positive on a diagnostic command. Flag the
# write forms and let the read forms through.
if (($scan -cmatch '(^|[;&|]|\s)git(\s|$).*config') -and
    ($scan -cmatch 'core\.(hooksPath|fsmonitor)') -and
    -not ($scan -cmatch '--(get|get-all|get-regexp|get-urlmatch|list|unset|unset-all)(\s|=|$)')) {
    [Console]::Error.WriteLine("BLOCKED: '$command' persists a git execution-indirection setting (core.hooksPath / core.fsmonitor). Git executes the named directory or command on ordinary operations, so this turns a later routine git call into arbitrary execution. The user has prevented you from doing this.")
    exit 2
}

# --- Protected-branch guard (opt-in via NEXUS_PROTECTED_BRANCHES) ---
# When a project declares protected (release-only) branches, block a direct
# `git commit` on them so feature/version work goes through a feature branch.
# Inert by default: does nothing unless NEXUS_PROTECTED_BRANCHES is set.
#   Configure : $env:NEXUS_PROTECTED_BRANCHES = "main develop"  (space- or comma-separated)
#   Override  : $env:NEXUS_PROTECTED_BRANCH_ALLOW = "1"         (allow one legitimate commit)
# Targets `git commit` only -- release merges (`git merge --no-ff` on the
# protected branch) and pushes are intentionally NOT blocked.
if ($env:NEXUS_PROTECTED_BRANCHES -and
    ($env:NEXUS_PROTECTED_BRANCH_ALLOW -ne '1') -and
    ($scan -cmatch '(^|[;&|]|\s)git\s+commit(\s|$)')) {
    $currentBranch = (& git rev-parse --abbrev-ref HEAD 2>$null | Out-String).Trim()
    if ($currentBranch) {
        $protectedList = $env:NEXUS_PROTECTED_BRANCHES -replace ',', ' '
        foreach ($b in ($protectedList -split '\s+' | Where-Object { $_ })) {
            if ($b -ceq $currentBranch) {
                [Console]::Error.WriteLine("BLOCKED: direct commit to protected branch '$currentBranch'. Branch off the integration branch first (e.g. 'git checkout -b feat/<slug>') and commit there; the protected branch receives release merges only. To allow this one commit, set NEXUS_PROTECTED_BRANCH_ALLOW=1.")
                exit 2
            }
        }
    }
}

# Command is safe
exit 0
