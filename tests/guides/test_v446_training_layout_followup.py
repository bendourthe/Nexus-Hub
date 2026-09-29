"""Training heading and terminal regressions in the seven-section layout."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"
MOBILE = ((320, 900), (420, 900))
DESKTOP = ((1280, 720), (1366, 768), (1440, 900), (1920, 1080))
THEMES = ("light", "dark")


def _page(context, theme: str):
    context.route(re.compile(r"^https?://"), lambda route: route.abort())
    page = context.new_page()
    page.goto(f"{GUIDE.resolve().as_uri()}#training/describe-review", wait_until="load")
    page.wait_for_function("window.NexusTraining && window.NexusShooter")
    page.evaluate("theme => document.documentElement.setAttribute('data-theme', theme)", theme)
    return page


def _playwright(render_gate: Callable[[str], None]):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        render_gate("Playwright is not installed")
        raise
    return sync_playwright


def test_mobile_training_title_has_no_isolated_word_or_overflow(render_gate: Callable[[str], None]) -> None:
    sync_playwright = _playwright(render_gate)
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as error:
            render_gate(f"Playwright Chromium cannot launch: {error}")
            raise
        try:
            for width, height in MOBILE:
                for theme in THEMES:
                    context = browser.new_context(viewport={"width": width, "height": height})
                    page = _page(context, theme)
                    title = page.evaluate("""() => {
                        const el = document.querySelector('[data-nht-section="describe-review"] h2');
                        const node = el.firstChild;
                        const words = [...el.textContent.matchAll(/\S+/g)];
                        const rows = new Map();
                        for (const word of words) {
                            const range = document.createRange();
                            range.setStart(node, word.index);
                            range.setEnd(node, word.index + word[0].length);
                            const top = Math.round(range.getBoundingClientRect().top);
                            rows.set(top, (rows.get(top) || 0) + 1);
                        }
                        return {text: el.textContent, counts: [...rows.values()],
                            overflow: document.documentElement.scrollWidth > innerWidth + 1,
                            visible: el.getBoundingClientRect().width > 0};
                    }""")
                    assert title["text"] == "Map the bug, then review it"
                    assert title["visible"] and not title["overflow"], (width, theme, title)
                    assert title["counts"][-1] > 1 or len(title["counts"]) == 1, (width, theme, title)
                    context.close()
        finally:
            browser.close()


def test_section_idle_reply_and_run_output_remain_visible(render_gate: Callable[[str], None]) -> None:
    sync_playwright = _playwright(render_gate)
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as error:
            render_gate(f"Playwright Chromium cannot launch: {error}")
            raise
        try:
            for width, height in DESKTOP:
                for theme in THEMES:
                    context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
                    page = _page(context, theme)
                    section = page.locator('[data-nht-section="describe-review"]')
                    idle = section.locator('[data-nht="idle"]')
                    assert idle.is_visible(), (width, height, theme)
                    assert section.locator('[data-nht="output"]').inner_text() == ""
                    section.locator('[data-nht="run"]').click()
                    output = section.locator('[data-nht="output"]')
                    assert not idle.is_visible()
                    assert "has-run" in (section.locator('[data-nht="terminal"]').get_attribute("class") or "")
                    assert output.is_visible()
                    assert "Wrote docs/analysis.md." in output.inner_text()
                    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
                    context.close()
        finally:
            browser.close()
