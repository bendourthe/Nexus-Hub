"""v4.13.10: the shared page opening, the interactive outline, and the workflow order.

Training carries all three now; Foundations and Cheatsheets adopt the opening and the
outline at the Phase 7 cutover, when removing the old in-guide Training gives the guide's
byte ceiling room. Training's parts must follow the Home page's Development Workflow, in order.

Browser tests skip when Playwright or Chromium is missing and fail closed under
NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "guides" / "website"
TRAINING = WEB / "training.html"
GUIDE = WEB / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
PARTS = ["Introduction", "Buggy game", "Describe", "Review", "Plan", "Implement", "Test", "Update", "The reward"]


def _text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def test_training_follows_the_home_development_workflow() -> None:
    """Revision 2: one pass; the workflow is the Home page's six commands, in the same order."""
    guide = _text(GUIDE)
    strip = guide[guide.index('id="nhg-loop"'):]
    strip = strip[: strip.index("</div>")]
    home = [cmd for cmd, _ in re.findall(r'<code data-ty="code">/([a-z]+)</code><span>([^<]+)</span>', strip)]
    training = _text(TRAINING)
    sections = re.findall(r'<section class="tr-stage" id="([a-z-]+)" data-stage=', training)
    assert sections == ["intro", "play-buggy", *home, "play-fixed"]
    assert "tr-loophead" not in training


def test_training_intro_opens_with_the_shared_component() -> None:
    html = _text(TRAINING)
    intro = re.search(r'data-stage="intro".*?</section>', html, re.DOTALL).group(0)
    assert 'class="pg-open"' in intro
    assert re.search(r'<h1 data-ty="h1" class="pg-open-title"[^>]*>.*<span class="gtext">', intro)
    assert 'class="pg-open-lead"' in intro
    _assert_opening_figure(intro, "training")


def _assert_opening_figure(block: str, name: str) -> None:
    """Maintainer review (WN-7, R2): an opening ends with one figure of the page's content, not a card row.

    Foundations links every scene, Training links every stop of the journey, and Cheatsheets
    walks through using the page; the subtitle above is one short sentence.
    """
    fig = re.search(r'<figure class="pg-fig ([a-z]+)" aria-label="([^"]+)">(.*?)</figure>', block, re.S)
    assert fig, f"{name}: the opening has no figure"
    kind, label, body = fig.groups()
    assert len(label) > 80, f"{name}: the figure needs a real text alternative"
    if name == "foundations":
        links = re.findall(r'href="#foundations/([a-z-]+)"', body)
        assert sorted(links) == sorted(["fx-tokens", "fx-model-lifecycle", "fx-prompts", "fx-context", "fx-agent-platform", "fx-harness"])
    elif name == "training":
        # A cursor demo: the buggy game, the six commands, the fixed game; never the boss or its logo.
        assert body.count('class="trf-card') == 3 and "trf-cursor" in body
        assert re.findall(r'<li class="trf-st" data-k="\d">(/[a-z]+)</li>', body) == ["/describe", "/review", "/plan", "/implement", "/test", "/update"]
        assert "nexus-mark" not in body and "boss" not in body.lower()
    else:
        assert len(re.findall(r"<li><b>\d</b>", body)) == 4, "the cheatsheet demo has four steps"
        assert "csf-cursor" in body and "csf-copied" in body
    assert "pg-map" not in block and "pg-glyph" not in block
    lead = re.search(r'class="[^"]*pg-open-lead[^"]*">(.*?)</p>', block, re.S).group(1)
    assert lead.count(". ") == 0 and len(lead) <= 100, f"{name}: the subtitle is one short sentence"


def test_guide_openings_carry_their_own_figures() -> None:
    guide = _text(GUIDE)
    for page, nxt in (("foundations", "fx-tokens"), ("cheatsheets", "data-outline-page")):
        start = guide.index(f'id="page-{page}"')
        block = guide[start: guide.index("</figure>", start) + len("</figure>")]
        _assert_opening_figure(block, page)


# --- Browser -----------------------------------------------------------------------


@pytest.fixture(scope="module")
def playwright_mod():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        sync_playwright = None
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


def _page(pw, width: int = 1280, route: str = "#intro", theme: str = "dark", reduced: str = "no-preference"):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": 900}, color_scheme=theme, reduced_motion=reduced)
    page.add_init_script(f"try {{ localStorage.setItem('portfolio-theme', '{theme}'); }} catch (e) {{}}")
    page.goto(TRAINING.as_uri() + route)
    page.wait_for_function("window.NexusTrainingPage && window.NexusTrainingPage.stage() !== null")
    return browser, page


def test_outline_lists_the_journey_and_follows_the_stage(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _page(pw)
        try:
            links = page.locator(".pg-outline a")
            assert links.all_inner_texts() == PARTS
            assert page.locator(".pg-outline a[aria-current]").inner_text() == "Introduction"
            page.evaluate("NexusTrainingPage.go('test')")
            page.wait_for_function("document.querySelector('.pg-outline a[aria-current]').textContent === 'Test'")
            links.nth(5).click()
            page.wait_for_function("NexusTrainingPage.stage() === 'implement'")
            assert page.locator(".pg-outline a[aria-current]").inner_text() == "Implement"
        finally:
            browser.close()


def test_outline_is_keyboard_operable(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _page(pw)
        try:
            page.locator(".pg-outline a").nth(1).focus()
            outline_color = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
            assert outline_color != "none", "a focused outline entry shows a visible focus ring"
            page.keyboard.press("Enter")
            page.wait_for_function("NexusTrainingPage.stage() === 'play-buggy'")
        finally:
            browser.close()


def test_outline_collapses_on_phones(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _page(pw, width=390, route="#plan")
        try:
            # v4.13.10 R1: with no margin, the navigation is a compact bar with a section menu.
            assert "pg-outline--bar" in page.locator(".pg-outline").get_attribute("class")
            toggle = page.locator(".pg-outline-toggle")
            assert toggle.is_visible() and toggle.get_attribute("aria-expanded") == "false"
            assert "Plan" in toggle.inner_text()
            assert page.locator(".pg-outline a").first.is_hidden()
            toggle.click()
            assert toggle.get_attribute("aria-expanded") == "true"
            page.locator(".pg-outline a", has_text="Review").click()
            page.wait_for_function("NexusTrainingPage.stage() === 'review'")
            assert page.locator(".pg-outline a").first.is_hidden(), "choosing an entry closes the phone menu"
        finally:
            browser.close()


def test_scroll_mode_jumps_without_changing_the_stage(playwright_mod) -> None:
    """The mode Foundations and Cheatsheets use: a jump scrolls in place and never routes."""
    with playwright_mod() as pw:
        browser, page = _page(pw, route="#plan", reduced="reduce")
        try:
            page.evaluate(
                """() => {
                    const host = document.createElement('div');
                    const box = document.querySelector('[data-stage="plan"] .container');
                    box.appendChild(host);
                    ['one', 'two', 'three'].forEach(n => {
                        const s = document.createElement('section');
                        s.id = 'probe-' + n; s.style.height = '1200px';
                        s.innerHTML = '<h2>' + n + '</h2>';
                        box.appendChild(s);
                    });
                    window.__probe = window.NexusOutline.mount(host, ['one', 'two', 'three'].map(n => (
                        { id: n, label: n, href: '#s-' + n, target: 'probe-' + n })), { mode: 'scroll' });
                }"""
            )
            page.locator('.pg-outline a[href="#s-three"]').click()
            page.wait_for_function("window.__probe.current() === 'three'")
            assert page.evaluate("NexusTrainingPage.stage()") == "plan"
            assert page.evaluate("location.hash") == "#s-three"
            assert page.evaluate("document.activeElement.textContent") == "three", "focus moves to the section heading"
            page.wait_for_function(
                "(() => { const t = document.getElementById('probe-three').getBoundingClientRect().top; return t > 0 && t < 200; })()",
                timeout=3000,
            )
            assert page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == "auto", (
                "reduced motion turns smooth scrolling off"
            )
        finally:
            browser.close()


@pytest.mark.parametrize("width", [1280, 390])
@pytest.mark.parametrize("theme", ["dark", "light"])
def test_no_stage_overflows_horizontally(playwright_mod, width: int, theme: str) -> None:
    with playwright_mod() as pw:
        browser, page = _page(pw, width=width, theme=theme)
        try:
            for stage in page.evaluate("NexusTrainingPage.stages()"):
                page.evaluate(f"location.hash = '#{stage}'")
                page.wait_for_function(f"NexusTrainingPage.stage() === '{stage}'")
                assert page.evaluate("document.documentElement.scrollWidth") <= width, stage
        finally:
            browser.close()


@pytest.mark.parametrize("width,form", [(1920, "rail"), (1440, "rail"), (1366, "slim"), (1280, "slim"), (1024, "bar"), (390, "bar")])
def test_navigation_never_takes_width_from_the_content(playwright_mod, width: int, form: str) -> None:
    """Maintainer review (R1): the rail lives in the left margin; with no margin it is a bar."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_function("document.body.dataset.page === 'foundations'")
            page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight * 0.45)")
            page.wait_for_timeout(400)
            m = page.evaluate("""() => {
                const n = document.querySelector('.page.active .pg-outline'), c = document.querySelector('.page.active .container');
                const nr = n.getBoundingClientRect(), cr = c.getBoundingClientRect();
                return { cls: n.className, right: nr.right, contentLeft: cr.left + parseFloat(getComputedStyle(c).paddingLeft),
                         colWidth: cr.width, current: !!n.querySelector('.is-current'),
                         fill: parseFloat(getComputedStyle(n).getPropertyValue('--pg-progress')) };
            }""")
            assert f"pg-outline--{form}" in m["cls"]
            assert m["colWidth"] == min(1120, width), "the content column keeps its width"
            if form != "bar":
                assert m["right"] <= m["contentLeft"], "the rail stays in the margin"
            assert m["current"] and 0.2 < m["fill"] < 0.8, "the navigation follows the reading position"
        finally:
            browser.close()


@pytest.mark.parametrize("width", [390, 768, 1024])
def test_the_training_bar_stays_under_the_header_while_scrolling(playwright_mod, width: int) -> None:
    """Rework review P1: the bar once sat in a 48 px container and scrolled off with it."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(TRAINING.as_uri())
            page.wait_for_function("window.NexusTrainingPage")
            for y in (3000, 9000):
                page.evaluate(f"window.scrollTo({{ top: {y}, behavior: 'instant' }})")
                page.wait_for_timeout(120)
                nav = page.evaluate("""(() => { const n = document.querySelector('.pg-outline'), r = n.getBoundingClientRect(),
                    h = document.querySelector('header').getBoundingClientRect(), c = document.querySelector('#app > .container').getBoundingClientRect();
                    return { bar: n.classList.contains('pg-outline--bar'), top: r.top, header: h.bottom, left: r.left, right: r.right, cl: c.left, cr: c.right }; })()""")
                assert nav["bar"], nav
                assert abs(nav["top"] - nav["header"]) <= 2, f"the bar left the screen at scroll {y}: {nav}"
                assert nav["left"] >= nav["cl"] and nav["right"] <= nav["cr"], f"the bar keeps the column's width: {nav}"
        finally:
            browser.close()
