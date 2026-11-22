<#
.SYNOPSIS
    PowerShell parity for worktree-policy.sh.

.DESCRIPTION
    PreToolUse hook that refuses a recognized `git worktree add` or `git worktree move`
    whose destination is not <root>/<identity>/<name>. The proposed command is read only
    from stdin tool_input.command and is handed to _worktree_policy.py, a pure policy
    check. This hook never runs the proposed command. Exit 0 allows; exit 2 denies.

    This is a mandatory guard: it does not honor NEXUS_HOOK_PROFILE=minimal or
    NEXUS_DISABLED_HOOKS and applies in every host permission mode. The only override is
    changing the worktree root (NEXUS_WORKTREE_ROOT or the user's own config file).
#>

$ErrorActionPreference = "Continue"
$script:NexusTag = "[Nexus-Hub: worktree-policy]"

function Write-NexusMessage {
    param([string]$Message)
    [Console]::Error.WriteLine("$script:NexusTag $Message")
}

if (-not [Console]::IsInputRedirected) { exit 0 }
$hookUtf8 = New-Object System.Text.UTF8Encoding($false)
$inputText = (New-Object System.IO.StreamReader([Console]::OpenStandardInput(), $hookUtf8, $true)).ReadToEnd()
# Windows PowerShell 5.1 without a console drains the raw handle into [Console]::In.
if (-not $inputText) { $inputText = [Console]::In.ReadToEnd() }
if (-not $inputText -or -not $inputText.Trim()) { exit 0 }

$helper = Join-Path $PSScriptRoot "_worktree_policy.py"
$OutputEncoding = $hookUtf8

foreach ($candidate in @("python", "python3", "py")) {
    $found = Get-Command $candidate -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $found) { continue }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $found.Source
    $psi.Arguments = '"' + $helper + '"'
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardError = $true
    $psi.RedirectStandardOutput = $true
    $psi.StandardErrorEncoding = $hookUtf8
    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
        $bytes = $hookUtf8.GetBytes($inputText)
        $proc.StandardInput.BaseStream.Write($bytes, 0, $bytes.Length)
        $proc.StandardInput.Close()
        $stderrTask = $proc.StandardError.ReadToEndAsync()
        $null = $proc.StandardOutput.ReadToEnd()
        $proc.WaitForExit()
        $stderrText = $stderrTask.Result
        $rc = $proc.ExitCode
    } catch {
        continue
    }
    # 0 allows and 42 is the helper's denial; any other code means this interpreter did not run it.
    if ($rc -eq 0 -or $rc -eq 42) {
        if ($stderrText) { [Console]::Error.Write($stderrText) }  # nexus: hook-msg-exempt relays the helper's own tagged message
        if ($rc -eq 42) { exit 2 }
        exit 0
    }
}

# No usable interpreter: a worktree add or move cannot be certified, anything else is allowed.
if ($inputText -match '(?i)worktree\s+(add|move)') {
    Write-NexusMessage "BLOCKED: no Python interpreter is available to certify a worktree add or move. Use: nexus-hub worktree create --repo <checkout> --branch <branch> --base <commit> --name <name>."
    exit 2
}
exit 0
