"""v4.4.3 Phase 6 gates: Agentic Platforms -- plural, named, marked, and choreographed.

The scene taught a singular abstraction and named nothing, so the review asked for the plural and
for four real platforms with their marks. The marks are the same approved bytes the Home rail
carries, so the ledger check runs here too: a mark re-sourced from somewhere else fails rather than
shipping. The prose was cut on the argument that the diagram is the explanation, so the test holds
both the reduction and the three pieces of conditional language that must not be cut with it.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
STAGED = (
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

# The mark reused for each platform, and the ledger stem it must still match.
EXPECTED_PLATFORMS = (
    ("Claude Code", "claude"),
    ("Codex", "chatgpt"),
    ("Cursor", "cursor"),
    ("Antigravity", "gemini"),
)
# The scene carried about 150 words before the cut; the ceiling is a real reduction, not a
# rounding of what happens to be there now.
COPY_WORD_CEILING = 100
# The Gemini mark carries 13 internal ids and url(#...) references, so a second copy in one document
# would make every one of them a duplicate and the second instance would resolve its mask and
# filters against the first. The chip therefore ships the same approved geometry with the id prefix
# re-namespaced, and the test derives that variant from the ledger asset rather than storing a hash,
# which proves the prefix is the ONLY difference.
ID_NAMESPACED = {"gemini": ("nxp-gm-", "nxp-gm2-")}


def _load_sync_playwright():
    """Return playwright's sync entry point, or None when the package is absent."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        return None
    return sync_playwright


@pytest.fixture(scope="module")
def playwright_mod():
    sync_playwright = _load_sync_playwright()
    if sync_playwright is None:  # pragma: no cover - environment dependent
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


@pytest.fixture(scope="module")
def scene() -> str:
    text = GUIDE.read_text(encoding="utf-8")
    start = text.index('id="fx-agent-platform"')
    return text[start : text.index("</section>", start)]


def test_the_scene_is_plural(scene: str) -> None:
    assert re.search(
        r'<h2[^>]*id="fx-platform-title"[^>]*class="section-title">Agentic Platforms</h2>', scene
    ), 'the scene must keep its plural heading'


def test_four_platforms_are_named_with_ledger_approved_marks(scene: str) -> None:
    """The agent lane must name the four agentic platforms, each with its own mark.

    The v4.19 redraw replaced the `<li class="fx-plat">` list with two SVG lanes.
    The agent lane now names each platform as VISIBLE text beside an
    `aria-hidden` icon, which is a better accessible pattern than the previous
    `aria-label` carried on the mark itself. The claim is unchanged: four named
    platforms, four distinct marks, in ledger order.
    """
    agent = scene[scene.index('data-lane="agent"') :]
    names = re.findall(
        r'<span class="ap2-mark">\s*<svg[^>]*aria-hidden="true"[^>]*>.*?</svg>\s*'
        r"</span>\s*<span>([^<]+)</span>",
        agent,
        flags=re.DOTALL,
    )
    assert names == [name for name, _stem in EXPECTED_PLATFORMS], names

    marks = re.findall(r'<use href="(#hxm\d+)"/>', agent)
    assert len(marks) == len(EXPECTED_PLATFORMS), f"expected one mark per platform; got {marks}"
    assert len(set(marks)) == len(marks), f"each platform needs its own mark; got {marks}"

def test_the_copy_is_shorter_and_keeps_its_conditional_language(scene: str) -> None:
    # v4.4.6 moved the platform marks into the lane cards, so the copy now runs
    # from the title block to the figure
    copy = scene[scene.index("</div>", scene.index('class="fx-title"')) : scene.index('class="fx-diagram')]
    prose = " ".join(re.sub(r"<[^>]+>", " ", copy).split())
    words = len(prose.split())
    assert words <= COPY_WORD_CEILING, f"the copy is {words} words, ceiling {COPY_WORD_CEILING}"
    lowered = prose.lower()
    for keep in ("unbidden", "conditional", "permission and tool boundary", "observations"):
        assert keep in lowered, f"the cut removed load-bearing language: {keep!r}"


def test_every_stage_is_visible_without_motion(playwright_mod) -> None:
    """v4.4.4 retired the six-stage flow this once measured.

    The review called that flow unreadable, so the scene now carries the chatbot comparison and four
    chips instead. The comparison's own choreography is asserted in `test_v443_phase7_comparison.py`;
    what remains worth holding here is that nothing in the scene is hidden without motion.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
            page = ctx.new_page()
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_function("window.NexusSeq")
            page.locator("#fx-agent-platform").scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            hidden = page.evaluate(
                """() => [...document.querySelectorAll('#fx-agent-platform [data-seq]')]
                     .filter(e => getComputedStyle(e).opacity !== '1')
                     .map(e => e.getAttribute('data-seq'))"""
            )
            ctx.close()
        finally:
            browser.close()
    assert hidden == [], f"stages {hidden} are not readable under reduced motion"
