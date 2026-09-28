"""Training layout regressions carried forward from the retired v4.4 fullscreen deck.

v4.13.4 replaces the deck, Outline, and presentation controls with seven stacked
sections. These tests retain the original visible-region, keyboard, and route-change
concerns against the current layout.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
SIZES = ((1920, 1080), (1440, 900), (1366, 768), (1280, 720), (900, 900), (420, 900))


@pytest.fixture(scope="module")
def playwright_mod():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    with sync_playwright() as playwright:
        try:
            playwright.chromium.launch().close()
        except Exception as error:
            if REQUIRE_RENDER:
                pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {error}")
            pytest.skip(f"chromium is unavailable: {error}")
    return sync_playwright


@pytest.mark.parametrize("size", SIZES)
def test_section_widgets_are_contained_and_do_not_overlap(playwright_mod, size) -> None:
    width, height = size
    with playwright_mod() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
            page.goto(GUIDE.as_uri() + "#training/describe-review")
            page.wait_for_function("window.NexusTraining && window.NexusShooter")
            section = page.locator('[data-nht-section="describe-review"]')
            terminal = section.locator('[data-nht="terminal"]').bounding_box()
            explorer = section.locator('[data-nht="explorer"]').bounding_box()
            assert terminal and explorer
            overlap_width = max(0, min(terminal["x"] + terminal["width"], explorer["x"] + explorer["width"]) - max(terminal["x"], explorer["x"]))
            overlap_height = max(0, min(terminal["y"] + terminal["height"], explorer["y"] + explorer["height"]) - max(terminal["y"], explorer["y"]))
            assert overlap_width * overlap_height < 1, (size, terminal, explorer)
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"), size
            assert page.locator('#page-training section[data-nht-section] h2').count() == 7
        finally:
            browser.close()


def test_keyboard_navigation_and_route_change_leave_the_page_usable(playwright_mod) -> None:
    with playwright_mod() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 900, "height": 900}, reduced_motion="reduce")
            page.goto(GUIDE.as_uri() + "#training/game")
            page.wait_for_function("window.NexusTraining && window.NexusShooter")
            jump = page.get_by_role("navigation", name="Training sections").get_by_role("link", name="Compare")
            jump.focus()
            page.keyboard.press("Enter")
            page.wait_for_function("window.NexusTraining.snapshot().sectionId === 'compare'")
            assert page.evaluate("location.hash") == "#training/compare"
            page.evaluate("location.hash = '#home'")
            page.wait_for_function("document.body.getAttribute('data-page') === 'home'")
            assert not page.locator("#page-home").evaluate("node => node.inert")
            page.evaluate("location.hash = '#training/fixed-game'")
            page.wait_for_function("window.NexusTraining.snapshot().sectionId === 'fixed-game'")
            assert page.locator('[data-arcade-id="fixed"] [data-arcade-start]').is_visible()
        finally:
            browser.close()


def test_game_instances_have_independent_controls(playwright_mod) -> None:
    with playwright_mod() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            page.goto(GUIDE.as_uri() + "#training/game")
            page.wait_for_function("window.NexusTraining && window.NexusShooter")
            result = page.evaluate("""() => {
                const buggy = window.NexusShooter.get('buggy');
                const fixed = window.NexusShooter.get('fixed');
                const featured = window.NexusShooter.get('featured');
                buggy.reset('enemy-hit'); fixed.reset('enemy-hit'); featured.reset('play');
                buggy.start();
                return {buggy: buggy.snapshot().lifecycle, fixed: fixed.snapshot().lifecycle,
                    featured: featured.snapshot().lifecycle, ids: window.NexusShooter.instances()};
            }""")
            assert sorted(result["ids"]) == ["buggy", "featured", "fixed"]
            assert result["buggy"] != "idle"
            assert result["fixed"] == "idle" and result["featured"] == "idle"
        finally:
            browser.close()
