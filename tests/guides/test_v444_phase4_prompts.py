"""v4.4.4 Phase 4 gates: the vague prompt beside its flaws, the engineered one full width.

The old layout put both prompts in a three-column grid with a sideways arrow between them, which in
a full-width scene left the arrow pointing at empty space. These tests assert the shape the review
asked for: flaws BESIDE the vague prompt, a downward connector, and the engineered prompt spanning
the diagram so its four labelled parts fit one row. The marker style is asserted too, because
"quieter" is measurable: a tint and an underline rather than a ring.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
# v4.7.0: the guide renamed the first part from "query" to "request"; the markup and
# the legend now carry one vocabulary, so the expectation follows the shipped names.
PARTS = ("request", "context", "goal", "format")


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


def _scene(browser, width: int = 1440, **ctx_kw):
    ctx = browser.new_context(viewport={"width": width, "height": 1000}, **ctx_kw)
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.locator("#fx-prompts").scroll_into_view_if_needed()
    page.wait_for_timeout(260)
    return ctx, page


def test_the_flaws_sit_under_the_vague_prompt_in_a_grid(playwright_mod) -> None:
    """v4.4.5 inverted the v4.4.4 arrangement, on the review's instruction.

    v4.4.4 put the flaws BESIDE the prompt because the round before that had them stacked
    under a sideways arrow pointing into empty space. The next round asked for the vague
    prompt on one full-width line with the flaws in a 2x2 grid below it, which is neither
    of the previous two shapes. The beside-assertion is inverted rather than deleted, and
    the grid is measured as two rows of two rather than described.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const box = document.querySelector('#fx-prompts .pe-box').getBoundingClientRect();
                    const flaws = [...document.querySelectorAll('#fx-prompts .pe-flaws li')];
                    const first = flaws[0].getBoundingClientRect();
                    const cross = getComputedStyle(flaws[0], '::before');
                    return {
                      count: flaws.length,
                      texts: flaws.map(l => l.textContent.trim()),
                      below: first.top >= box.bottom - 1,
                      rows: new Set(flaws.map(l => Math.round(l.getBoundingClientRect().top))).size,
                      cols: new Set(flaws.map(l => Math.round(l.getBoundingClientRect().left))).size,
                      spansBox: Math.abs(box.width - document.querySelector('#fx-prompts .pe').getBoundingClientRect().width) <= 1,
                      crossWidth: parseFloat(cross.width),
                      crossColor: cross.backgroundColor,
                      redish: getComputedStyle(document.documentElement).getPropertyValue('--red').trim(),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["count"] == 4, data["texts"]
    assert data["below"], "the flaws must sit under the prompt, not beside it"
    assert data["spansBox"], "the vague prompt must take a full-width row of its own"
    assert data["rows"] == 2 and data["cols"] == 2, (
        f"the four flaws must read as a 2x2 grid, not {data['rows']}x{data['cols']}"
    )
    assert data["crossWidth"] >= 8, f"each flaw needs a visible mark: {data}"
    for expected in ("No request", "No context", "No goal", "No format"):
        assert any(t.startswith(expected) for t in data["texts"]), (expected, data["texts"])


def test_the_engineered_prompt_uses_the_whole_diagram(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(
                """() => {
                    const wrap = document.querySelector('#fx-prompts .pe');
                    const pre = document.querySelector('#fx-prompts .pe-precise');
                    const vague = document.querySelector('#fx-prompts .pe-vague');
                    const tip = document.querySelector('#fx-prompts .pe-tip');
                    const legend = document.querySelector('#fx-prompts .ann-legend');
                    return {
                      fill: +(pre.getBoundingClientRect().width / wrap.getBoundingClientRect().width).toFixed(3),
                      below: pre.getBoundingClientRect().top >= vague.getBoundingClientRect().bottom - 1,
                      tipBetween: tip.getBoundingClientRect().top >= vague.getBoundingClientRect().bottom - 1
                                  && tip.getBoundingClientRect().bottom <= pre.getBoundingClientRect().top + 1,
                      pointsDown: parseFloat(getComputedStyle(tip).borderTopWidth) >= 10,
                      legendColumns: getComputedStyle(legend).gridTemplateColumns.trim().split(/\\s+/).length,
                      legendRows: new Set([...legend.querySelectorAll('.ann-legend-row')]
                                    .map(r => Math.round(r.getBoundingClientRect().top))).size,
                      parts: [...document.querySelectorAll('#fx-ann-prompt .ann')].map(m => m.dataset.part),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["fill"] >= 0.98, f"the engineered prompt fills only {data['fill']} of the diagram"
    assert data["below"], "it must sit below the vague prompt, not beside it"
    assert data["tipBetween"] and data["pointsDown"], "a downward connector must sit between them"
    assert data["parts"] == list(PARTS), data["parts"]
    assert data["legendColumns"] == 4, f"four parts want four tracks, not {data['legendColumns']}"
    assert data["legendRows"] == 1, f"the four parts should read as one row at 1440: {data}"


def test_the_active_marker_is_quiet(playwright_mod) -> None:
    """A ring around a phrase reads as a button; a tint plus an underline reads as a highlight."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            page.wait_for_function(
                "() => { const s = window.NexusSeq.state(document.getElementById('fx-ann-prompt'));"
                " return s && s.step >= 1; }"
            )
            data = page.evaluate(
                """() => {
                    const on = document.querySelector('#fx-ann-prompt .ann.is-on');
                    if (!on) return null;
                    const cs = getComputedStyle(on);
                    return { shadow: cs.boxShadow, hasInset: cs.boxShadow.includes('inset'),
                             decoration: cs.textDecorationLine,
                             opacity: parseFloat(cs.opacity) };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data, "no marker was lit"
    # v4.7.0: the rule is that a marker reads as a highlight, never as a button. The guide
    # now draws the underline with text-decoration instead of an inset shadow, so the check
    # follows the intent rather than the mechanism: an underline by either means is fine, an
    # OUTSET ring is not.
    underlined = data["hasInset"] or "underline" in data["decoration"]
    assert underlined, f"the marker must underline rather than ring: {data}"
    assert data["shadow"] == "none" or data["hasInset"], (
        f"an outset ring reads as a button: {data['shadow']}"
    )
    assert data["opacity"] == 1, "a marker must never signal state by fading its text"


def test_the_downward_connector_stops_under_reduced_motion(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser, reduced_motion="reduce")
            name = page.evaluate(
                "() => getComputedStyle(document.querySelector('#fx-prompts .pe-tip')).animationName"
            )
            ctx.close()
        finally:
            browser.close()
    assert name == "none", f"the connector keeps animating under reduced motion: {name}"
