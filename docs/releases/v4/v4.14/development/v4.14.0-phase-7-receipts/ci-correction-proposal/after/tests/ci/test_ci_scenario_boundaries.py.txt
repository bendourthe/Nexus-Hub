"""Smoke-helper containment, cleanup and optional editor acceptance controls."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.ci import verify_scenarios as scenarios


@pytest.mark.parametrize("installed,accepted", [("nexus-hub.cursor-usage-monitor", True), ("wrong.extension", False), ("nexus-hub.cursor-usage-monitor\nnexus-hub.claude-usage-monitor", False), ("nexus-hub.cursor-usage-monitor\nnexus-hub.codex-usage-monitor", False), ("nexus-hub.cursor-usage-monitor\nnexus-hub.github-usage-monitor", False)])
def test_cursor_profile_uses_both_private_stores_and_checks_delivery(monkeypatch, tmp_path, installed, accepted):
    package = tmp_path / "packed-vsix/monitor.vsix"
    package.parent.mkdir()
    package.touch()
    monkeypatch.setattr(scenarios.shutil, "which", lambda *args, **kwargs: "cursor-fixture")
    commands = []
    def run(argv, **kwargs):
        commands.append(argv)
        return subprocess.CompletedProcess(argv, 0, installed, "")
    monkeypatch.setattr(scenarios, "run", run)
    if accepted:
        scenarios.cursor_profile(tmp_path, tmp_path, {})
    else:
        with pytest.raises(RuntimeError):
            scenarios.cursor_profile(tmp_path, tmp_path, {})
    assert len(commands) == 2
    for command in commands:
        assert command[command.index("--user-data-dir") + 1] == str(tmp_path / "cursor-profile")
        assert command[command.index("--extensions-dir") + 1] == str(tmp_path / "cursor-extensions")


def test_cursor_absence_skips_without_attempting_install(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(scenarios.shutil, "which", lambda *args, **kwargs: None)
    def unexpected(*args, **kwargs):
        pytest.fail("missing optional CLI must not be invoked")
    monkeypatch.setattr(scenarios, "run", unexpected)
    scenarios.cursor_profile(tmp_path, tmp_path, {})
    assert "SKIP: Cursor CLI absent" in capsys.readouterr().out


@pytest.mark.parametrize("fail", [False, True])
def test_cli_cleans_disposable_target_after_success_and_failure(monkeypatch, tmp_path, fail):
    (tmp_path / "AGENTS.md").write_text("Fixture root.\n", encoding="utf-8")
    observed = []
    def scenario(root, work, env):
        observed.append(work)
        assert root == tmp_path.resolve()
        assert Path(env["HOME"]).is_relative_to(work)
        (work / "created-output").touch()
        if fail:
            raise RuntimeError("fixture failure")
    monkeypatch.setattr(scenarios, "registry", scenario)
    if fail:
        with pytest.raises(RuntimeError, match="fixture failure"):
            scenarios.main(["registry", "--root", str(tmp_path)])
    else:
        assert scenarios.main(["registry", "--root", str(tmp_path)]) == 0
    assert len(observed) == 1 and not observed[0].exists()


def test_linux_registry_requires_actual_project_workflows(monkeypatch, tmp_path):
    monkeypatch.setattr(scenarios.sys, "platform", "linux")
    messages = "Claude -- commands:ok, skills:ok\nCodex / ChatGPT -- ~/.agents/skills:ok\nGemini IDE -- GEMINI.md:ok\nAntigravity 2.0 IDE (global) -- skills:ok\nOpenCode -- skills:ok"
    def run(argv, **kwargs):
        if "--target" in argv and "init" in argv:
            target = Path(argv[argv.index("--target") + 1]) / ".agents/workflows"
            target.mkdir(parents=True)
            (target / "command.md").touch()
        return subprocess.CompletedProcess(argv, 0, messages, "")
    monkeypatch.setattr(scenarios, "run", run)
    scenarios.registry(tmp_path, tmp_path, {"HOME": str(tmp_path)})
    assert (tmp_path / "project/.agents/workflows/command.md").is_file()


@pytest.mark.parametrize("selector", ["PIP_TARGET", "PIP_PREFIX", "PIP_ROOT", "PIP_CONFIG_FILE"])
def test_package_destination_selectors_cannot_escape_scratch(monkeypatch, tmp_path, selector):
    import json
    import os
    import sys

    outside = tmp_path / "outside"
    outside.mkdir()
    config = tmp_path / "external-pip.ini"
    config.write_text("[global]\ntarget = " + str(outside) + "\n", encoding="utf-8")
    for key in ("PIP_TARGET", "PIP_PREFIX", "PIP_ROOT", "PIP_CONFIG_FILE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(selector, str(config if selector == "PIP_CONFIG_FILE" else outside))
    constraint = tmp_path / "constraints.txt"
    constraint.write_text("", encoding="utf-8")
    monkeypatch.setenv("PIP_CONSTRAINT", str(constraint))
    monkeypatch.setenv("PIP_INDEX_URL", "https://example.invalid/simple")
    work = tmp_path / "scratch"
    work.mkdir()
    env = scenarios.isolated_environment(work)
    parser = "from pip._internal.commands import create_command; import json; o,a=create_command('install').parse_args([]); print(json.dumps({k:getattr(o,k,None) for k in ['target_dir','prefix_path','root_path']}))"
    parsed = subprocess.run([sys.executable, "-c", parser], cwd=work, env=env, capture_output=True, text=True, check=True, timeout=30)
    assert all(value is None for value in json.loads(parsed.stdout).values())
    assert not any(key in env for key in ("PIP_TARGET", "PIP_PREFIX", "PIP_ROOT"))
    assert env["PIP_CONFIG_FILE"] == os.devnull
    assert env["PIP_CONSTRAINT"] == str(constraint)
    assert env["PIP_INDEX_URL"] == "https://example.invalid/simple"
    assert list(outside.iterdir()) == []


def test_uv_config_cannot_create_external_target_lock(monkeypatch, tmp_path):
    import json
    import shutil
    import sys

    uv = shutil.which("uv")
    if not uv:
        pytest.skip("uv not installed; destination environment controls remain mandatory")
    outside = tmp_path / "outside"
    outside.mkdir()
    config = tmp_path / "uv.toml"
    config.write_text("[pip]\ntarget = " + json.dumps(str(outside)) + "\n", encoding="utf-8")
    monkeypatch.setenv("UV_CONFIG_FILE", str(config))
    monkeypatch.delenv("UV_NO_CONFIG", raising=False)
    work = tmp_path / "scratch"
    work.mkdir()
    env = scenarios.isolated_environment(work)
    requirements = work / "empty.txt"
    requirements.write_text("", encoding="utf-8")
    result = subprocess.run([uv, "pip", "install", "--dry-run", "--offline", "--no-index", "--python", sys.executable, "-r", str(requirements)], cwd=work, env=env, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    assert list(outside.iterdir()) == []
    assert "UV_CONFIG_FILE" not in tuple(env) and env["UV_NO_CONFIG"] == "1"


def test_uv_destination_config_is_disabled_even_without_uv(monkeypatch, tmp_path):
    monkeypatch.setenv("UV_CONFIG_FILE", str(tmp_path / "external.toml"))
    monkeypatch.setenv("UV_NO_CONFIG", "0")
    env = scenarios.isolated_environment(tmp_path)
    assert "UV_CONFIG_FILE" not in tuple(env) and env["UV_NO_CONFIG"] == "1"

@pytest.mark.parametrize("selector,field", [
    ("PIP_PYTHON", "python"), ("PIP_BUILD_TRACKER", None),
    ("PIP_LOG", "log"), ("PIP_LOG_FILE", "log"), ("PIP_LOCAL_LOG", "log"),
    ("PIP_REPORT", "json_report_file"), ("PIP_SRC", "src_dir"),
    ("PIP_SOURCE", "src_dir"), ("PIP_SOURCE_DIR", "src_dir"), ("PIP_SOURCE_DIRECTORY", "src_dir"),
])
def test_pip_interpreter_and_output_selectors_are_not_inherited(monkeypatch, tmp_path, selector, field):
    import json
    import sys

    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setenv(selector, str(outside))
    work = tmp_path / "scratch"
    work.mkdir()
    env = scenarios.isolated_environment(work)
    assert selector not in tuple(env)
    if field is None:
        parser = "from pip._internal.operations.build.build_tracker import get_build_tracker; import json; c=get_build_tracker(); t=c.__enter__(); print(json.dumps(t._root)); c.__exit__(None,None,None)"
    else:
        parser = "from pip._internal.commands import create_command; import json; o,a=create_command('install').parse_args([]); print(json.dumps(getattr(o," + repr(field) + ",None)))"
    parsed = subprocess.run([sys.executable, "-c", parser], cwd=work, env=env, capture_output=True, text=True, check=True, timeout=30)
    assert json.loads(parsed.stdout) != str(outside)
    assert list(outside.iterdir()) == []
