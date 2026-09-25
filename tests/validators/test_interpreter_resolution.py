"""Probe the shell used by each host's registered Nexus-Hub hooks.

The original Bash probe caught a Windows WSL launcher shim, but current Windows
registrations use PowerShell siblings and must be checked through that shell.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_interpreter_resolution import main  # noqa: E402
from scripts.lib.integrations import _interpreters  # noqa: E402


def _write_stub(
    directory: Path, *, exit_code: int, to_stdout: str, name: str = "bash"
) -> Path:
    """A native stand-in for an interpreter that does not run the probe.

    A shebang script is not runnable on Windows (WinError 193), so the stub must
    be a `.cmd` there.
    """
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        stub = directory / f"{name}.cmd"
        lines = ["@echo off"]
        if to_stdout:
            lines.append(f"echo {to_stdout}")
        lines.append(f"exit /b {exit_code}")
        stub.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
        return stub
    stub = directory / name
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"print({to_stdout!r})\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return stub


def test_a_working_bash_is_reported_usable():
    if shutil.which("bash") is None:
        pytest.skip("no bash on this host")
    status = _interpreters.check_bash()
    assert status.usable, status.detail
    assert status.resolved


def test_a_stub_bash_is_not_mistaken_for_a_working_one(tmp_path, monkeypatch):
    """Exit code alone is the signal; a banner on stdout must not pass."""
    stub = _write_stub(
        tmp_path / "stub",
        exit_code=1,
        to_stdout="Windows Subsystem for Linux has no installed distributions.",
    )
    monkeypatch.setattr(shutil, "which", lambda name: str(stub) if name == "bash" else None)
    monkeypatch.setattr(_interpreters, "_WINDOWS_BASH_CANDIDATES", ())

    status = _interpreters.check_bash(prefer_git_bash=False)

    assert not status.usable
    assert status.needs_action
    assert "exited 1" in status.detail


def test_a_zero_exit_without_the_probe_output_is_rejected(tmp_path, monkeypatch):
    """A shim that swallows the script and succeeds is still not a usable bash."""
    stub = _write_stub(tmp_path / "quiet", exit_code=0, to_stdout="")
    monkeypatch.setattr(shutil, "which", lambda name: str(stub) if name == "bash" else None)
    monkeypatch.setattr(_interpreters, "_WINDOWS_BASH_CANDIDATES", ())

    status = _interpreters.check_bash(prefer_git_bash=False)

    assert not status.usable
    assert "did not reproduce" in status.detail


def test_missing_bash_is_reported_rather_than_raised(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.setattr(_interpreters, "_WINDOWS_BASH_CANDIDATES", ())

    status = _interpreters.check_bash(prefer_git_bash=False)

    assert not status.usable
    assert status.detail == "not found on PATH"


def test_missing_powershell_is_reported_rather_than_raised(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)

    status = _interpreters.check_powershell()

    assert not status.usable
    assert status.detail == "not found on PATH"


@pytest.mark.skipif(os.name != "nt", reason="Windows PowerShell host probe")
def test_a_working_powershell_is_reported_usable():
    status = _interpreters.check_powershell()

    assert status.usable, status.detail
    assert status.resolved


def test_powershell_shim_without_probe_marker_is_rejected(tmp_path, monkeypatch):
    stub = _write_stub(
        tmp_path / "quiet", exit_code=0, to_stdout="ready", name="powershell"
    )
    monkeypatch.setattr(shutil, "which", lambda name: str(stub))

    status = _interpreters.check_powershell()

    assert not status.usable
    assert "did not reproduce" in status.detail


def test_windows_checks_the_registered_powershell_interpreter(monkeypatch):
    working = _interpreters.InterpreterStatus("powershell", "powershell.exe", True, "ok")
    monkeypatch.setattr(_interpreters, "is_windows_host", lambda: True, raising=False)
    monkeypatch.setattr(_interpreters, "check_powershell", lambda: working, raising=False)
    monkeypatch.setattr(
        _interpreters,
        "check_bash",
        lambda: pytest.fail("Windows hook registrations do not launch Bash"),
    )

    assert _interpreters.check_all() == [working]


def test_non_windows_still_checks_bash(monkeypatch):
    working = _interpreters.InterpreterStatus("bash", "/usr/bin/bash", True, "ok")
    monkeypatch.setattr(_interpreters, "is_windows_host", lambda: False, raising=False)
    monkeypatch.setattr(_interpreters, "check_bash", lambda: working)
    monkeypatch.setattr(
        _interpreters,
        "check_powershell",
        lambda: pytest.fail("POSIX hook registrations do not launch PowerShell"),
        raising=False,
    )

    assert _interpreters.check_all() == [working]


def test_gate_flag_controls_the_exit_code(monkeypatch, capsys):
    """Advisory by default so a contributor is told; --gate is what CI runs."""
    failing = _interpreters.InterpreterStatus("bash", None, False, "not found on PATH")
    monkeypatch.setattr(
        "scripts.check_interpreter_resolution.check_all", lambda: [failing]
    )

    assert main([]) == 0
    assert main(["--gate"]) == 1
    assert "silently inert" in capsys.readouterr().out


def test_gate_passes_when_every_interpreter_runs(monkeypatch):
    working = _interpreters.InterpreterStatus("bash", "/usr/bin/bash", True, "ok")
    monkeypatch.setattr(
        "scripts.check_interpreter_resolution.check_all", lambda: [working]
    )

    assert main(["--gate"]) == 0
