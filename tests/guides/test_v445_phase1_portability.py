"""v4.4.5 Phase 1 -- the portability figure is readable at rest.

The third review round asked for four things on this one figure, and each is a measurement
rather than a description: nothing is revealed in steps, every platform carries its own mark,
every connector triangle sits on the centre of its own box, and the mid-task strip uses the
width the figure already had.

The centring assertion is the one worth keeping. A flex row with percentage margins LOOKED
centred at the width it was authored for and drifted at every other width, because its spacing
was a function of its own content rather than of the grid below it. Sharing the track
definition is what makes the property true at every width, so the test measures it at five.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
PLATFORMS = ("Claude Code", "Codex", "Cursor", "Antigravity")


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

WIDTHS = (1440, 1024, 720, 480, 320)

PROBE = """() => {
  const fig = document.querySelector('#nhg-commands .ph');
  const boxes = [...fig.querySelectorAll('.ph-src, .ph-target, .ph-switch')];
  const lanes = [...fig.querySelectorAll('.ph-lane')];
  const live = lanes.filter(l => l.getBoundingClientRect().width > 0);
  const targets = [...fig.querySelectorAll('.ph-target')];
  const fan = fig.querySelector('.ph-fan').getBoundingClientRect();
  const anchors = live.length === targets.length
    ? targets.map(t => t.getBoundingClientRect()) : [fan];
  const sw = fig.querySelector('.ph-switch');
  const cs = getComputedStyle(sw);
  const inner = sw.getBoundingClientRect().width
    - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)
    - parseFloat(cs.borderLeftWidth) - parseFloat(cs.borderRightWidth);
  return {
    faded: boxes.filter(b => parseFloat(getComputedStyle(b).opacity) < 0.99).length,
    marks: targets.map(t => {
      const svg = t.querySelector('.ph-mark svg');
      if (!svg) return null;
      const r = svg.getBoundingClientRect();
      return r.width > 8 && r.height > 8;
    }),
    offsets: live.map((l, i) => {
      const lr = l.getBoundingClientRect(), a = anchors[i] || fan;
      return Math.abs((lr.left + lr.width / 2) - (a.left + a.width / 2));
    }),
    runWidth: Math.round(fig.querySelector('.ph-run').getBoundingClientRect().width),
    innerWidth: Math.round(inner),
    dots: fig.querySelectorAll('.ph-dot').length,
    overflow: Math.round(fig.scrollWidth - fig.clientWidth),
  };
}"""


def _probe(browser, width, reduced=False):
    kwargs = {"viewport": {"width": width, "height": 900}}
    if reduced:
        kwargs["reduced_motion"] = "reduce"
    ctx = browser.new_context(**kwargs)
    page = ctx.new_page()
    page.goto(GUIDE.as_uri())
    page.wait_for_timeout(350)
    page.locator("#nhg-commands").scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    data = page.evaluate(PROBE)
    ctx.close()
    return data


def test_no_box_is_ever_hidden_and_nothing_overflows(playwright_mod) -> None:
    """The review's complaint was legibility, so the figure has to be whole at first paint."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in WIDTHS:
                data = _probe(browser, width)
                assert data["faded"] == 0, f"{width}: {data['faded']} boxes below full opacity"
                assert data["overflow"] <= 0, f"{width}: overflows by {data['overflow']}px"
        finally:
            browser.close()


def test_every_platform_carries_its_mark(playwright_mod) -> None:
    """A mark that is present in the markup but paints nothing is not a logo.

    This is measured as a painted box rather than as an element, because hoisting the marks
    into shared symbols produced exactly that failure: the Gemini artwork was in the document,
    referenced correctly, and rendered blank, because a <use> clone cannot resolve the mask it
    carries. It stays inline for that reason.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            data = _probe(browser, 1440)
        finally:
            browser.close()
    assert len(data["marks"]) == 4, data["marks"]
    assert all(data["marks"]), f"a platform mark did not paint: {data['marks']}"


def test_each_triangle_sits_on_the_centre_of_its_own_box(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in WIDTHS:
                data = _probe(browser, width)
                worst = max(data["offsets"])
                assert worst <= 2, f"{width}: a triangle is {worst:.1f}px off centre"
        finally:
            browser.close()


def test_the_mid_task_strip_uses_the_width_it_has(playwright_mod) -> None:
    """It was a left-packed row inside a full-width box, so most of the box was empty."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for width in (1440, 1024):
                data = _probe(browser, width)
                assert data["runWidth"] >= data["innerWidth"] - 2, (
                    f"{width}: strip {data['runWidth']}px inside {data['innerWidth']}px"
                )
        finally:
            browser.close()


def test_connectors_have_no_dots_with_either_motion_preference(playwright_mod) -> None:
    """The distribution lines stay static with either motion preference."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            normal = _probe(browser, 1440)
            reduced = _probe(browser, 1440, reduced=True)
        finally:
            browser.close()
    assert normal["dots"] == 0
    assert reduced["dots"] == 0
    assert reduced["faded"] == 0, "reduced motion must not hide a box"
