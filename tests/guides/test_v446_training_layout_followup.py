"""Browser regressions for the bounded v4.4 Training heading and idle-terminal repair."""

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
    page.goto(f"{GUIDE.resolve().as_uri()}#training/describe", wait_until="load")
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


def test_mobile_training_title_has_no_isolated_word_or_overflow(
    render_gate: Callable[[str], None],
) -> None:
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
                    title = page.evaluate(
                        """() => {
                          const el = document.querySelector('[data-nht="title"]');
                          const node = el.firstChild;
                          const words = [...el.textContent.matchAll(/\\S+/g)];
                          const rows = new Map();
                          for (const word of words) {
                            const range = document.createRange();
                            range.setStart(node, word.index);
                            range.setEnd(node, word.index + word[0].length);
                            const top = Math.round(range.getBoundingClientRect().top);
                            rows.set(top, (rows.get(top) || 0) + 1);
                          }
                          return {
                            text: el.textContent,
                            counts: [...rows.values()],
                            overflow: document.documentElement.scrollWidth > innerWidth + 1,
                            visible: el.getBoundingClientRect().width > 0,
                          };
                        }"""
                    )
                    assert title["text"] == "Trace the damage"
                    assert title["visible"] and not title["overflow"], (width, theme, title)
                    assert title["counts"][-1] > 1 or len(title["counts"]) == 1, (
                        width,
                        theme,
                        title,
                    )
                    context.close()
        finally:
            browser.close()


def test_fullscreen_idle_reply_is_compact_and_run_output_remains_visible(
    render_gate: Callable[[str], None],
) -> None:
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
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        reduced_motion="reduce",
                    )
                    page = _page(context, theme)
                    page.locator("#nhtPresent").click()
                    page.wait_for_function(
                        "document.getElementById('nhTraining').classList.contains('is-present')"
                    )
                    idle = page.evaluate(
                        """() => {
                          const term = document.querySelector('.term--nht');
                          return {
                            height: term.getBoundingClientRect().height,
                            outputDisplay: getComputedStyle(document.querySelector('.nht-out')).display,
                            placeholderVisible: document.querySelector('.nht-idle').getBoundingClientRect().height > 0,
                          };
                        }"""
                    )
                    assert idle["placeholderVisible"] and idle["outputDisplay"] == "none", (
                        width,
                        height,
                        theme,
                        idle,
                    )
                    assert idle["height"] < height * 0.3, (width, height, theme, idle)

                    page.locator('[data-nht="run"]').click()
                    page.wait_for_function(
                        "document.querySelector('[data-nht=\"run\"]').textContent === 'Run again'"
                    )
                    terminal = page.locator('[data-nht="terminal"]')
                    output = page.locator('[data-nht="output"]')
                    assert terminal.get_attribute("class") is not None
                    assert "has-run" in (terminal.get_attribute("class") or "")
                    assert output.is_visible()
                    assert "Wrote docs/analysis.md." in output.inner_text()
                    last_line_visible = page.evaluate(
                        """() => {
                          const output = document.querySelector('[data-nht="output"]');
                          output.scrollTop = output.scrollHeight;
                          const panel = output.getBoundingClientRect();
                          const last = output.lastElementChild.getBoundingClientRect();
                          return last.top >= panel.top - 1 && last.bottom <= panel.bottom + 1;
                        }"""
                    )
                    assert last_line_visible, (width, height, theme)
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth + 1"
                    )
                    context.close()
        finally:
            browser.close()
