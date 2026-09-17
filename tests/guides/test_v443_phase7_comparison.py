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
  const card = sel => document.querySelector('#fx-agent-platform .ap2-card[data-lane=' + sel + ']');
  const read = sel => {
    const c = card(sel), svg = c.querySelector('.ap2-svg');
    return {
      lane: sel,
      node: c.querySelector('.ap2-leaves').dataset.phase3Node,
      tracks: svg.querySelectorAll('.ml-lane-track').length,
      nodes: svg.querySelectorAll('.ml-nd').length,
      ends: [...svg.querySelectorAll('.ml-endlab')].map(t => t.textContent.trim()),
      bounds: c.querySelectorAll('[data-grammar=boundary]').length,
      trails: svg.querySelectorAll('.ml-lane-trail').length,
      chip: c.querySelector('.ap2-leaves').textContent.trim(),
    };
  };
  return { lanes: [read('chat'), read('agent')] };
}"""


def test_both_lanes_draw_the_same_kind_of_flow(playwright_mod) -> None:
    """v4.4.6 draws both lanes as paths, in the reasoning figure's grammar.

    The argument has not moved since this file was written: the lanes must be drawn the SAME way,
    so the only thing a reader compares is how far each path goes and how it branches. A rebuild
    that gave each lane a different KIND of diagram would look tidy and teach nothing.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            data = page.evaluate(LANES)
            ctx.close()
        finally:
            browser.close()
    chat, agent = data["lanes"]
    assert [lane["node"] for lane in data["lanes"]] == ["chatbot-handoff", "agent-handoff"], data["lanes"]
    for lane in data["lanes"]:
        assert lane["tracks"] >= 1, lane
        assert lane["trails"] >= 1, lane
        assert lane["nodes"] >= 2, lane
        assert lane["ends"][0] == "request", lane["ends"]
    # both start from a request; only the agentic side fans into more than one path
    assert agent["trails"] > chat["trails"], (chat["trails"], agent["trails"])


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
    # the chatbot platform stops at a response and the person finishes the job;
    # the agentic one carries on to a report of its own
    assert "response" in chat["ends"], chat["ends"]
    assert chat["ends"][-1] == "task complete", chat["ends"]
    assert agent["ends"][-1] == "report", agent["ends"]
    # only the agentic lane branches, and neither lane carries the boundary now
    # that it lives on the shared key below both of them
    assert chat["bounds"] == 0 and agent["bounds"] == 0, (chat["bounds"], agent["bounds"])
    assert agent["trails"] > chat["trails"], (chat["trails"], agent["trails"])
    # and the chatbot lane says plainly that it does not act
    assert "no actions" in chat["chip"].lower(), chat["chip"]
    assert "take actions" in agent["chip"].lower(), agent["chip"]


def test_the_lane_chips_keep_full_text_contrast(playwright_mod) -> None:
    """A state is never signalled by dimming text below AA (BG-13, BG-14).

    The chatbot lane's "takes no actions" claim moved from a list row into the lane chip, so the
    contrast rule moves with it.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser)
            ratio = page.evaluate(
                """() => {
                  const el = document.querySelector('#fx-agent-platform .ap2-card[data-lane=chat] .ap2-leaves');
                  const rgb = s => s.match(/[0-9.]+/g).slice(0, 3).map(Number);
                  const lum = c => { const a = c.map(v => { v /= 255;
                    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
                    return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]; };
                  let bg = [0, 0, 0];
                  for (let n = el; n; n = n.parentElement) {
                    const c = getComputedStyle(n).backgroundColor;
                    if (c && c !== 'rgba(0, 0, 0, 0)') { bg = rgb(c); break; }
                  }
                  const fg = rgb(getComputedStyle(el).color);
                  const [x, y] = [lum(fg), lum(bg)];
                  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert ratio >= MIN_CONTRAST, f"the chatbot chip measures {ratio:.2f}, floor {MIN_CONTRAST}"

def test_the_flow_is_complete_without_motion(playwright_mod) -> None:
    """Under reduced motion the scene must show its finished state, not an empty one.

    The paths draw by animating stroke-dashoffset from 1 to 0, so a reader with motion disabled
    would otherwise be shown lanes with no paths in them at all.
    """
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _scene(browser, reduced_motion="reduce")
            data = page.evaluate(
                """() => {
                  const trails = [...document.querySelectorAll('#fx-agent-platform .ml-lane-trail')];
                  return { total: trails.length,
                           drawn: trails.filter(t => +t.getAttribute('stroke-dashoffset') <= 0.001).length,
                           hidden: trails.filter(t => {
                             const s = getComputedStyle(t);
                             return s.display === 'none' || +s.opacity === 0 || s.visibility === 'hidden';
                           }).length };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["total"] >= 5, data
    assert data["hidden"] == 0, f"{data['hidden']} paths are hidden without motion"
    assert data["drawn"] == data["total"], f"only {data['drawn']} of {data['total']} paths are drawn"
