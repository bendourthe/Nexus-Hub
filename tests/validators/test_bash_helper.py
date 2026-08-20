"""Tests for tests/validators/bash_helper.py.

The resolver decides whether two suites run at all, so a defect in it is a
FAIL-OPEN: `resolve_bash()` returning None makes both the classifier and the
aggregate-gate suites skip, and a skipped suite reports green while asserting
nothing. That is the same shape as the CI defect those suites exist to guard.

It exists because `shutil.which("bash")` is not a reliable answer on Windows:
the System32 WSL launcher stub precedes Git Bash on PATH and, with no
distribution installed, prints a UTF-16 message and exits 1. That failed the
classifier suite on the GitHub Windows runner while it passed locally and on
ubuntu, and it is the same PATH shadowing v3.15.6 Phase 4 identified for the
installer.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bash_helper import BASH, resolve_bash


def test_a_working_bash_is_found_on_this_host() -> None:
    """Guards the fail-open: None here silently disables two whole suites.

    Every platform this repository tests on (ubuntu, macOS, and Windows via Git
    Bash) ships a usable bash, so None means the resolver is broken rather than
    that the host lacks a shell.
    """
    assert BASH is not None, (
        "no working bash resolved. Both the classifier and aggregate-gate suites "
        "would silently skip, reporting green while asserting nothing."
    )


def test_the_resolved_bash_actually_executes_a_script(tmp_path: Path) -> None:
    """Probing with `-c` is not proof it can run a FILE, which is the real use."""
    assert BASH is not None
    script = tmp_path / "probe.sh"
    script.write_text("printf ready\n", encoding="utf-8", newline="\n")
    proc = subprocess.run(
        [BASH, str(script)], capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "ready"


def test_a_stub_that_exits_non_zero_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The WSL-stub case, reproduced without needing WSL.

    The resolver probes candidates empirically rather than filtering them by
    path, so anything that fails to echo the token is rejected whatever it is
    called and wherever it lives. This asserts that property directly by making
    the FIRST candidate a stub and confirming the resolver does not return it.
    """
    import bash_helper

    stub = tmp_path / "bash"
    stub.write_text(
        "#!/bin/sh\necho 'no installed distributions' >&2\nexit 1\n",
        encoding="utf-8",
        newline="\n",
    )
    stub.chmod(0o755)

    monkeypatch.setattr(
        bash_helper.shutil, "which", lambda name: str(stub) if name == "bash" else None
    )
    resolved = bash_helper.resolve_bash()
    assert resolved != str(stub), "a non-working stub was accepted as bash"


def test_returns_none_when_no_candidate_works(monkeypatch: pytest.MonkeyPatch) -> None:
    """With nothing usable, the answer is None so the suites skip explicitly.

    Skipping is correct here; the fail-open would be returning a path that does
    not work, because the consuming suites would then report real failures that
    say nothing about the code under test.
    """
    import bash_helper

    monkeypatch.setattr(bash_helper.shutil, "which", lambda name: None)
    monkeypatch.setattr(bash_helper.sys, "platform", "linux")
    assert resolve_bash() is None
