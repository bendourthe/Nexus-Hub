"""Keep browser-required guide contracts explicit and profile-owned."""

from pathlib import Path

import pytest

from scripts.ci.profiles import groups_for
from scripts.ci.run import select_groups

yaml = pytest.importorskip("yaml")

CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def test_browser_group_is_explicit_only() -> None:
    browser = next(group for group in groups_for("full") if group.name == "guide-browser")
    assert browser not in select_groups("full", None)
    assert select_groups("full", ["guide-browser"]) == (browser,)
    assert len(browser.commands) == 1
    command = browser.commands[0]
    assert set(command.argv) >= {
        "tests/guides/",
        "tests/verification/test_visual_defect_detector.py",
        "--junitxml=reports/junit/guide-render.xml",
    }
    assert command.env["NEXUS_REQUIRE_RENDER"] == "1"


def test_guide_job_invokes_only_the_browser_group() -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["guide-render"]["steps"]
    run = next(step for step in steps if step.get("name") == "Run guide and visual detector browser contracts")
    assert run["run"] == (
        "python scripts/ci/run.py --profile full --only guide-browser --reports-dir reports"
    )
    assert "env" not in run
