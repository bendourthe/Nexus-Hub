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
    m = re.search(r'<section class="fx-scene[^"]*" id="fx-model-lifecycle"[\s\S]*?</section>', guide_text)
    assert m, "missing the Models scene"
    return m.group(0)


def _staged_hash(name: str) -> str:
    return hashlib.sha256((ASSETS / name).read_bytes()).hexdigest()


# ------------------------------------------------------------------ approved media bytes


def test_embedded_image_matches_the_approved_asset(models_scene: str) -> None:
    # v4.4.4 moved the image into the multimodal tier, so the wrapper carries a second class.
    m = re.search(r'<span class="[^"]*fx-out-media" data-media="image">(<svg[\s\S]*?</svg>)</span>', models_scene)
    assert m, "the image output must inline the approved SVG verbatim"
    embedded = hashlib.sha256(m.group(1).encode("utf-8")).hexdigest()
    assert embedded == _staged_hash("model-output-image.svg"), (
        "the inline image no longer matches the approved ledger bytes"
    )


def test_embedded_gif_and_poster_match_the_approved_assets(models_scene: str) -> None:
    img = re.search(r'<img class="fx-out-motion"[^>]*>', models_scene)
    assert img, "missing the moving-image element"
    tag = img.group(0)
    poster = re.search(r'data-poster-src="data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)"', tag)
    src = re.search(r' src="data:image/gif;base64,([A-Za-z0-9+/=]+)"', tag)
    motion = src
    assert poster and src, tag[:200]
    # v4.4.3: the animation is the element's own src, so there is no second copy of the GIF and no
    # data-motion-src. The approved-bytes rule is unchanged: both assets still hash to the ledger.
    assert "data-motion-src" not in tag, "the GIF must appear once, as the src"
    assert src.group(1) != poster.group(1), "the src must be the animation, not the still"
    assert hashlib.sha256(base64.b64decode(poster.group(1))).hexdigest() == _staged_hash(
        "model-output-video-poster.svg"
    )
    assert hashlib.sha256(base64.b64decode(motion.group(1))).hexdigest() == _staged_hash(
        "model-output-video.gif"
    )
    assert re.search(r'alt="[^"]{20,}"', tag), "the moving image needs a substantive alt text"


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
    assert fx.count('data-grammar="entry"') == 1, "the entry motif belongs to the Models scene alone"
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


def test_moving_image_plays_unaided_and_stills_under_reduced_motion(playwright_mod) -> None:
    """v4.4.3 inverts the v4.4.1 rule, and keeps its accessibility half.

    The old rule was that motion never starts without a press. The review asked for the opposite,
    so the animation is the element's own src and no control exists. A reader who asks for reduced
    motion still gets the still frame, which is the half of the old rule that was about access
    rather than about asking.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_timeout(400)
            assert page.locator("[data-media-toggle]").count() == 0, "there is nothing to press"
            img = page.locator(".fx-out-motion")
            assert img.get_attribute("src").startswith("data:image/gif"), (
                "the moving image must play without being asked"
            )
            assert img.get_attribute("data-motion-state") == "playing"
            page.close()

            reduced = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            reduced.goto(GUIDE.as_uri() + "#foundations")
            reduced.wait_for_timeout(400)
            still = reduced.locator(".fx-out-motion")
            assert still.get_attribute("src").startswith("data:image/svg+xml"), (
                "reduced motion must show the still frame"
            )
            assert still.get_attribute("data-motion-state") == "still"
        finally:
            browser.close()


def test_inside_the_model_is_complete_under_reduced_motion(playwright_mod) -> None:
    """v4.4.4 replaced the three-step block with the token strip; the rule is unchanged.

    Whatever the scene uses to show what happens inside a model must be fully readable without
    motion, and the honesty caveat must survive the rebuild.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        try:
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_timeout(400)
            state = page.evaluate(
                """() => {
                    const pass = document.querySelector('#fx-model-lifecycle .fx-pass');
                    const chips = [...pass.querySelectorAll('.mx-tok-chip')];
                    const nodes = [...document.querySelectorAll('#fx-model-lifecycle .mx-node')];
                    return {
                        chips: chips.length,
                        nodes: nodes.length,
                        allVisible: [...chips, ...nodes].every(e => getComputedStyle(e).opacity === '1'
                                                                    && e.getBoundingClientRect().height > 0),
                        rings: document.querySelectorAll('#fx-model-lifecycle .fx-cycle').length,
                        note: pass.querySelector('.fx-pass-note').textContent.toLowerCase(),
                    };
                }"""
            )
        finally:
            browser.close()
    assert state["rings"] == 0, "the work-cycle ring must not come back"
    # v4.4.5 moved `.mx-lanes` OUT of `.fx-pass`. It had been a child, which meant
    # harvesting `.fx-pass` for one stage dragged the lanes into it and rendered them
    # twice. The nodes are still asserted, and still asserted visible under reduced
    # motion; they are just no longer reached through the token block.
    assert state["chips"] >= 6 and state["nodes"] >= 5, state
    assert state["allVisible"], state
    assert "not a transcript of hidden reasoning" in state["note"], (
        "the honesty caveat must survive the rebuild"
    )
