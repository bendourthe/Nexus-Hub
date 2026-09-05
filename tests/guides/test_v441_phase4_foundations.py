"""Retained Agentic Platforms boundary contract after the Models-only rebuild."""

from pathlib import Path
import re
import pytest

GUIDE = Path(__file__).resolve().parents[2] / "guides/website/nexus-hub-guide.html"


@pytest.fixture(scope="module")
def guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


def test_the_agentic_scene_carries_the_comparison_and_the_boundary(guide_text: str) -> None:
    """The adjacent scene retains one request, two lanes, and a permissions boundary."""
    fx = guide_text[guide_text.index('id="page-foundations"'): guide_text.index('id="page-training"')]
    assert "fx-chatbot-agent" not in fx, "the separate comparison scene must not come back"
    agent = re.search(r'<section class="fx-scene[^"]*" id="fx-agent-platform"[\s\S]*?</section>', fx).group(0)
    # one request, two lanes, chatbot first, and the boundary that makes the capability conditional
    assert agent.count('data-phase3-node="shared-request"') == 1
    assert agent.index('data-phase3-node="chatbot-handoff"') < agent.index('data-phase3-node="agent-handoff"')
    assert agent.count('data-grammar="boundary"') == 1
    assert "when permitted" in agent and "when supported" in agent
    # the four things the agentic lane runs, that the chatbot lane cannot
    assert agent.count('class="ap-step"') == 4, "four steps expected"
