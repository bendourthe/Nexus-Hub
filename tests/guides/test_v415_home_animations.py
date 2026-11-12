"""v4.15: Home follows the README, with the README's own animations beside the guide.

Decision: docs/decisions/implemented/architecture/2026-11-10-guide-home-shows-readme-animations.md.
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "guides" / "website"
GUIDE = WEB / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
ANIMATIONS = ("workflow", "settings", "usage", "continuity", "platforms")
# 2026-11-10 (second pass): the maintainer's order; the hero above Installation already says what Nexus Hub is.
HOME_ORDER = ["Installation", "Platform Coverage", "The Development Workflow", "Centralized IDE Settings", "Handoffs",
              "Usage Monitors", "Why Nexus Hub"]
HOME_ANIMATION_ORDER = ("platforms", "workflow", "settings", "continuity", "usage")
WHY_CARDS = ["Multiplatform Intelligence", "Expert Skills", "Repeatable Workflow", "Enforced Guardrails",
             "Centralized Settings", "Monitoring & Continuity"]


def _home() -> str:
    html = GUIDE.read_text(encoding="utf-8")
    start = html.index('id="page-home"')
    return html[start : html.index('<section class="page', start + 10)]


@pytest.mark.parametrize("name", ANIMATIONS)
def test_each_animation_is_a_byte_identical_readme_copy_with_a_poster(name: str) -> None:
    for ext in ("gif", "png"):
        copy, source = WEB / "assets" / f"nexus-hub-{name}.{ext}", ROOT / "assets" / "readme" / f"nexus-hub-{name}.{ext}"
        assert copy.read_bytes() == source.read_bytes(), f"{copy.name} drifted from assets/readme; copy it again"
    figures = {re.search(r'src="assets/nexus-hub-([a-z]+)\.gif"', f).group(1): f
               for f in re.findall(r'<figure class="demo-fig"><picture>(.*?)</picture></figure>', _home(), re.S)}
    figure = figures[name]
    assert f'<source media="(prefers-reduced-motion: reduce)" srcset="assets/nexus-hub-{name}.png">' in figure
    assert 'loading="lazy"' in figure and 'alt="' in figure


def test_home_follows_the_readme_order_without_the_repeated_sections() -> None:
    home = _home()
    assert re.findall(r'<h2 data-ty="h2" class="section-title">([^<]+)</h2>', home) == HOME_ORDER
    for removed in ('id="nhg-how"', 'class="ph-switch"', 'id="nhg-loop"', "Raw Prompting vs Nexus Hub", 'class="tbl-migrate"',
                    'id="nhg-guardrails"', 'class="guard-fig"', 'class="cmp"'):
        assert removed not in home, f"{removed} left Home in the 2026-11-10 restructure"


def test_why_nexus_hub_closes_with_one_card_per_benefit_and_a_call_to_action() -> None:
    home = _home()
    why = home[home.index('id="nhg-why"') :]
    cards = re.findall(r'<li class="why-card seq-rise" data-seq="(\d)"[^>]*>(.*?)</li>', why, re.DOTALL)
    assert [html.unescape(re.search(r"<h3[^>]*>([^<]+)</h3>", body).group(1)) for _, body in cards] == WHY_CARDS
    for _, body in cards:
        assert re.match(r'<div class="why-head"><span class="ico"[^>]*>.*?</svg></span><h3 ', body, re.DOTALL), "icon sits beside the title"
    assert [int(n) for n, _ in cards] == list(range(1, len(WHY_CARDS) + 1)), "cards reveal in reading order"
    for _, body in cards:
        assert 'class="why-with"' in body and '<span data-ty="eyebrow" data-tone="warn" class="why-tag">Without</span>' in body
    assert "data-seq-root" in why and '<span data-count="skills">' in why
    assert '<a class="btn btn--primary" href="#home/install" data-go="home/install">' in why
    assert '<a class="btn" href="training.html" data-training-link>' in why
    assert "makes ai safe" not in re.sub(r"<[^>]+>", " ", why).lower(), "an enforcement statement, not a safety guarantee"


def test_the_builtin_comparison_lives_on_cheatsheets() -> None:
    html = GUIDE.read_text(encoding="utf-8")
    catalog = html[html.index('id="cs-catalog"') :]
    catalog = catalog[: catalog.index("</section>")]
    assert "Built-in Commands Compared" in catalog and 'class="tbl-migrate"' in catalog


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


def test_reduced_motion_shows_the_still_posters(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            page.goto(GUIDE.as_uri())
            sources = page.evaluate("""async () => { const imgs = [...document.querySelectorAll('#page-home .demo-fig img')];
              imgs.forEach(i => { i.loading = 'eager'; });
              await Promise.all(imgs.map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
              return imgs.map(i => [i.currentSrc.split('/').pop(), i.naturalWidth > 0]); }""")
        finally:
            browser.close()
    assert [name for name, _ in sources] == [f"nexus-hub-{n}.png" for n in HOME_ANIMATION_ORDER], sources
    assert all(loaded for _, loaded in sources), sources


def test_the_installer_terminal_keeps_its_newest_line_in_a_fixed_frame(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(GUIDE.as_uri())
            # The guide opens the detected system's tab, so select Windows explicitly on any host.
            page.locator("#install-tab-win").click()
            terminal = page.locator('[data-tm="win"]')
            terminal.scroll_into_view_if_needed()
            terminal.evaluate("el => new Promise(r => { const t = setInterval(() => { if (el.querySelectorAll('.tm-l.is-on').length > 20) { clearInterval(t); r(); } }, 50); })")
            frame = terminal.evaluate("""el => { const body = el.querySelector('.tm-body'), box = body.getBoundingClientRect();
              const last = [...el.querySelectorAll('.tm-l.is-on')].at(-1).getBoundingClientRect();
              return { height: Math.round(box.height), scrolled: body.scrollTop > 0, inView: last.top >= box.top - 1 && last.bottom <= box.bottom + 1 }; }""")
        finally:
            browser.close()
    assert frame == {"height": 350, "scrolled": True, "inView": True}, frame


def test_why_cards_reveal_on_scroll_and_the_install_button_returns_to_installation(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        try:
            results = {}
            for motion in ("no-preference", "reduce"):
                page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion=motion)
                page.goto(GUIDE.as_uri())
                page.wait_for_function("window.NexusSeq")
                hidden = page.evaluate("() => [...document.querySelectorAll('#nhg-why .why-card')].filter(c => getComputedStyle(c).opacity === '0').length")
                page.locator("#nhg-why-grid").scroll_into_view_if_needed()
                page.wait_for_function("() => { const s = NexusSeq.state(document.getElementById('nhg-why-grid')); return s && s.step === s.total; }", timeout=5000)
                page.wait_for_timeout(600)
                shown = page.evaluate("() => [...document.querySelectorAll('#nhg-why .why-card')].every(c => getComputedStyle(c).opacity === '1')")
                page.click('#nhg-why a[data-go="home/install"]')
                page.wait_for_function("() => Math.abs(document.getElementById('nhg-install').getBoundingClientRect().top) < 2", timeout=5000)
                results[motion] = (hidden, shown, page.evaluate("location.hash"))
                page.close()
        finally:
            browser.close()
    assert results["no-preference"] == (6, True, "#home/install"), results
    assert results["reduce"][1:] == (True, "#home/install"), results
