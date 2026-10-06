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
WORKFLOW = ["/describe", "/review", "/plan", "/implement", "/test", "/update"]
# R19: the file each command writes or edits in the opening's IDE, following the Training story.
FILES = ["docs/describe.md", "docs/review.md", "docs/plans/v1.1.0-damage-fix.md", "src/damage.js", "tests/damage.test.js", "CHANGELOG.md"]


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
    # v4.13.10 R21: a keyword title in solid ink, with no gradient phrase.
    assert re.search(r'<h1 data-ty="h1" class="pg-open-title"[^>]*>Development Workflow Training</h1>', intro)
    assert "gtext" not in intro.split("<figure", 1)[0]
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
        # R19: two real game scenes (SkySentinel.demo hosts) and an agent panel; no Play button, no cursor.
        assert body.count('class="tro-card') == 3 and body.count('<div class="tro-demo"></div>') == 2
        assert "window.SkySentinel" in body and "SS.demo(" in body and "amount: 6" in body
        assert not re.search(r">\s*Play\s*<", body) and "cursor" not in body and "trf" not in body
        # The six commands are typed into a chat and sent, in the Home page's order.
        assert re.findall(r'<li class="tro-msg" data-k="\d"><code>(/[a-z]+)</code></li>', body) == WORKFLOW
        assert 'class="tro-composer"' in body and 'class="tro-typed"' in body
        # The IDE answers each command with a file it writes or edits; /implement edits the damage code.
        assert re.findall(r'<ol class="tro-code" data-f="\d" data-path="([^"]+)"', body) == FILES
        assert "tro-del\">  return { ...ship, destroyed: true };" in body and "ship.health - DAMAGE[source]" in body
        assert "Claude Opus 5.5" in body and "GPT-6.1 Sol" in body
        # The 6-damage meaning: the bug destroys the ship, the fix leaves 94, and the verdict marks.
        assert "<b>-6</b> hit, ship destroyed" in body and "<b>-6</b> hit, hull 94" in body
        assert "tro-verdict--bug" in body and "tro-verdict--ok" in body
        assert "6 damage" in label and "100 to 94" in label and "red cross" in label and "green check" in label
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
                    h = document.querySelector('header').getBoundingClientRect(), box = document.querySelector('#app > .container'), c = box.getBoundingClientRect(), pad = parseFloat(getComputedStyle(box).paddingLeft);
                    return { bar: n.classList.contains('pg-outline--bar'), top: r.top, header: h.bottom, left: r.left, right: r.right, cl: c.left + pad, cr: c.right - pad }; })()""")
                assert nav["bar"], nav
                assert abs(nav["top"] - nav["header"]) <= 2, f"the bar left the screen at scroll {y}: {nav}"
                assert nav["left"] >= nav["cl"] - 1 and nav["right"] <= nav["cr"] + 1, f"the bar sits in the content column, never flush to the window: {nav}"
        finally:
            browser.close()


@pytest.mark.parametrize("width", [1280, 1440, 1920])
def test_the_current_ring_is_never_clipped_by_the_rail(playwright_mod, width: int) -> None:
    """Revision 3 (R12): the current entry's ring showed only in part at the rail's left edge."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            for url in (TRAINING.as_uri(), GUIDE.as_uri() + "#foundations", GUIDE.as_uri() + "#cheatsheets"):
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.goto(url)
                page.wait_for_timeout(500)
                box = page.evaluate("""(() => { const nav = [...document.querySelectorAll('.pg-outline--rail')].find(n => n.getClientRects().length);
                    const node = nav.querySelector('a[aria-current] .pg-outline-node'), r = node.getBoundingClientRect(), n = nav.getBoundingClientRect();
                    const halo = parseFloat(getComputedStyle(node).boxShadow.split(' ').slice(-1)[0]) || 4;
                    return { ringLeft: r.left - halo, ringTop: r.top - halo, navLeft: n.left, navTop: n.top }; })()""")
                assert box["ringLeft"] >= box["navLeft"] - 0.5 and box["ringTop"] >= box["navTop"] - 0.5, (url, box)
                page.close()
        finally:
            browser.close()


# --- R19: the Training opening on real demo scenes and a typed chat -------------------------


def _training_figure(html: str) -> str:
    start = html.index('<figure class="pg-fig tro"')
    return html[start: html.index("</figure>", start)]


def test_every_class_in_the_training_opening_has_a_style_rule() -> None:
    """The Foundations discipline (test_v443_phase8_harness) applied to the Training opening."""
    html = _text(TRAINING)
    css = "".join(block.split("</style>", 1)[0] for block in html.split("<style>")[1:])
    declared = set(re.findall(r"\.([A-Za-z][\w-]*)", css))
    used: set[str] = set()
    for match in re.finditer(r'class="([^"]+)"', _training_figure(html)):
        used.update(match.group(1).split())
    undeclared = sorted(name for name in used if name not in declared)
    assert not undeclared, f"the Training opening uses classes with no style rule: {undeclared}"
    assert "trf-" not in css and "trf-" not in html, "the R13 cursor figure's rules and markup are gone"


def _opening(pw, width: int, height: int, reduced: str = "no-preference"):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion=reduced)
    page.goto(TRAINING.as_uri())
    page.wait_for_function("window.NexusTrainingOpening && window.NexusTrainingPage")
    return browser, page


SCROLLBARS = """() => [...document.querySelectorAll('figure.tro, figure.tro *')].filter(e => {
    const cs = getComputedStyle(e), auto = v => v === 'auto' || v === 'scroll';
    return (auto(cs.overflowX) && e.scrollWidth > e.clientWidth) || (auto(cs.overflowY) && e.scrollHeight > e.clientHeight);
}).map(e => e.className)"""

VIEW = """() => { const f = document.querySelector('figure.tro'), s = NexusTrainingOpening.state();
    const canv = [...f.querySelectorAll('.tro-demo .ss-canvas')].map(c => c.getBoundingClientRect());
    return { s, canvases: canv.map(r => [Math.round(r.width), Math.round(r.height)]),
             tab: f.querySelector('.tro-tab-name').textContent, typed: f.querySelector('.tro-typed').textContent,
             sent: [...f.querySelectorAll('.tro-msg.is-sent')].map(m => m.textContent),
             bugX: f.querySelector('.tro-verdict--bug').classList.contains('is-on'),
             okV: f.querySelector('.tro-verdict--ok').classList.contains('is-on'),
             hulls: [...f.querySelectorAll('.tro-hull b')].map(b => b.textContent),
             del: f.querySelector('.tro-del').classList.contains('is-on'),
             height: Math.round(f.getBoundingClientRect().height) }; }"""


def test_the_training_opening_plays_one_loop_on_real_demo_scenes(playwright_mod) -> None:
    """R19 (T087): the buggy scene ends destroyed (red cross), the six commands are typed, sent, and
    answered with a file each, and the fixed scene ends at hull 94 (green check), on one timeline."""
    with playwright_mod() as pw:
        browser, page = _opening(pw, 1440, 900)
        try:
            m = page.evaluate("NexusTrainingOpening.marks")
            assert page.evaluate("NexusTrainingOpening.commands") == WORKFLOW
            seen_files, sent_order, typing_seen, heights = [], [], False, set()
            start = page.evaluate(f"NexusTrainingOpening.seek(0); ({VIEW})()")
            assert start["sent"] == [] and start["hulls"] == ["100", "100"] and not start["bugX"]
            assert len(start["canvases"]) == 2 and all(w >= 360 and h >= 220 for w, h in start["canvases"]), start["canvases"]
            for ms in range(0, page.evaluate("NexusTrainingOpening.duration"), 125):
                page.evaluate(f"NexusTrainingOpening.seek({ms})")
                v = page.evaluate(f"({VIEW})()")
                heights.add(v["height"])
                if v["tab"] not in seen_files:
                    seen_files.append(v["tab"])
                for cmd in v["sent"]:
                    if cmd not in sent_order:
                        sent_order.append(cmd)
                if v["typed"] and v["typed"] not in WORKFLOW:
                    typing_seen = True
                if ms == m["bug"] + 3000:
                    assert v["s"]["buggy"]["destroyed"] and v["s"]["buggy"]["health"] == 0 and v["bugX"], v
                    assert v["sent"] == [] and not v["okV"], "the workflow starts after the bug"
                if m["flow"] + 3 * m["slot"] + m["done"] <= ms < m["flow"] + 4 * m["slot"]:
                    assert v["tab"] == "src/damage.js" and v["del"] and v["s"]["model"] == "GPT-6.1 Sol", v
                assert page.evaluate(SCROLLBARS) == [], f"a scroll bar inside the figure at {ms} ms"
            end = page.evaluate(f"NexusTrainingOpening.seek({m['end'] + 100}); ({VIEW})()")
            assert end["s"]["fixed"]["health"] == 94 and not end["s"]["fixed"]["destroyed"] and end["okV"] and end["bugX"]
            assert end["hulls"] == ["0", "94"] and end["sent"] == WORKFLOW
            assert sent_order == WORKFLOW, "the commands are sent one at a time, in order"
            assert typing_seen, "each command is typed before it is sent"
            assert set(FILES) <= set(seen_files), seen_files
            assert len(heights) == 1, f"the figure keeps one height through the loop: {heights}"
            # The loop wraps back to the start: both scenes reset and the chat empties.
            again = page.evaluate(f"NexusTrainingOpening.seek(0); ({VIEW})()")
            assert again["sent"] == [] and again["hulls"] == ["100", "100"] and not again["bugX"] and not again["okV"]
        finally:
            browser.close()


def test_the_training_opening_runs_on_its_own_clock(playwright_mod) -> None:
    """Live playback, not only seeks: the timeline advances and drives the buggy scene to its hit."""
    with playwright_mod() as pw:
        browser, page = _opening(pw, 1440, 900)
        try:
            page.wait_for_function("NexusTrainingOpening.state().t > 2600", timeout=8000)
            s = page.evaluate("NexusTrainingOpening.state()")
            assert s["buggy"]["hit"] and s["buggy"]["destroyed"] and not s["buggy"]["playing"], "the page seeks the demo; its own clock stays off"
        finally:
            browser.close()


def test_the_training_opening_fits_a_phone(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _opening(pw, 390, 844)
        try:
            heights = set()
            for ms in range(0, page.evaluate("NexusTrainingOpening.duration"), 500):
                page.evaluate(f"NexusTrainingOpening.seek({ms})")
                v = page.evaluate(f"({VIEW})()")
                heights.add(v["height"])
                assert page.evaluate("document.documentElement.scrollWidth") <= 390, ms
                assert page.evaluate(SCROLLBARS) == [], ms
            assert len(heights) == 1, f"no layout jump while the loop plays: {heights}"
            order = page.evaluate("[...document.querySelectorAll('.tro-card')].sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top).map(c => c.querySelector('.tro-cap').textContent)")
            assert order == ["1Buggy Game", "2Agent Workflow", "3Fixed Game"], order
        finally:
            browser.close()


def test_the_training_opening_under_reduced_motion_shows_the_end_state(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _opening(pw, 1440, 900, reduced="reduce")
        try:
            page.wait_for_timeout(400)
            v = page.evaluate(f"({VIEW})()")
            assert v["sent"] == WORKFLOW and v["bugX"] and v["okV"] and v["hulls"] == ["0", "94"], v
            assert v["tab"] == "CHANGELOG.md" and v["typed"] == ""
            assert v["s"]["buggy"]["destroyed"] and v["s"]["fixed"]["health"] == 94
            t0 = page.evaluate("NexusTrainingOpening.state().t")
            page.wait_for_timeout(500)
            assert page.evaluate("NexusTrainingOpening.state().t") == t0, "nothing plays"
            anims = page.evaluate("document.querySelector('figure.tro').getAnimations({ subtree: true }).filter(a => a.playState === 'running').length")
            assert anims == 0
        finally:
            browser.close()
