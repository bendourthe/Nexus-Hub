"""v4.13.4 Phase 4: the arcade uses a wide logical world and DPR backing store."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"


@pytest.fixture()
def page():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page(viewport={"width": 1440, "height": 940})
        errors: list[str] = []
        pg.on("pageerror", lambda error: errors.append(str(error)))
        pg.goto(GUIDE.as_uri() + "#training")
        pg.wait_for_function("window.NexusShooter && window.NexusShooter.instances().length")
        yield pg, errors
        browser.close()


def test_arena_is_landscape(page):
    pg, errors = page
    world = pg.evaluate("() => window.NexusShooter.world")
    assert (world["width"], world["height"]) == (640, 400)
    assert not errors, errors


def test_backing_store_matches_device_pixel_ratio(page):
    pg, errors = page
    got = pg.evaluate(
        """() => {
          const c = document.querySelector('[data-arcade-canvas]');
          const dpr = window.devicePixelRatio || 1;
          const w = window.NexusShooter.world.width, h = window.NexusShooter.world.height;
          const t = c.getContext('2d').getTransform();
          return {width: c.width, height: c.height, expectedWidth: Math.round(w*dpr),
                  expectedHeight: Math.round(h*dpr), scaleX: t.a, scaleY: t.d, dpr};
        }"""
    )
    assert (got["width"], got["height"]) == (got["expectedWidth"], got["expectedHeight"])
    assert (got["scaleX"], got["scaleY"]) == (got["dpr"], got["dpr"])
    assert not errors, errors


def test_stage_keeps_eight_to_five_ratio_after_resize(page):
    pg, errors = page
    for width in (1440, 700, 420):
        pg.set_viewport_size({"width": width, "height": 940})
        box = pg.locator(".nag-stage").first.bounding_box()
        assert box is not None
        assert abs(box["width"] / box["height"] - 8 / 5) < 0.02, (width, box)
    assert not errors, errors


def test_section_stages_and_canvases_stay_inside_their_game_panels(page):
    pg, errors = page
    for width in (1440, 420):
        pg.set_viewport_size({"width": width, "height": 940})
        results = pg.evaluate(
            """() => [...document.querySelectorAll('[data-arcade-game]')].map(root => {
              const game = root.getBoundingClientRect();
              const stage = root.querySelector('.nag-stage').getBoundingClientRect();
              const canvas = root.querySelector('.nag-canvas').getBoundingClientRect();
              const inside = (outer, inner) => inner.left >= outer.left - 1 && inner.right <= outer.right + 1
                  && inner.top >= outer.top - 1 && inner.bottom <= outer.bottom + 1;
              return {id: root.dataset.arcadeId, stage: inside(game, stage), canvas: inside(stage, canvas)};
            })"""
        )
        assert len(results) == 3 and all(item["stage"] and item["canvas"] for item in results), (width, results)
    assert not errors, errors


def test_two_x_backing_store_survives_steps_and_resize():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page(viewport={"width": 1440, "height": 940}, device_scale_factor=2)
        errors: list[str] = []
        pg.on("pageerror", lambda error: errors.append(str(error)))
        pg.goto(GUIDE.as_uri() + "#training")
        pg.wait_for_function("window.NexusShooter && window.NexusShooter.instances().length")
        observe = """() => {
          const c=document.querySelector('[data-arcade-canvas]');
          const t=c.getContext('2d').getTransform();
          return [c.width,c.height,t.a,t.d];
        }"""
        assert pg.evaluate(observe) == [1280, 800, 2, 2]
        pg.evaluate("() => { const g=window.NexusShooter.get('buggy'); g.start(); for(let i=0;i<15;i++) g.step(); }")
        assert pg.evaluate(observe) == [1280, 800, 2, 2]
        pg.set_viewport_size({"width": 700, "height": 940})
        assert pg.evaluate(observe) == [1280, 800, 2, 2]
        assert not errors, errors
        browser.close()


def test_wide_fixtures_retain_damage_and_asteroid_outcomes(page):
    pg, errors = page
    outcomes = pg.evaluate(
        """() => {
          const g=window.NexusShooter.get('buggy');
          function finish(fixture, mode) {
            g.reset(fixture);g.setDamageMode(mode);g.start();
            for(let i=0;i<700 && g.snapshot().lifecycle!=='destroyed';i++) g.step();
            const s=g.snapshot();return {lifecycle:s.lifecycle,lives:s.lives,tick:s.tick};
          }
          return {buggy:finish('enemy-hit','buggy'),fixed:finish('enemy-hit','fixed'),
                  asteroid:finish('asteroid-hit','fixed')};
        }"""
    )
    assert outcomes["buggy"]["lifecycle"] == "destroyed"
    assert outcomes["buggy"]["lives"] == 3
    assert outcomes["fixed"]["lifecycle"] == "destroyed"
    assert outcomes["fixed"]["lives"] == 0
    assert outcomes["fixed"]["tick"] > outcomes["buggy"]["tick"]
    assert outcomes["asteroid"]["lifecycle"] == "destroyed"
    assert outcomes["asteroid"]["lives"] == 3
    assert not errors, errors
