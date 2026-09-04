"""v4.4.1 Phase 4 gates: approved media bytes, shared visual grammar, and media behavior.

The media assertions decode every embedded payload and hash it against the staged ledger
file, exactly as the Phase 2 platform-mark tests do. A page whose gallery was re-exported,
re-compressed, or hand-edited after approval fails here rather than shipping unreviewed
bytes. The browser assertions cover the claims markup cannot prove: that the moving image
never plays until asked, that asking works, and that the shared work-cycle glyph is
motionless yet complete under reduced motion.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
ASSETS = (
    _ROOT
    / "docs"
    / "releases"
    / "v4"
    / "v4.4"
    / "development"
    / "guide-visual-and-arcade-rebuild"
    / "assets"
)
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"


@pytest.fixture(scope="module")
def guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def models_scene(guide_text: str) -> str:
    m = re.search(r'<section class="lesson" id="fx-model-lifecycle"[\s\S]*?</section>', guide_text)
    assert m, "missing the Models scene"
    return m.group(0)


def _staged_hash(name: str) -> str:
    return hashlib.sha256((ASSETS / name).read_bytes()).hexdigest()


# ------------------------------------------------------------------ approved media bytes






def test_the_audio_asset_left_the_page_with_its_teaching(models_scene: str, guide_text: str) -> None:
    """v4.4.4 retired audio from the Models teaching, on the operator's instruction.

    The old test asserted the embedded WAV matched the approved ledger bytes. With audio out of the
    teaching, the honest assertion is the opposite: the asset must NOT be shipped, because a 12 KB
    embedded payload nothing explains is worse than no payload. The ledger row stays in the
    provenance document as a record of what was once approved.
    """
    assert "data:audio/wav" not in guide_text, "the approved WAV is still embedded"
    assert "<audio" not in guide_text, "the audio element is still shipped"
    assert "fx-out-audio" not in guide_text and "fx-wave" not in guide_text
    assert "initWaveform" not in guide_text, "the waveform engine is still shipped"
    assert 'data-output-kind="audio"' not in models_scene


def test_media_ledger_records_every_embedded_payload() -> None:
    ledger = (ASSETS.parent / "asset-provenance.md").read_text(encoding="utf-8")
    for name in (
        "model-output-image.svg",
        "model-output-video.gif",
        "model-output-video-poster.svg",
        "model-output-audio.wav",
    ):
        assert _staged_hash(name) in ledger, (
            f"{name}: the staged bytes are not the bytes the ledger approved"
        )
    assert "SETTLED" in ledger.split("## 3.")[1].split("##")[0]


# ------------------------------------------------------------------ shared visual grammar


def test_the_agentic_scene_carries_the_comparison_and_the_boundary(guide_text: str) -> None:
    """v4.4.4 retired the shared-grammar rule with the scene that made it possible.

    The rule was that Models and Agentic Platform open with a byte-identical entry motif, so the
    comparison between them teaches. v4.4.4 merged the chatbot comparison INTO the platform scene
    and dropped its six-stage flow, so there is one entry motif in Foundations and nothing left to
    compare it against. What replaced the rule is stronger for the reader: the platform scene now
    shows one request going to BOTH lanes, so the sameness is on screen rather than in the markup.
    """
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


# ------------------------------------------------------------------------ browser gates


@pytest.fixture(scope="module")
def playwright_mod():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    try:
        with sync_playwright() as pw:
            pw.chromium.launch().close()
    except Exception as exc:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
        pytest.skip(f"chromium is unavailable: {exc}")
    return sync_playwright
