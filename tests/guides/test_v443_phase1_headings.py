"""v4.4.3 Phase 1 gates: one heading rule, comparison-grade table headers, and no second person.

The operator's review of the shipped v4.4.2 build asked for three things that are all measurable:
the segment label three times larger, the segment title half its size, and no title left wrapping.
A stylesheet cannot promise the third on its own, because a fixed size does not know its container,
so NexusFit measures and shrinks. These tests hold the rule where it matters (720px and wider, one
line always) and hold the floor where a single line is impossible, rather than pretending a 320px
viewport can carry a 33px heading on one line.

The second-person sweep is asserted over the static document, which is what the reader loads. Text
the Training simulation injects at runtime is out of this version's scope and is not claimed here.

v4.4.4 removed the Foundations scene subtitle from this measurement. It is no longer a heading: the
review inverted the pair so the scene NAME is the title and the descriptive phrase is a sentence
beneath it, which should wrap like prose rather than shrink to one line. Titles and Home labels are
still measured here; the new pair order is asserted in `test_v442_phase3_foundations.py`.
"""

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
FIT_FLOOR = 15
SECOND_PERSON = re.compile(r"\b(you|your|yours|yourself|yourselves|you're|you'll|you've|you'd)\b", re.I)


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


def test_label_is_tripled_and_title_is_halved(playwright_mod) -> None:
    """One token each: the label at three times 11px, the title at half the v4.4.2 65.3px."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _page(browser, 1440, "home")
            data = page.evaluate(
                """() => {
                    const eb = document.querySelector('#nhg-why .eyebrow');
                    const ti = document.querySelector('#nhg-why .section-title');
                    const root = getComputedStyle(document.documentElement);
                    return {
                        label: +parseFloat(eb.getAttribute('data-fit-base')).toFixed(2),
                        title: +parseFloat(ti.getAttribute('data-fit-base')).toFixed(2),
                        eyebrowToken: root.getPropertyValue('--eyebrow-scale').trim(),
                        titleToken: root.getPropertyValue('--title-scale').trim(),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    assert data["eyebrowToken"] == "3", data
    assert data["titleToken"] == "1.2", data
    assert data["label"] == pytest.approx(33, abs=0.6), data
    assert data["title"] == pytest.approx(65.28 / 2, abs=1.2), data


@pytest.mark.parametrize("width", ONE_LINE_WIDTHS)
def test_no_heading_wraps_from_720_upward(playwright_mod, width: int) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        wrapped = {}
        try:
            for route in PAGES:
                ctx, page = _page(browser, width, route)
                wrapped[route] = [r for r in page.evaluate(MEASURE) if r["lines"] > 1 or r["wrap"] != "nowrap"]
                ctx.close()
        finally:
            browser.close()
    assert not any(wrapped.values()), f"headings wrapped at {width}px: {wrapped}"


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
                    assert r["px"] <= r["base"] + 0.5, (width, route, r)
                ctx.close()
        finally:
            browser.close()
    assert not any(spills.values()), f"headings spill past their container at {width}px: {spills}"


def test_migration_table_headers_carry_the_comparison_grade(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            ctx, page = _page(browser, 1440, "home")
            data = page.evaluate(
                """() => {
                    const read = el => { const cs = getComputedStyle(el);
                      return {t: el.textContent.trim(), px: +parseFloat(cs.fontSize).toFixed(1),
                              weight: cs.fontWeight, upper: cs.textTransform, color: cs.color}; };
                    return {
                      th: [...document.querySelectorAll('.tbl-migrate th')].map(read),
                      without: read(document.querySelector('.cmp-side--without')),
                      with_: read(document.querySelector('.cmp-side--with')),
                    };
                }"""
            )
            ctx.close()
        finally:
            browser.close()
    th, without, with_ = data["th"], data["without"], data["with_"]
    assert len(th) == 3, th
    for cell in th:
        assert cell["px"] == without["px"], (cell, without)
        assert cell["weight"] == without["weight"], (cell, without)
        assert cell["upper"] == without["upper"] == "uppercase", (cell, without)
    assert th[0]["color"] == without["color"], (th[0], without)
    assert th[1]["color"] == with_["color"], (th[1], with_)
    assert th[2]["color"] not in (without["color"], with_["color"]), th[2]


def test_static_document_never_addresses_the_reader(guide_text: str) -> None:
    body = guide_text[guide_text.index("<body") :]
    for tag in ("script", "style"):
        body = re.sub(rf"<{tag}\b.*?</{tag}>", " ", body, flags=re.S)
    # Speaker labels and usage notices belong to the requested illustrative session dialogue.
    body = re.sub(r'<div class="ph-run">[\s\S]*?(?=<p class="ph-note">)', " ", body)
    prose = re.sub(r"<[^>]+>", " ", body)
    assert not SECOND_PERSON.findall(prose), sorted(set(SECOND_PERSON.findall(prose)))
    facing = re.findall(r'(?:aria-label|alt|title|data-th|placeholder)="([^"]*)"', body)
    offenders = [v for v in facing if SECOND_PERSON.search(v)]
    assert not offenders, offenders
