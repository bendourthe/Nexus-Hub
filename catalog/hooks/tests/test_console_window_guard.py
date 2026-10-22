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
    assert "without CREATE_NO_WINDOW or a shared default" in result.stderr
    assert "CREATE_NO_WINDOW" in result.stderr


def test_conftest_guard_clears_the_unguarded_finding(tmp_path: Path) -> None:
    write(tmp_path, "tests/test_a.py", UNGUARDED_TEST)
    write(tmp_path, "tests/conftest.py", "import runpy\npolicy = runpy.run_path(\"nexus_process.py\")\npolicy[\"install_no_window_default\"]()\n")
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
                                  "subprocess.Popen(['x'], creationflags=subprocess.DETACHED_PROCESS)  # nexus: console-window-ok explicit scenario\n")
    write(tmp_path, "tools/b.py", "import subprocess\n"
                                  "subprocess.Popen(['x'], creationflags=subprocess.DETACHED_PROCESS)  # nexus: console-window-ok explicit scenario\n")
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


@pytest.mark.parametrize("command", ["git status", "echo pytest-free", "ls tests"])
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


def test_an_exhausted_scan_budget_blocks_until_verifiable(tmp_path: Path, monkeypatch, capsys) -> None:
    """An unobserved launch cannot be treated as window-safe."""
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location("console_window_guard_budget", HOOK)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    write(tmp_path, "tests/test_a.py", UNGUARDED_TEST)
    monkeypatch.setattr(guard, "_budget", lambda: -1.0)
    incomplete = [False]
    assert guard.scan(tmp_path, incomplete) == [] and incomplete == [True]
    monkeypatch.setenv("NEXUS_CONSOLE_GUARD_PLATFORM", "nt")
    monkeypatch.delenv("NEXUS_DISABLED_HOOKS", raising=False)
    monkeypatch.delenv("NEXUS_CONSOLE_GUARD", raising=False)
    payload = {"tool_name": "Bash", "tool_input": {"command": "pytest"}, "cwd": str(tmp_path)}
    monkeypatch.setattr(guard.sys, "stdin", io.StringIO(json.dumps(payload)))
    assert guard.main() == 2
    assert "scan stopped after" in capsys.readouterr().err


def test_nexus_hub_itself_has_no_window_unsafe_launch() -> None:
    """The repository keeps its own rule: every process launch is window-safe or marked with a reason."""
    repo = Path(__file__).resolve().parents[3]
    result = run_hook(repo, "python -m pytest -q")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("command", ["npm install", "npm.cmd ci", "npm run build", "uv sync", "python build.py", "powershell -File scripts/installer.ps1", "bash scripts/installer.sh", "cmake --build out", "python helper.py"])
def test_installer_build_and_helper_commands_are_guarded(tmp_path: Path, command: str) -> None:
    write(tmp_path, "src/launch.py", "import subprocess\nsubprocess.run(['git', 'status'])\n")
    result = run_hook(tmp_path, command)
    assert result.returncode == 2, (command, result.stderr)
    assert "src/launch.py:" in result.stderr


@pytest.mark.parametrize("body", [
    "import subprocess\nsubprocess.run(['git'], creationflags=0)\n",
    "import asyncio\nasyncio.create_subprocess_exec('git')\n",
    "import os\nos.system('git status')\n",
    "import subprocess as sp\nsp.Popen(['git'])\n",
    "from subprocess import check_output as launch\nlaunch(['git'])\n",
])
def test_new_product_launch_without_window_policy_fails(tmp_path: Path, body: str) -> None:
    write(tmp_path, "src/new.py", body)
    assert run_hook(tmp_path, "npm run build").returncode == 2


def test_conftest_in_an_unrelated_tree_does_not_guard_a_launch(tmp_path: Path) -> None:
    write(tmp_path, "tests/conftest.py", "import runpy\np=runpy.run_path('nexus_process.py')\np['install_no_window_default']()\n")
    write(tmp_path, "other/test_launch.py", UNGUARDED_TEST)
    assert run_hook(tmp_path, "pytest").returncode == 2


def test_a_flag_mention_does_not_install_a_default(tmp_path: Path) -> None:
    write(tmp_path, "tests/conftest.py", "# CREATE_NO_WINDOW\n")
    write(tmp_path, "tests/test_launch.py", UNGUARDED_TEST)
    assert run_hook(tmp_path, "pytest").returncode == 2


def test_false_windows_hide_is_not_safe(tmp_path: Path) -> None:
    write(tmp_path, "src/a.js", "require('child_process').spawn('cmd', [], { windowsHide: false });\n")
    assert run_hook(tmp_path, "npm run build").returncode == 2


def test_exception_marker_requires_a_reason_on_the_launch_line(tmp_path: Path) -> None:
    write(tmp_path, "src/a.py", "import subprocess\nsubprocess.run(['git'])  # nexus: console-window-ok\n")
    assert run_hook(tmp_path, "pytest").returncode == 2


def test_child_process_namespace_alias_is_guarded(tmp_path: Path) -> None:
    write(tmp_path, "src/a.ts", "import * as processes from 'node:child_process';\nprocesses.spawn('git', []);\n")
    assert run_hook(tmp_path, "npm run build").returncode == 2



def test_explicit_external_python_helper_is_checked(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    write(tmp_path, "helper.py", "import subprocess\nsubprocess.run(['git'])\n")
    result = run_hook(project, 'python "' + str(tmp_path / "helper.py") + '"')
    assert result.returncode == 2 and "helper.py:" in result.stderr


@pytest.mark.parametrize("command", ["npm.cmd test", "nexus-hub upgrade", "npx tsc", "vite build"])
def test_additional_build_and_install_entry_points_are_guarded(tmp_path: Path, command: str) -> None:
    write(tmp_path, "launch.py", "import subprocess\nsubprocess.run(['git'])\n")
    assert run_hook(tmp_path, command).returncode == 2


@pytest.mark.parametrize("flags", ["subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_CONSOLE", "0x08000000 | 0x8", "subprocess.DETACHED_PROCESS"])
def test_named_conflicting_flags_are_rejected(tmp_path: Path, flags: str) -> None:
    write(tmp_path, "launch.py", f"import subprocess\nflags={flags}\nsubprocess.Popen(['git'], creationflags=flags)\n")
    assert run_hook(tmp_path, "pytest").returncode == 2


@pytest.mark.parametrize("body", ["import { spawn as launch } from 'node:child_process';\nlaunch('git', []);\n", "const {spawn: launch} = require('child_process');\nlaunch('git', []);\n"])
def test_named_node_aliases_are_guarded(tmp_path: Path, body: str) -> None:
    write(tmp_path, "src/a.ts", body)
    assert run_hook(tmp_path, "npm run build").returncode == 2


def test_quoted_python_executable_checks_external_helper(tmp_path: Path) -> None:
    project=tmp_path / "project"
    project.mkdir()
    helper=tmp_path / "helper.py"
    write(tmp_path, "helper.py", "import subprocess\nsubprocess.run(['git'])\n")
    assert run_hook(project, f"& '{sys.executable}' -B '{helper}'").returncode == 2


@pytest.mark.parametrize("override", ["subprocess.CREATE_NEW_CONSOLE", "0"])
def test_dictionary_expansion_cannot_override_hidden_flags(tmp_path: Path, override: str) -> None:
    write(tmp_path, "launch.py", "import subprocess\noptions={'creationflags': subprocess.CREATE_NO_WINDOW, **{'creationflags': " + override + "}}\nsubprocess.Popen(['git'], **options)\n")
    assert run_hook(tmp_path, "pytest").returncode == 2


def test_mutated_options_with_new_console_are_rejected(tmp_path: Path) -> None:
    write(tmp_path, "launch.py", "import subprocess\noptions={'creationflags': subprocess.CREATE_NO_WINDOW}\noptions.update(creationflags=subprocess.CREATE_NEW_CONSOLE)\nsubprocess.Popen(['git'], **options)\n")
    assert run_hook(tmp_path, "pytest").returncode == 2
