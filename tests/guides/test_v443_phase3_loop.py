"""v4.4.3 Phase 3 gates: the command loop fills its column, with triangular heads.

The review's complaint was that the loop occupied roughly two thirds of the content column and left
the rest empty, with arrows too faint to read. Widening the boxes alone would have been the wrong
fix, so the test holds both halves: the strip fills the column AND the type inside grew with it.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"


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


LOOP = """() => {
  const strip = document.querySelector('#nhg-loop');
  const host = strip.parentElement, hcs = getComputedStyle(host);
  const avail = host.clientWidth - parseFloat(hcs.paddingLeft) - parseFloat(hcs.paddingRight);
  const sr = strip.getBoundingClientRect();
  const steps = [...strip.querySelectorAll('.loop-step')].map(s => {
    const code = s.querySelector('code'), r = s.getBoundingClientRect();
    return { cmd: code.textContent.trim(), px: +parseFloat(getComputedStyle(code).fontSize).toFixed(1),
             notePx: +parseFloat(getComputedStyle(s.querySelector('span')).fontSize).toFixed(1),
             w: +r.width.toFixed(1), spill: +(r.right - sr.right).toFixed(1) };
  });
  const arrows = [...strip.querySelectorAll('.loop-arrow')].map(a => {
    const cs = getComputedStyle(a);
    return { text: a.textContent.trim(), left: parseFloat(cs.borderLeftWidth),
             top: parseFloat(cs.borderTopWidth), transform: cs.transform };
  });
  return { fill: +(sr.width / avail).toFixed(3), column: getComputedStyle(strip).flexDirection,
           steps, arrows, stepCount: steps.length };
}"""


def _loop(browser, width: int):
    ctx = browser.new_context(viewport={"width": width, "height": 1000})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#home")
    page.wait_for_function("window.NexusFit")
    page.locator("#nhg-loop").scroll_into_view_if_needed()
    page.wait_for_timeout(220)
    return ctx, page


@pytest.mark.parametrize("width,floor_px", ((1440, 20), (1100, 20), (1000, 16)))
def test_the_loop_fills_its_column_with_legible_boxes(playwright_mod, width: int, floor_px: int) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _loop(browser, width)
            data = page.evaluate(LOOP)
            ctx.close()
        finally:
            browser.close()
    assert data["stepCount"] == 6, data["steps"]
    assert data["fill"] >= 0.98, f"the loop fills only {data['fill']} of its column at {width}px"
    for step in data["steps"]:
        assert step["px"] >= floor_px, step
        assert step["notePx"] >= 13, step
        assert step["spill"] <= 1.0, step


def test_the_heads_are_triangles_not_glyphs(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _loop(browser, 1440)
            data = page.evaluate(LOOP)
            ctx.close()
        finally:
            browser.close()
    assert len(data["arrows"]) == 5, data["arrows"]
    for arrow in data["arrows"]:
        assert arrow["text"] == "", f"an arrow glyph is still printed beside the triangle: {arrow}"
        assert arrow["left"] >= 12, arrow
        assert arrow["top"] >= 8, arrow


def test_the_loop_stacks_and_rotates_its_heads_when_narrow(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _loop(browser, 760)
            data = page.evaluate(LOOP)
            ctx.close()
        finally:
            browser.close()
    assert data["column"] == "column", data["column"]
    for arrow in data["arrows"]:
        assert arrow["transform"] not in ("none", ""), f"a stacked head still points sideways: {arrow}"
    for step in data["steps"]:
        assert step["spill"] <= 1.0, step
