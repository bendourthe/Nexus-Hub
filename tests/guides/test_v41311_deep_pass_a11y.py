"""v4.13.11 Tier 3 deep pass, fix cycle 3: guide accessibility defects.

1. Foundations opening figure: below 720 px the WN-8 phone layout hides the attachment chips and
   the prompt text is aria-hidden, so the "compose" link had an empty accessible name; at 1280 px
   its name was the attachment text, which did not say where it goes. The link now carries an
   explicit name for its destination, like the figure's other parts.
2. Phone menu (``#navToggle``, shared ``nav.js`` stamped into both pages): Escape closes it,
   resets ``aria-expanded``, and returns focus to the toggle; focus leaving the menu closes it,
   so Tab never reaches the content the open menu covers.
3. Light theme: "Send" and the two context-meter labels reach 4.5:1; the dark theme keeps its
   colors.
4. Guide home: the four benefit headings followed the h1 at level 3. They are exposed at level 2
   (``aria-level``) because R47 keeps any h2 element out of the hero; the look is unchanged.

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
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
THEME_KEY = "portfolio-theme"


def _text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


# --- Static -------------------------------------------------------------------------


def test_compose_link_names_its_destination_in_markup() -> None:
    tag = re.search(r'<a class="fxo-compose"[^>]*>', _text(GUIDE))
    assert tag and 'href="#foundations/fx-prompts"' in tag.group(0)
    assert re.search(r'aria-label="[^"]*Prompt', tag.group(0)), tag.group(0)


# --- Browser ------------------------------------------------------------------------


@pytest.fixture(scope="module")
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
        return  # unreachable: pytest.skip raises; tells static analysis the name is bound below
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception as exc:  # pragma: no cover - environment dependent
            if REQUIRE_RENDER:
                pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
            pytest.skip(f"chromium is unavailable: {exc}")
            return  # unreachable: pytest.skip raises
        yield b
        b.close()


def _page(browser, url: str, width: int, theme: str | None = None, height: int = 900):
    context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
    requests: list[str] = []

    def route(r):
        if r.request.url.startswith(("file:", "data:", "blob:")):
            r.continue_()
        else:
            requests.append(r.request.url)
            r.abort()

    context.route("**/*", route)
    if theme:
        context.add_init_script(f"try {{ localStorage.setItem('{THEME_KEY}', '{theme}'); }} catch (e) {{}}")
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url)
    page.wait_for_function("!!document.body.getAttribute('data-page') || !!document.getElementById('navToggle')")
    page.wait_for_timeout(300)
    page.requests, page.errors = requests, errors  # type: ignore[attr-defined]
    return context, page


def _ax_name(context, page, selector: str) -> str:
    cdp = context.new_cdp_session(page)
    oid = cdp.send("Runtime.evaluate", {"expression": f"document.querySelector({selector!r})"})["result"]["objectId"]
    node = cdp.send("Accessibility.getPartialAXTree", {"objectId": oid, "fetchRelatives": False})["nodes"][0]
    return (node.get("name") or {}).get("value", "")


@pytest.mark.parametrize("width", [390, 1280])
def test_every_figure_link_has_a_destination_name(browser, width: int) -> None:
    """The compose link was nameless at 390 px after WN-8 and named by attachment text at 1280 px."""
    context, page = _page(browser, GUIDE.as_uri() + "#foundations", width)
    try:
        count = page.evaluate("document.querySelectorAll('figure.fxo a').length")
        names = [_ax_name(context, page, sel) for sel in (
            "figure.fxo a.fxo-compose", "figure.fxo a.fxo-ctx", "figure.fxo a.fxo-tokrow", "figure.fxo a.fxo-node--model")]
        tags = page.evaluate("[...document.querySelectorAll('figure.fxo a.fxo-tag')].map(a => a.textContent.trim())")
        errors = page.errors  # type: ignore[attr-defined]
    finally:
        context.close()
    assert count == 6
    compose = names[0]
    assert compose.startswith("Prompt"), f"compose link name at {width}px: {compose!r}"
    assert "contract.pdf" not in compose, "the name states the destination, not the attachments"
    assert all(names) and all(tags), (names, tags)
    assert not errors, errors


def _open_menu(page) -> None:
    page.focus("#navToggle")
    if page.get_attribute("#navToggle", "aria-expanded") != "true":
        page.keyboard.press("Enter")
    page.wait_for_function("document.getElementById('navToggle').getAttribute('aria-expanded') === 'true'")


MENU_STATE = """() => { const t = document.getElementById('navToggle'), l = document.getElementById('navLinks'), a = document.activeElement;
  return { expanded: t.getAttribute('aria-expanded'), shown: getComputedStyle(l).display !== 'none',
           onToggle: a === t, inMenu: l.contains(a), tag: a.tagName, text: (a.textContent || '').trim().slice(0, 30) }; }"""

MENU_PAGES = [(GUIDE, "#home"), (TRAINING, "")]


@pytest.mark.parametrize("path,route", MENU_PAGES, ids=["guide", "training"])
def test_escape_closes_the_phone_menu_and_returns_focus(browser, path: Path, route: str) -> None:
    context, page = _page(browser, path.as_uri() + route, 390, height=844)
    try:
        _open_menu(page)
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        assert page.evaluate(MENU_STATE)["inMenu"], "two Tabs from the toggle land inside the menu"
        page.keyboard.press("Escape")
        state = page.evaluate(MENU_STATE)
        errors = page.errors  # type: ignore[attr-defined]
    finally:
        context.close()
    assert state["expanded"] == "false" and not state["shown"], state
    assert state["onToggle"], f"focus returns to the toggle: {state}"
    assert not errors, errors


@pytest.mark.parametrize("path,route", MENU_PAGES, ids=["guide", "training"])
def test_tab_never_reaches_content_under_the_open_menu(browser, path: Path, route: str) -> None:
    context, page = _page(browser, path.as_uri() + route, 390, height=844)
    try:
        _open_menu(page)
        steps = []
        for _ in range(10):
            page.keyboard.press("Tab")
            steps.append(page.evaluate(MENU_STATE))
        back = []
        _open_menu(page)
        for _ in range(3):
            page.keyboard.press("Shift+Tab")
            back.append(page.evaluate(MENU_STATE))
        requests = page.requests  # type: ignore[attr-defined]
    finally:
        context.close()
    leaked = [s for s in steps + back if s["shown"] and not (s["inMenu"] or s["onToggle"])]
    assert not leaked, f"focus reached covered content while the menu was open: {leaked}"
    assert any(not s["shown"] and s["expanded"] == "false" for s in steps), "leaving the menu closes it"
    assert not requests, requests


CONTRAST_JS = """sels => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 1; const g = cv.getContext('2d', { willReadFrequently: true });
  const rgba = c => { g.clearRect(0, 0, 1, 1); g.fillStyle = '#000'; g.fillStyle = c; g.fillRect(0, 0, 1, 1); const d = g.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const over = (top, bot) => [0, 1, 2].map(i => top[i] * top[3] + bot[i] * (1 - top[3])).concat(1);
  const bgOf = el => { const layers = []; for (let e = el; e; e = e.parentElement) { const c = rgba(getComputedStyle(e).backgroundColor);
      if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } }
    let acc = rgba(getComputedStyle(document.body).backgroundColor); acc[3] = 1;
    for (let i = layers.length - 1; i >= 0; i--) acc = over(layers[i], acc); return acc; };
  const lin = v => { v /= 255; return v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
  const L = c => .2126 * lin(c[0]) + .7152 * lin(c[1]) + .0722 * lin(c[2]);
  return sels.map(s => { const el = document.querySelector(s), cs = getComputedStyle(el), bg = bgOf(el), fg = over(rgba(cs.color), bg);
    const a = L(fg), b = L(bg); return { sel: s, color: cs.color, fg: fg.slice(0, 3).map(Math.round), bg: bg.slice(0, 3).map(Math.round),
      ratio: Math.round((Math.max(a, b) + .05) / (Math.min(a, b) + .05) * 100) / 100 }; });
}"""
CONTRAST_SELS = [".fxo-send", ".fx-seg--waste", ".fx-seg--use"]
# The dark theme's colors before this fix: "Send" ink on the accent, and each label in its own token.
DARK_TOKENS = """() => { const p = document.createElement('i'); document.body.appendChild(p);
  const r = v => { p.style.color = v; return getComputedStyle(p).color; };
  const out = { send: r('#06201c'), amber: r('var(--amber)'), accent: r('var(--accent)') }; p.remove(); return out; }"""


@pytest.mark.parametrize("width", [390, 1280])
def test_light_theme_figure_text_reaches_4_5_to_1(browser, width: int) -> None:
    context, page = _page(browser, GUIDE.as_uri() + "#foundations", width, theme="light")
    try:
        assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
        res = page.evaluate(CONTRAST_JS, CONTRAST_SELS)
    finally:
        context.close()
    low = [r for r in res if r["ratio"] < 4.5]
    assert not low, low


def test_dark_theme_keeps_its_figure_colours(browser) -> None:
    context, page = _page(browser, GUIDE.as_uri() + "#foundations", 1280, theme="dark")
    try:
        assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark"
        res = {r["sel"]: r for r in page.evaluate(CONTRAST_JS, CONTRAST_SELS)}
        tokens = page.evaluate(DARK_TOKENS)
    finally:
        context.close()
    assert res[".fxo-send"]["color"] == tokens["send"], res
    assert res[".fx-seg--waste"]["color"] == tokens["amber"], res
    assert res[".fx-seg--use"]["color"] == tokens["accent"], res
    assert all(r["ratio"] >= 4.5 for r in res.values()), res


HEADINGS_SEL = "[...document.querySelectorAll('#page-home :is(h1, h2, h3, h4, h5, h6, [role=heading])')].filter(h => h.getClientRects().length)"
HEADINGS_AX = "() => " + HEADINGS_SEL + """.map(h => ({ text: h.textContent.trim().replace(/\\s+/g, ' '), tag: h.tagName }))"""


@pytest.mark.parametrize("width", [390, 1280])
def test_home_heading_levels_never_skip(browser, width: int) -> None:
    """The accessibility tree, not the tag, decides the level a screen reader announces.

    Headings are walked in document order (the full AX tree dump is not ordered) and each
    element's level is read from its own accessibility node."""
    context, page = _page(browser, GUIDE.as_uri() + "#home", width)
    try:
        cdp = context.new_cdp_session(page)
        styles = page.evaluate(HEADINGS_AX)
        levels = []
        for i, s in enumerate(styles):
            oid = cdp.send("Runtime.evaluate", {"expression": f"{HEADINGS_SEL}[{i}]"})["result"]["objectId"]
            node = cdp.send("Accessibility.getPartialAXTree", {"objectId": oid, "fetchRelatives": False})["nodes"][0]
            level = next((p["value"]["value"] for p in node.get("properties", []) if p["name"] == "level"), None)
            levels.append((s["text"][:30], level))
    finally:
        context.close()
    assert levels and levels[0][1] == 1, levels
    jumps = [(a, b) for a, b in zip(levels, levels[1:]) if b[1] > a[1] + 1]
    assert not jumps, f"heading levels skip: {jumps}"
    cards = {s["text"]: s for s in styles if s["text"] in ("Depth", "Safety", "Cross-Platform", "Transparency")}
    assert len(cards) == 4 and all(s["tag"] == "H3" for s in cards.values()), "the cards keep their h3 look"
