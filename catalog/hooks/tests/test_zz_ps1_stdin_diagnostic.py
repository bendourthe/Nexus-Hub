"""TEMPORARY diagnostic for the hosted Windows leg (v4.13.1 PR #337); removed with the fix.

The PowerShell guard adapters exit 0 with no output on the hosted runner but not locally.
This copies the real adapter, inserts a trace line after each early step, runs it the way
the suite does, and fails with the trace so the runner's behavior is visible in the report.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="diagnostic for the Windows leg only")


def test_ps1_adapter_trace(powershell_bin, tmp_path):
    source = (_HOOKS_DIR / "user-edit-guard.ps1").read_text(encoding="utf-8")
    markers = [
        ('$hookName = "user-edit-guard"', "start"),
        ("if (-not [Console]::IsInputRedirected) { exit 0 }",
         'redirected=$([Console]::IsInputRedirected) disabled=$env:NEXUS_DISABLED_HOOKS'),
        ("$inputBytes = $buffer.ToArray()", 'rawbytes=$($inputBytes.Length)'),
        ("if ($inputBytes.Length -eq 0) { exit 0 }", 'finalbytes=$($inputBytes.Length)'),
        ('if (-not $python) { Invoke-Fallback "Python not found" }', 'helper=$helper python=$python'),
        ("$status = $process.ExitCode", 'exit=$status out=$($stdoutTask.Result.Length) err=$($stderrTask.Result.Length)'),
    ]
    traced = source
    for anchor, message in markers:
        assert traced.count(anchor) == 1, anchor
        traced = traced.replace(anchor, anchor + '\n[Console]::Error.WriteLine("DBG ' + message + '")')
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    (hooks / "user-edit-guard.ps1").write_text(traced, encoding="utf-8")
    work = tmp_path / "work"
    work.mkdir()
    deck = work / "deck.pptx"
    deck.write_bytes(b"not an archive, never recorded")
    env = {**os.environ, "NEXUS_EDIT_GUARD_DIR": str(tmp_path / "store"),
           "NEXUS_EDIT_GUARD_SCRIPT": str(_HOOKS_DIR.parent / "skills" / "workflow" / "user-edit-preservation"
                                          / "scripts" / "edit_guard.py"),
           "NEXUS_EDIT_GUARD_TIMEOUT_SECONDS": "60"}
    payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": str(work),
                          "tool_input": {"file_path": str(deck)}})
    result = subprocess.run([powershell_bin, "-NoProfile", "-File", str(hooks / "user-edit-guard.ps1")],
                            input=payload, text=True, capture_output=True, cwd=str(work), env=env, timeout=180,
                            check=False)
    trace = f"exit={result.returncode}\nSTDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout[:500]}"
    pytest.fail("diagnostic run (fails on purpose so the trace reaches the report):\n" + trace)
