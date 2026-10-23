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


def test_windows_installer_corpus_runs_in_its_own_job() -> None:
    """The installer corpus keeps 5.1 coverage but no longer shares the hooks job's time cap."""
    installer = next(group for group in groups_for("platform") if group.name == "windows-installer")
    selected = {arg for command in installer.commands for arg in command.argv if arg.startswith("tests/")}
    assert selected == {"tests/installer", "tests/validators"}
    assert len(installer.commands) == 4, "installer and three validator partitions keep their own time bounds"
    assert all(command.env["NEXUS_TEST_POWERSHELL"] == "powershell" for command in installer.commands)
    hooks = next(group for group in groups_for("platform") if group.name == "windows-hooks")
    assert not any("tests/installer" in c.argv for c in hooks.commands)
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["tests-windows-installer"]["steps"]
    assert any("--only windows-installer" in str(step.get("run", "")) for step in steps)


def test_windows_validator_partitions_cover_every_test_file() -> None:
    """Every current or future validator filename runs in exactly one partition."""
    import fnmatch

    installer = next(group for group in groups_for("platform") if group.name == "windows-installer")
    partitions = [c for c in installer.commands if "tests/validators" in c.argv]
    assert [c.name for c in partitions] == [
        "validators a-c (Windows)",
        "validators co-h (Windows)",
        "validators i-z (Windows)",
    ]
    assert all(c.timeout == 1800 for c in partitions)
    assert all(c.env["NEXUS_TEST_POWERSHELL"] == "powershell" for c in partitions)
    assert all(c.runs_on("windows") and not c.runs_on("linux") and not c.runs_on("macos") for c in partitions)
    ignores = [
        [arg.split("=", 1)[1] for arg in partition.argv if arg.startswith("--ignore-glob=")]
        for partition in partitions
    ]
    files = sorted((Path(__file__).resolve().parents[1] / "validators").glob("test_*.py"))
    assert files
    future_names = [f"test_{letter}_future.py" for letter in "abcdefghijklmnopqrstuvwxyz"]
    future_names += ["test_co_future.py", "test_completion_future.py", "test_1_future.py", "test__future.py"]
    for path in files + [Path("future") / name for name in future_names]:
        # pytest matches --ignore-glob with fnmatch against the full path string.
        runs_in = [not any(fnmatch.fnmatch(str(path), g) for g in globs) for globs in ignores]
        assert runs_in.count(True) == 1, f"{path.name} runs in {runs_in.count(True)} validator partitions"
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    assert workflow["jobs"]["tests-windows-installer"]["timeout-minutes"] == 60
