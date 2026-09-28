"""Keep catalog shell lint selection in the platform profile."""

from pathlib import Path

import pytest

from scripts.ci.profiles import groups_for

yaml = pytest.importorskip("yaml")

CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def test_catalog_shell_lint_is_profile_owned() -> None:
    shell = next(group for group in groups_for("platform") if group.name == "shell-lint")
    commands = [command for command in shell.commands if command.name == "shellcheck catalog"]
    assert len(commands) == 1
    command = commands[0]
    assert command.argv == [
        "bash",
        "-c",
        "find catalog -name '*.sh' -print0 | xargs -0 shellcheck --severity=warning",
    ]
    assert command.runs_on("linux") and command.runs_on("macos")
    assert not command.runs_on("windows")


def test_shellcheck_job_uses_the_profile_only() -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["shellcheck"]["steps"]
    assert not any(step.get("name") == "Lint catalog shell scripts" for step in steps)
    profile = next(step for step in steps if step.get("name") == "Shell and PowerShell profile groups")
    assert "--only shell-lint,powershell-parse" in profile["run"]
