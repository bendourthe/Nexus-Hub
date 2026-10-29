"""The Antigravity launcher is chosen by a bounded `--version` probe, not by existence.

Two Antigravity installs can coexist, and a stale launcher can sit first on PATH
(an Electron launcher whose V8 binary and snapshot come from different builds
crashes at startup). Picking the first launcher that merely exists made the
Gemini usage monitor fail to install while a working launcher sat next to it.
Both installers now probe each candidate in order and use the first one whose
`--version` exits 0 within a timeout.

These tests load the helpers' exact text from each installer and drive them with
fake launcher scripts in a temp directory (never the real Antigravity): a first
candidate that exits non-zero, one that hangs, a working one, and a list where
nothing works. Child processes inherit the suite-wide no-window default from
tests/conftest.py.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
INSTALLER_SH = ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = ROOT / "scripts" / "installer.ps1"


def _function(text: str, start: str) -> str:
    match = re.search(rf"^{re.escape(start)}.*?^}}", text, re.MULTILINE | re.DOTALL)
    assert match, f"{start!r} not found"
    return match.group(0)


def test_both_installers_select_the_antigravity_launcher_by_probe() -> None:
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    ps1 = INSTALLER_PS1.read_text(encoding="utf-8")
    assert 'select_working_launcher "$antigravity_label" 30' in sh
    assert "Select-WorkingLauncher -Candidates $antigravityCandidates" in ps1
    assert "--version" in _function(sh, "select_working_launcher() {")
    assert "--version" in _function(ps1, "function Select-WorkingLauncher {")
    # The probe must be the only way a launcher is chosen: no branch assigns the
    # first existing candidate directly.
    assert 'antigravity_cli="antigravity-ide"' not in sh
    assert '$antigravityCli = "antigravity-ide"' not in ps1
    assert "$antigravityCli = $candidate" not in ps1
    assert 'antigravity_cli="$antigravity_candidate"' not in sh


def test_both_installers_keep_the_antigravity_candidate_order() -> None:
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    ps1 = INSTALLER_PS1.read_text(encoding="utf-8")
    assert sh.index("antigravity-ide antigravity; do") < sh.index("Antigravity IDE.app/Contents")
    assert ps1.index('@("antigravity-ide", "antigravity")') < ps1.index("Programs\\Antigravity IDE\\bin\\antigravity-ide.cmd")
    ps1_known = ps1[ps1.index("$antigravityKnownPaths = @("):]
    assert ps1_known.index("Antigravity IDE\\bin\\antigravity-ide.cmd") < ps1_known.index(
        "Programs\\Antigravity\\bin\\antigravity-ide.cmd"
    )


@pytest.mark.skipif(sys.platform == "win32", reason="installer.sh runs on macOS and Linux; Windows uses installer.ps1")
@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_bash_selector_skips_failing_and_hanging_launchers(tmp_path: Path) -> None:
    text = INSTALLER_SH.read_text(encoding="utf-8")
    helpers = _function(text, "run_with_timeout() {") + "\n" + _function(text, "select_working_launcher() {")
    launchers = tmp_path / "Antigravity IDE" / "bin"
    launchers.mkdir(parents=True)
    scripts = {
        "bad": "#!/bin/sh\necho 'Fatal error: version mismatch' >&2\nexit 3\n",
        "hang": "#!/bin/sh\nsleep 20\n",
        "good": "#!/bin/sh\necho '1.107.0'\nexit 0\n",
    }
    paths: dict[str, str] = {}
    for name, body in scripts.items():
        launcher = launchers / name
        launcher.write_text(body, encoding="utf-8", newline="\n")
        launcher.chmod(0o755)
        paths[name] = launcher.as_posix()

    script = tmp_path / "drive.sh"
    script.write_text(
        "set -e\n"
        "YELLOW=''\n"
        'write_item() { echo "NOTE: $1"; }\n'
        f"{helpers}\n"
        f'select_working_launcher Antigravity 20 "{paths["bad"]}" "{paths["good"]}"; echo "bad-then-good=$selected_launcher"\n'
        f'select_working_launcher Antigravity 1 "{paths["hang"]}" "{paths["good"]}"; echo "hang-then-good=$selected_launcher"\n'
        f'select_working_launcher Antigravity 20 "{paths["bad"]}"; echo "only-bad=[$selected_launcher]"\n'
        'select_working_launcher Antigravity 20; echo "none=[$selected_launcher]"\n'
        f'select_working_launcher Antigravity 20 "{paths["good"]}" "{paths["bad"]}"; echo "first-wins=$selected_launcher"\n',
        encoding="utf-8",
        newline="\n",
    )
    started = time.monotonic()
    proc = subprocess.run(["bash", script.as_posix()], capture_output=True, text=True, timeout=60, check=False)
    elapsed = time.monotonic() - started

    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    assert f"bad-then-good={paths['good']}" in proc.stdout
    assert f"hang-then-good={paths['good']}" in proc.stdout
    assert "only-bad=[]" in proc.stdout
    assert "none=[]" in proc.stdout
    assert f"first-wins={paths['good']}" in proc.stdout
    assert f'launcher "{paths["bad"]}": --version exited with status 3' in proc.stdout
    assert f'launcher "{paths["hang"]}": did not answer --version within 1s' in proc.stdout
    assert elapsed < 30, f"the hanging launcher was not stopped promptly ({elapsed:.1f}s)"


@pytest.mark.skipif(sys.platform != "win32", reason="the PowerShell selector drives cmd.exe launchers")
def test_powershell_selector_skips_failing_and_hanging_launchers(tmp_path: Path) -> None:
    text = INSTALLER_PS1.read_text(encoding="utf-8")
    helpers = "\n".join(
        _function(text, header)
        for header in (
            "function Write-Item {",
            "function Invoke-CommandWithTimeout {",
            "function Select-WorkingLauncher {",
        )
    )
    launchers = tmp_path / "Antigravity IDE" / "bin"
    launchers.mkdir(parents=True)
    scripts = {
        "bad.cmd": "@echo off\r\necho Fatal error: version mismatch 1>&2\r\nexit /b 3\r\n",
        "hang.cmd": "@echo off\r\nping -n 30 127.0.0.1 >nul\r\n",
        "good.cmd": "@echo off\r\necho 1.107.0\r\nexit /b 0\r\n",
    }
    for name, body in scripts.items():
        (launchers / name).write_bytes(body.encode("ascii"))
    bad, hang, good = (str(launchers / name) for name in scripts)

    driver = tmp_path / "drive.ps1"
    driver.write_text(
        f"{helpers}\n"
        f"$bad = '{bad}'; $hang = '{hang}'; $good = '{good}'\n"
        "$r1 = Select-WorkingLauncher -Candidates @($bad, $good) -DisplayName 'Antigravity' -TimeoutSeconds 20\n"
        "$r2 = Select-WorkingLauncher -Candidates @($hang, $good) -DisplayName 'Antigravity' -TimeoutSeconds 1\n"
        "$r3 = Select-WorkingLauncher -Candidates @($bad) -DisplayName 'Antigravity' -TimeoutSeconds 20\n"
        "$r4 = Select-WorkingLauncher -Candidates @() -DisplayName 'Antigravity' -TimeoutSeconds 20\n"
        "$r5 = Select-WorkingLauncher -Candidates @($good, $bad) -DisplayName 'Antigravity' -TimeoutSeconds 20\n"
        "@{ badThenGood = $r1; hangThenGood = $r2; onlyBad = $r3; none = $r4; firstWins = $r5 } | ConvertTo-Json -Compress\n",
        encoding="utf-8",
    )
    shell = "powershell" if shutil.which("powershell") else "pwsh"
    started = time.monotonic()
    proc = subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(driver)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    elapsed = time.monotonic() - started

    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    lines = proc.stdout.strip().splitlines()
    result = json.loads(lines[-1])
    assert result["badThenGood"] == good
    assert result["hangThenGood"] == good
    assert result["onlyBad"] is None
    assert result["none"] is None
    assert result["firstWins"] == good
    notes = "\n".join(lines[:-1])
    assert f'launcher "{bad}": --version exited with code 3' in notes
    assert f'launcher "{hang}": did not answer --version within 1s' in notes
    assert elapsed < 90, f"the hanging launcher was not stopped promptly ({elapsed:.1f}s)"
