<#
.SYNOPSIS
    Consume typed implementation reconciliation through the installed trusted core.
.NOTES
    NEXUS_DISABLED_HOOKS=implementation-state or NEXUS_HOOK_PROFILE=minimal disables this consumer.
    No bound record is silent. The installed core owns usage, authority, waits and loop bounds.
#>
$ErrorActionPreference = "Continue"
$hookName = "implementation-state"
$disabled = ($env:NEXUS_DISABLED_HOOKS -split ",") | ForEach-Object { $_.Trim() }
if ($disabled -contains $hookName -or $env:NEXUS_HOOK_PROFILE -eq "minimal") {
    if ([Console]::IsInputRedirected) {
        try { [Console]::OpenStandardInput().CopyTo([System.IO.Stream]::Null) } catch { }
    }
    exit 0
}
$homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
if (-not $homeDir) { exit 0 }
$core = Join-Path $homeDir ".nexus-hub\scripts\completion_gate.py"
$python = $null
foreach ($candidate in @("python3", "python")) {
    $command = Get-Command $candidate -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { continue }
    if ($command.Source -match 'WindowsApps') {
        $probe = New-Object System.Diagnostics.ProcessStartInfo
        $probe.FileName = $command.Source
        $probe.Arguments = '-B -c "import sys"'
        $probe.UseShellExecute = $false; $probe.CreateNoWindow = $true
        $probe.RedirectStandardOutput = $true; $probe.RedirectStandardError = $true
        try {
            $check = [System.Diagnostics.Process]::Start($probe)
            $null = $check.StandardOutput.ReadToEnd(); $null = $check.StandardError.ReadToEnd()
            $check.WaitForExit()
            if ($check.ExitCode -ne 0) { continue }
        } catch { continue }
    }
    $python = $command.Source
    break
}
$inputBytes = [byte[]]@()
if ([Console]::IsInputRedirected) {
    $buffer = New-Object System.IO.MemoryStream
    try { [Console]::OpenStandardInput().CopyTo($buffer) } catch { }
    $inputBytes = $buffer.ToArray()
    if ($inputBytes.Length -eq 0) {
        try { $fallbackText = [Console]::In.ReadToEnd() } catch { $fallbackText = "" }
        if ($fallbackText) { $inputBytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($fallbackText) }
    }
}
if (-not $python -or -not (Test-Path -LiteralPath $core -PathType Leaf)) { exit 0 }
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python
$psi.Arguments = '-B "' + $core + '" reconcile-stop'
$psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
$psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
$utf8 = New-Object System.Text.UTF8Encoding($false)
$psi.StandardOutputEncoding = $utf8; $psi.StandardErrorEncoding = $utf8
$psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
try { $proc = [System.Diagnostics.Process]::Start($psi) } catch { exit 0 }
try {
    $proc.StandardInput.BaseStream.Write($inputBytes, 0, $inputBytes.Length)
    $proc.StandardInput.BaseStream.Flush()
    $proc.StandardInput.BaseStream.Close()
} catch { }
$out = $proc.StandardOutput.ReadToEnd(); $err = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
if ($out) { [Console]::Out.Write($out) }
if ($err) { [Console]::Error.Write($err) } # nexus: hook-msg-exempt relays the installed completion_gate.py core's output verbatim
exit $proc.ExitCode
