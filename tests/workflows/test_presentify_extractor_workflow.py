"""Required-check and cost controls for the Presentify extractor workflow."""

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "presentify-extractor.yml"
ON_KEY = True


def load() -> dict[str, Any]:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_required_verify_check_is_not_event_path_filtered() -> None:
    """An absent path-filtered required context leaves every unrelated PR pending."""
    triggers = load()[ON_KEY]
    assert "push" not in triggers
    assert "paths" not in triggers["pull_request"]
    assert "paths-ignore" not in triggers["pull_request"]


def test_detector_owns_the_presentify_path_filter() -> None:
    workflow = load()
    detect = workflow["jobs"]["detect"]
    assert detect["outputs"]["presentify"] == "${{ steps.paths.outputs.presentify }}"
    checkout = detect["steps"][0]
    assert checkout["with"]["fetch-depth"] == 0
    detector = next(step for step in detect["steps"] if step.get("id") == "paths")
    script = detector["run"]
    for required_path in (
        "catalog/skills/specialized-domains/document-to-interactive-html/",
        "catalog/commands/presentify",
        "tests/skills/",
        "tests/fixtures/presentify/",
        ".github/workflows/presentify-extractor",
    ):
        assert required_path in script


def test_verify_always_exists_but_heavy_steps_are_conditional() -> None:
    verify = load()["jobs"]["verify"]
    assert verify["needs"] == "detect"
    assert verify["if"] == "always() && github.event_name == 'pull_request'"
    assert verify["steps"]
    detector_gate = verify["steps"][0]
    assert detector_gate["if"] == "needs.detect.result != 'success'"
    assert "exit 1" in detector_gate["run"]
    assert all(
        step.get("if")
        == "needs.detect.result == 'success' && needs.detect.outputs.presentify == 'true'"
        for step in verify["steps"][1:]
    )


def test_render_is_weekly_without_a_duplicate_protected_push_leg() -> None:
    render = load()["jobs"]["render"]
    assert render["needs"] == "detect"
    assert render["if"] == "github.event_name == 'schedule'"
