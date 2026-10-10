"""v4.13.11 Phase 7: two guide defects found after the known-gaps sweep.

1. Foundations opening figure, Model node: below 720 px the status ("Done") painted over the
   "Model" name, because a narrow-width ``align-items:flex-start`` shrank the head row and the
   absolutely positioned status reserved no width. The longer states ("Reading 2 files and 31
   tokens") overlapped at 720-900 px too. The states now share one in-flow grid cell, so the row
   reserves the widest state and wraps it under the name when it does not fit. The CSS lives in
   ``guides/website/shared/opening.css`` and is stamped into both pages; only the guide renders
   the figure.
2. Cheatsheets cards: the command name was a styled span (WCAG 1.3.1), the two copy buttons on a
   card shared the name "Copy to clipboard", and scope descriptions started at a different x on
   each row because a long key outgrew a ``min-width`` column. Names are now h3 headings in the
   code role, each button names what it copies, and every row shares the card's key track.

Browser tests skip when Playwright or Chromium is missing, and fail closed under
NEXUS_REQUIRE_RENDER=1 so CI cannot silently lose coverage.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "guides" / "website"
GUIDE = WEB / "nexus-hub-guide.html"
TRAINING = WEB / "training.html"
OPENING = WEB / "shared" / "opening.css"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"


def _text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _card_names() -> list[str]:
    return re.findall(r'class="cs-name">(/[a-z-]+)<', _text(GUIDE))


# --- Static -------------------------------------------------------------------------


@pytest.mark.parametrize("path", [OPENING, GUIDE, TRAINING], ids=["source", "guide", "training"])
def test_model_status_reserves_its_width(path: Path) -> None:
    css = _text(path)
    assert ".fxo-node--model{align-items:flex-start;}" not in css, "the narrow-width rule shrank the head row"
    span = re.search(r"\.fxo-status span\{([^}]+)\}", css)
    assert span and "position:absolute" not in span.group(1), "an absolute status reserves no width"
    assert "grid-area:1/1" in span.group(1), "the states share one in-flow cell"


def test_card_names_are_h3_headings_in_markup() -> None:
    html = _text(GUIDE)
    assert len(_card_names()) == 24
    assert len(re.findall(r'<h3 data-ty="code" data-tone="accent" class="cs-name">/[a-z-]+</h3>', html)) == 24
    assert '<span data-ty="code" data-tone="accent" class="cs-name">' not in html
    assert "min-width:92px" not in html, "a fixed key width let long keys push their description"


# --- Browser ------------------------------------------------------------------------


@pytest.fixture(scope="module")
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception as exc:  # pragma: no cover - environment dependent
            if REQUIRE_RENDER:
                pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
            pytest.skip(f"chromium is unavailable: {exc}")
        yield b
        b.close()


def _page(browser, route: str, width: int):
    context = browser.new_context(viewport={"width": width, "height": 900})
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:")) else r.abort())
    page = context.new_page()
    page.goto(GUIDE.as_uri() + route)
    page.wait_for_function("!!document.body.getAttribute('data-page')")
    page.wait_for_timeout(300)
    return context, page


MODEL_JS = """() => {
  const n = document.querySelector('.fxo-node--model'), R = e => e.getBoundingClientRect();
  const name = R(n.querySelector('.fxo-name')), core = R(n.querySelector('.fxo-core')), status = R(n.querySelector('.fxo-status'));
  const area = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
  const node = R(n);
  return { statusWidth: status.width, states: [...n.querySelectorAll('.fxo-status span')].map(s => { const r = R(s);
    return { text: s.textContent, onName: area(r, name), onCore: area(r, core), inside: r.left >= node.left - .5 && r.right <= node.right + .5 }; }) };
}"""


@pytest.mark.parametrize("width", [320, 390, 719, 720, 900, 1280])
def test_model_status_never_paints_over_the_name(browser, width: int) -> None:
    """Every status state, not only "Done", stays clear of the name and the core at every width."""
    context, page = _page(browser, "#foundations", width)
    try:
        res = page.evaluate(MODEL_JS)
    finally:
        context.close()
    assert res["statusWidth"] > 0, f"the status box is {res['statusWidth']}px wide at {width}px"
    assert len(res["states"]) == 4
    for state in res["states"]:
        assert state["onName"] == 0 and state["onCore"] == 0, (width, state)
        assert state["inside"], (width, state)


CARDS_JS = """() => [...document.querySelectorAll('#page-cheatsheets .cs-cmd')].map(c => {
  const h = c.querySelector('.cs-name'), cs = getComputedStyle(h);
  const ref = document.createElement('span'); ref.dataset.ty = 'code'; ref.dataset.tone = 'accent'; ref.textContent = h.textContent;
  h.parentNode.insertBefore(ref, h); const rs = getComputedStyle(ref);
  const P = ['fontSize', 'fontWeight', 'lineHeight', 'color', 'fontFamily', 'letterSpacing'];
  const look = P.every(p => cs[p] === rs[p]) && cs.marginTop === '0px' && cs.marginBottom === '0px'
    && Math.abs(h.getBoundingClientRect().height - ref.getBoundingClientRect().height) < .5;
  ref.remove();
  const group = c.closest('section.cs-group'), h2 = group && group.querySelector(':scope > h2');
  const rows = [...c.querySelectorAll('.cs-scope')].map(r => { const k = r.children[0].getBoundingClientRect(), d = r.children[1].getBoundingClientRect();
    return { cells: r.children.length, key: k.right, x: d.left, sameRow: Math.abs(k.top - d.top) < 12 }; });
  return { name: h.textContent, tag: h.tagName, look, groupH2: !!h2, rows,
           copies: [...c.querySelectorAll('.copy-btn')].map(b => ({ label: b.getAttribute('aria-label'), copy: b.parentNode.querySelector('[data-copy]').getAttribute('data-copy') })) };
})"""


def test_card_names_are_level_3_headings_with_the_code_look(browser) -> None:
    context, page = _page(browser, "#cheatsheets", 1280)
    try:
        cards = page.evaluate(CARDS_JS)
        names = [c["name"] for c in cards]
        assert names == _card_names() and len(names) == 24
        root = page.locator("#page-cheatsheets")
        for name in names:
            assert root.get_by_role("heading", level=3, name=name, exact=True).count() == 1, name
        levels = page.evaluate("[...document.querySelectorAll('#page-cheatsheets h1, #page-cheatsheets h2, #page-cheatsheets h3, #page-cheatsheets h4')]"
                               ".filter(h => !h.closest('figure')).map(h => +h.tagName[1])")
        assert levels[0] == 1 and all(b - a <= 1 for a, b in zip(levels, levels[1:])), levels
    finally:
        context.close()
    for card in cards:
        assert card["tag"] == "H3" and card["groupH2"], card["name"]
        assert card["look"], f"{card['name']} no longer looks like the code role"


def test_copy_buttons_name_what_they_copy(browser) -> None:
    context, page = _page(browser, "#cheatsheets", 1280)
    try:
        cards = page.evaluate(CARDS_JS)
        card_loc = page.locator("#page-cheatsheets .cs-cmd")
        for i, card in enumerate(cards):
            labels = [c["label"] for c in card["copies"]]
            assert labels, card["name"]
            assert len(set(labels)) == len(labels), (card["name"], labels)
            for c in card["copies"]:
                assert c["label"] == "Copy " + c["copy"], c
                assert card_loc.nth(i).get_by_role("button", name=c["label"], exact=True).count() == 1, c
        assert page.get_by_role("button", name="Copy to clipboard", exact=True).count() == 0
    finally:
        context.close()
    assert any(len(c["copies"]) > 1 for c in cards), "no card with two copy lines; the distinctness check is vacuous"


@pytest.mark.parametrize("width", [320, 390, 1280])
def test_scope_descriptions_start_at_one_x_per_card(browser, width: int) -> None:
    context, page = _page(browser, "#cheatsheets", width)
    try:
        cards = page.evaluate(CARDS_JS)
    finally:
        context.close()
    checked = 0
    for card in cards:
        rows = card["rows"]
        if not rows:
            continue
        xs = [r["x"] for r in rows]
        assert max(xs) - min(xs) <= 0.5, (width, card["name"], xs)
        for r in rows:
            assert r["cells"] == 2 and r["sameRow"] and r["key"] <= r["x"] + 0.5, (width, card["name"], r)
        checked += len(rows)
    assert checked >= 50, checked
