"""Child-process output reaches three .ps1 hooks as exact UTF-8 (WN-45).

Windows PowerShell 5.1 decodes a native command's output with the console code
page, so a program that writes UTF-8 reached the hook as mojibake, and a Python
child writing to a pipe encoded with the ANSI code page and failed outright on
text outside it. rewrite-command.ps1, lint-on-write.ps1 and session-summary.ps1
now launch their child through System.Diagnostics.ProcessStartInfo with UTF-8
output decoding (PYTHONUTF8=1 for Python children), without changing the
console code page shared with the parent.

Each case puts a stub where the hook already looks for its child: a directory
first on PATH holding ``python3.cmd`` / ``ruff.cmd`` / ``eslint.cmd`` (which
also exercises the ``cmd.exe /d /s /c`` route .cmd shims take), or a stub
``plan_status.py`` under the temp home (run by the real python.exe). Stubs emit
MULTIBYTE either through ``print`` (needs the UTF-8 child environment) or as raw
UTF-8 bytes (needs the UTF-8 decode), and each assertion is on the exact text.

The .sh siblings capture child output as bytes with ``$(...)`` and need no
change for decoding; they are not driven here.

Run (Windows PowerShell 5.1 is the edition this guards):
    NEXUS_TEST_POWERSHELL=powershell python -m pytest catalog/hooks/tests/test_hook_child_output_utf8.py -q
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent

# 4 code points, 12 UTF-8 bytes: 2-, 3-, 3- and 4-byte sequences.
MULTIBYTE = "é漢字\U0001f600"
WRITERS = ("print", "bytes")

pytestmark = pytest.mark.skipif(
    os.name != "nt", reason="the .cmd stub route and the 5.1 code-page defect are Windows-only"
)

# Prologue shared by every stub: emit(text, stream) writes either via print
# (encoded by the child's own stdio settings) or as raw UTF-8 bytes.
_STUB_PROLOGUE = '''import sys
MB = "\\u00e9\\u6f22\\u5b57\\U0001f600"
WRITER = {writer!r}
def emit(text, stream=sys.stdout):
    if WRITER == "bytes":
        stream.flush(); stream.buffer.write((text + "\\n").encode("utf-8")); stream.buffer.flush()
    else:
        print(text, file=stream)
'''


def _write_stub(path: Path, writer: str, body: str) -> Path:
    path.write_text(_STUB_PROLOGUE.format(writer=writer) + body, encoding="utf-8")
    return path


def _cmd_shim(bin_dir: Path, name: str, stub: Path) -> None:
    (bin_dir / f"{name}.cmd").write_text(
        f'@"{sys.executable}" "{stub}" %*\r\n', encoding="ascii"
    )


def _env(tmp_path: Path, bin_dir: Path | None = None) -> dict[str, str]:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {**os.environ}
    for key in (
        "NEXUS_DISABLED_HOOKS",
        "NEXUS_HOOK_PROFILE",
        "NEXUS_SESSION_DIGEST",
        "NEXUS_SESSION_DIGEST_PATH",
        "CLAUDE_CONFIG_DIR",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "PYTHONPATH",
    ):
        env.pop(key, None)
    env.update({"HOME": str(home), "USERPROFILE": str(home), "NEXUS_SESSION_DIGEST_NOW": "T"})
    if bin_dir is not None:
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    return env


def _run_ps1(powershell_bin: str, stem: str, payload: dict | None, cwd: Path, env: dict[str, str]):
    data = b"" if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return subprocess.run(
        [powershell_bin, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_HOOKS_DIR / f"{stem}.ps1")],
        input=data,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        timeout=180,
        check=False,
    )


# -- rewrite-command.ps1: python3.cmd stub answers `-m nexus_context_compressor rewrite` --

_REWRITE_BODY = '''
args = sys.argv[1:]
if "-c" in args:
    sys.exit(0)
if "rewrite" in args:
    emit("REWRITTEN " + args[args.index("--cmd") + 1])
    sys.exit(int(EXIT_CODE))
sys.exit(1)
'''


@pytest.mark.parametrize("writer", WRITERS)
@pytest.mark.parametrize(("code", "decision"), [(0, "allow"), (2, "deny"), (3, "ask")])
def test_rewrite_command_carries_multibyte_rewrite_and_exit_code(
    writer: str, code: int, decision: str, powershell_bin: str, tmp_path: Path
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = _write_stub(tmp_path / "py_stub.py", writer, _REWRITE_BODY.replace("EXIT_CODE", str(code)))
    _cmd_shim(bin_dir, "python3", stub)
    work = tmp_path / "work"
    work.mkdir()
    payload = {"tool_name": "Bash", "tool_input": {"command": f"echo {MULTIBYTE}"}}
    proc = _run_ps1(powershell_bin, "rewrite-command", payload, work, _env(tmp_path, bin_dir))
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert proc.stdout.strip(), "hook passed through: the rewrite child produced no usable output"
    out = json.loads(proc.stdout.decode("utf-8"))["hookSpecificOutput"]
    assert out["permissionDecision"] == decision
    assert out["updatedInput"]["command"] == f"REWRITTEN echo {MULTIBYTE}"


# -- lint-on-write.ps1: ruff.cmd / eslint.cmd stubs write findings to stdout and stderr --

_LINT_BODY = '''
emit("finding " + MB + " " + " ".join(sys.argv[1:-1]))
emit("note " + MB, sys.stderr)
sys.exit(1)
'''


@pytest.mark.parametrize("writer", WRITERS)
@pytest.mark.parametrize(
    ("tool", "name", "flags"),
    [
        ("ruff", "x.py", "check"),
        ("eslint", "x.js", "--no-error-on-unmatched-pattern --format compact"),
    ],
)
def test_lint_on_write_reports_multibyte_linter_output(
    writer: str, tool: str, name: str, flags: str, powershell_bin: str, tmp_path: Path
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _cmd_shim(bin_dir, tool, _write_stub(tmp_path / "lint_stub.py", writer, _LINT_BODY))
    work = tmp_path / "work"
    work.mkdir()
    target = work / name
    target.write_text("x = 1\n", encoding="utf-8")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(target)}}
    proc = _run_ps1(powershell_bin, "lint-on-write", payload, work, _env(tmp_path, bin_dir))
    assert proc.returncode == 0
    lines = proc.stderr.decode("utf-8", "replace").splitlines()
    assert f"[lint] {tool} warnings for {name}:" in lines, lines
    assert f"finding {MULTIBYTE} {flags}" in lines, lines
    assert f"note {MULTIBYTE}" in lines, lines


# -- session-summary.ps1: stub plan_status.py run by the real python.exe --

_PLAN_BODY = '''
emit("Plan: " + MB + " phase 1 of 2")
'''


@pytest.mark.parametrize("writer", WRITERS)
def test_session_summary_digest_carries_multibyte_plan_line(
    writer: str, powershell_bin: str, tmp_path: Path
) -> None:
    env = _env(tmp_path)
    scripts = tmp_path / "home" / ".nexus-hub" / "scripts"
    scripts.mkdir(parents=True)
    _write_stub(scripts / "plan_status.py", writer, _PLAN_BODY)
    work = tmp_path / "work"
    work.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    proc = _run_ps1(powershell_bin, "session-summary", None, work, env)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    body = (work / ".nexus" / "context" / "last-session.md").read_bytes().decode("utf-8", "replace")
    assert f"Plan: {MULTIBYTE} phase 1 of 2" in body.splitlines(), body


# -- session-summary.sh: the same plan line under Git Bash (WN-45 shell residual) --


def test_session_summary_sh_carries_multibyte_plan_line(tmp_path: Path) -> None:
    """A Python child writing with print() encodes through the ANSI code page on
    Windows Git Bash unless the hook sets UTF-8 mode for it."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available")
    env = _env(tmp_path)
    scripts = tmp_path / "home" / ".nexus-hub" / "scripts"
    scripts.mkdir(parents=True)
    _write_stub(scripts / "plan_status.py", "print", _PLAN_BODY)
    work = tmp_path / "work"
    work.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    proc = subprocess.run(
        [bash, str(_HOOKS_DIR / "session-summary.sh")],
        input=b"", capture_output=True, cwd=str(work), env=env, timeout=180, check=False,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    body = (work / ".nexus" / "context" / "last-session.md").read_bytes().decode("utf-8", "replace")
    assert f"Plan: {MULTIBYTE} phase 1 of 2" in body.splitlines(), body


# -- cmd.exe injection through a .cmd/.bat shim (v4.13.11 AF-1, AF-2) --
#
# cmd.exe re-parses the whole command line, and no quoting carries arbitrary text
# through it safely. Each case puts a marker-writing ``pwnmarker.cmd`` on PATH next
# to the stub shim and feeds an argument that names it after a cmd metacharacter.
# The hook must never start the shim with such an argument: the marker stays
# absent, lint-on-write skips the file, rewrite-command passes the command through
# with no permission decision, and session-summary keeps "Plan: unavailable".


def _marker_bin(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "pwned.txt"
    (bin_dir / "pwnmarker.cmd").write_text(f'@echo pwned> "{marker}"\r\n', encoding="ascii")
    return bin_dir, marker


_SAFE_STUB = '''import sys
if "-c" in sys.argv[1:]:
    sys.exit(0)
if "rewrite" in sys.argv[1:]:
    print("REWRITTEN")
    sys.exit(0)
print("Plan: injected run")
sys.exit(1)
'''


def _plain_stub(tmp_path: Path) -> Path:
    stub = tmp_path / "plain_stub.py"
    stub.write_text(_SAFE_STUB, encoding="ascii")
    return stub


@pytest.mark.parametrize(
    "command",
    ['echo a" & pwnmarker & echo "b', "echo a & pwnmarker", 'git log | pwnmarker', "echo %PATH%^&pwnmarker"],
)
def test_rewrite_command_never_hands_cmd_metacharacters_to_a_cmd_shim(
    command: str, powershell_bin: str, tmp_path: Path
) -> None:
    bin_dir, marker = _marker_bin(tmp_path)
    _cmd_shim(bin_dir, "python3", _plain_stub(tmp_path))
    work = tmp_path / "work"
    work.mkdir()
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    proc = _run_ps1(powershell_bin, "rewrite-command", payload, work, _env(tmp_path, bin_dir))
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert not marker.exists(), "cmd.exe ran the injected command"
    assert proc.stdout.strip() == b"", f"expected passthrough, got {proc.stdout!r}"


def test_lint_on_write_never_hands_cmd_metacharacters_to_a_cmd_shim(
    powershell_bin: str, tmp_path: Path
) -> None:
    bin_dir, marker = _marker_bin(tmp_path)
    _cmd_shim(bin_dir, "eslint", _plain_stub(tmp_path))
    work = tmp_path / "work"
    work.mkdir()
    target = work / "x&pwnmarker&.js"
    target.write_text("x = 1\n", encoding="utf-8")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(target)}}
    proc = _run_ps1(powershell_bin, "lint-on-write", payload, work, _env(tmp_path, bin_dir))
    assert proc.returncode == 0
    assert not marker.exists(), "cmd.exe ran the injected command"
    assert b"[lint]" not in proc.stderr, proc.stderr.decode("utf-8", "replace")


def test_session_summary_never_hands_cmd_metacharacters_to_a_cmd_shim(
    powershell_bin: str, tmp_path: Path
) -> None:
    bin_dir, marker = _marker_bin(tmp_path)
    _cmd_shim(bin_dir, "python3", _plain_stub(tmp_path))
    env = _env(tmp_path, bin_dir)
    scripts = tmp_path / "home" / ".nexus-hub" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "plan_status.py").write_text("print('Plan: real')\n", encoding="ascii")
    work = tmp_path / "w&pwnmarker&x"
    work.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    proc = _run_ps1(powershell_bin, "session-summary", None, work, env)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert not marker.exists(), "cmd.exe ran the injected command"
    body = (work / ".nexus" / "context" / "last-session.md").read_text(encoding="utf-8")
    assert "Plan: injected run" not in body, body
