"""Keep the pre-commit validator in the repository-native profile."""

from pathlib import Path

import pytest

from scripts.ci.profiles import groups_for
from scripts.ci.run import select_groups

yaml = pytest.importorskip("yaml")

CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def test_precommit_is_an_explicit_only_profile_group() -> None:
    group = next(group for group in groups_for("full") if group.name == "pre-commit")
    assert group not in select_groups("full", None)
    assert select_groups("full", ["pre-commit"]) == (group,)
    assert len(group.commands) == 1
    command = group.commands[0]
    assert command.argv == ["pre-commit", "run", "--all-files"]
    assert command.env["SKIP"] == "lint-templates,build-catalogs"


def test_validation_job_selects_precommit_through_the_profile() -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["validate"]["steps"]
    assert not any(step.get("name") == "Run pre-commit hooks (standard checks only)" for step in steps)
    profile = next(step for step in steps if step.get("name") == "Repository-native validation profile")
    assert "--only catalog-parse,pre-commit,hygiene" in profile["run"]
