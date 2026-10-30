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
      4. An opt-in bypass-flag mode (v4.14.4): when ~/.nexus-hub/guardrails.json sets
         "block_git_bypass_flags": true (or NEXUS_GUARD_GIT_BYPASS=1), the flags that
         skip git hooks or commit signing are blocked: --no-verify, git commit -n,
         --no-gpg-sign, and gpgsign=false set inline or persisted. Off by default; the
         file is read on every run, so it needs no restart.

    Runs for the Bash tool and the PowerShell tool (settings.json matcher
    "Bash|PowerShell"); both send the command as tool_input.command.

    This script mirrors the .sh implementation so Windows users who run hooks
    through PowerShell get the same guardrail.

.NOTES
    Limitation (read this before trusting it): these are fixed regexes matched
    against the RAW command string, not an argv decomposition. Quoting, unusual
    spacing, environment indirection, and equivalent alternate flags can all
    evade them, and a flag nobody listed will pass silently. This hook is
    defense-in-depth, NOT a boundary. See the "Limits and Honest Boundaries"
    section of catalog/skills/security-operations/agentic-endpoint-hardening/SKILL.md.

    Limits of the opt-in bypass-flag mode: environment-variable skips (HUSKY=0, SKIP=,
    LEFTHOOK=0, GIT_CONFIG_*), git plumbing (commit-tree, update-ref), shell aliases
    and scripts, bypassPermissions mode, and an agent that edits guardrails.json
    itself. The full list is on the mode's block below and in
    docs/decisions/*/tooling/2026-10-14-opt-in-git-bypass-flag-guard.md.

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
# Hook payloads are UTF-8 whatever the console code page is (WN-37): decode the raw
# handle and reply through UTF-8 writers rather than calling SetConsoleCP.
$hookUtf8 = New-Object System.Text.UTF8Encoding($false)
$raw = (New-Object System.IO.StreamReader([Console]::OpenStandardInput(), $hookUtf8, $true)).ReadToEnd()
# Windows PowerShell 5.1 without a console drains the raw handle into [Console]::In.
if (-not $raw) { $raw = [Console]::In.ReadToEnd() }
# Full access (Claude Code or Codex permission_mode "bypassPermissions"): the
# user chose to run without approval gates, so this Nexus-Hub guard steps aside.
# Contract: docs/policy/permission-mode-contract.md
try {
    $hostPayload = $raw | ConvertFrom-Json -ErrorAction Stop
    if ($hostPayload -is [pscustomobject] -and $hostPayload.permission_mode -is [string] -and $hostPayload.permission_mode -ceq 'bypassPermissions') { exit 0 }
} catch { }
$utf8Writer = New-Object System.IO.StreamWriter([Console]::OpenStandardOutput(), $hookUtf8); $utf8Writer.AutoFlush = $true; [Console]::SetOut($utf8Writer)
$utf8Writer = New-Object System.IO.StreamWriter([Console]::OpenStandardError(), $hookUtf8); $utf8Writer.AutoFlush = $true; [Console]::SetError($utf8Writer)
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
    # git reads config keys case-insensitively, so the core.* entries must too.
    $ci = $entry.Pattern -clike '*core\.*'
    $scanHit = if ($ci) { $scan -imatch $entry.Pattern } else { $scan -cmatch $entry.Pattern }
    $cmdHit = if ($ci) { $command -imatch $entry.Pattern } else { $command -cmatch $entry.Pattern }
    if ($scanHit) {
        [Console]::Error.WriteLine("BLOCKED: '$command' matches dangerous git pattern. $($entry.Desc). The user has prevented you from doing this.")
        exit 2
    }
    if ($cmdHit) {
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
    ($scan -imatch 'core\.(hooksPath|fsmonitor)') -and
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

# --- Opt-in git bypass-flag guard (v4.14.4; parity with the .sh) ---
# Blocks the flags that skip git hooks or commit signing, when a team opts in.
# Inert by default. Specification: docs/decisions/*/tooling/2026-10-14-opt-in-git-bypass-flag-guard.md
#   Switch   : ~/.nexus-hub/guardrails.json  {"block_git_bypass_flags": true}
#              Read on EVERY run, so editing it takes effect on the next command.
#   Override : $env:NEXUS_GUARD_GIT_BYPASS = "1" (on) or "0" (off), read ONLY from
#              this hook's own environment. It is never parsed from the command text.
#   A missing file means off. A malformed file means off plus one stderr warning
#   naming the file; it never crashes the hook, which would block every command.
#
# Blocked when on: --no-verify (and prefixes from --no-v) on commit, push, merge,
# rebase, am; -n as a `git commit` option (the short-option scan stops at an
# option that takes an argument, so -mn and -uno are not -n); --no-gpg-sign (and
# prefixes from --no-g) on commit, merge, rebase, cherry-pick, revert; inline
# -c commit.gpgsign=<false-like> and persistent `git config commit.gpgsign|
# tag.gpgsign <false-like>`, key in any letter case; all of these after git
# global options (git -C repo commit -n). Not blocked: git push -n, git log -n,
# git commit --no-edit.
#
# Before matching, quoted -m/--message/-F/--file values and heredoc bodies that
# only write a file are stripped; a heredoc body fed to an interpreter (bash, sh,
# zsh, pwsh, powershell, python) is kept and scanned.
#
# Documented limits (this is defense-in-depth, NOT a boundary):
#   - environment-variable skips (HUSKY=0, SKIP=, LEFTHOOK=0, GIT_CONFIG_*)
#   - git plumbing (commit-tree, update-ref, hash-object)
#   - shell aliases, wrapper scripts, and git aliases
#   - bypassPermissions mode (this whole hook steps aside)
#   - an agent that edits guardrails.json or this hook itself
#   - a flag built at run time (variables, command substitution, eval), quoted
#     as a separate word, or handed to a program that runs git later
#   - git invoked through a path that contains spaces
#   - git config --unset commit.gpgsign
function Test-BypassModeOn {
    if ($env:NEXUS_GUARD_GIT_BYPASS -ceq '1') { return $true }
    if ($env:NEXUS_GUARD_GIT_BYPASS -ceq '0') { return $false }
    # HOME first, then USERPROFILE, to match the .sh sibling.
    $homeDir = ''
    if ($env:HOME) { $homeDir = $env:HOME } elseif ($env:USERPROFILE) { $homeDir = $env:USERPROFILE }
    if (-not $homeDir) { return $false }
    $cfg = Join-Path $homeDir '.nexus-hub/guardrails.json'
    if (-not (Test-Path -LiteralPath $cfg -PathType Leaf)) { return $false }
    $verdict = 'invalid'
    try {
        # ReadAllText drops a UTF-8 byte order mark; ConvertFrom-Json rejects malformed JSON.
        $text = [System.IO.File]::ReadAllText($cfg, (New-Object System.Text.UTF8Encoding($false)))
        $obj = $text | ConvertFrom-Json -ErrorAction Stop
        # [pscustomobject] is the PSObject wrapper in 5.1, so -is is true for any value;
        # check the concrete type to accept a JSON object and nothing else.
        if (($null -ne $obj) -and ($obj.GetType().FullName -ceq 'System.Management.Automation.PSCustomObject')) {
            $verdict = 'false'
            if (($obj.PSObject.Properties.Name -contains 'block_git_bypass_flags') -and
                ($obj.block_git_bypass_flags -is [bool]) -and $obj.block_git_bypass_flags) {
                $verdict = 'true'
            }
        }
    } catch { $verdict = 'invalid' }
    if ($verdict -ceq 'true') { return $true }
    if ($verdict -ceq 'false') { return $false }
    [Console]::Error.WriteLine("WARNING: git-guardrails: $cfg is not a valid JSON object; the git bypass-flag guard stays off.")
    return $false
}

# Like Remove-HeredocBodies, but keeps a body whose opener line names an
# interpreter, and does not mistake a here-string (<<<) for a heredoc.
function Remove-BypassHeredocs {
    param([string] $Text)
    $delimRe = '(^|[^<])<<-?\s*["'']?([A-Za-z_][A-Za-z0-9_]*)["'']?'
    $interpRe = '(^|[^A-Za-z0-9_.-])(bash|sh|zsh|pwsh|powershell|python[0-9.]*)(\.exe)?([^A-Za-z0-9_.-]|$)'
    $kept = New-Object System.Collections.Generic.List[string]
    $delim = $null
    $inBody = $false
    $keep = $false
    foreach ($line in ($Text -split "`r?`n")) {
        if ($inBody) {
            if ($line.Trim() -ceq $delim) { $inBody = $false }
            elseif ($keep) { $kept.Add($line) | Out-Null }
            continue
        }
        $m = [regex]::Match($line, $delimRe)
        if ($m.Success) {
            $delim = $m.Groups[2].Value
            $inBody = $true
            $keep = [regex]::IsMatch($line, $interpRe)
        }
        $kept.Add($line) | Out-Null
    }
    return ($kept -join "`n")
}

# Replace each quoted -m/--message/-F/--file value (also attached to a short
# cluster such as -am "text") with "", so a message that names a flag is not one.
function Remove-BypassMessages {
    param([string] $Text)
    $re = '(^|\s)(-[a-zA-Z]*[mF]|--message|--file)\s*=?\s*("[^"]*"|''[^'']*'')'
    return [regex]::Replace($Text, $re, '$1$2 ""')
}

# Returns a short reason when $Command holds a bypass flag, otherwise $null.
function Find-GitBypass {
    param([string] $Command)
    $text = Remove-BypassHeredocs -Text $Command
    $text = Remove-BypassMessages -Text $text
    $text = $text -replace '\\\r?\n', ' ' -replace '`\r?\n', ' '
    $q = '["'']'
    $val = '("[^"]*"|''[^'']*''|\S+)'
    $gopt = '(-C\s+' + $val + '|-c\s+' + $val + '|--(git-dir|work-tree|namespace|super-prefix|config-env)(=|\s+)' + $val +
        '|--exec-path(=\S+)?|--(no-pager|paginate|bare|no-replace-objects|literal-pathspecs|glob-pathspecs|noglob-pathspecs|icase-pathspecs|no-optional-locks|no-lazy-fetch|html-path|man-path|info-path)|-p|-P)'
    $pre = '(^|[\s(`{"''])(\S*[/\\])?git(\.exe)?' + $q + '?(\s+' + $gopt + ')*'
    $end = '(\s|"|''|=|$)'
    $reNv = $pre + '\s+(commit|push|merge|rebase|am)\s+(.*\s)?' + $q + '?--no-v(e(r(i(f(y)?)?)?)?)?' + $end
    $reN = $pre + '\s+commit\s+(.*\s)?-[ABDEGHIJKLMNOPQRTUVWXYZabdefghijklnopqrsvwxyz]*n[^\s"'']*(\s|"|''|$)'
    $reNg = $pre + '\s+(commit|merge|rebase|cherry-pick|revert)\s+(.*\s)?' + $q + '?--no-g(p(g(-(s(i(g(n)?)?)?)?)?)?)?' + $end
    $reInline = $pre + '\s+-c\s*' + $q + '?(commit|tag)\.gpgsign\s*=\s*' + $q + '?(false|no|off|0)?' + $q + '?(\s|$)'
    $reCfg = $pre + '\s+config((\s+(--file|-f|--blob)\s+' + $val + ')|(\s+-{1,2}[A-Za-z][A-Za-z-]*(=\S+)?))*\s+' + $q +
        '?(commit|tag)\.gpgsign' + $q + '?\s+(' + $q + '?(false|no|off|0)' + $q + '?|""|'''')(\s|$)'
    foreach ($seg in ($text -split '[;|&\r\n]+')) {
        if ($seg -cnotmatch 'git') { continue }
        if ($seg -cmatch $reNv) { return '--no-verify skips git hooks' }
        if ($seg -cmatch $reN) { return '-n skips git hooks' }
        if ($seg -cmatch $reNg) { return '--no-gpg-sign skips commit signing' }
        if ($seg -imatch $reInline) { return 'an inline gpgsign=false setting skips commit signing' }
        if ($seg -imatch $reCfg) { return 'persisting gpgsign=false skips commit signing' }
    }
    return $null
}

# The pre-filter keeps the switch file unread (and a malformed-file warning
# unprinted) for commands that do not mention git at all.
if ($command -cmatch 'git') {
    if (Test-BypassModeOn) {
        $bypassReason = Find-GitBypass -Command $command
        if ($bypassReason) {
            [Console]::Error.WriteLine("BLOCKED: '$command' skips git hooks or commit signing ($bypassReason). The opt-in bypass-flag guard is on (~/.nexus-hub/guardrails.json key block_git_bypass_flags; override NEXUS_GUARD_GIT_BYPASS=0 or 1 in the hook environment). To turn this mode off, set block_git_bypass_flags to false in that file; the next command is judged by the new value, with no restart. The user has prevented you from doing this.")
            exit 2
        }
    }
}

# Command is safe
exit 0
