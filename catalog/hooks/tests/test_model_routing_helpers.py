"""Direct tests for the model-routing detect/enumerate helpers (v4.13 AR-08).

`detect-platform.{sh,ps1}` and `enumerate-models.{sh,ps1}` were previously
covered only indirectly through `switch-model.sh` (v3.4 DF-v34-1). These tests
run each implementation directly under a hermetic environment: host marker
variables removed, PATH reduced to a stub directory (plus the Windows system
directory), and HOME / USERPROFILE pointed at an empty temp directory. That is
what makes "the tool is missing" observable on a workstation that really has
`codex`, `agy`, or `opencode` installed.

The contract pinned here:

  - detect prints exactly one normalized id; host markers beat binaries; with
    no markers, no binaries and no config directories it prints `unknown`;
  - enumerate never fabricates a model list: a missing or failing platform CLI
    yields the documented picker sentinel (an empty `models` array), a working
    CLI's own output is passed through unchanged, and an unrecognized id is a
    clean exit-2 refusal.

No case sets ANTHROPIC_API_KEY, so no test can reach the network.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_model_routing_helpers.py -v
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / "catalog"
    / "skills"
    / "ai-development"
    / "model-routing"
    / "scripts"
)

PICKER_SENTINEL = {
    "source": "picker",
    "models": [],
    "note": "no scriptable model list; read models from the platform model picker",
}

_MARKERS = {
    "CLAUDECODE": "claude-code",
    "CLAUDE_CODE_ENTRYPOINT": "claude-code",
    "CLAUDE_CODE_SSE_PORT": "claude-code",
    "CODEX_HOME": "codex",
    "CODEX_SANDBOX": "codex",
    "CURSOR_TRACE_ID": "cursor",
    "CURSOR_AGENT": "cursor",
    "COPILOT_AGENT_ID": "copilot",
    "GITHUB_COPILOT_CLI": "copilot",
    "OPENCODE": "opencode",
    "OPENCODE_BIN_PATH": "opencode",
}

_STUB_OUTPUT = '{"source":"stub","models":["stub-model-from-cli"]}'


class Sandbox:
    """An isolated home directory plus a stub-binary directory used as PATH."""

    def __init__(self, root: Path) -> None:
        self.home = root / "home"
        self.bin = root / "bin"
        self.home.mkdir()
        self.bin.mkdir()

    def add_tool(self, name: str, *, exit_code: int = 0) -> None:
        """Install a stub CLI that prints _STUB_OUTPUT (or nothing) and exits."""
        out = _STUB_OUTPUT if exit_code == 0 else ""
        sh = self.bin / name
        sh.write_text(
            f"#!/bin/sh\nprintf '%s\\n' '{out}'\nexit {exit_code}\n"
            if out
            else f"#!/bin/sh\nexit {exit_code}\n",
            encoding="utf-8",
            newline="\n",
        )
        sh.chmod(sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        cmd = self.bin / f"{name}.cmd"
        cmd.write_text(
            ("@echo " + out + "\r\n" if out else "") + f"@exit /b {exit_code}\r\n",
            encoding="utf-8",
        )

    def env(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in _MARKERS and k not in ("ANTHROPIC_API_KEY", "PATH", "Path")
        }
        path = [str(self.bin)]
        system_root = os.environ.get("SystemRoot")
        if os.name == "nt" and system_root:
            path.append(str(Path(system_root) / "System32"))
        env["PATH"] = os.pathsep.join(path)
        env["HOME"] = str(self.home)
        env["USERPROFILE"] = str(self.home)
        if extra:
            env.update(extra)
        return env


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    return Sandbox(tmp_path)


@pytest.fixture(params=["sh", "ps1"])
def impl(request):
    """Return a runner `(script_stem, args, env) -> CompletedProcess` for one implementation."""
    if request.param == "sh":
        bash = request.getfixturevalue("bash_bin")

        def _prefix(stem: str) -> list[str]:
            return [bash, str(_SCRIPTS / f"{stem}.sh")]

    else:
        ps = request.getfixturevalue("powershell_bin")

        def _prefix(stem: str) -> list[str]:
            return [
                ps,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(_SCRIPTS / f"{stem}.ps1"),
            ]

    def _run(stem: str, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            [*_prefix(stem), *args],
            text=True,
            capture_output=True,
            env=env,
            stdin=subprocess.DEVNULL,
            timeout=120,
            check=False,
        )

    _run.kind = request.param  # type: ignore[attr-defined]
    return _run


def _detect(impl, sandbox: Sandbox, extra: dict[str, str] | None = None) -> str:
    r = impl("detect-platform", [], sandbox.env(extra))
    assert r.returncode == 0, r.stderr
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1, r.stdout
    return lines[0].strip()


def _enumerate_json(impl, sandbox: Sandbox, platform: str, extra=None) -> dict:
    r = impl("enumerate-models", [platform], sandbox.env(extra))
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip())


# -- detect-platform ---------------------------------------------------------


def test_detect_with_no_markers_tools_or_config_is_unknown(impl, sandbox):
    assert _detect(impl, sandbox) == "unknown"


@pytest.mark.parametrize("marker,expected", sorted(_MARKERS.items()))
def test_detect_host_marker_names_the_platform(impl, sandbox, marker, expected):
    assert _detect(impl, sandbox, {marker: "1"}) == expected


def test_detect_marker_beats_binary_on_path(impl, sandbox):
    sandbox.add_tool("codex")
    assert _detect(impl, sandbox, {"CLAUDECODE": "1"}) == "claude-code"


@pytest.mark.parametrize(
    "tool,expected", [("agy", "antigravity"), ("codex", "codex"), ("gemini", "gemini-cli"), ("opencode", "opencode")]
)
def test_detect_binary_on_path_is_the_availability_fallback(impl, sandbox, tool, expected):
    sandbox.add_tool(tool)
    assert _detect(impl, sandbox) == expected


def test_detect_gemini_config_dir_without_binary(impl, sandbox):
    (sandbox.home / ".gemini").mkdir()
    assert _detect(impl, sandbox) == "gemini-cli"


def test_detect_antigravity_dir_wins_over_generic_gemini_dir(impl, sandbox):
    (sandbox.home / ".gemini" / "antigravity-cli").mkdir(parents=True)
    assert _detect(impl, sandbox) == "antigravity"


# -- enumerate-models: documented fallbacks, never fabricated models ---------


@pytest.mark.parametrize("platform", ["cursor", "copilot", "opencode", "unknown"])
def test_enumerate_picker_platforms_return_the_sentinel(impl, sandbox, platform):
    assert _enumerate_json(impl, sandbox, platform) == PICKER_SENTINEL


@pytest.mark.parametrize("platform", ["codex", "antigravity"])
def test_enumerate_missing_cli_returns_the_sentinel(impl, sandbox, platform):
    assert _enumerate_json(impl, sandbox, platform) == PICKER_SENTINEL


def test_enumerate_claude_code_without_api_key_returns_the_sentinel(impl, sandbox):
    assert _enumerate_json(impl, sandbox, "claude-code") == PICKER_SENTINEL


def test_enumerate_gemini_cli_without_settings_returns_the_sentinel(impl, sandbox):
    assert _enumerate_json(impl, sandbox, "gemini-cli") == PICKER_SENTINEL


def test_enumerate_gemini_cli_with_settings_points_at_the_alias_config(impl, sandbox):
    (sandbox.home / ".gemini").mkdir()
    (sandbox.home / ".gemini" / "settings.json").write_text("{}", encoding="utf-8")
    got = _enumerate_json(impl, sandbox, "gemini-cli")
    assert got["source"] == "config" and got["models"] == []


@pytest.mark.parametrize("platform,tool", [("codex", "codex"), ("antigravity", "agy")])
def test_enumerate_passes_a_working_cli_output_through(impl, sandbox, platform, tool):
    sandbox.add_tool(tool)
    assert _enumerate_json(impl, sandbox, platform) == json.loads(_STUB_OUTPUT)


@pytest.mark.parametrize("platform,tool", [("codex", "codex"), ("antigravity", "agy")])
def test_enumerate_failing_cli_falls_back_to_the_sentinel(impl, sandbox, platform, tool):
    sandbox.add_tool(tool, exit_code=1)
    assert _enumerate_json(impl, sandbox, platform) == PICKER_SENTINEL


def test_enumerate_unrecognized_platform_is_refused_with_exit_2(impl, sandbox):
    r = impl("enumerate-models", ["not-a-platform"], sandbox.env())
    assert r.returncode == 2
    assert "unknown platform" in r.stderr
    assert "models" not in r.stdout


def test_enumerate_ps1_unknown_platform_exits_2_for_a_stop_preference_caller(powershell_bin):
    """A caller running with $ErrorActionPreference = 'Stop' still sees exit 2 (AF-6).

    Write-Error turned terminating under the caller's preference, so `exit 2` was
    never reached and an in-process caller read $LASTEXITCODE 0.
    """
    script = _SCRIPTS / "enumerate-models.ps1"
    command = (
        "$ErrorActionPreference = 'Stop'; "
        f"try {{ & '{script}' not-a-platform }} catch {{ exit 9 }}; exit $LASTEXITCODE"
    )
    r = subprocess.run(
        [powershell_bin, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command],
        text=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=120, check=False,
    )
    assert r.returncode == 2, (r.returncode, r.stderr)
    assert "unknown platform" in r.stderr
