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
    m = re.search(r'<span class="fx-out-media" data-media="image">(<svg[\s\S]*?</svg>)</span>', models_scene)
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
    motion = re.search(r'data-motion-src="data:image/gif;base64,([A-Za-z0-9+/=]+)"', tag)
    src = re.search(r' src="data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)"', tag)
    assert poster and motion and src
    assert src.group(1) == poster.group(1), "the resting src must be the poster, not the GIF"
    assert hashlib.sha256(base64.b64decode(poster.group(1))).hexdigest() == _staged_hash(
        "model-output-video-poster.svg"
    )
    assert hashlib.sha256(base64.b64decode(motion.group(1))).hexdigest() == _staged_hash(
        "model-output-video.gif"
    )
    assert re.search(r'alt="[^"]{20,}"', tag), "the moving image needs a substantive alt text"


def test_embedded_audio_matches_the_approved_asset(models_scene: str) -> None:
    m = re.search(r'<audio class="fx-out-audio"[^>]*src="data:audio/wav;base64,([A-Za-z0-9+/=]+)"', models_scene)
    assert m, "missing the audio output"
    assert hashlib.sha256(base64.b64decode(m.group(1))).hexdigest() == _staged_hash(
        "model-output-audio.wav"
    )
    tag = models_scene[m.start(): models_scene.index(">", m.start()) + 1]
    assert "controls" in tag and 'preload="none"' in tag and "autoplay" not in tag


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


def test_models_and_agentic_platform_share_visual_grammar(guide_text: str) -> None:
    """The comparison only teaches if the two scenes are the same picture up to the fork."""
    fx = guide_text[guide_text.index('id="page-foundations"'): guide_text.index('id="page-training"')]
    assert fx.count('data-grammar="entry"') == 2, "both scenes must open with the entry motif"
    assert fx.count('data-grammar="work-cycle"') == 2, "both scenes must share the cycle glyph"
    # The entry motif must be byte-identical between the scenes: same prompt, same kinds.
    entries = re.findall(r'<div class="fx-entry" data-grammar="entry">[\s\S]*?</div>\s*<div class="fx-ctx-plus"', fx)
    assert len(entries) == 2 and entries[0] == entries[1], (
        "the prompt/context entry cards must be identical in Models and Agentic Platform"
    )
    assert fx.count('data-agent-mission') == 3, "exactly three specialized missions"
    assert fx.count('data-grammar="boundary"') == 1
    # DOM order inside Agentic Platform: entry -> cycle -> missions -> boundary -> report.
    agent = re.search(r'<section class="fx-scene[^"]*" id="fx-agent-platform"[\s\S]*?</section>', fx).group(0)
    order = [agent.index(m) for m in (
        'data-grammar="entry"', 'data-grammar="work-cycle"', "data-agent-mission",
        'data-grammar="boundary"', 'data-stage="observations"', 'data-stage="report"',
    )]
    assert order == sorted(order), "the agentic flow must read in execution order"


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


def test_moving_image_plays_only_on_request(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_timeout(400)
            img = page.locator(".fx-out-motion")
            btn = page.locator("[data-media-toggle]")
            assert img.get_attribute("src").startswith("data:image/svg+xml"), (
                "the moving image must rest on its poster"
            )
            btn.scroll_into_view_if_needed()
            btn.click()
            assert img.get_attribute("src").startswith("data:image/gif"), (
                "clicking Play must swap in the approved GIF"
            )
            assert btn.get_attribute("aria-pressed") == "true"
            btn.click()
            assert img.get_attribute("src").startswith("data:image/svg+xml"), (
                "clicking again must restore the still poster"
            )
            assert btn.get_attribute("aria-pressed") == "false"
        finally:
            browser.close()


def test_work_cycle_is_static_and_complete_under_reduced_motion(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        try:
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_timeout(400)
            state = page.evaluate(
                """() => {
                    const svg = document.querySelector('#fx-model-lifecycle .fx-cycle svg');
                    svg.closest('.fx-scene').classList.add('live');
                    const cs = getComputedStyle(svg);
                    const label = svg.querySelector('text');
                    return {
                        animation: cs.animationName,
                        labelShown: getComputedStyle(label).display !== 'none',
                    };
                }"""
            )
        finally:
            browser.close()
    assert state["animation"] == "none", "the cycle must not spin under reduced motion"
    assert state["labelShown"], "the static cycle must still show its label"
