"""Host interpreter resolution checks (v4.3.0 Phase 5).

Nexus-Hub registers hooks as `bash <script>` and the assistant HOST performs that
launch. A host whose `bash` cannot execute a script leaves every hook silently
inert, and no other gate observes it because they all run Python directly.

The condition is not hypothetical: the v4.3.0 integration run was red twice on a
Windows runner for exactly this reason while the full local suite was green.
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


def _write_stub(directory: Path, *, exit_code: int, to_stdout: str) -> Path:
    """A stand-in for the WSL launcher stub: talks on stdout, exits non-zero.

    Written as a native executable per host. A shebang script named `bash` is not
    runnable on Windows (WinError 193), which is the platform the real defect
    occurs on, so the stub must be a `.cmd` there.
    """
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        stub = directory / "bash.cmd"
        lines = ["@echo off"]
        if to_stdout:
            lines.append(f"echo {to_stdout}")
        lines.append(f"exit /b {exit_code}")
        stub.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
        return stub
    stub = directory / "bash"
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
