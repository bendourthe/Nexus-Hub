"""Retained cross-page heading bounds; superseded typography policies are registered in assertion-migration.json."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

PAGES = ("home", "foundations", "commands", "cheatsheets")
ALL_WIDTHS = (320, 420, 720, 900, 1440)
ONE_LINE_WIDTHS = (720, 900, 1440)
FIT_FLOOR = 14


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


def _page(browser, width: int, route: str):
    ctx = browser.new_context(viewport={"width": width, "height": 900})
    page = ctx.new_page()
    page.goto(GUIDE.as_uri() + f"#{route}")
    page.wait_for_function("window.NexusFit && window.NexusSeq")
    page.wait_for_timeout(180)
    return ctx, page


MEASURE = """() => {
  const rows = [];
  document.querySelectorAll('.page.active .section-title, .page.active .eyebrow')
    .forEach(el => {
      const cs = getComputedStyle(el);
      const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.2;
      const r = el.getBoundingClientRect();
      const host = el.parentElement, hcs = getComputedStyle(host);
      const avail = host.clientWidth - parseFloat(hcs.paddingLeft) - parseFloat(hcs.paddingRight);
      /* the glyph run, not the box: a capped box hides its own overflow */
      const range = document.createRange(); range.selectNodeContents(el);
      const ink = range.getBoundingClientRect().width; range.detach();
      rows.push({
        kind: el.classList.contains('section-title') ? 'title' : 'label',
        text: el.textContent.replace(/\\s+/g, ' ').trim().slice(0, 46),
        px: +parseFloat(cs.fontSize).toFixed(2),
        base: +parseFloat(el.getAttribute('data-fit-base')).toFixed(2),
        wrap: el.getAttribute('data-fit-wrap'),
        lines: Math.max(1, Math.round(r.height / lh)),
        spill: +(ink - avail).toFixed(1),
      });
    });
  return rows;
}"""






@pytest.mark.parametrize("width", ALL_WIDTHS)
def test_no_heading_spills_past_its_container(playwright_mod, width: int) -> None:
    """The absolute rule at every width: the glyph run stays inside the container that holds it."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        spills = {}
        try:
            for route in PAGES:
                ctx, page = _page(browser, width, route)
                rows = page.evaluate(MEASURE)
                spills[route] = [r for r in rows if r["spill"] > 1.5]
                for r in rows:
                    assert r["px"] >= FIT_FLOOR - 0.01, (width, route, r)
                ctx.close()
        finally:
            browser.close()
    assert not any(spills.values()), f"headings spill past their container at {width}px: {spills}"
