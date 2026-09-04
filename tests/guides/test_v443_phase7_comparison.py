"""v4.4.3 Phase 7 gates: chatbot versus agentic platforms, as an illustration of reach.

v4.4.4 merged this comparison INTO the Agentic Platforms scene, so every selector here moved with
it. The rules are unchanged: both lanes show the same two zones, only the reach differs, the
unreached zone keeps full text contrast, and the split is choreographed and complete without motion.

The scene was two columns of prose that asked the reader to hold four labelled sentences per lane
and compare them. The rebuild draws what actually differs: both lanes show the SAME two zones, and
only the reach changes. These tests assert that symmetry, because it is the whole argument -- a
rebuild that gave each lane different zones would look tidy and teach nothing.

The unreached zone is marked with a dashed edge and a full-contrast label. That is the v4.4.2
contrast rule (BG-13, BG-14) applied to a state marker: never signal a state by dimming text.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
MIN_CONTRAST = 4.5


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
    page.locator("#fx-agent-platform").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    return ctx, page


LANES = """() => {
  const lanes = [...document.querySelectorAll('#fx-agent-platform .fx-state')].map(a => ({
    lane: a.dataset.lane,
    node: a.dataset.phase3Node,
    zones: [...a.querySelectorAll('.cv-zone')].map(z => ({
      name: z.querySelector('.cv-zone-name').textContent.trim(),
      state: z.querySelector('.cv-zone-state').textContent.trim().toLowerCase(),
      reached: z.classList.contains('cv-zone--reached'),
      dashed: getComputedStyle(z).borderStyle === 'dashed',
      art: z.querySelectorAll('svg.cv-art').length,
      changes: [...z.querySelectorAll('.cv-changes li')].map(l => l.textContent.trim()),
    })),
    parts: [...a.querySelectorAll('.fx-part dt')].map(d => d.textContent.trim()),
  }));
  const shared = document.querySelectorAll('#fx-agent-platform [data-phase3-node="shared-request"]');
  return { lanes, shared: shared.length,
           sharedText: shared[0] ? shared[0].querySelector('p').textContent.trim() : null,
           tips: document.querySelectorAll('#fx-agent-platform .cv-tip').length,
           svgText: document.querySelectorAll('#fx-agent-platform svg text, #fx-agent-platform svg tspan').length };
}"""


def test_both_lanes_show_the_same_two_zones(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(LANES)
            ctx.close()
        finally:
            browser.close()
    assert data["shared"] == 1, "there must be exactly one shared request"
    assert "rate limiting" in data["sharedText"].lower(), data["sharedText"]
    assert data["tips"] == 2, "the shared request must visibly split into both lanes"
    assert data["svgText"] == 0, "the zone drawings must carry no SVG text"
    assert [lane["lane"] for lane in data["lanes"]] == ["chatbot", "agentic"], data["lanes"]
    assert [lane["node"] for lane in data["lanes"]] == ["chatbot-handoff", "agent-handoff"], data["lanes"]
    names = [[z["name"] for z in lane["zones"]] for lane in data["lanes"]]
    assert names[0] == names[1], f"the lanes must show the same zones to be comparable: {names}"
    assert len(names[0]) == 2, names
    for lane in data["lanes"]:
        assert lane["parts"] == ["Boundary", "Action", "Outcome", "Leaves behind"], lane["parts"]
        for zone in lane["zones"]:
            assert zone["art"] == 1, f"every zone needs its own drawing: {zone}"


def test_only_the_reach_differs_between_the_lanes(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(LANES)
            ctx.close()
        finally:
            browser.close()
    chat, agent = data["lanes"]
    assert [z["reached"] for z in chat["zones"]] == [True, False], chat["zones"]
    assert [z["reached"] for z in agent["zones"]] == [True, True], agent["zones"]
    unreached = chat["zones"][1]
    assert unreached["dashed"], "an unreached zone must be marked by its edge"
    assert unreached["state"] == "untouched", unreached
    assert "when permitted" in agent["zones"][1]["state"], agent["zones"][1]
    assert agent["zones"][1]["changes"], "the reached work surface must show what changed"
    assert not chat["zones"][1]["changes"], "the chatbot lane must not show work-surface changes"


def test_the_unreached_zone_keeps_full_text_contrast(playwright_mod) -> None:
    """State is signalled by the edge and the label, never by fading the words."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            worst = page.evaluate(
                """() => {
                  const lum = c => { const [r,g,b] = c.match(/[\\d.]+/g).slice(0,3).map(Number)
                      .map(v => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); });
                    return 0.2126*r + 0.7152*g + 0.0722*b; };
                  const bgOf = el => { let n = el; while (n && n !== document.documentElement) {
                      const c = getComputedStyle(n).backgroundColor;
                      if (c && !/rgba\\(0, 0, 0, 0\\)|transparent/.test(c)) return c; n = n.parentElement; }
                    return getComputedStyle(document.body).backgroundColor; };
                  let worst = 99;
                  document.querySelectorAll('#fx-agent-platform .cv-zone .cv-zone-name, #fx-agent-platform .cv-zone .cv-zone-state')
                    .forEach(el => { const cs = getComputedStyle(el);
                      if (parseFloat(cs.opacity) < 1) worst = 0;
                      const a = lum(cs.color), b = lum(bgOf(el));
                      const hi = Math.max(a,b), lo = Math.min(a,b);
                      worst = Math.min(worst, (hi + 0.05) / (lo + 0.05)); });
                  return +worst.toFixed(2);
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert worst >= MIN_CONTRAST, f"a zone label drops to {worst}:1, below {MIN_CONTRAST}:1"


def test_the_split_is_choreographed_and_complete_without_motion(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            page.wait_for_function(
                "() => { const s = window.NexusSeq.state(document.querySelector('#fx-agent-platform .fx-cv'));"
                " return s && s.step === s.total; }"
            )
            total = page.evaluate(
                "() => window.NexusSeq.state(document.querySelector('#fx-agent-platform .fx-cv')).total"
            )
            ctx.close()

            rctx, rpage = _scene(browser, reduced_motion="reduce")
            hidden = rpage.evaluate(
                """() => [...document.querySelectorAll('#fx-agent-platform .fx-cv [data-seq]')]
                     .filter(e => getComputedStyle(e).opacity !== '1').map(e => e.dataset.seq)"""
            )
            rctx.close()
        finally:
            browser.close()
    assert total == 4, f"expected four steps: the request, then three reaches; got {total}"
    assert hidden == [], f"steps {hidden} are unreadable under reduced motion"
