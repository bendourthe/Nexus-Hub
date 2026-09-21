"""Retained harness structure, choreography, reduced-motion and responsive-label gates."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIDTHS = (320, 420, 720, 721, 900, 1440)


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


def _open(browser, width: int = 1440, **ctx):
    context = browser.new_context(viewport={"width": width, "height": 900}, **ctx)
    page = context.new_page()
    requests: list[str] = []
    page.on("request", lambda r: requests.append(r.url) if r.url.startswith("http") else None)
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_function("window.NexusSeq")
    page.wait_for_timeout(200)
    return context, page, requests


def test_harness_shows_three_layers_in_order(playwright_mod) -> None:
    """v4.4.6 rebuilt the scene as three cards; the reveal choreography retired with the old figure.

    What the choreography protected was that the layers arrive in order and none of them is hidden.

    The scene is a nested graph now: the model is the innermost box, the platform harness wraps it
    and the Nexus Hub harness wraps that. DOM order is therefore outermost-first, and the reading
    order is carried by the numbering, 1 at the innermost box. Containment is a stronger claim than
    the left-to-right ordering this used to assert, so that is what it checks.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser)
        try:
            page.locator("#fx-harness").scroll_into_view_if_needed()
            page.wait_for_timeout(220)
            data = page.evaluate(
                """() => {
                    const cards = [...document.querySelectorAll('#fx-harness .hx-col')];
                    return { layers: cards.map(c => c.dataset.layer),
                             names: cards.map(c => c.querySelector('header b').textContent.trim()),
                             hidden: cards.filter(c => {
                               const s = getComputedStyle(c);
                               return s.display === 'none' || +s.opacity === 0;
                             }).length,
                             nested: cards[0].contains(cards[1]) && cards[1].contains(cards[2]) };
                }"""
            )
        finally:
            browser.close()
    assert data["layers"] == ["nexus", "platform", "model"], data["layers"]
    assert data["names"] == ["Nexus Hub harness", "Platform harness", "Model"], data["names"]
    assert data["hidden"] == 0, "no layer may be hidden"
    assert data["nested"], "each layer must be built around the one inside it"


def test_harness_is_complete_without_motion(playwright_mod) -> None:
    """Nothing in the scene may depend on an animation that never runs."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser, reduced_motion="reduce")
        try:
            page.locator("#fx-harness").scroll_into_view_if_needed()
            page.wait_for_timeout(220)
            shown = page.evaluate(
                """() => [...document.querySelectorAll('#fx-harness .hx-col, #fx-harness .hx-eq,"""
                """ #fx-harness .hx-span')].filter(e => {
                     const s = getComputedStyle(e);
                     return s.display !== 'none' && +s.opacity > 0 && s.visibility !== 'hidden';
                   }).length"""
            )
        finally:
            browser.close()
    assert shown == 5, shown


@pytest.mark.parametrize("width", WIDTHS)
def test_harness_text_stays_inside_its_own_box(playwright_mod, width: int) -> None:
    """The figure is HTML now, so the property is stronger and simpler: no label may spill out of
    the element that owns it. The old form inspected SVG text, which this figure no longer has, so
    it would have passed vacuously rather than failing honestly."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        _ctx, page, _req = _open(browser, width=width)
        try:
            page.locator("#fx-harness").scroll_into_view_if_needed()
            page.wait_for_timeout(220)
            bad = page.evaluate(
                """() => {
                    const out = [];
                    const fig = document.querySelector('#fx-harness .hx');
                    if (!fig) return ['the harness figure is missing'];
                    fig.querySelectorAll('*').forEach(el => {
                        if (el.children.length) return;
                        const box = el.getBoundingClientRect();
                        const range = document.createRange();
                        range.selectNodeContents(el);
                        const ink = range.getBoundingClientRect();
                        range.detach();
                        if (ink.width && (ink.right > box.right + 1.5 || ink.left < box.left - 1.5))
                            out.push((el.className.toString().split(' ')[0] || el.tagName) + ': ' + el.textContent.trim().slice(0, 40));
                    });
                    return out;
                }"""
            )
        finally:
            browser.close()
    assert not bad, f"harness text escapes its own box at {width}px: {bad}"
