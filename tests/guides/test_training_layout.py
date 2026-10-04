"""v4.13.10 Phase 5: the Training page has no large empty areas (DoD 10).

Every stage is measured at 1280 px and 390 px in both themes with the empty-rectangle
measure recorded in docs/releases/v4/v4.13/development/v4.13.10-inventory.md. A self-test
proves the same measure fails on a layout like the v4.13.4 Training, so a passing result
means the page is dense, not that the measure is blind. Skipped without Playwright or
Chromium; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

_spec = importlib.util.spec_from_file_location("empty_space", Path(__file__).parent / "tools" / "empty_space.py")
empty_space = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(empty_space)


@pytest.fixture(scope="module")
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception as exc:  # pragma: no cover - environment dependent
            if REQUIRE_RENDER:
                pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
            pytest.skip(f"chromium is unavailable: {exc}")
        yield b
        b.close()


def test_the_measure_flags_a_layout_like_v4134(browser, tmp_path: Path) -> None:
    fixture = tmp_path / "old.html"
    fixture.write_text(
        """<!doctype html><html><body style="margin:0;background:#07141a">
        <section id="s" style="width:1072px;padding:24px;box-sizing:content-box">
          <div style="width:700px;height:640px;background:#0c1f26;border:1px solid #123038"></div>
          <div style="width:500px;height:300px;margin-top:16px;background:#0c1f26"></div>
        </section></body></html>""",
        encoding="utf-8",
    )
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    try:
        page.goto(fixture.as_uri())
        result = empty_space.largest_empty_rect(page.locator("#s"))
        assert empty_space.too_empty(result, 1280), result
    finally:
        page.close()


@pytest.mark.parametrize("width", [1280, 390])
@pytest.mark.parametrize("theme", ["dark", "light"])
def test_no_stage_has_a_large_empty_area(browser, width: int, theme: str) -> None:
    context = browser.new_context(viewport={"width": width, "height": 900}, color_scheme=theme)
    context.add_init_script(f"try {{ localStorage.setItem('portfolio-theme', '{theme}'); }} catch (e) {{}}")
    page = context.new_page()
    try:
        page.goto(TRAINING.as_uri() + "#intro")
        page.wait_for_function("window.NexusTrainingPage && NexusTrainingPage.story()")
        failures = []
        for stage in page.evaluate("NexusTrainingPage.stages()"):
            page.evaluate(f"location.hash = '#{stage}'")
            page.wait_for_function(f"NexusTrainingPage.stage() === '{stage}'")
            page.wait_for_timeout(60)
            result = empty_space.largest_empty_rect(page.locator(f'section[data-stage="{stage}"] > .container'))
            if empty_space.too_empty(result, width):
                failures.append((stage, result))
        assert not failures, failures
    finally:
        context.close()


def test_the_arena_fits_with_its_banner_on_a_desktop(browser) -> None:
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    try:
        page.goto(TRAINING.as_uri() + "#play-buggy")
        page.wait_for_function("window.SkySentinel && SkySentinel.get('buggy')")
        top = page.evaluate("document.querySelector('[data-ss-id=buggy] .ss-canvas').getBoundingClientRect().top")
        assert top < 900 * 0.6, f"the arena starts at {top}px; the banner and callout should leave most of it on the first screen"
    finally:
        page.close()
