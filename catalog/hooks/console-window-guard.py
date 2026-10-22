#!/usr/bin/env python3
"""
PreToolUse hook: stop console windows from flooding the desktop when tests run on Windows.

On Windows, a console program started by a process that has no console opens a
new, focus-stealing window. A test suite that starts hundreds of git, bash,
PowerShell or Python children from such a process makes the machine unusable
until it finishes. This hook runs before a test command, scans the project for
process launches that can open windows, and blocks the command (exit 2) with the
exact fixes, so the agent repairs the code before the tests run.

Scope:
  - Acts only on Windows (or when NEXUS_CONSOLE_GUARD_PLATFORM=nt, for tests).
  - Acts only on commands that run a test runner; every other command passes.
  - Off when NEXUS_DISABLED_HOOKS contains console-window-guard, or when
    NEXUS_CONSOLE_GUARD=off.

A deliberate launch is accepted when its line, or the line above it, carries the
marker `nexus: console-window-ok` followed by a reason.

Part of Nexus-Hub.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

HOOK_NAME = "console-window-guard"
MARKER = "nexus: console-window-ok"
MAX_FILES = 20000
MAX_FILE_BYTES = 1_000_000
MAX_REPORTED = 12
SCAN_BUDGET_SECONDS = 20.0  # past this the scan stops and judges what it has read

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "dist", "build", "out", "target", "bin", "obj", "coverage",
    ".next", ".nuxt", "vendor", "site-packages", ".gradle", ".idea", ".vscode-test",
}

TEST_COMMAND = re.compile(
    r"(?:^|[\s;&|(`'\"/\\])(?:"
    r"py\.test|pytest|tox|nox"
    r"|(?:npm|pnpm|yarn|bun)(?:\s+run)?\s+test"
    r"|(?:npx\s+|pnpm\s+exec\s+|yarn\s+)?(?:vitest|jest|mocha|ava)"
    r"|(?:npx\s+)?playwright\s+test"
    r"|go\s+test|cargo\s+(?:test|nextest)|dotnet\s+test|ctest"
    r"|mvn(?:w)?\s+(?:\S+\s+)*test|gradle(?:w)?\s+(?:\S+\s+)*test"
    r"|Invoke-Pester|make\s+test"
    r"|scripts/ci/run\.py"
    r")(?=$|[\s;&|)`'\".:])",
    re.IGNORECASE,
)

PY_LAUNCH = re.compile(
    r"\bsubprocess\.(?:run|Popen|call|check_call|check_output|getoutput|getstatusoutput)\s*\("
    r"|\basyncio\.create_subprocess_(?:exec|shell)\s*\("
    r"|\bos\.(?:system|popen|spawn[lv]p?e?)\s*\("
)
PY_EXPLICIT = re.compile(r"\b(?:DETACHED_PROCESS|CREATE_NEW_CONSOLE)\b|creationflags[\"']?\s*[:=]\s*0x0*(?:8|10)\b")
PS_PSI = re.compile(r"ProcessStartInfo", re.IGNORECASE)
PS_NO_WINDOW = re.compile(r"CreateNoWindow\s*=\s*\$true", re.IGNORECASE)
PS_START_PROCESS = re.compile(r"\bStart-Process\b", re.IGNORECASE)
PS_HIDDEN = re.compile(r"-WindowStyle\s+Hidden|-NoNewWindow", re.IGNORECASE)
JS_LAUNCH = re.compile(
    r"(?<![\w.$])(?:spawn|spawnSync|exec|execSync|execFile|execFileSync|fork)\s*\("
    r"|\b(?:child_process(?:_\d+)?|childProcess|cp)\.(?:spawn|spawnSync|exec|execSync|execFile|execFileSync|fork)\b"
)
PREFILTER = (b"subprocess", b"create_subprocess", b"os.system", b"os.popen", b"os.spawn", b"DETACHED_PROCESS",
             b"CREATE_NEW_CONSOLE", b"creationflags", b"ProcessStartInfo", b"Start-Process", b"child_process",
             b"execa", b"cross-spawn", b"exec.Command")
SUFFIXES = (".py", ".ps1", ".psm1", ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".go")
GO_LAUNCH = re.compile(r"\bexec\.Command(?:Context)?\s*\(")
GO_GUARD = re.compile(r"HideWindow\s*:\s*true|CREATE_NO_WINDOW|0x08000000")
JS_CHILD_PROCESS = re.compile(r"child_process|node:child_process|\bexeca\b|cross-spawn")

CONFTEST_GUARD = '''import os
import subprocess

if os.name == "nt" and not getattr(subprocess.Popen.__init__, "_no_window", False):
    _original_init = subprocess.Popen.__init__
    _keep = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_CONSOLE  # nexus: console-window-ok honor an explicit request

    def _init(self, *args, **kwargs):
        flags = kwargs.get("creationflags") or 0
        if not flags & _keep:
            kwargs["creationflags"] = flags | subprocess.CREATE_NO_WINDOW
        _original_init(self, *args, **kwargs)

    _init._no_window = True
    subprocess.Popen.__init__ = _init'''


class Finding(NamedTuple):
    path: str
    line: int
    rule: str
    fix: str


def _disabled() -> bool:
    disabled = {item.strip() for item in os.environ.get("NEXUS_DISABLED_HOOKS", "").split(",")}
    return HOOK_NAME in disabled or os.environ.get("NEXUS_CONSOLE_GUARD", "").lower() in {"off", "0", "false"}


def _on_windows() -> bool:
    return os.environ.get("NEXUS_CONSOLE_GUARD_PLATFORM", os.name) == "nt"


def is_test_command(command: str) -> bool:
    return bool(TEST_COMMAND.search(command or ""))


def project_root(cwd: Path) -> Path:
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return cwd


def _marked(lines: list[str], index: int) -> bool:
    return MARKER in lines[index] or (index > 0 and MARKER in lines[index - 1])


def _call_text(lines: list[str], index: int) -> str:
    """The call starting on this line, up to its closing parenthesis or 24 lines."""
    text, depth, started = [], 0, False
    for line in lines[index:index + 24]:
        text.append(line)
        for char in line:
            if char == "(":
                depth += 1
                started = True
            elif char == ")":
                depth -= 1
        if started and depth <= 0:
            break
    return "\n".join(text)


def _is_test_file(rel: Path) -> bool:
    name = rel.name.lower()
    parts = {part.lower() for part in rel.parts[:-1]}
    return (name.startswith("test_") or name.endswith(("_test.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js", ".test.mjs"))
            or name == "conftest.py" or bool(parts & {"tests", "test", "__tests__", "e2e"}))


def _python_guard_present(files: list[tuple[Path, Path]]) -> bool:
    for path, rel in files:
        if rel.name == "conftest.py":
            try:
                if "CREATE_NO_WINDOW" in path.read_text(encoding="utf-8", errors="replace"):
                    return True
            except OSError:
                continue
    return False


def _git_files(root: Path) -> list[str] | None:
    """Tracked plus untracked-but-not-ignored files, so vendored and build output is skipped."""
    if not (root / ".git").exists():
        return None
    flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    try:
        result = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
                                capture_output=True, timeout=30, check=False, **flags)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return [item for item in result.stdout.decode("utf-8", "replace").split("\0") if item]


def _candidates(root: Path) -> list[tuple[Path, Path]]:
    listed = _git_files(root)
    if listed is None:
        listed = []
        for current, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".venv")]
            listed.extend(str((Path(current) / name).relative_to(root)) for name in names)
    files = []
    for rel in listed:
        rel_path = Path(rel)
        name = rel_path.name
        if name.endswith(SUFFIXES) and not name.endswith(".d.ts") and not set(rel_path.parts[:-1]) & SKIP_DIRS:
            files.append((root / rel_path, rel_path))
            if len(files) >= MAX_FILES:
                break
    return files


def _go_guard_present(files: list[tuple[Path, Path]]) -> bool:
    for path, rel in files:
        if rel.suffix == ".go":
            try:
                if GO_GUARD.search(path.read_text(encoding="utf-8", errors="replace")):
                    return True
            except OSError:
                continue
    return False


def _budget() -> float:
    try:
        return max(1.0, float(os.environ.get("NEXUS_CONSOLE_GUARD_BUDGET", SCAN_BUDGET_SECONDS)))
    except ValueError:
        return SCAN_BUDGET_SECONDS


def scan(root: Path, incomplete: list[bool] | None = None) -> list[Finding]:
    """Findings for root; when the time budget runs out, sets incomplete[0] and returns what was found."""
    deadline = time.monotonic() + _budget()
    # The guard and its tests have to spell out every pattern they detect.
    own = {Path(__file__).name, "test_console_window_guard.py"}
    files = [item for item in _candidates(root) if item[1].name not in own]
    guarded = _python_guard_present(files)
    go_guarded = _go_guard_present(files)
    unguarded_go: list[Finding] = []
    findings: list[Finding] = []
    unguarded_tests: list[Finding] = []
    for path, rel in files:
        if time.monotonic() > deadline:
            if incomplete is not None:
                incomplete[:] = [True]
            break
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            raw = path.read_bytes()
            if not any(token in raw for token in PREFILTER):
                continue
            lines = raw.decode("utf-8", errors="replace").splitlines()
        except OSError:
            continue
        shown = rel.as_posix()
        suffix = path.suffix.lower()
        if suffix == ".py":
            for i, line in enumerate(lines):
                if _marked(lines, i) or line.lstrip().startswith("#"):
                    continue
                if PY_EXPLICIT.search(line):
                    findings.append(Finding(shown, i + 1, "explicit detached or new-console launch",
                                            "Use creationflags=subprocess.CREATE_NO_WINDOW instead; a detached child has no "
                                            "console, so every console program it starts opens a window. If detaching is "
                                            f"required, mark the line with '# {MARKER} <reason>'."))
                elif not guarded and _is_test_file(rel) and PY_LAUNCH.search(line):
                    unguarded_tests.append(Finding(shown, i + 1, "test starts a process without a no-window guard", ""))
        elif suffix in {".ps1", ".psm1"}:
            text = "\n".join(lines)
            if PS_PSI.search(text) and not PS_NO_WINDOW.search(text):
                index = next(i for i, line in enumerate(lines) if PS_PSI.search(line))
                if not _marked(lines, index):
                    findings.append(Finding(shown, index + 1, "ProcessStartInfo without CreateNoWindow",
                                            "Set '$psi.UseShellExecute = $false; $psi.CreateNoWindow = $true'."))
            for i, line in enumerate(lines):
                if PS_START_PROCESS.search(line) and not line.lstrip().startswith("#") and not _marked(lines, i):
                    if not PS_HIDDEN.search(_call_text(lines, i)):
                        findings.append(Finding(shown, i + 1, "Start-Process opens a new window",
                                                "Add '-NoNewWindow' (or '-WindowStyle Hidden'), or call the program directly."))
        elif suffix == ".go":
            if go_guarded or not rel.name.endswith("_test.go"):
                continue
            for i, line in enumerate(lines):
                if GO_LAUNCH.search(line) and not line.lstrip().startswith("//") and not _marked(lines, i):
                    unguarded_go.append(Finding(shown, i + 1, "Go test starts a process without a no-window helper", ""))
        else:
            text = "\n".join(lines)
            if not JS_CHILD_PROCESS.search(text):
                continue
            for i, line in enumerate(lines):
                stripped = line.lstrip()
                if stripped.startswith(("//", "*", "/*")) or _marked(lines, i) or not JS_LAUNCH.search(line):
                    continue
                if "windowsHide" not in _call_text(lines, i):
                    findings.append(Finding(shown, i + 1, "child_process call without windowsHide",
                                            "Pass { windowsHide: true } in the options object."))
    if unguarded_go:
        first = unguarded_go[0]
        findings.insert(0, Finding(first.path, first.line,
                                   f"{len(unguarded_go)} exec.Command call(s) in Go tests and no Windows no-window helper",
                                   "Add a //go:build windows helper that sets cmd.SysProcAttr = &syscall.SysProcAttr"
                                   "{HideWindow: true, CreationFlags: 0x08000000} and call it for every test command."))
    if unguarded_tests:
        first = unguarded_tests[0]
        findings.insert(0, Finding(first.path, first.line,
                                   f"{len(unguarded_tests)} process launch(es) in test code and no conftest.py no-window guard",
                                   "Add this block to the top-level tests conftest.py (applies CREATE_NO_WINDOW to every "
                                   "child the suite starts):\n" + CONFTEST_GUARD))
    return findings


def report(command: str, root: Path, findings: list[Finding]) -> str:
    lines = [
        "Blocked: on Windows this test run could flood the desktop with console windows.",
        f"Project: {root}",
        f"Command: {command[:160]}",
        "Fix these before running the tests (each launch must be window-safe):",
    ]
    for item in findings[:MAX_REPORTED]:
        lines.append(f"- {item.path}:{item.line}: {item.rule}.")
        if item.fix:
            lines.extend("    " + part for part in item.fix.splitlines())
    if len(findings) > MAX_REPORTED:
        lines.append(f"- ...and {len(findings) - MAX_REPORTED} more of the same kinds.")
    lines.append(f"A deliberate case: put '{MARKER} <reason>' in a comment on the line or the line above it.")
    return "\n".join(lines)


def main() -> int:
    if _disabled() or not _on_windows():
        return 0
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not is_test_command(command):
        return 0
    root = project_root(Path(payload.get("cwd") or os.getcwd()).resolve())
    incomplete: list[bool] = [False]
    findings = scan(root, incomplete)
    if not findings:
        if incomplete[0]:
            print(f"console-window-guard: scan stopped after {_budget():g}s with no unsafe launch found so far; "
                  "the test run proceeds.", file=sys.stderr)
        return 0
    print(report(command, root, findings), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
