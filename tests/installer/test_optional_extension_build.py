"""Optional extension failures and shared Settings delivery through real installer helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("failure", ["out_cleanup", "cleanup", "package", "no_vsix"])
def test_optional_extension_build_failure_continues_install(tmp_path: Path, failure: str) -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is unavailable")

    source = (REPO_ROOT / "scripts" / "installer.sh").read_text(encoding="utf-8")
    function = source.split("build_and_install_one_extension() {", 1)[1].split(
        "# --- Template & Script Installation ---", 1
    )[0]
    extension = tmp_path / "extension"
    (extension / "out").mkdir(parents=True)
    (extension / "node_modules").mkdir(parents=True)
    shell = (
        """set -euo pipefail
        DARK_YELLOW='' RESET='' RED='' GREEN='' GRAY='' YELLOW=''
        write_item() { printf '%s\\n' "$1"; }
        rm() {
            if [[ "$FAIL_STEP" == out_cleanup && "$*" == */out* ]]; then return 12; fi
            if [[ "$FAIL_STEP" == cleanup && "$*" == *node_modules* ]]; then return 13; fi
            command rm "$@"
        }
        npm() { return 0; }
        npx() { if [[ "$FAIL_STEP" == package ]]; then return 23; fi; return 0; }
        build_and_install_one_extension() {
        """
        + function
        + """
        build_and_install_one_extension "$PWD/extension" test.optional Optional '--%' '' Editor
        build_and_install_one_extension missing test.next Next '--%' '' Editor
        printf 'CONTINUED\\n'
        """
    )
    env = os.environ.copy()
    env["FAIL_STEP"] = failure
    result = subprocess.run(
        [bash, "-c", shell], cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Extension source not found at: missing" in result.stdout
    assert "CONTINUED" in result.stdout
    assert "failed" in result.stdout.lower()


@pytest.mark.parametrize("shell_name", ["bash", "powershell"])
@pytest.mark.parametrize("scenario", ["all_hosts", "without_vscode", "failed_cursor"])
def test_settings_builds_once_for_all_detected_hosts(
    tmp_path: Path, shell_name: str, scenario: str
) -> None:
    """Exercise shipped routing and build code without npm, editor launches, or a real home."""
    shell = shutil.which(shell_name)
    if shell is None:
        pytest.skip(f"{shell_name} is unavailable")
    monitors = {
        "claude-usage-monitor": "vscode",
        "codex-usage-monitor": "vscode",
        "copilot-usage-monitor": "vscode",
        "cursor-usage-monitor": "cursor",
        "gemini-usage-monitor": "antigravity",
    }
    extensions = [*monitors, "nexus-hub-settings"]
    for extension in extensions:
        (tmp_path / "repo" / "extensions" / extension).mkdir(parents=True)
    events = tmp_path / "events.txt"
    env = os.environ.copy()
    env["TEST_EVENTS"] = events.as_posix()
    env["TEST_REPO"] = str(tmp_path / "repo")
    env["FAIL_HOST"] = "cursor" if scenario == "failed_cursor" else ""
    env["NO_VSCODE"] = "1" if scenario == "without_vscode" else ""
    if shell_name == "bash":
        source = (REPO_ROOT / "scripts" / "installer.sh").read_text(encoding="utf-8")
        body = source.split("build_and_install_one_extension() {", 1)[1].split(
            "# --- Template & Script Installation ---", 1
        )[0]
        calls = "\n".join(
            line for line in source.splitlines()
            if line.strip().startswith('build_and_install_one_extension "$repo_root/extensions/')
        )
        script = r"""set -euo pipefail
        DARK_YELLOW='' RESET='' RED='' GREEN='' GRAY='' YELLOW=''
        write_item() { :; }
        run_with_timeout() { shift 2; "$@"; }
        npm() { return 0; }
        npx() { printf 'PACKAGE|%s\n' "$(basename "$PWD")" >> "$TEST_EVENTS"; touch package.vsix; }
        editor_stub() {
            local host="$1"; shift
            if [ "$1" = --install-extension ]; then
                printf 'INSTALL|%s|%s\n' "$host" "$2" >> "$TEST_EVENTS"
                if [ "$host" = "$FAIL_HOST" ]; then return 9; fi
            fi
            return 0
        }
        code_stub() { editor_stub vscode "$@"; }
        cursor_stub() { editor_stub cursor "$@"; }
        antigravity_stub() { editor_stub antigravity "$@"; }
        repo_root="$PWD/repo"
        vscode_cli=code_stub; vscode_label='VS Code'
        cursor_cli=cursor_stub; cursor_label=Cursor
        antigravity_cli=antigravity_stub; antigravity_label=Antigravity
        if [ -n "$NO_VSCODE" ]; then vscode_cli=''; fi
        build_and_install_one_extension() {
        """ + body + calls
        script_file = tmp_path / "exercise.sh"
        script_file.write_text(script + "\n", encoding="utf-8")
        command = [shell, script_file.as_posix()]
    else:
        source = (REPO_ROOT / "scripts" / "installer.ps1").read_text(encoding="utf-8")
        body = source.split("function Build-And-Install-One-Extension {", 1)[1].split(
            "# --- Template & Script Installation ---", 1
        )[0]
        calls = "\n".join(
            line for line in source.splitlines()
            if line.strip().startswith("Build-And-Install-One-Extension -ExtensionDir (Join-Path $RepoRoot")
        )
        script = r"""$ErrorActionPreference = 'Stop'
        function Write-Item { param($Message, $Color) }
        function Restore-Title { }
        function Invoke-CommandWithTimeout { return @{ ExitCode = 0; TimedOut = $false; Output = @() } }
        function npm { $global:LASTEXITCODE = 0 }
        function npx {
            $name = Split-Path (Get-Location).Path -Leaf
            [System.IO.File]::AppendAllText($env:TEST_EVENTS, "PACKAGE|$name`n")
            [System.IO.File]::WriteAllText((Join-Path (Get-Location).Path 'package.vsix'), '')
            $global:LASTEXITCODE = 0
        }
        function Editor-Stub {
            param($EditorName, [string[]]$CliArgs)
            $global:LASTEXITCODE = 0
            if ($CliArgs[0] -eq '--install-extension') {
                [System.IO.File]::AppendAllText($env:TEST_EVENTS, "INSTALL|$EditorName|$($CliArgs[1])`n")
                if ($EditorName -eq $env:FAIL_HOST) { $global:LASTEXITCODE = 9 }
            }
        }
        function code_stub { Editor-Stub 'vscode' $args }
        function cursor_stub { Editor-Stub 'cursor' $args }
        function antigravity_stub { Editor-Stub 'antigravity' $args }
        $RepoRoot = $env:TEST_REPO
        $vscodeCli = 'code_stub'; $vscodeLabel = 'VS Code'
        $cursorCli = 'cursor_stub'; $cursorLabel = 'Cursor'
        $antigravityCli = 'antigravity_stub'; $antigravityLabel = 'Antigravity'
        if ($env:NO_VSCODE) { $vscodeCli = $null }
        function Build-And-Install-One-Extension {
        """ + body + calls
        script_file = tmp_path / "exercise.ps1"
        script_file.write_text(script + "\n", encoding="utf-8-sig")
        command = [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script_file)]
    result = subprocess.run(
        command, cwd=tmp_path, env=env, text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=30, check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    observed = [line.split("|") for line in events.read_text(encoding="utf-8").splitlines()]
    packages = [event[1] for event in observed if event[0] == "PACKAGE"]
    assert sorted(packages) == sorted(extensions), "Each extension must be packaged exactly once"
    installed: dict[str, list[tuple[str, str]]] = {}
    for event in observed:
        if event[0] == "INSTALL":
            extension = event[2].replace("\\", "/").split("/")[-2]
            installed.setdefault(extension, []).append((event[1], event[2]))
    expected_hosts = ["cursor", "antigravity"] if scenario == "without_vscode" else ["vscode", "cursor", "antigravity"]
    assert [host for host, _ in installed["nexus-hub-settings"]] == expected_hosts
    assert len({artifact for _, artifact in installed["nexus-hub-settings"]}) == 1, "All editors must receive the same build"
    for extension, host in monitors.items():
        expected = [] if scenario == "without_vscode" and host == "vscode" else [host]
        assert [editor for editor, _ in installed.get(extension, [])] == expected
