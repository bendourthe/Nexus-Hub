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
PARTS = ["Introduction", "Buggy Game", "Describe", "Review", "Plan", "Implement", "Test", "Update", "Fixed Game"]
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
    # R24: Training's statement names the workflow and the example, so the cap allows one longer sentence.
    assert lead.count(". ") == 0 and len(lead) <= 130, f"{name}: the subtitle is one sentence"


TRAINING_LEAD = ("A hands-on walkthrough of the Nexus Hub recommended development workflow, "
                 "using the practical example of fixing a buggy game.")


def test_the_training_subtitle_names_the_workflow_and_the_example() -> None:
    """Maintainer review 8 (R24): the subtitle says what the page trains and through which example."""
    intro = re.search(r'data-stage="intro".*?</section>', _text(TRAINING), re.DOTALL).group(0)
    lead = re.search(r'<p data-ty="callout" class="pg-open-lead">([^<]+)</p>', intro).group(1)
    assert lead == TRAINING_LEAD
    assert lead.isascii() and not re.search(r"\byou\b", lead, re.I)


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
            assert order == ["Buggy Game", "Agent Workflow", "Fixed Game"], order
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
            # R23: the static end state rests the highlight on Fixed Game, with no transition to animate it.
            assert page.evaluate(ACTIVE) == ["Fixed Game"]
            assert page.evaluate("getComputedStyle(document.querySelector('.tro-card--ok')).transitionDuration") in ("0s", "0s, 0s")
        finally:
            browser.close()


# --- R23 (maintainer review 8): the active-panel highlight and the chat inside the IDE ------------

ACTIVE = "[...document.querySelectorAll('figure.tro .tro-card.is-active')].map(c => c.querySelector('.tro-cap').textContent)"


def test_the_training_opening_highlights_one_panel_at_a_time_in_story_order(playwright_mod) -> None:
    """Buggy Game while its scene plays, Agent Workflow while the six commands run, then Fixed Game,
    which keeps the highlight through the end hold until the loop resets."""
    with playwright_mod() as pw:
        browser, page = _opening(pw, 1440, 900)
        try:
            m = page.evaluate("NexusTrainingOpening.marks")
            order = []
            for ms in range(0, page.evaluate("NexusTrainingOpening.duration"), 100):
                page.evaluate(f"NexusTrainingOpening.seek({ms})")
                active = page.evaluate(ACTIVE)
                assert len(active) == 1, f"exactly one panel is active at {ms} ms: {active}"
                assert page.evaluate("NexusTrainingOpening.state().active") == {"Buggy Game": "bug", "Agent Workflow": "agent", "Fixed Game": "ok"}[active[0]]
                if not order or order[-1] != active[0]:
                    order.append(active[0])
                if m["flow"] <= ms < m["ok"]:
                    assert active == ["Agent Workflow"], (ms, active)
            assert order == ["Buggy Game", "Agent Workflow", "Fixed Game"], order
            page.evaluate(f"NexusTrainingOpening.seek({m['end'] + 1500})")
            assert page.evaluate(ACTIVE) == ["Fixed Game"], "the end hold rests on Fixed Game"
            page.evaluate("NexusTrainingOpening.seek(0)")
            assert page.evaluate(ACTIVE) == ["Buggy Game"], "the loop resets to Buggy Game"
            ring = page.evaluate("""(() => { const a = getComputedStyle(document.querySelector('.tro-card--bug')),
                b = getComputedStyle(document.querySelector('.tro-card--ok'));
                return { on: a.borderTopColor, off: b.borderTopColor, shadow: a.boxShadow, dur: a.transitionDuration }; })()""")
            assert ring["on"] != ring["off"] and ring["shadow"] != "none", ring
            assert ring["dur"] != "0s", "the highlight moves with a transition"
        finally:
            browser.close()


CHAT = """() => { const f = document.querySelector('figure.tro'), r = s => f.querySelector(s).getBoundingClientRect();
    const ide = r('.tro-ide'), body = r('.tro-ide-body'), ed = r('.tro-editor'), ch = r('.tro-chat');
    const bubbles = [...f.querySelectorAll('.tro-msg')].map(b => b.scrollWidth <= b.clientWidth + 1 && b.getBoundingClientRect().right <= ch.right + 1);
    return { inside: !!f.querySelector('.tro-ide > .tro-ide-body > .tro-chat'), chrome: f.querySelectorAll('.tro-ide > .tro-ide-bar i').length,
             ide: [ide.left, ide.right, ide.bottom], body: [body.top, body.bottom], ed: [ed.left, ed.right, ed.top, ed.bottom],
             ch: [ch.left, ch.right, ch.top, ch.bottom], bubbles,
             parts: !!f.querySelector('.tro-chat .tro-model') && !!f.querySelector('.tro-chat .tro-composer') && f.querySelectorAll('.tro-chat .tro-msg').length }; }"""


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_the_training_chat_is_the_ides_right_hand_pane(playwright_mod, width: int, height: int) -> None:
    """One window chrome holds explorer | editor | chat at desktop; on a phone the chat stacks under the editor."""
    with playwright_mod() as pw:
        browser, page = _opening(pw, width, height)
        try:
            page.evaluate("NexusTrainingOpening.seek(NexusTrainingOpening.marks.end + 100)")
            g = page.evaluate(CHAT)
            assert g["inside"] and g["chrome"] == 3 and g["parts"] == 6, g
            assert all(g["bubbles"]), f"no command bubble is truncated: {g}"
            ide, ed, ch = g["ide"], g["ed"], g["ch"]
            assert ide[0] - 1 <= ed[0] and ch[1] <= ide[1] + 1 and ch[3] <= ide[2] + 1, g
            if width >= 960:
                assert ch[0] >= ed[1] - 1 and abs(ch[2] - ed[2]) <= 1, f"the chat sits right of the editor: {g}"
                assert page.evaluate("document.querySelector('.tro-files').getClientRects().length") > 0, "the explorer shows"
            else:
                assert ch[2] >= ed[3] - 1, f"the chat stacks under the editor: {g}"
            assert page.evaluate("document.documentElement.scrollWidth") <= width
            assert page.evaluate(SCROLLBARS) == []
        finally:
            browser.close()



# --- Review 7 follow-up: readable agent pace and one-row tokens in the Foundations opening ----


def test_the_training_opening_gives_each_command_time_to_read(playwright_mod) -> None:
    """Each command is typed, sent, and its file written in about 2.5 to 3 s; cards carry no step numbers."""
    assert "tro-num" not in _training_figure(_text(TRAINING))
    with playwright_mod() as pw:
        browser, page = _opening(pw, 1440, 900)
        try:
            m = page.evaluate("NexusTrainingOpening.marks")
            first_key = m["flow"] + 50
            for k in range(6):
                base = m["flow"] + k * m["slot"]
                typing = next(ms for ms in range(base, base + m["slot"], 25)
                              if page.evaluate(f"NexusTrainingOpening.seek({ms}).typed") != "")
                saved = next(ms for ms in range(base, base + m["slot"], 25)
                             if page.evaluate(f"NexusTrainingOpening.seek({ms}); document.querySelector('.tro-status').textContent").startswith("Saved"))
                assert 2500 <= saved - typing <= 3000, (WORKFLOW[k], typing - base, saved - base)
                assert m["slot"] - (saved - base) >= 300, "the saved file holds before the next command"
            assert first_key > m["bug"], "the buggy scene still plays first"
            assert m["ok"] >= m["flow"] + 6 * m["slot"], "the fixed scene still plays after the workflow"
        finally:
            browser.close()


TOKEN_ROWS = """() => [...document.querySelectorAll('#page-foundations .fxo-tline')].map(line => {
    const chips = [...line.querySelectorAll('.fxo-t')];
    const tops = [...new Set(chips.map(c => Math.round(c.getBoundingClientRect().top)))].sort((a, b) => a - b);
    const leads = tops.map(top => chips.find(c => Math.round(c.getBoundingClientRect().top) === top).textContent.trim());
    return { k: line.dataset.k, rows: tops.length, leads };
})"""


@pytest.mark.parametrize("width", (1280, 1440, 1920, 390))
def test_each_prompt_sentence_tokens_fill_one_row_at_desktop(playwright_mod, width: int) -> None:
    """At desktop widths each sentence's tokens sit on one line; a narrow wrap never starts with punctuation."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_selector("#page-foundations .fxo-tline")
            lines = page.evaluate(TOKEN_ROWS)
        finally:
            browser.close()
    assert [line["k"] for line in lines] == ["request", "goal", "format"], lines
    for line in lines:
        if width >= 1280:
            assert line["rows"] == 1, (width, line)
        assert all(re.match(r"\w", lead) for lead in line["leads"]), (width, line)


# --- Navigation (v4.13.10 R25, maintainer review 8) ---------------------------------------
# Leaving Training for Foundations or Cheatsheets flashed Home first, because the router runs at
# the end of a large file. The observer below records what CSS would show at the moment each
# page section is parsed, before any later script can correct it.
FIRST_PAINT_JS = """
window.__firstPaint = {};
new MutationObserver(function (records) {
  records.forEach(function (r) {
    r.addedNodes.forEach(function (n) {
      if (n.nodeType === 1 && n.classList && n.classList.contains('page') && !(n.id in window.__firstPaint)) {
        window.__firstPaint[n.id] = getComputedStyle(n).display;
      }
    });
  });
}).observe(document, { childList: true, subtree: true });
"""


@pytest.mark.parametrize("route", ["home", "foundations", "cheatsheets", "foundations/fx-tokens", "cheatsheets/plan"])
def test_the_guide_paints_the_hash_page_first(playwright_mod, route: str) -> None:
    target = "page-" + route.split("/")[0]
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.add_init_script(FIRST_PAINT_JS)
            page.goto(GUIDE.as_uri() + "#" + route)
            page.wait_for_timeout(300)
            seen = page.evaluate("window.__firstPaint")
            boot = page.evaluate("document.documentElement.getAttribute('data-boot')")
            active = page.evaluate("document.querySelector('.page.active').id")
        finally:
            browser.close()
    # Maintainer review 9: after the Home fix, a no-script fallback still painted Foundations first.
    others = {k: v for k, v in seen.items() if k != target}
    assert set(others.values()) == {"none"}, f"another page painted before {route}: {seen}"
    assert seen.get(target) == "block", f"{target} was not shown on first paint: {seen}"
    assert boot is None, "the router clears the first-paint mark"
    assert active == target


def test_the_guide_still_opens_on_home_without_a_hash(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.add_init_script(FIRST_PAINT_JS)
            page.goto(GUIDE.as_uri())
            page.wait_for_timeout(300)
            seen = page.evaluate("window.__firstPaint")
        finally:
            browser.close()
    assert seen.get("page-home") == "block", seen


@pytest.mark.parametrize(
    "route, prev, nxt",
    [
        ("foundations", ("Home", "#home"), ("Training", "training.html")),
        ("cheatsheets", ("Training", "training.html"), None),
    ],
)
def test_previous_and_next_follow_the_site_order(playwright_mod, route: str, prev, nxt) -> None:
    """Maintainer review 8: the end of Foundations named Cheatsheets as the next page."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(GUIDE.as_uri() + "#" + route)
            page.wait_for_timeout(300)
            data = page.evaluate(
                """(id) => {
                    const nav = document.querySelector('#page-' + id + ' [data-pagenav]');
                    const pick = (cls) => { const a = nav.querySelector('a.' + cls + ':not(.disabled)');
                        return a ? [a.querySelector('.pn-t').textContent.replace(/[^A-Za-z ]/g, '').trim(), a.getAttribute('href')] : null; };
                    const dots = [...document.querySelectorAll('#page-' + id + ' [data-progress] a')];
                    return { prev: pick('prev'), next: pick('next'),
                             dots: dots.map(a => a.getAttribute('aria-label')),
                             on: dots.findIndex(a => a.classList.contains('on')) };
                }""",
                route,
            )
        finally:
            browser.close()
    assert data["prev"] == (list(prev) if prev else None), data
    assert data["next"] == (list(nxt) if nxt else None), data
    assert data["dots"] == ["Go to Home", "Go to Foundations", "Go to Training", "Go to Cheatsheets"], data
    assert data["on"] == ["home", "foundations", "training", "cheatsheets"].index(route), data


def test_training_ends_with_the_same_previous_next_and_dots(playwright_mod) -> None:
    """R25 (T097): Training's footer names Foundations and Cheatsheets and matches the guide's look."""
    read = """(sel) => { const nav = document.querySelector(sel + ' [data-pagenav]'), dots = [...document.querySelectorAll(sel + ' [data-progress] a')];
        const pick = (cls) => { const a = nav.querySelector('a.' + cls + ':not(.disabled)');
            return a ? [a.querySelector('.pn-t').textContent.replace(/[^A-Za-z ]/g, '').trim(), a.getAttribute('href')] : null; };
        const look = (el) => { const s = getComputedStyle(el); return [s.borderTopColor, s.borderRadius, s.paddingTop, s.fontSize, s.backgroundColor]; };
        return { prev: pick('prev'), next: pick('next'), dots: dots.map(a => [a.getAttribute('aria-label'), a.getAttribute('title'), a.getAttribute('aria-current')]),
                 on: dots.findIndex(a => a.classList.contains('on')), last: !nav.parentElement.nextElementSibling,
                 look: [look(nav.querySelector('a.prev')), look(nav.querySelector('.pn-k')), look(dots[0]), getComputedStyle(nav).marginTop] }; }"""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(TRAINING.as_uri())
            page.wait_for_function("window.NexusTrainingPage")
            training = page.evaluate(read, "main")
            page.goto(GUIDE.as_uri() + "#foundations")
            page.wait_for_timeout(300)
            guide = page.evaluate(read, "#page-foundations")
        finally:
            browser.close()
    assert training["prev"] == ["Foundations", "nexus-hub-guide.html#foundations"], training
    assert training["next"] == ["Cheatsheets", "nexus-hub-guide.html#cheatsheets"], training
    assert training["dots"] == [["Go to Home", "Home", None], ["Go to Foundations", "Foundations", None],
                                ["Go to Training", "Training", "page"], ["Go to Cheatsheets", "Cheatsheets", None]], training
    assert training["on"] == 2 and training["last"], training
    assert training["look"] == guide["look"], "the Training footer is styled exactly like the guide's"


@pytest.mark.parametrize("width", [1440, 390])
def test_the_opening_subtitle_shares_one_larger_size(playwright_mod, width: int) -> None:
    """R24 (T094): one size on Foundations, Training, and Cheatsheets, between body text and H2."""
    probe = """() => { const vis = s => [...document.querySelectorAll(s)].find(e => e.getClientRects().length);
        const px = e => parseFloat(getComputedStyle(e).fontSize);
        return { lead: px(vis('.pg-open-lead')), h2: px(vis('main h2:not(.tr-reward-title)')), body: px(vis('main [data-ty="body"]') || document.body) }; }"""
    sizes = {}
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": 900})
            for name, url in (("foundations", GUIDE.as_uri() + "#foundations"), ("training", TRAINING.as_uri()),
                              ("cheatsheets", GUIDE.as_uri() + "#cheatsheets")):
                page.goto(url)
                page.wait_for_timeout(300)
                sizes[name] = page.evaluate(probe)
        finally:
            browser.close()
    leads = {s["lead"] for s in sizes.values()}
    assert len(leads) == 1, sizes
    lead = leads.pop()
    for s in sizes.values():
        assert s["body"] + 1.5 <= lead <= s["h2"] - 2, sizes
    if width == 1440:
        assert 21 <= lead <= 24, sizes


# --- Page titles and the framed subtitle (v4.13.10 R29, T102) -----------------------------
FOUNDATIONS_LEAD = ("A general reference on how generative AI works: the terminology, the models, "
                    "and the ideas behind every AI-assisted project.")


def test_foundations_is_titled_as_a_general_reference() -> None:
    """Maintainer review (revision 7): the title names Foundations; the subtitle says what the page is."""
    guide = _text(GUIDE)
    block = guide[guide.index('id="page-foundations"'):guide.index("<figure", guide.index('id="page-foundations"'))]
    assert re.search(r'<h1 data-ty="h1" class="[^"]*pg-open-title[^"]*">Generative AI Foundations</h1>', block)
    lead = re.search(r'<p data-ty="callout" class="[^"]*pg-open-lead[^"]*">([^<]+)</p>', block).group(1)
    assert lead == FOUNDATIONS_LEAD
    assert lead.isascii() and not re.search(r"\byou\b", lead, re.I)


CALLOUT = """() => { const e = [...document.querySelectorAll('.pg-open-lead')].find(n => n.getClientRects().length);
    const t = [...document.querySelectorAll('.pg-open-title')].find(n => n.getClientRects().length);
    const c = getComputedStyle(e), r = e.getBoundingClientRect(), tr = t.getBoundingClientRect();
    const box = e.closest('.container').getBoundingClientRect();
    return { role: e.dataset.ty, look: [c.fontSize, c.fontWeight, c.lineHeight, c.color, c.backgroundColor, c.borderTopColor,
                                        c.borderTopWidth, c.borderTopLeftRadius, c.paddingTop, c.paddingLeft, c.textAlign].join('|'),
             bg: c.backgroundColor, border: parseFloat(c.borderTopWidth), radius: parseFloat(c.borderTopLeftRadius),
             centre: Math.abs((r.left + r.width / 2) - (tr.left + tr.width / 2)), inside: r.left >= box.left - .5 && r.right <= box.right + .5,
             below: r.top >= tr.bottom }; }"""


@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("width", [1440, 390])
def test_the_opening_subtitle_is_one_framed_callout(playwright_mod, width: int, theme: str) -> None:
    """R29 (T102): a softly tinted, rounded panel with a thin border, centred under the title, the same on all three pages."""
    looks = {}
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": 900}, color_scheme=theme)
            page.add_init_script(f"try {{ localStorage.setItem('portfolio-theme', '{theme}'); }} catch (e) {{}}")
            for name, url in (("foundations", GUIDE.as_uri() + "#foundations"), ("training", TRAINING.as_uri()),
                              ("cheatsheets", GUIDE.as_uri() + "#cheatsheets")):
                page.goto(url)
                page.wait_for_timeout(300)
                looks[name] = page.evaluate(CALLOUT)
        finally:
            browser.close()
    assert {v["look"] for v in looks.values()} == {looks["foundations"]["look"]}, looks
    for name, v in looks.items():
        assert v["role"] == "callout", (name, v)
        assert v["bg"] not in ("rgba(0, 0, 0, 0)", "transparent") and v["border"] >= 1 and v["radius"] >= 8, (name, v)
        assert v["centre"] < 2 and v["inside"] and v["below"], (name, v)


# --- No scroll fade (v4.13.10 R30, T104) ---------------------------------------------------
FIGURES = ('figure, .pg-fig, .ide, .ss-host, .tro, .fxo, .cx-preview, svg, .fx-diagram, .ml-flow, .ml-tier-list, '
           '.ml-scale, .ph, .term, .loop-strip, .tr-flow, .ide-wrap, .tr-reward, [data-seq-root]')
SCROLL_VISIBLE = """async (figures) => {
  const frame = () => new Promise(r => requestAnimationFrame(() => r()));
  const flat = t => t === 'none' || t === 'matrix(1, 0, 0, 1, 0, 0)';
  const tops = [...document.querySelectorAll('main section')].filter(s => s.getClientRects().length && !s.closest(figures)
    && !s.parentElement.closest('section:not(.page)'));
  const bad = [];
  for (const s of tops) {
    window.scrollTo({ top: s.getBoundingClientRect().top + scrollY - 40, behavior: 'instant' });
    await frame();
    const c = getComputedStyle(s);
    if (+c.opacity < 1 || !flat(c.transform)) bad.push([s.id || s.className, c.opacity, c.transform]);
    for (const e of s.querySelectorAll('*')) {
      if (e.closest(figures) || !e.getClientRects().length) continue;
      const ec = getComputedStyle(e);
      if (+ec.opacity < 1) bad.push([(s.id || s.className) + ' > ' + e.tagName + '.' + [...e.classList].join('.'), ec.opacity]);
    }
  }
  return { sections: tops.length, bad, reveal: document.querySelectorAll('.reveal, .seq-rise:not([data-seq-root] .seq-rise)').length };
}"""


@pytest.mark.parametrize("route", ["home", "foundations", "cheatsheets", "training"])
def test_every_section_is_fully_visible_the_frame_it_scrolls_in(playwright_mod, route: str) -> None:
    """Maintainer review (revision 7): no fade, offset, or delay before a segment appears, on any page."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(TRAINING.as_uri() if route == "training" else GUIDE.as_uri() + "#" + route)
            page.wait_for_timeout(500)
            out = page.evaluate(SCROLL_VISIBLE, FIGURES)
        finally:
            browser.close()
    assert out["sections"] >= 3, out
    assert out["reveal"] == 0, out
    assert not out["bad"], out["bad"][:12]


# --- Foundations opening, third pass (v4.13.10 R26, T098) ---------------------------------
FXO_LAYOUT = """() => { const f = document.querySelector('#page-foundations figure.fxo');
  const rows = [...f.querySelectorAll('.fxo-chat > *')];
  const labs = rows.map(r => r.querySelector(':scope > .fxo-lab'));
  const look = e => { const c = getComputedStyle(e); return [c.fontSize, c.fontWeight, c.letterSpacing, c.textTransform, c.color].join('|'); };
  const mid = e => { const r = e.getBoundingClientRect(); return r.top + r.height / 2; };
  const reply = f.querySelector('.fxo-reply'), node = f.querySelector('.fxo-node'), outs = [...reply.querySelectorAll('.fxo-out')];
  return { labels: labs.map(l => l && l.textContent.trim()), looks: labs.map(l => l && look(l)),
           composeInPrompt: !!rows[0].querySelector('.fxo-compose'),
           barMid: mid(f.querySelector('.fxo-gauge')), labMid: mid(labs[1]),
           replyGap: reply.getBoundingClientRect().bottom - outs[outs.length - 1].getBoundingClientRect().bottom,
           nodeGap: node.getBoundingClientRect().bottom - reply.getBoundingClientRect().bottom,
           replyH: reply.getBoundingClientRect().height }; }"""
FXO_AT = """(ms) => { document.getAnimations().forEach(a => { a.pause(); a.currentTime = ms; });
  const f = document.querySelector('#page-foundations figure.fxo');
  return Object.fromEntries([...f.querySelectorAll('.fxo-keys [data-k]')].map(k => [k.dataset.k,
    { shown: +getComputedStyle(k).opacity, seg: f.querySelector('.fxo-g[data-k="' + k.dataset.k + '"]').getBoundingClientRect().width }])); }"""
SEGMENT_START = {"system": .5, "files": 2, "request": 9, "goal": 28, "format": 45, "reply": 74}   # percent of the 24 s loop


def _foundations(pw, width: int = 1440, reduced: str = "no-preference"):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion=reduced)
    page.goto(GUIDE.as_uri() + "#foundations")
    page.wait_for_timeout(400)
    return browser, page


def test_the_composer_column_reads_prompt_context_window_tokens(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _foundations(pw)
        try:
            page.evaluate(FXO_AT, 22000)
            data = page.evaluate(FXO_LAYOUT)
        finally:
            browser.close()
    assert data["labels"] == ["Prompt", "Context Window", "Tokens"], data
    assert data["composeInPrompt"], "the chat box sits beside the Prompt label"
    assert len(set(data["looks"])) == 1, data["looks"]
    assert abs(data["barMid"] - data["labMid"]) <= 1, data
    # The answer fills the model box: no large empty band under the last line, and no gap under the reply.
    assert data["replyGap"] <= 40 and data["nodeGap"] <= 16, data


def test_each_legend_item_appears_with_its_segment(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _foundations(pw)
        try:
            for key, start in SEGMENT_START.items():
                before = page.evaluate(FXO_AT, start * 240 - 60)[key]
                after = page.evaluate(FXO_AT, start * 240 + 200)[key]
                assert before["shown"] == 0 and before["seg"] < 1, (key, before)
                assert after["shown"] == 1 and after["seg"] > 0, (key, after)
            reset = page.evaluate(FXO_AT, 23700)
            assert all(v["shown"] == 0 for v in reset.values()), reset
        finally:
            browser.close()


def test_the_composer_legend_shows_its_end_state_under_reduced_motion(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page = _foundations(pw, reduced="reduce")
        try:
            data = page.evaluate("""() => { const f = document.querySelector('#page-foundations figure.fxo');
              return [...f.querySelectorAll('.fxo-keys [data-k]')].map(k => [k.dataset.k, +getComputedStyle(k).opacity,
                f.querySelector('.fxo-g[data-k="' + k.dataset.k + '"]').getBoundingClientRect().width]); }""")
        finally:
            browser.close()
    assert len(data) == 6 and all(shown == 1 and seg > 0 for _k, shown, seg in data), data


# --- Review 10 (v4.13.10) ---------------------------------------------------------------------
# A thick coloured left edge on a box is a template marker the maintainer rejected. A box may have
# an even border; its left edge is never heavier than its other edges. The IDE mockups copy the
# real editor's activity bar, and zero-size CSS triangles use borders as shapes, so both are exempt.
STRIPE_JS = """() => [...document.querySelectorAll('body *')].filter(e => {
    if (!e.getClientRects().length || e.closest('.ide, .ide-wrap, .tro-ide')) return false;
    const c = getComputedStyle(e), r = e.getBoundingClientRect();
    /* A zero-size box drawn with borders is a CSS triangle (an arrow), not a stripe. */
    if (r.width < 4 || r.height < 4 || e.clientWidth === 0 || e.clientHeight === 0) return false;
    const left = parseFloat(c.borderLeftWidth), top = parseFloat(c.borderTopWidth);
    return c.borderLeftStyle !== 'none' && left >= 2 && left > top && c.borderLeftColor !== 'rgba(0, 0, 0, 0)';
  }).map(e => e.tagName + '.' + e.className)"""


@pytest.mark.parametrize("url", ["#home", "#foundations", "#cheatsheets", "training"])
def test_no_box_carries_a_left_edge_stripe(playwright_mod, url: str) -> None:
    target = TRAINING.as_uri() if url == "training" else GUIDE.as_uri() + url
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            page.goto(target)
            page.wait_for_timeout(400)
            found = page.evaluate(STRIPE_JS)
        finally:
            browser.close()
    assert not found, found


@pytest.mark.parametrize("url", ["#foundations", "#cheatsheets", "training"])
def test_page_titles_share_one_top_offset(playwright_mod, url: str) -> None:
    """Review 10: the Foundations title sat higher than the other pages' titles."""
    target = TRAINING.as_uri() if url == "training" else GUIDE.as_uri() + url
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(GUIDE.as_uri() + "#cheatsheets")
            page.wait_for_timeout(300)
            ref = page.evaluate("Math.round(document.querySelector('#page-cheatsheets h1').getBoundingClientRect().top)")
            page.goto(target)
            page.wait_for_timeout(300)
            top = page.evaluate("Math.round([...document.querySelectorAll('h1.pg-open-title')].find(e => e.getClientRects().length).getBoundingClientRect().top)")
        finally:
            browser.close()
    assert top == ref, (url, top, ref)


@pytest.mark.parametrize("target", ["foundations", "cheatsheets"])
def test_the_outline_holds_still_after_a_page_switch(playwright_mod, target: str) -> None:
    """Review 10: the outline first appeared lower, then shifted up, because the page slid in."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            # A slowed CPU widens the gap between showing a page and placing its outline, which is
            # where the shift lived; at full speed it lasted a frame or two and passed by luck.
            page.context.new_cdp_session(page).send("Emulation.setCPUThrottlingRate", {"rate": 6})
            page.goto(GUIDE.as_uri() + "#home")
            page.wait_for_timeout(800)
            page.click(f'.nav-links a[data-go="{target}"]')
            tops = []
            for _ in range(15):
                tops.append(page.evaluate(f"Math.round(document.querySelector('#page-{target} .pg-outline').getBoundingClientRect().top)"))
                page.wait_for_timeout(30)
        finally:
            browser.close()
    shown = [t for t in tops if t]  # 0 is the instant before the new page becomes visible
    assert shown and len(set(shown)) == 1, tops


@pytest.mark.parametrize("url", ["#foundations", "#cheatsheets", "training"])
def test_the_outline_label_is_level_with_the_page_title(playwright_mod, url: str) -> None:
    """Review 11: the outline sat higher than the page title."""
    target = TRAINING.as_uri() if url == "training" else GUIDE.as_uri() + url
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1690, "height": 900})
            page.goto(target)
            page.wait_for_timeout(400)
            data = page.evaluate(
                """() => { const h = [...document.querySelectorAll('h1.pg-open-title')].find(e => e.getClientRects().length);
                    const nav = [...document.querySelectorAll('.pg-outline--rail')].find(e => e.getClientRects().length);
                    return { title: Math.round(h.getBoundingClientRect().top),
                             label: Math.round(nav.querySelector('.pg-outline-label').getBoundingClientRect().top) }; }"""
            )
        finally:
            browser.close()
    assert abs(data["label"] - data["title"]) <= 1, data
