"""console-window-guard.py blocks a Windows test run whose code can flood the desktop with console windows."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "console-window-guard.py"
WINDOWS = {"NEXUS_CONSOLE_GUARD_PLATFORM": "nt"}


def run_hook(project: Path, command: str, env: dict[str, str] | None = None, tool: str = "Bash") -> subprocess.CompletedProcess:
    payload = {"tool_name": tool, "tool_input": {"command": command}, "cwd": str(project)}
    merged = {key: value for key, value in __import__("os").environ.items()
              if key not in {"NEXUS_DISABLED_HOOKS", "NEXUS_CONSOLE_GUARD", "NEXUS_CONSOLE_GUARD_PLATFORM"}}
    merged.update(env if env is not None else WINDOWS)
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True,
                          text=True, env=merged, timeout=60, check=False)


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


UNGUARDED_TEST = "import subprocess\n\ndef test_x():\n    subprocess.run(['git', 'status'])\n"


def test_non_test_command_passes_even_with_risky_code(tmp_path: Path) -> None:
    write(tmp_path, "tests/test_a.py", UNGUARDED_TEST)
    result = run_hook(tmp_path, "git status")
    assert result.returncode == 0 and not result.stderr


def test_clean_project_passes(tmp_path: Path) -> None:
    write(tmp_path, "tests/test_a.py", "def test_x():\n    assert True\n")
    assert run_hook(tmp_path, "python -m pytest tests -q").returncode == 0


def test_unguarded_python_test_launch_blocks_with_conftest_fix(tmp_path: Path) -> None:
    write(tmp_path, "tests/test_a.py", UNGUARDED_TEST)
    result = run_hook(tmp_path, "python -m pytest tests -q")
    assert result.returncode == 2
    assert "no conftest.py no-window guard" in result.stderr
    assert "CREATE_NO_WINDOW" in result.stderr and "subprocess.Popen.__init__" in result.stderr


def test_conftest_guard_clears_the_unguarded_finding(tmp_path: Path) -> None:
    write(tmp_path, "tests/test_a.py", UNGUARDED_TEST)
    write(tmp_path, "tests/conftest.py", "import subprocess\nFLAG = subprocess.CREATE_NO_WINDOW\n")
    assert run_hook(tmp_path, "pytest").returncode == 0


@pytest.mark.parametrize(("rel", "text", "rule"), [
    ("tools/launch.py", "import subprocess\nsubprocess.Popen(['x'], creationflags=subprocess.DETACHED_PROCESS)\n",
     "explicit detached or new-console launch"),
    ("tools/launch.py", "import subprocess\nsubprocess.run(['x'], **{\"creationflags\": 0x00000008})\n",
     "explicit detached or new-console launch"),
    ("hooks/run.ps1", "$psi = New-Object System.Diagnostics.ProcessStartInfo\n$psi.UseShellExecute = $false\n",
     "ProcessStartInfo without CreateNoWindow"),
    ("hooks/run.ps1", "Start-Process git -ArgumentList 'status'\n", "Start-Process opens a new window"),
    ("test/run.test.ts", "import { spawnSync } from 'child_process';\nspawnSync('git', ['status']);\n",
     "child_process call without windowsHide"),
])
def test_each_rule_blocks_and_names_the_site(tmp_path: Path, rel: str, text: str, rule: str) -> None:
    write(tmp_path, rel, text)
    result = run_hook(tmp_path, "npm test")
    assert result.returncode == 2, result.stderr
    assert f"{rel}:" in result.stderr and rule in result.stderr


@pytest.mark.parametrize(("rel", "text"), [
    ("hooks/run.ps1", "$psi = New-Object System.Diagnostics.ProcessStartInfo\n$psi.UseShellExecute = $false; $psi.CreateNoWindow = $true\n"),
    ("hooks/run.ps1", "Start-Process git -NoNewWindow -Wait\n"),
    ("test/run.test.ts", "import { spawnSync } from 'child_process';\nspawnSync('git', ['status'], { windowsHide: true });\n"),
    ("src/parse.ts", "import 'child_process';\nconst m = /x/.exec(line);\n"),
])
def test_window_safe_forms_pass(tmp_path: Path, rel: str, text: str) -> None:
    write(tmp_path, rel, text)
    assert run_hook(tmp_path, "npx vitest run").returncode == 0


GO_TEST = 'package x\n\nimport (\n\t"os/exec"\n\t"testing"\n)\n\nfunc TestX(t *testing.T) {\n\t_ = exec.Command("git", "status").Run()\n}\n'


def test_go_test_launch_without_helper_blocks(tmp_path: Path) -> None:
    write(tmp_path, "x_test.go", GO_TEST)
    result = run_hook(tmp_path, "go test ./...")
    assert result.returncode == 2 and "no Windows no-window helper" in result.stderr and "HideWindow: true" in result.stderr


def test_go_windows_helper_clears_the_finding(tmp_path: Path) -> None:
    write(tmp_path, "x_test.go", GO_TEST)
    write(tmp_path, "proc_windows.go", "//go:build windows\n\npackage x\n\nimport \"syscall\"\n\n"
                                       "var attrs = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}\n")
    assert run_hook(tmp_path, "go test ./...").returncode == 0


def test_marker_on_the_line_or_above_accepts_a_deliberate_launch(tmp_path: Path) -> None:
    write(tmp_path, "tools/a.py", "import subprocess\n# nexus: console-window-ok must detach\n"
                                  "subprocess.Popen(['x'], creationflags=subprocess.DETACHED_PROCESS)\n")
    write(tmp_path, "tools/b.py", "import subprocess\n"
                                  "subprocess.Popen(['x'], creationflags=subprocess.DETACHED_PROCESS)  # nexus: console-window-ok\n")
    assert run_hook(tmp_path, "go test ./...").returncode == 0


@pytest.mark.parametrize("env", [
    {},  # not Windows: the hook does nothing
    {**WINDOWS, "NEXUS_DISABLED_HOOKS": "lint-on-write,console-window-guard"},
    {**WINDOWS, "NEXUS_CONSOLE_GUARD": "off"},
])
def test_off_windows_or_disabled_passes(tmp_path: Path, env: dict[str, str]) -> None:
    write(tmp_path, "tests/test_a.py", UNGUARDED_TEST)
    env = env or {"NEXUS_CONSOLE_GUARD_PLATFORM": "posix"}
    assert run_hook(tmp_path, "pytest", env=env).returncode == 0


@pytest.mark.parametrize("command", [
    "python -m pytest tests -q", "py.test", "npm run test", "pnpm test", "yarn test", "npx vitest run",
    "npx playwright test", "go test ./...", "cargo test", "dotnet test", "mvn -q test", "./gradlew test",
    "Invoke-Pester", "python scripts/ci/run.py --profile fast", "cd x && pytest",
])
def test_recognises_test_runners(tmp_path: Path, command: str) -> None:
    write(tmp_path, "tests/test_a.py", UNGUARDED_TEST)
    assert run_hook(tmp_path, command).returncode == 2, command


@pytest.mark.parametrize("command", ["git status", "npm install", "python build.py", "echo pytest-free", "ls tests"])
def test_ignores_non_test_commands(tmp_path: Path, command: str) -> None:
    write(tmp_path, "tests/test_a.py", UNGUARDED_TEST)
    assert run_hook(tmp_path, command).returncode == 0, command


def test_git_listing_skips_ignored_and_vendored_code(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    write(tmp_path, ".gitignore", "generated/\n")
    write(tmp_path, "generated/launch.py", "import subprocess\nsubprocess.Popen(['x'], creationflags=subprocess.DETACHED_PROCESS)\n")
    write(tmp_path, "node_modules/pkg/index.js", "require('child_process').spawnSync('x');\n")
    write(tmp_path, "tests/test_a.py", "def test_x():\n    assert True\n")
    assert run_hook(tmp_path, "pytest").returncode == 0


def test_nexus_hub_itself_has_no_window_unsafe_launch() -> None:
    """The repository keeps its own rule: every process launch is window-safe or marked with a reason."""
    repo = Path(__file__).resolve().parents[3]
    result = run_hook(repo, "python -m pytest -q")
    assert result.returncode == 0, result.stderr
