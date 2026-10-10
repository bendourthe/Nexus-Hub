"""v4.13.11 Phase 5 (T023): Training game lifecycle and shared header semantics.

Closes v4.13.10 WN-5 and WN-6 against the generated offline pages:

- WN-5: a game started or resumed through the API while its host is not rendered pauses at
  once with reason "stage", stays paused across repeated tab visibility changes, and never
  asks for a frame, so no second loop can start.
- WN-6: the shared header carries a working skip link (stamped into both pages, its target
  checked by the stamp script), the theme toggle no longer misuses ``aria-pressed``, and the
  guide router marks the active page link with ``aria-current="page"``.

Browser tests skip when Playwright or Chromium is missing, and fail closed under
NEXUS_REQUIRE_RENDER=1 so CI cannot silently lose coverage.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "guides" / "website"
GUIDE = WEB / "nexus-hub-guide.html"
TRAINING = WEB / "training.html"
HEADER = WEB / "shared" / "header.html"
STAMP = ROOT / "scripts" / "stamp_guide_shared.py"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

# Counts every request the shared game loop makes, and the most ever pending at once. The
# engine's loop is told apart by its body: the constellation also names its callback "loop".
LOOP_PROBE = """
(() => {
  const raf = window.requestAnimationFrame.bind(window);
  window.__loop = { requested: 0, pending: 0, maxPending: 0 };
  const isEngine = cb => cb && cb.name === 'loop' && String(cb).indexOf('instances[k].frame(now)') !== -1;
  window.requestAnimationFrame = function (cb) {
    if (isEngine(cb)) {
      const L = window.__loop; L.requested++; L.pending++; L.maxPending = Math.max(L.maxPending, L.pending);
      return raf(function (t) { L.pending--; cb(t); });
    }
    return raf(cb);
  };
  window.__vis = 'visible';
  Object.defineProperty(Document.prototype, 'visibilityState', { configurable: true, get() { return window.__vis; } });
  Object.defineProperty(Document.prototype, 'hidden', { configurable: true, get() { return window.__vis === 'hidden'; } });
})();
"""


def _text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _header_region(html: str) -> str:
    match = re.search(r"<!-- shared:header -->\n(.*?)<!-- /shared:header -->", html, re.DOTALL)
    assert match, "the page has no shared header region"
    return match.group(1)


# --- Static -------------------------------------------------------------------------


def test_header_source_has_a_skip_link_first_and_no_pressed_toggle() -> None:
    src = _text(HEADER)
    assert src.lstrip().startswith('<a class="skip-link" href="#app">Skip to content</a>'), "the skip link is the first focusable element"
    toggle = re.search(r"<button[^>]*id=\"themeToggle\"[^>]*>", src)
    assert toggle and "aria-pressed" not in toggle.group(0)
    assert "aria-pressed" not in _text(WEB / "shared" / "theme.js")


@pytest.mark.parametrize("page", [GUIDE, TRAINING], ids=["guide", "training"])
def test_generated_headers_carry_the_skip_link_and_one_target(page: Path) -> None:
    html = _text(page)
    region = _header_region(html)
    assert region.count('class="skip-link"') == 1
    assert 'aria-pressed' not in re.search(r"<button[^>]*id=\"themeToggle\"[^>]*>", region).group(0)
    assert len(re.findall(r'(?<![\w-])id="app"', html)) == 1, "the skip link target is the page's one main"
    assert re.search(r'<main id="app"', html)


def test_generated_headers_differ_only_in_their_link_values() -> None:
    guide, training = _header_region(_text(GUIDE)), _header_region(_text(TRAINING))
    strip = lambda s: re.sub(r"<a (?:class=\"brand\" )?(href=\"[^\"]*\"[^>]*?)(?= aria-label|>)", "<a LINK", s)  # noqa: E731
    assert strip(guide) == strip(training)


def _site(tmp_path: Path, page_body: str) -> Path:
    web = tmp_path / "guides" / "website"
    (web / "shared").mkdir(parents=True)
    (web / "shared" / "head.html").write_text('<a class="skip-link" href="#app">Skip to content</a>\n', encoding="utf-8")
    (web / "shared" / "fragments.json").write_text(json.dumps({
        "fragments": {"head": {"syntax": "html", "file": "head.html"}},
        "pages": {"a.html": {}},
    }), encoding="utf-8")
    (web / "a.html").write_text("<body>\n<!-- shared:head -->\nold\n<!-- /shared:head -->\n" + page_body + "</body>\n", encoding="utf-8", newline="\n")
    return web


@pytest.mark.parametrize(("body", "found"), [
    ("<main>x</main>\n", 0),
    ('<main id="app">x</main>\n<div id="app"></div>\n', 2),
    ('<main data-id="app">x</main>\n', 0),
])
def test_stamp_refuses_a_skip_link_without_exactly_one_target(tmp_path: Path, body: str, found: int) -> None:
    web = _site(tmp_path, body)
    before = (web / "a.html").read_bytes()
    for args in ((), ("--check",)):
        result = subprocess.run([sys.executable, str(STAMP), "--root", str(tmp_path), *args], capture_output=True, text=True, check=False)
        assert result.returncode == 2, result.stderr
        assert f"skip link target #app must match exactly one id, found {found}" in result.stderr
    assert (web / "a.html").read_bytes() == before, "a refused stamp writes nothing"


def test_stamp_accepts_a_skip_link_with_one_target(tmp_path: Path) -> None:
    _site(tmp_path, '<main id="app">x</main>\n')
    result = subprocess.run([sys.executable, str(STAMP), "--root", str(tmp_path)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


# --- Browser ------------------------------------------------------------------------


@pytest.fixture(scope="module")
def playwright_mod():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
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


def _open(pw, page_path: Path, route: str, init: str | None = None):
    browser = pw.chromium.launch()
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:")) else r.abort())
    if init:
        context.add_init_script(init)
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(page_path.as_uri() + route)
    if page_path == TRAINING:
        page.wait_for_function("window.NexusTrainingPage && window.NexusTrainingPage.stage() !== null")
    else:
        page.wait_for_function("!!document.body.getAttribute('data-page')")
    return browser, page, errors


GAME = "(() => { const s = SkySentinel.get('fixed').state(); return { state: s.state, pausedBy: s.pausedBy, tick: s.tick }; })()"


def test_hidden_host_start_and_resume_stay_paused_without_a_second_loop(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page, errors = _open(pw, TRAINING, "#intro", init=LOOP_PROBE)
        try:
            page.evaluate("""() => {
              window.__events = [];
              const g = SkySentinel.get('fixed');
              g.on('start', () => __events.push('start'));
              g.on('resume', () => __events.push('resume'));
              g.on('pause', e => __events.push('pause:' + e.reason));
              document.querySelector('section[data-stage="play-fixed"]').style.display = 'none';
            }""")
            assert page.evaluate("document.querySelector('[data-ss-id=\"fixed\"]').offsetParent") is None
            assert page.evaluate("SkySentinel.ids().every(id => !SkySentinel.get(id).running())")
            before = page.evaluate("__loop.requested")
            page.evaluate("SkySentinel.get('fixed').start()")
            first = page.evaluate(GAME)
            assert first["state"] == "paused" and first["pausedBy"] == "stage", first
            assert page.evaluate("__events") == ["start", "pause:stage"]
            for _ in range(5):
                page.evaluate("__vis = 'hidden'; document.dispatchEvent(new Event('visibilitychange'))")
                page.evaluate("__vis = 'visible'; document.dispatchEvent(new Event('visibilitychange'))")
                page.evaluate("SkySentinel.get('fixed').resume(); SkySentinel.get('fixed').start()")
            page.keyboard.press("Escape")
            page.wait_for_timeout(600)
            after = page.evaluate(GAME)
            assert after == {**first}, "a hidden host stays paused with its stage reason and never ticks"
            assert page.evaluate("__loop.requested") == before, "a hidden host never asks for a frame"
            # Shown again, one Start runs it on exactly one loop, however often it is asked.
            page.evaluate("document.querySelector('section[data-stage=\"play-fixed\"]').style.display = ''")
            page.evaluate("SkySentinel.get('fixed').start(); SkySentinel.get('fixed').start(); SkySentinel.get('fixed').resume()")
            page.wait_for_function("SkySentinel.get('fixed').state().tick > " + str(first["tick"] + 10))
            assert page.evaluate("SkySentinel.get('fixed').state().state") == "running"
            assert page.evaluate("__loop.maxPending") == 1, "waking twice never starts a second loop"
            page.evaluate("SkySentinel.get('fixed').pause('user')")
            assert not errors, errors
        finally:
            browser.close()


# Training loads without a fragment: a fragment such as #plan moves the browser's sequential
# focus starting point to that section, so the first Tab would no longer start at the page top.
@pytest.mark.parametrize(("page_path", "route", "where"), [(TRAINING, "", "intro"), (GUIDE, "#foundations", "foundations")], ids=["training", "guide"])
def test_tab_from_the_top_reaches_the_skip_link_and_enter_lands_on_main(playwright_mod, page_path: Path, route: str, where: str) -> None:
    with playwright_mod() as pw:
        browser, page, errors = _open(pw, page_path, route)
        try:
            if page_path == GUIDE:
                page.wait_for_function("document.body.getAttribute('data-page') === 'foundations'")
            page.evaluate("window.scrollTo(0, 0)")
            hidden = page.evaluate("document.querySelector('.skip-link').getBoundingClientRect().bottom")
            assert hidden <= 0, "the skip link stays off screen until focused"
            page.keyboard.press("Tab")
            shown = page.evaluate("""() => { const a = document.activeElement, r = a.getBoundingClientRect(), s = getComputedStyle(a);
              return { cls: a.className, text: a.textContent, top: r.top, bottom: r.bottom, color: s.color, bg: s.backgroundColor,
                       z: s.zIndex, onTop: document.elementFromPoint(r.left + 4, r.top + r.height / 2) === a }; }""")
            assert shown["cls"] == "skip-link" and shown["text"] == "Skip to content", shown
            assert shown["top"] >= 0 and shown["bottom"] <= 80 and shown["onTop"], shown
            assert shown["color"] != shown["bg"], shown
            hash_before = page.evaluate("location.hash")
            page.keyboard.press("Enter")
            assert page.evaluate("document.activeElement.id") == "app"
            assert page.evaluate("location.hash") == hash_before, "the skip link never re-routes the page"
            if page_path == TRAINING:
                assert page.evaluate("NexusTrainingPage.stage()") == where
                assert page.locator("#trNotice").is_hidden()
            else:
                assert page.evaluate("document.body.getAttribute('data-page')") == where
            page.keyboard.press("Tab")
            assert page.evaluate("document.getElementById('app').contains(document.activeElement) && document.activeElement !== document.getElementById('app')")
            assert not errors, errors
        finally:
            browser.close()


def test_guide_marks_exactly_the_active_page_link_current(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page, errors = _open(pw, GUIDE, "#home")
        try:
            current = "els => els.filter(a => a.getAttribute('aria-current') === 'page').map(a => a.textContent)"
            assert page.locator("#navLinks a").evaluate_all(current) == ["Home"]
            for label, pid in (("Foundations", "foundations"), ("Cheatsheets", "cheatsheets"), ("Home", "home")):
                page.click(f"#navLinks a:text-is('{label}')")
                page.wait_for_function(f"document.body.getAttribute('data-page') === '{pid}'")
                assert page.locator("#navLinks a").evaluate_all(current) == [label]
                assert page.locator("#navLinks a.active").inner_text() == label
            assert not errors, errors
        finally:
            browser.close()


@pytest.mark.parametrize("page_path", [GUIDE, TRAINING], ids=["guide", "training"])
def test_theme_toggle_has_an_action_label_and_navigation_works_in_both_themes(playwright_mod, page_path: Path) -> None:
    with playwright_mod() as pw:
        browser, page, errors = _open(pw, page_path, "#home" if page_path == GUIDE else "#intro")
        try:
            toggle = "#themeToggle"
            for theme, label in (("dark", "Switch to light theme"), ("light", "Switch to dark theme"), ("dark", "Switch to light theme")):
                assert page.evaluate("document.documentElement.dataset.theme") == theme
                assert page.get_attribute(toggle, "aria-label") == label
                assert page.get_attribute(toggle, "aria-pressed") is None
                page.click(toggle)
            assert page.evaluate("document.documentElement.dataset.theme") == "light"
            if page_path == GUIDE:
                page.click("#navLinks a:text-is('Foundations')")
                page.wait_for_function("document.body.getAttribute('data-page') === 'foundations'")
                assert page.locator('#navLinks a[aria-current="page"]').inner_text() == "Foundations"
            else:
                assert page.locator('#navLinks a[aria-current="page"]').inner_text() == "Training"
                page.click("#navLinks a:text-is('Cheatsheets')")
                page.wait_for_url(re.compile(r"nexus-hub-guide\.html#cheatsheets$"))
                page.wait_for_function("document.body.getAttribute('data-page') === 'cheatsheets'")
                assert page.locator('#navLinks a[aria-current="page"]').inner_text() == "Cheatsheets"
            assert page.evaluate("document.documentElement.dataset.theme") == "light", "the chosen theme survives navigation"
            assert not errors, errors
        finally:
            browser.close()
