"""Keep the Windows native test selection in the repository-native profile."""

from pathlib import Path

import pytest

from scripts.ci.profiles import groups_for

yaml = pytest.importorskip("yaml")

CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
NATIVE_TESTS = {
    "tests/integrations/test_codex_native.py",
    "tests/integrations/test_copilot_hermes_native.py",
    "tests/integrations/test_kimi_native.py",
    "tests/integrations/test_settings_hooks.py",
    "tests/integrations/test_catalog_adapters.py",
    "tests/integrations/test_codex_invocation_policy.py",
}


def test_windows_native_selection_is_profile_owned() -> None:
    windows = next(group for group in groups_for("platform") if group.name == "windows-hooks")
    commands = [command for command in windows.commands if command.name == "native integrations (Windows)"]
    assert len(commands) == 1
    command = commands[0]
    assert NATIVE_TESTS == {arg for arg in command.argv if arg.startswith("tests/")}
    assert command.env["NEXUS_TEST_POWERSHELL"] == "powershell"
    assert command.runs_on("windows")
    assert not command.runs_on("linux") and not command.runs_on("macos")


def test_windows_workflow_has_no_second_native_test_list() -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["tests-windows"]["steps"]
    assert not any("Codex, Copilot, Kimi" in step.get("name", "") for step in steps)
    profile = next(step for step in steps if step.get("name") == "Windows platform profile group")
    assert "--only interpreters,windows-hooks" in profile["run"]
