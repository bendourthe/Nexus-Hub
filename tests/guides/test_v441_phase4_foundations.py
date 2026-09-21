"""Retained Agentic Platforms boundary contract after the Models-only rebuild."""

from pathlib import Path
import re
import pytest

GUIDE = Path(__file__).resolve().parents[2] / "guides/website/nexus-hub-guide.html"


@pytest.fixture(scope="module")
def guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


def test_the_agentic_scene_carries_the_comparison_and_the_boundary(guide_text: str) -> None:
    """The scene retains two lanes, chatbot first, and one permissions boundary.

    v4.4.6 rebuilt the scene as two flow cards. The shared-request node and the four ap-steps went
    with the old layout; what has to survive is the comparison itself and the single boundary that
    makes every capability conditional.
    """
    fx = guide_text[guide_text.index('id="page-foundations"'): guide_text.index('id="page-training"')]
    assert "fx-chatbot-agent" not in fx, "the separate comparison scene must not come back"
    agent = re.search(r'<section class="fx-scene[^"]*" id="fx-agent-platform"[\s\S]*?</section>', fx).group(0)
    # two lanes, chatbot first, and the boundary that makes the capability conditional
    assert agent.index('data-phase3-node="chatbot-handoff"') < agent.index('data-phase3-node="agent-handoff"')
    assert agent.count('data-grammar="boundary"') == 1
    assert agent.count('class="ap2-card"') == 2, "two lanes expected"
    assert "conditional" in agent and "unbidden" in agent, "the conditional grammar must survive"
    # the boundary marks the half of the key whose actions can change the work
    gated = agent[agent.index('data-grammar="boundary"'):]
    assert gated.count("<li") >= 4, "the boundary must mark the gated action set"
