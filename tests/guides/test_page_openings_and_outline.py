"""v4.13.10 Phase 2: the shared page opening, the interactive outline, and the loop tracker.

Training carries all three now; Foundations and Cheatsheets adopt the opening and the
outline at the Phase 7 cutover, when removing the old in-guide Training gives the guide's
byte ceiling room. The tracker's steps must stay the Home page's loop, in the same order.

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
PARTS = ["Introduction", "Buggy game", "Loop 1", "Play again", "Loop 2", "Fixed game"]


def _text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def test_tracker_steps_are_the_home_loop_in_order() -> None:
    guide = _text(GUIDE)
    loop = guide[guide.index('id="nhg-loop"'):]
    loop = loop[: loop.index("</div>")]
    home = re.findall(r'<code data-ty="code">/([a-z]+)</code><span>([^<]+)</span>', loop)
    training = _text(TRAINING)
    track = training[training.index('id="trTrack"'):]
    track = track[: track.index("</ol>")]
    steps = re.findall(r'<li data-step="([a-z]+)"><a [^>]*><code data-ty="code">/([a-z]+)</code><small>([^<]+)</small>', track)
    assert [(cmd, label) for _, cmd, label in steps] == home, "the tracker shows the Home loop's six steps, in order"
    assert all(step == cmd for step, cmd, _ in steps)


def test_training_intro_opens_with_the_shared_component() -> None:
    html = _text(TRAINING)
    intro = re.search(r'data-stage="intro".*?</section>', html, re.DOTALL).group(0)
    assert 'class="pg-open"' in intro
    assert re.search(r'<h1 data-ty="h1" class="pg-open-title"[^>]*>.*<span class="gtext">', intro)
    assert 'class="pg-open-lead"' in intro
    _assert_opening_figure(intro, "training")


def _assert_opening_figure(block: str, name: str) -> None:
    """Maintainer review (WN-7): an opening ends with one animated figure, not a card row.

    The figure is a NexusSeq root holding a wide and a narrow drawing, labelled as one image,
    and the subtitle above it is a single sentence.
    """
    fig = re.search(r'<figure class="pg-fig" role="img" aria-label="([^"]+)" data-seq-root data-seq-loop[^>]*>(.*?)</figure>', block, re.S)
    assert fig, f"{name}: the opening has no animated figure"
    assert len(fig.group(1)) > 40, f"{name}: the figure needs a real text alternative"
    body = fig.group(2)
    assert 'class="pgf-svg pgf-svg--wide"' in body and 'class="pgf-svg pgf-svg--narrow"' in body
    assert len(set(re.findall(r'data-seq="(\d+)"', body))) >= 5, f"{name}: the figure should build in steps"
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
            page.evaluate("location.hash = '#loop1/test'")
            page.wait_for_function("document.querySelector('.pg-outline a[aria-current]').textContent === 'Loop 1'")
            links.nth(4).click()
            page.wait_for_function("NexusTrainingPage.stage() === 'loop2/review'")
            assert page.locator(".pg-outline a[aria-current]").inner_text() == "Loop 2"
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
        browser, page = _page(pw, width=390, route="#loop1/plan")
        try:
            # v4.13.10 R1: with no margin, the navigation is a compact bar with a section menu.
            assert "pg-outline--bar" in page.locator(".pg-outline").get_attribute("class")
            toggle = page.locator(".pg-outline-toggle")
            assert toggle.is_visible() and toggle.get_attribute("aria-expanded") == "false"
            assert "Loop 1" in toggle.inner_text()
            assert page.locator(".pg-outline a").first.is_hidden()
            toggle.click()
            assert toggle.get_attribute("aria-expanded") == "true"
            page.locator(".pg-outline a", has_text="Play again").click()
            page.wait_for_function("NexusTrainingPage.stage() === 'play-partial'")
            assert page.locator(".pg-outline a").first.is_hidden(), "choosing an entry closes the phone menu"
        finally:
            browser.close()


def test_scroll_mode_jumps_without_changing_the_stage(playwright_mod) -> None:
    """The mode Foundations and Cheatsheets use: a jump scrolls in place and never routes."""
    with playwright_mod() as pw:
        browser, page = _page(pw, route="#loop1/plan", reduced="reduce")
        try:
            page.evaluate(
                """() => {
                    const host = document.createElement('div');
                    const box = document.querySelector('[data-stage="loop1/plan"] .container');
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
            assert page.evaluate("NexusTrainingPage.stage()") == "loop1/plan"
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


@pytest.mark.parametrize(
    ("route", "states"),
    [
        ("#play-buggy", ["todo"] * 6),
        ("#loop1/implement", ["done", "done", "done", "current", "todo", "todo"]),
        ("#play-partial", ["done"] * 6),
        ("#loop2/plan", ["mapped", "done", "current", "todo", "todo", "todo"]),
        ("#play-fixed", ["mapped", "done", "done", "done", "done", "done"]),
    ],
)
def test_tracker_lights_the_current_step(playwright_mod, route: str, states: list[str]) -> None:
    with playwright_mod() as pw:
        browser, page = _page(pw, route=route)
        try:
            got = page.locator("#trTrack [data-step]").evaluate_all("els => els.map(e => e.dataset.state)")
            assert got == states
            loop = "Loop 2" if route in ("#loop2/plan", "#play-fixed") else "Loop 1"
            assert page.locator("#trTrackLoop").inner_text() == loop
            if "mapped" in states:
                describe = page.locator('#trTrack [data-step="describe"]')
                assert "already mapped" in describe.inner_text()
                assert describe.locator("a").get_attribute("href") == "#loop2/review"
        finally:
            browser.close()


def test_tracker_is_hidden_on_the_intro_and_links_to_its_stages(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _page(pw)
        try:
            assert page.locator("#trTrack").is_hidden(), "the intro's journey map replaces the tracker"
            page.evaluate("location.hash = '#loop1/describe'")
            page.wait_for_function("NexusTrainingPage.stage() === 'loop1/describe'")
            page.locator('#trTrack [data-step="test"] a').click()
            page.wait_for_function("NexusTrainingPage.stage() === 'loop1/test'")
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
