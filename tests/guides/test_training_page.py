"""v4.13.10: the Training page is a second, self-contained offline page.

Static checks guard the publication contract (no external resources, a byte ceiling,
the shared fragments in place, the footer attribution). Browser checks guard routing:
every stage hash resolves, aliases resolve, an unknown hash falls back to the
introduction with a notice, and a page whose storage is blocked still works.

Browser tests skip when Playwright or Chromium is missing, and fail closed under
NEXUS_REQUIRE_RENDER=1 so CI cannot silently lose coverage.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
# Raised from 400,000 by the maintainer on 2026-10-04 (R5) for the shaded game art and IDE sessions.
TRAINING_CEILING_BYTES = 900_000

STAGES = ["intro", "play-buggy", "describe", "review", "plan", "implement", "test", "update", "play-fixed"]


@pytest.fixture(scope="module")
def html() -> str:
    return TRAINING.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def test_training_page_stays_under_its_byte_ceiling() -> None:
    size = len(TRAINING.read_bytes().replace(b"\r\n", b"\n"))
    assert size < TRAINING_CEILING_BYTES, f"training.html is {size} bytes (LF), ceiling {TRAINING_CEILING_BYTES}"


def test_training_page_loads_no_external_resource(html: str) -> None:
    assert not re.search(r"<script\b[^>]*\bsrc=", html, re.IGNORECASE), "no <script src>: the page must work offline"
    assert not re.search(r"<link\b[^>]*rel=\"stylesheet\"", html, re.IGNORECASE)
    loads = re.findall(r'\bsrc="([^"]+)"', html) + re.findall(r'<link\b[^>]*\bhref="([^"]+)"', html)
    for url in loads:
        assert not re.match(r"(?:[a-z]+:)?//", url, re.IGNORECASE), f"the page loads an external resource: {url}"
    allowed = {
        "https://github.com/bendourthe/Nexus-Hub",
        "https://creativecommons.org/licenses/by/4.0/",
        # Maintainer review (2026-10-04): the reward for defeating the Nexus boss links to Nexus AI Studio.
        "https://github.com/bendourthe/Nexus-AI/releases/latest/download/NexusSetup.exe",
        "https://github.com/bendourthe/Nexus-AI/releases/latest",
    }
    for url in re.findall(r'<a\b[^>]*\bhref="(https?:[^"]+)"', html):
        assert url in allowed, f"unexpected outbound link: {url}"


def test_shared_fragments_are_current() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "stamp_guide_shared.py"), "--check"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_footer_attribution_travels_inside_the_page(html: str) -> None:
    assert 'class="site-footer"' in html
    assert "Codicons icon set by Microsoft Corporation" in html
    assert "CC BY 4.0" in html


def test_every_stage_has_one_section_with_a_heading(html: str) -> None:
    found = re.findall(r'data-stage="([^"]+)"', html)
    assert found == STAGES
    for stage in STAGES:
        block = re.search(r'data-stage="' + re.escape(stage) + r'"[^>]*>(.*?)</section>', html, re.DOTALL)
        assert block and re.search(r"<h[12]\b", block.group(1)), stage
    assert len(re.findall(r"<h1\b", html)) == 1, "one scrolling page carries one h1"


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


def _open(pw, route: str = "#intro", block_storage: bool = False):
    browser = pw.chromium.launch()
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    external: list[str] = []

    def guard(request_route):
        url = request_route.request.url
        if url.startswith(("file:", "data:")):
            request_route.continue_()
        else:
            external.append(url)
            request_route.abort()

    context.route("**/*", guard)
    if block_storage:
        context.add_init_script(
            "Object.defineProperty(window, 'localStorage', {get() { throw new Error('blocked'); }});"
        )
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto(TRAINING.as_uri() + route)
    page.wait_for_function("window.NexusTrainingPage && window.NexusTrainingPage.stage() !== null")
    return browser, page, errors, external


def test_every_stage_hash_resolves_offline(playwright_mod) -> None:
    """v4.13.10 R3: one scrolling page; every hash lands its section just under the header."""
    with playwright_mod() as pw:
        browser, page, errors, external = _open(pw)
        try:
            assert page.evaluate("NexusTrainingPage.stages()") == STAGES
            assert page.locator("section[data-stage]:visible").count() == len(STAGES), "every stage is on the page"
            for stage in STAGES:
                page.evaluate(f"NexusTrainingPage.go('{stage}')")
                page.wait_for_function(f"NexusTrainingPage.stage() === '{stage}'")
                top = page.evaluate(f"document.querySelector('section[data-stage=\"{stage}\"]').getBoundingClientRect().top")
                if stage != "play-fixed":
                    assert 40 <= top <= 140, (stage, top)
            assert not errors, errors
            assert not external, external
        finally:
            browser.close()


def test_training_is_one_scrolling_page_in_workflow_order(playwright_mod) -> None:
    """Maintainer review (R3, revision 2): no stage switching, no Continue buttons, one pass of six steps."""
    with playwright_mod() as pw:
        browser, page, errors, _external = _open(pw)
        try:
            order = page.evaluate("[...document.querySelectorAll('main > section')].map(s => s.id)")
            assert order == STAGES
            assert page.locator(".tr-next").count() == 0
            tops = page.evaluate("[...document.querySelectorAll('section[data-stage]')].map(s => s.getBoundingClientRect().top)")
            assert tops == sorted(tops), "the stages follow one another down the page"
            assert not errors, errors
        finally:
            browser.close()

def test_aliases_and_unknown_hashes(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page, _errors, _external = _open(pw, "#")
        try:
            assert page.evaluate("NexusTrainingPage.stage()") == "intro"
            assert page.locator("#trNotice").is_hidden()
            # Links from the two-loop page land on the matching part of the one pass.
            for old, new in (("loop2/describe", "describe"), ("loop1/implement", "implement"), ("play-partial", "review")):
                page.evaluate(f"location.hash = '#{old}'")
                page.wait_for_function(f"NexusTrainingPage.stage() === '{new}'")
            page.evaluate("location.hash = '#no-such-stage'")
            page.wait_for_function("NexusTrainingPage.stage() === 'intro'")
            assert page.locator("#trNotice").is_visible()
            assert page.evaluate("location.hash") == "#intro"
            page.evaluate("location.hash = '#plan'")
            page.wait_for_function("NexusTrainingPage.stage() === 'plan'")
            page.evaluate("location.hash = '#s-anything'")
            page.wait_for_timeout(100)
            assert page.evaluate("NexusTrainingPage.stage()") == "plan", "an in-stage anchor never changes the stage"
        finally:
            browser.close()


def test_blocked_storage_falls_back_to_defaults(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page, errors, _external = _open(pw, "#intro", block_storage=True)
        try:
            assert page.evaluate("document.documentElement.dataset.theme") == "dark"
            page.click("#themeToggle")
            assert page.evaluate("document.documentElement.dataset.theme") == "light"
            assert not [e for e in errors if "blocked" in e], errors
        finally:
            browser.close()


def test_menu_links_point_back_to_the_guide(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page, _errors, _external = _open(pw)
        try:
            hrefs = page.locator("#navLinks a").evaluate_all("els => els.map(a => a.getAttribute('href'))")
            assert hrefs[:4] == [
                "nexus-hub-guide.html#home",
                "nexus-hub-guide.html#foundations",
                "training.html#intro",
                "nexus-hub-guide.html#cheatsheets",
            ]
            assert page.locator('#navLinks a[aria-current="page"]').inner_text() == "Training"
            assert page.locator("#site-footer").is_visible()
        finally:
            browser.close()


def test_starting_a_game_brings_it_into_view(playwright_mod) -> None:
    """Maintainer review (WN-3): at 1440 x 900 the arena starts below the fold; Start scrolls it in."""
    with playwright_mod() as pw:
        browser, page, _errors, _external = _open(pw, "#play-buggy")
        try:
            page.set_viewport_size({"width": 1440, "height": 900})
            page.evaluate("window.scrollTo(0, 0)")
            host = '[data-ss-id="buggy"]'
            assert page.evaluate(f"document.querySelector('{host}').getBoundingClientRect().bottom") > 900
            # A DOM click, not page.click(): Playwright's click scrolls its target into view itself.
            page.evaluate("h => document.querySelector(h + ' .ss-start').click()", host)
            page.wait_for_function(
                "h => { const r = document.querySelector(h).getBoundingClientRect();"
                " return r.top >= 0 && r.bottom <= innerHeight + 1; }",
                arg=host,
            )
        finally:
            browser.close()


SESSION = 'section[data-stage="review"]'
DEFEAT_BOSS = """() => { const g = SkySentinel.get('fixed'); SkySentinel.manual(true);
  g.configure({ level: 3, bossNow: true }); g.start(); g.step(600);
  for (let i = 0; i < 4; i++) g.hitBoss('node' + i, 8); g.hitBoss('core', 24); SkySentinel.manual(false); }"""


def test_reduced_motion_never_hides_a_report(playwright_mod) -> None:
    """Revision 2: under reduced motion every step shows its finished frame, with its controls."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
            page.goto(TRAINING.as_uri() + "#review")
            page.wait_for_function("window.NexusTrainingPage && NexusTrainingPage.stage() === 'review'")
            assert page.evaluate("NexusTrainingPage.story().state('review').done")
            assert page.locator(f"{SESSION} .ide-reply h3").count() >= 1
            assert page.locator(f"{SESSION} .ide-player").is_visible()
        finally:
            browser.close()


def test_the_fixed_game_is_presented_as_a_reward_with_a_hint(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page, _errors, _external = _open(pw, "#play-fixed")
        try:
            banner = page.locator('section[data-stage="play-fixed"] .tr-head, section[data-stage="play-fixed"] .tr-notes')
            text = " ".join(banner.all_inner_texts()).lower()
            assert "the reward" in text
            assert "something is waiting at the end" in text
            assert page.locator(".tr-jump-boss").count() == 0, "the boss is a surprise, not a shortcut"
            assert page.evaluate("NexusTrainingPage.reward()") is False
            assert not page.locator("#trReward").is_visible()
        finally:
            browser.close()


def test_defeating_the_nexus_boss_opens_the_reward_and_download(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser, page, errors, external = _open(pw, "#play-fixed")
        try:
            page.evaluate(DEFEAT_BOSS)
            page.wait_for_function("NexusTrainingPage.reward()")
            reward = page.locator("#trReward")
            assert reward.is_visible()
            assert page.locator("#trRewardTitle").inner_text() == "You defeated the Nexus boss"
            assert page.evaluate("document.activeElement.id") == "trReward"
            assert page.locator(".tr-download").get_attribute("href") == (
                "https://github.com/bendourthe/Nexus-AI/releases/latest/download/NexusSetup.exe"
            )
            assert page.locator(".tr-trailer .tr-scene").count() == 6
            assert len(page.locator(".tr-trailer").get_attribute("aria-label")) > 80
            assert not errors, errors
            assert not external, "the reward links out but loads nothing"
        finally:
            browser.close()
