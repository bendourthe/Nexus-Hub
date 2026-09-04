"""v4.4.5 Phase 5 -- the Models scene on the mockup's eight-stage spine.

The operator supplied an eight-stage mockup and named four fixes. Three of the four are
properties that can only be checked by measurement, and each assertion here exists because the
mockup fails it:

  * **No tab switching.** The mockup hides three prompt kinds behind one `role="tablist"` and
    three output kinds behind another. A reader comparing three things cannot compare them one
    at a time. Asserted as: no tab role in the scene, and all three modality tiers painted at
    once.

  * **A legible stage 07.** The mockup rings four labels around a core by absolute offset and
    draws the arrows in a separate fixed viewBox. Two unrelated coordinate systems cannot be
    nudged into agreement, so the passes are a grid here. Asserted as: no pass box overlaps
    another, at five widths. This is the assertion that would have caught the mockup.

  * **Nothing waiting to be operated.** Its `<select>`, `<textarea>`, effort buttons, and run
    button are static content here.

The stage spine itself is asserted in document order, because the order IS the teaching: two
stages happen once and long before, three happen when a request arrives, two happen inside the
model, and one comes back out.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIDTHS = (1440, 1024, 720, 480, 320)
STAGES = (
    ("01", "Train"),
    ("02", "Release"),
    ("03", "Select"),
    ("04", "Prompt"),
    ("05", "Tokenize"),
    ("06", "Predict"),
    ("07", "Reason"),
    ("08", "Produce"),
)


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
def guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


def _scene(browser, width: int = 1440):
    ctx = browser.new_context(viewport={"width": width, "height": 1000})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.locator("#fx-model-lifecycle").scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    return ctx, page


def test_the_eight_stages_read_in_order(guide_text: str) -> None:
    """The order is the teaching: prepared once, then activated per request."""
    start = guide_text.index('id="fx-model-lifecycle"')
    scene = guide_text[start : guide_text.index("</section>", start)]
    positions = []
    for number, name in STAGES:
        needle = f'data-mx-stage="{number}"'
        assert needle in scene, f"stage {number} ({name}) is missing"
        assert f"<b>{name}</b>" in scene, f"stage {number} is not named {name}"
        positions.append(scene.index(needle))
    assert positions == sorted(positions), f"the stages are out of order: {positions}"
    # The provider region must still come strictly before the request region: a prompt never
    # retrains a model, and reading the two the other way round is the misconception.
    assert scene.index('data-region="provider"') < scene.index('data-region="user"')


def test_nothing_in_the_scene_waits_to_be_operated(guide_text: str) -> None:
    start = guide_text.index('id="fx-model-lifecycle"')
    scene = guide_text[start : guide_text.index("</section>", start)]
    for banned in ('role="tablist"', 'role="tab"', "<textarea", "<select", "<button"):
        assert banned not in scene, f"the mockup's {banned} came along for the ride"


def test_all_three_modality_tiers_are_visible_at_once(playwright_mod) -> None:
    """The mockup showed one at a time behind tabs. Three things cannot be compared serially."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const tiers = [...document.querySelectorAll('#fx-model-lifecycle .mx-tier')];
                    return tiers.map(t => {
                      const r = t.getBoundingClientRect();
                      return { tag: t.querySelector('.mx-tier-tag').textContent.trim(),
                               painted: r.width > 40 && r.height > 40,
                               hidden: t.hasAttribute('hidden') || t.offsetParent === null };
                    });
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert len(data) == 3, data
    assert all(t["painted"] and not t["hidden"] for t in data), data
    assert [t["tag"] for t in data] == ["Text", "Multimodal", "Omni"], data


def test_no_reasoning_pass_overlaps_another(playwright_mod) -> None:
    """The assertion that would have caught the mockup's stage 07.

    Its version placed four labels around a ring by absolute offset and drew the arrows in a
    separate fixed viewBox, so the labels collided with each other and with the arrowheads at
    every width but the authored one. A grid cannot reach that state, and this measures it
    rather than trusting it.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in WIDTHS:
                ctx, page = _scene(browser, width)
                overlaps = page.evaluate(
                    """() => {
                        const boxes = [...document.querySelectorAll('#fx-model-lifecycle .mx-passes li')]
                          .map(li => li.getBoundingClientRect());
                        const bad = [];
                        for (let i = 0; i < boxes.length; i++)
                          for (let j = i + 1; j < boxes.length; j++) {
                            const a = boxes[i], b = boxes[j];
                            const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
                            const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
                            if (w > 1 && h > 1) bad.push([i, j, Math.round(w), Math.round(h)]);
                          }
                        return { count: boxes.length, bad };
                    }"""
                )
                ctx.close()
                assert overlaps["count"] == 4, f"{width}: {overlaps['count']} passes, expected 4"
                assert not overlaps["bad"], f"{width}: passes overlap {overlaps['bad']}"
        finally:
            browser.close()


def test_the_prediction_panel_shows_scored_candidates_with_a_caveat(playwright_mod) -> None:
    """Next-token prediction is the mechanism the whole scene rests on, so it is shown."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const rows = [...document.querySelectorAll('#fx-model-lifecycle .mx-prob-row')];
                    const scene = document.querySelector('#fx-model-lifecycle').textContent.toLowerCase();
                    return {
                      widths: rows.map(r => r.querySelector('.mx-prob-bar span')
                                .getBoundingClientRect().width),
                      top: rows[0] ? rows[0].classList.contains('mx-prob-row--top') : false,
                      caveat: scene.includes('illustrative, not measured'),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert len(data["widths"]) == 3, data
    assert data["widths"] == sorted(data["widths"], reverse=True), (
        f"the bars must fall with the scores: {data['widths']}"
    )
    assert data["top"], "the most likely candidate must be marked"
    assert data["caveat"], "invented percentages must say they are illustrative"


def test_the_scene_does_not_overflow_at_any_width(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in WIDTHS:
                ctx, page = _scene(browser, width)
                over = page.evaluate(
                    """() => { const s = document.querySelector('#fx-model-lifecycle');
                        return Math.round(s.scrollWidth - s.clientWidth); }"""
                )
                ctx.close()
                assert over <= 0, f"{width}: the Models scene overflows by {over}px"
        finally:
            browser.close()
