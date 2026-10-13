"""v4.13.11 WN-12-v41310: the slim rail's empty progress dots read clearly.

At 1280 px the page navigation is a slim rail of dots. An empty dot's ring is the only
thing that shows a section exists, so it is a non-text UI boundary (WCAG 1.4.11, 3:1).
The ring measured 3.20:1 in the light theme, legal but faint; it is now held to 4.5:1 in
both themes on both pages. Ratios use the WCAG 2 formula on canvas-resolved colours.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PAGES = {
    "guide": ROOT / "guides" / "website" / "nexus-hub-guide.html",
    "training": ROOT / "guides" / "website" / "training.html",
}
ROUTES = {"guide": "#foundations", "training": "#intro"}
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

RING = r"""() => { const cv = document.createElement('canvas'); cv.width = cv.height = 1;
  const g = cv.getContext('2d', {willReadFrequently: true});
  const rgba = c => { g.clearRect(0, 0, 1, 1); g.fillStyle = '#000'; g.fillStyle = c; g.fillRect(0, 0, 1, 1);
    const d = g.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const over = (t, b) => [0, 1, 2].map(i => t[i] * t[3] + b[i] * (1 - t[3])).concat([1]);
  const back = el => { let col = rgba(getComputedStyle(document.documentElement).backgroundColor); const ch = [];
    for (let p = el; p; p = p.parentElement) ch.push(p);
    for (const p of ch.reverse()) { const b = rgba(getComputedStyle(p).backgroundColor); if (b[3] > 0) col = over(b, col); }
    return col; };
  const lum = c => { const f = v => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const nav = document.querySelector('.pg-outline');
  const empty = [...nav.querySelectorAll('li:not(.is-current) .pg-outline-node')];
  return {layout: nav.className, ratios: empty.map(n => { const b = back(n.parentElement);
    const ring = over(rgba(getComputedStyle(n).borderTopColor), b); const x = lum(ring), y = lum(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); })}; }"""


@pytest.fixture(scope="module")
def chromium():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:  # noqa: BLE001 - pragma: no cover, environment dependent
            if REQUIRE_RENDER:
                pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
            pytest.skip(f"chromium is unavailable: {exc}")
        yield browser
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("page_key", ["guide", "training"])
def test_an_empty_rail_dot_ring_reaches_4_5_to_1(chromium, page_key: str, theme: str) -> None:
    ctx = chromium.new_context(viewport={"width": 1280, "height": 900}, color_scheme=theme)
    try:
        page = ctx.new_page()
        page.add_init_script(f"try {{ localStorage.setItem('portfolio-theme', '{theme}'); }} catch (e) {{}}")
        page.goto(PAGES[page_key].as_uri() + ROUTES[page_key])
        page.wait_for_timeout(800)
        data = page.evaluate(RING)
    finally:
        ctx.close()
    assert "pg-outline--rail" in data["layout"], data["layout"]
    assert data["ratios"], "no empty rail dot was found"
    assert min(data["ratios"]) >= 4.5, data
