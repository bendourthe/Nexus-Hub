"""v4.4.3 Phase 2 gates: the guardrails figure, rebuilt so a label cannot escape its box.

The v4.4.2 figure drew every label as SVG text at a fixed size inside a viewBox that scaled with
the column, so a label wider than its chip escaped the chip and two hook names collided with the
rings. These tests assert the property that failure violated, at four widths: each leaf's glyph run
stays inside the element that owns it, and nothing in the figure leaves the figure. The absence of
SVG text is asserted directly, because that is the construction that made the defect possible.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
WIDTHS = (360, 700, 1024, 1440)


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


def _figure(browser, width: int):
    ctx = browser.new_context(viewport={"width": width, "height": 1000})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + "#home")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.locator("#nhg-guard-fig").scroll_into_view_if_needed()
    page.wait_for_timeout(260)
    return ctx, page


GEOMETRY = """() => {
  const fig = document.querySelector('#nhg-guard-fig');
  const fr = fig.getBoundingClientRect();
  const outFig = [], textOut = [];
  fig.querySelectorAll('*').forEach(el => {
    const r = el.getBoundingClientRect();
    if (!r.width) return;
    const name = (el.className.toString().trim().split(/\\s+/)[0]) || el.tagName;
    if (r.left < fr.left - 1 || r.right > fr.right + 1) outFig.push(name);
    if (el.children.length === 0) {
      const range = document.createRange(); range.selectNodeContents(el);
      const ink = range.getBoundingClientRect(); range.detach();
      if (ink.width && (ink.right > r.right + 1.5 || ink.left < r.left - 1.5)) textOut.push(name);
    }
  });
  const box = sel => { const e = fig.querySelector(sel); return e && e.getBoundingClientRect(); };
  const nexus = box('.gf-ring--nexus'), platform = box('.gf-ring--platform'), core = box('.gf-core');
  const inside = (a, b) => a.left >= b.left - 1 && a.right <= b.right + 1 && a.top >= b.top - 1 && a.bottom <= b.bottom + 1;
  return {
    outFig, textOut,
    nested: inside(platform, nexus) && inside(core, platform),
    svg: fig.querySelectorAll('svg').length,
    logo: fig.querySelector('.gf-logo use')?.getAttribute('href'),
    svgText: fig.querySelectorAll('svg text, svg tspan').length,
  };
}"""


@pytest.mark.parametrize("width", WIDTHS)
def test_no_guardrails_label_escapes_its_box(playwright_mod, width: int) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _figure(browser, width)
            data = page.evaluate(GEOMETRY)
            ctx.close()
        finally:
            browser.close()
    assert not data["outFig"], f"at {width}px these left the figure: {data['outFig']}"
    assert not data["textOut"], f"at {width}px this text left its own box: {data['textOut']}"
    assert data["nested"], f"the rings are not nested at {width}px"


def test_the_figure_carries_no_svg_text(playwright_mod) -> None:
    """The construction that caused the defect is gone, not merely tuned."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _figure(browser, 1440)
            data = page.evaluate(GEOMETRY)
            ctx.close()
        finally:
            browser.close()
    assert data["svgText"] == 0, "labels are SVG text again, which cannot be contained by a chip"
    assert data["svg"] == 6 and data["logo"] == "#nexus-mark", "the Nexus logo, four platform marks, and neural network must render"


def test_every_attempt_shows_both_rings_and_a_result(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _figure(browser, 1440)
            lanes = page.evaluate(
                """() => [...document.querySelectorAll('#nhg-guard-fig .gf-lane')].map(l => ({
                    action: l.children[0].textContent.trim(),
                    platform: l.children[1].textContent.trim(),
                    nexus: l.children[2].textContent.trim(),
                    result: l.children[3].textContent.trim(),
                    hook: (l.querySelector('.gf-cell--stop b') || {textContent: null}).textContent,
                    stopped: l.children[2].classList.contains('gf-cell--stop'),
                }))"""
            )
            ctx.close()
        finally:
            browser.close()
    assert len(lanes) == 3, lanes
    # every lane is permitted at the prompt: that is the whole point of the comparison
    for lane in lanes:
        assert "allowed" in lane["platform"].lower(), lane
        assert lane["action"] and lane["result"], lane
    allowed = [lane for lane in lanes if not lane["stopped"]]
    blocked = [lane for lane in lanes if lane["stopped"]]
    assert len(allowed) == 1 and len(blocked) == 2, lanes
    assert allowed[0]["result"].lower() == "runs", allowed
    for lane in blocked:
        assert lane["result"].lower() == "blocked", lane
        assert lane["hook"], f"a blocked attempt must name the hook that blocked it: {lane}"
