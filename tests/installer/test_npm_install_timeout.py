"""The extension build's npm install is bounded in both installers.

A stalled package download hung `npm install` with no limit, which held the whole
installer (and CI's installer jobs) until an outer timeout killed it. Each
installer now runs it through a timeout helper. These tests load the helper's
exact text from the installer and drive it with an overrun, a success, and a
failure, so the shipped code is what is proven.

Child processes inherit the suite-wide no-window default from tests/conftest.py.
"""

from __future__ import annotations

import json
import os
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


def test_both_installers_bound_the_extension_npm_install() -> None:
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    ps1 = INSTALLER_PS1.read_text(encoding="utf-8")
    assert 'run_with_timeout "$npm_timeout" "$npm_log" npm install --silent' in sh
    assert '"${NEXUS_HUB_NPM_TIMEOUT:-300}"' in sh
    assert 'Invoke-CommandWithTimeout -CommandLine "npm install --silent"' in ps1
    assert "$npmTimeout = 300" in ps1 and "NEXUS_HUB_NPM_TIMEOUT" in ps1
    assert "$npmOutput = & npm install" not in ps1, "an unbounded npm install call remains"
    assert "npm_log=$(npm install" not in sh, "an unbounded npm install call remains"


@pytest.mark.skipif(sys.platform == "win32", reason="installer.sh runs on macOS and Linux; Windows uses installer.ps1")
@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
def test_bash_helper_stops_an_overrun_and_keeps_exit_codes(tmp_path: Path) -> None:
    helper = _function(INSTALLER_SH.read_text(encoding="utf-8"), "run_with_timeout() {")
    log = (tmp_path / "out.log").as_posix()
    script = tmp_path / "drive.sh"
    script.write_text(
        f"{helper}\n"
        f'rc=0; run_with_timeout 1 "{log}" sleep 20 || rc=$?; echo "overrun=$rc"\n'
        f'rc=0; run_with_timeout 10 "{log}" echo hello-from-npm || rc=$?; echo "success=$rc"\n'
        f'rc=0; run_with_timeout 10 "{log}" sh -c "exit 3" || rc=$?; echo "failure=$rc"\n',
        encoding="utf-8",
        newline="\n",
    )
    started = time.monotonic()
    proc = subprocess.run(["bash", str(script)], capture_output=True, text=True, timeout=60, check=False)
    elapsed = time.monotonic() - started

    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    assert "overrun=124" in proc.stdout
    assert "success=0" in proc.stdout
    assert "failure=3" in proc.stdout
    assert elapsed < 15, f"the overrun was not stopped promptly ({elapsed:.1f}s)"
    assert "hello-from-npm" in Path(log).read_text(encoding="utf-8")


@pytest.mark.skipif(sys.platform != "win32", reason="the PowerShell helper drives cmd.exe")
def test_powershell_helper_stops_an_overrun_and_keeps_exit_codes() -> None:
    helper = _function(INSTALLER_PS1.read_text(encoding="utf-8"), "function Invoke-CommandWithTimeout {")
    script = (
        f"{helper}\n"
        "$o = Invoke-CommandWithTimeout -CommandLine 'ping -n 30 127.0.0.1' -TimeoutSeconds 1\n"
        "$s = Invoke-CommandWithTimeout -CommandLine 'echo hello-from-npm' -TimeoutSeconds 10\n"
        "$f = Invoke-CommandWithTimeout -CommandLine 'exit /b 3' -TimeoutSeconds 10\n"
        "@{ overrun = $o.ExitCode; timedOut = $o.TimedOut; success = $s.ExitCode;"
        " output = ($s.Output -join ' '); failure = $f.ExitCode } | ConvertTo-Json -Compress\n"
    )
    shell = "powershell" if shutil.which("powershell") else "pwsh"
    started = time.monotonic()
    proc = subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    elapsed = time.monotonic() - started

    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    assert result["overrun"] == 124 and result["timedOut"] is True
    assert result["success"] == 0 and "hello-from-npm" in result["output"]
    assert result["failure"] == 3
    assert elapsed < 45, f"the overrun was not stopped promptly ({elapsed:.1f}s)"



def test_both_installers_bound_the_runtime_process_probe() -> None:
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    ps1 = INSTALLER_PS1.read_text(encoding="utf-8-sig")
    assert 'run_with_timeout 10 /dev/null "$process_python" -B -c "import psutil; psutil.Process().create_time()"' in sh
    assert "Invoke-CommandWithTimeout -CommandLine" in ps1
    block = ps1.split("# Match nexus-hub.cmd's launcher order;", 1)[1].split("# v0.9.7:", 1)[0]
    assert '-TimeoutSeconds 10' in block and 'import psutil; psutil.Process().create_time()' in block


@pytest.mark.parametrize("available,mode,selected", [
    ("python3 python py", "success", "python3"),
    ("python3", "missing", "python3"),
    ("python3", "hang", "python3"),
    ("", "success", None),
    ("python py", "success", "python"),
    ("py", "success", "py"),
])
def test_bash_runtime_probe_is_bounded_advisory_and_never_installs(tmp_path: Path, available: str, mode: str, selected: str | None) -> None:
    # tests/conftest.py owns working Bash selection and Windows PATH repair.
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is required for the POSIX installer probe control")
    source = INSTALLER_SH.read_text(encoding="utf-8")
    helper = _function(source, "run_with_timeout() {")
    probe = source.split("    # Match the nexus-hub shell launcher's order;", 1)[1].split("    # v0.9.7:", 1)[0]
    probe = "    # Match the nexus-hub shell launcher's order;" + probe
    script = tmp_path / "probe.sh"
    journal = tmp_path / "probe-calls.txt"
    prelude = r"""set -euo pipefail
GREEN=green
YELLOW=yellow
write_item() { printf '%s\n' "$1"; }
command() {
    if [ "${1:-}" = "-v" ]; then
        case "${2:-}" in
            python3|python|py)
                case " $PRIVATE_AVAILABLE " in *" $2 "*) printf '%s\n' "$2"; return 0;; esac
                return 1;;
        esac
    fi
    builtin command "$@"
}
fake_python() {
    local selected="$1"
    shift
    printf '%s|%s\n' "$selected" "$*" >> "$PRIVATE_PROBE_JOURNAL"
    if [ "$#" -ne 3 ] || [ "$1" != "-B" ] || [ "$2" != "-c" ] || [ "$3" != "import psutil; psutil.Process().create_time()" ]; then
        printf 'unexpected invocation\n' >> "$PRIVATE_PROBE_JOURNAL"
        return 97
    fi
    case "$PRIVATE_MODE" in
        success) return 0;;
        missing) return 1;;
        hang) sleep 13; return 0;;
    esac
}
python3() { fake_python python3 "$@"; }
python() { fake_python python "$@"; }
py() { fake_python py "$@"; }
pip() { printf 'pip invoked\n' >> "$PRIVATE_PROBE_JOURNAL"; return 98; }
"""
    script.write_text(prelude + "\n" + helper + "\nprobe() {\n" + probe + "\n}\nprobe\nprintf 'advisory-completed\\n'\n", encoding="utf-8", newline="\n")
    env = {key: value for key, value in os.environ.items() if key.upper() in {"SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATHEXT", "PATH", "PROGRAMFILES"}}
    env.update(HOME=str(tmp_path), USERPROFILE=str(tmp_path), TEMP=str(tmp_path), TMP=str(tmp_path), TMPDIR=str(tmp_path),
               PRIVATE_AVAILABLE=available, PRIVATE_MODE=mode, PRIVATE_PROBE_JOURNAL=journal.as_posix())
    started = time.monotonic()
    result = subprocess.run([bash, "--noprofile", "--norc", script.as_posix()], env=env, capture_output=True, text=True, timeout=18,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False)
    elapsed = time.monotonic() - started
    assert result.returncode == 0, result.stdout + result.stderr
    assert "advisory-completed" in result.stdout
    calls = journal.read_text(encoding="utf-8").splitlines() if journal.exists() else []
    assert calls == ([] if selected is None else [selected + "|-B -c import psutil; psutil.Process().create_time()"])
    if selected is None:
        assert "requires a Python CLI launcher and psutil" in result.stdout
    elif mode == "success":
        assert "[OK] Process observation support (psutil)" in result.stdout
    else:
        assert "requires usable psutil" in result.stdout and "-m pip install psutil" in result.stdout
    if mode == "hang":
        assert 8 <= elapsed < 17, f"the psutil probe was not stopped at its10-second bound ({elapsed:.1f}s)"
