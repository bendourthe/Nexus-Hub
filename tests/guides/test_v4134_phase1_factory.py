"""v4.13.4 Phase 1: the arcade engine is an instance-per-element factory."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"



def _sync_playwright():
    """Import Playwright, skipping (or failing under NEXUS_REQUIRE_RENDER=1) when it is absent."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    return sync_playwright


@pytest.fixture()
def page():
    sync_playwright = _sync_playwright()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page(viewport={"width": 1440, "height": 940})
        errors: list[str] = []
        pg.on("pageerror", lambda error: errors.append(str(error)))
        pg.goto(GUIDE.as_uri() + "#training")
        yield pg, errors
        browser.close()


def test_factory_exposes_named_instances(page):
    pg, errors = page
    ids = pg.evaluate("() => window.NexusShooter.instances()")
    assert ids == ["buggy", "fixed", "featured"]
    assert pg.evaluate("() => window.NexusShooter.get('buggy').id") == "buggy"
    assert not errors, f"page errors: {errors}"


def test_three_game_roots_keep_independent_state(page):
    pg, errors = page
    pg.evaluate(
        "() => { const first = window.NexusShooter.get('buggy');"
        " first.start(); first.pause('manual');"
        " for (let i = 0; i < 5; i++) first.step(); }"
    )
    assert pg.evaluate("() => window.NexusShooter.get('buggy').snapshot().tick") == 5
    assert pg.evaluate("() => window.NexusShooter.get('fixed').snapshot().tick") == 0
    assert pg.evaluate("() => window.NexusShooter.get('featured').snapshot().tick") == 0
    assert not errors, f"page errors: {errors}"


def test_duplicate_game_ids_fail_before_partial_boot(tmp_path):
    sync_playwright = _sync_playwright()

    source = GUIDE.read_text(encoding="utf-8")
    marker = "  var registry = [];"
    injection = (
        '  var originalGame = document.querySelector("[data-arcade-game]");\n'
        "  originalGame.parentNode.appendChild(originalGame.cloneNode(true));\n"
    )
    guide_copy = tmp_path / "duplicate-games.html"
    guide_copy.write_text(source.replace(marker, injection + marker, 1), encoding="utf-8")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page()
        errors: list[str] = []
        pg.on("pageerror", lambda error: errors.append(str(error)))
        pg.goto(guide_copy.as_uri() + "#training")
        assert any("Duplicate arcade id: buggy" in error for error in errors)
        assert pg.evaluate("() => window.NexusShooter") is None
        browser.close()


def test_dispose_unregisters_instance(page):
    pg, errors = page
    pg.evaluate(
        "() => { window.retiredGame = window.NexusShooter.get('buggy');"
        " window.retiredGame.start(); window.retiredGame.pause('manual');"
        " document.querySelector('[data-arcade-game]').focus();"
        " window.retiredGame.dispose(); }"
    )
    assert pg.evaluate("() => window.NexusShooter.instances()") == ["fixed", "featured"]
    assert pg.evaluate("() => window.NexusShooter.get('buggy')") is None
    pg.evaluate(
        "() => { const root = document.querySelector('[data-arcade-game]');"
        " root.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowLeft', bubbles: true}));"
        " root.style.transform = 'translateY(-3000px)'; }"
    )
    pg.evaluate("() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)))")
    assert pg.evaluate("() => window.retiredGame.step().player.x") == 320
    assert "offscreen" not in pg.evaluate("() => window.retiredGame.snapshot().pauseReasons")
    assert not errors, f"page errors: {errors}"


def test_offscreen_instance_pauses(page):
    pg, errors = page
    pg.evaluate("() => window.NexusShooter.get('buggy').start()")
    pg.evaluate("() => document.querySelector('[data-arcade-game]').style.transform = 'translateY(-3000px)'")
    pg.wait_for_function(
        "() => window.NexusShooter.get('buggy').snapshot().pauseReasons.includes('offscreen')"
    )
    assert not errors, f"page errors: {errors}"
