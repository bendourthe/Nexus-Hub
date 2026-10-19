"""Real Git controls for the configuration fixture in both pytest roots."""

from __future__ import annotations

import ast
import importlib.util
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "conftest_rel", ["catalog/hooks/tests/conftest.py", "tests/conftest.py"]
)
@pytest.mark.parametrize("route", ["global", "system", "process"])
def test_host_git_config_isolated_and_local_hooks_retained(
    tmp_path: Path,
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
    conftest_rel: str,
    route: str,
) -> None:
    source_path = REPO_ROOT / conftest_rel
    tree = ast.parse(source_path.read_text(encoding="utf-8-sig"))
    fixture = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "isolated_git_configuration"
        ),
        None,
    )
    assert fixture is not None, "both pytest roots require the Git isolation fixture"
    assert any(
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and isinstance(decorator.func.value, ast.Name)
        and decorator.func.value.id == "pytest"
        and decorator.func.attr == "fixture"
        and any(
            keyword.arg == "autouse"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in decorator.keywords
        )
        for decorator in fixture.decorator_list
    ), "Git isolation must apply automatically to every test"
    module_name = "_git_fixture_" + conftest_rel.replace("/", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, source_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    isolate = module.isolated_git_configuration.__wrapped__

    external_hooks = tmp_path / "external-hooks"
    external_hooks.mkdir()
    external_marker = tmp_path / "external-marker"
    hook = external_hooks / "pre-commit"
    hook.write_text(
        "#!/bin/sh\nprintf external > "
        + shlex.quote(external_marker.as_posix())
        + "\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)
    caller_config = tmp_path / "caller.gitconfig"
    caller_config.write_text("", encoding="utf-8")
    for key in tuple(os.environ):
        if key == "GIT_CONFIG" or key.startswith("GIT_CONFIG_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(caller_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    if route in ("global", "system"):
        subprocess.run(
            [
                "git",
                "config",
                "--file",
                str(caller_config),
                "core.hooksPath",
                str(external_hooks),
            ],
            check=True,
            capture_output=True,
        )
        if route == "system":
            empty_global = tmp_path / "empty-global.gitconfig"
            empty_global.write_text("", encoding="utf-8")
            monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty_global))
            monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(caller_config))
            monkeypatch.delenv("GIT_CONFIG_NOSYSTEM")
    else:
        monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
        monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.hooksPath")
        monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(external_hooks))
    caller_bytes = caller_config.read_bytes()
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.name", "fixture")
    git("config", "user.email", "fixture@example.invalid")
    (repo / "one").write_text("one", encoding="utf-8")
    git("add", "one")
    git("commit", "-m", "first")
    assert external_marker.read_text() == "external", (
        "negative control hook did not execute"
    )
    external_marker.unlink()

    isolate(monkeypatch, tmp_path_factory)
    (repo / "two").write_text("two", encoding="utf-8")
    git("add", "two")
    git("commit", "-m", "second")
    assert not external_marker.exists(), "external user hook executed after isolation"
    assert Path(os.environ["GIT_CONFIG_GLOBAL"]) != caller_config
    assert os.environ["GIT_CONFIG_NOSYSTEM"] == "1"
    assert "GIT_CONFIG_COUNT" not in os.environ

    local_marker = tmp_path / "local-marker"
    local_hook = repo / ".git" / "hooks" / "pre-commit"
    local_hook.write_text(
        "#!/bin/sh\nprintf local > " + shlex.quote(local_marker.as_posix()) + "\n",
        encoding="utf-8",
    )
    local_hook.chmod(0o755)
    (repo / "three").write_text("three", encoding="utf-8")
    git("add", "three")
    git("commit", "-m", "third")
    assert local_marker.read_text() == "local", "repository hook was disabled"
    assert not external_marker.exists()
    assert caller_config.read_bytes() == caller_bytes
