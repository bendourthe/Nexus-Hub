"""v4.4.1 arcade-shooter engine suite: the executable half of arcade-shooter-scenario.md.

Every test here drives the REAL engine in a real browser through its public seam,
`window.NexusShooter`, because the engine only exists inside the shipped page. The suite
replaces `test_asteroids_game.py` wholesale, per the Phase 1 superseded-assertion register:
the wrap-collision scenario retired with its engine, and keeping its assertions alive would
have tested history.

Determinism is the load-bearing property: a seeded fixed-step world is what makes the
Training walkthrough honest, because the learner and the tests see the same game.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

ROUTES = ("describe", "review", "plan", "implement", "compare", "test", "update", "presentify")


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


@pytest.fixture()
def page_ctx(playwright_mod):
    """A fresh page at the Training route with the engine booted."""
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 940})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(GUIDE.as_uri() + "#training/describe")
        page.wait_for_function("window.NexusShooter && window.NexusTraining")
        yield page, errors
        browser.close()


def run_js(page, script: str):
    return page.evaluate("() => { const api = window.NexusShooter; " + script + " }")


# ------------------------------------------------------------------------ determinism


def test_equal_seed_and_inputs_produce_deep_equal_snapshots(page_ctx) -> None:
    page, errors = page_ctx
    result = run_js(page, """
        const run = () => {
            api.reset('play'); api.setDamageMode('fixed'); api.start();
            api.input('left', true);
            let s; for (let i = 0; i < 240; i++) s = api.step();
            api.input('left', false);
            const copy = JSON.parse(JSON.stringify(s)); delete copy.generation; return copy;
        };
        return [run(), run()];
    """)
    assert result[0] == result[1], "two runs with one seed and identical inputs diverged"
    assert not errors


def test_snapshots_are_deep_frozen_and_detached(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('enemy-hit'); api.start(); api.step();
        const a = api.snapshot();
        let mutated = true;
        try { a.lives = 99; a.player.x = -1; a.enemyShots.push({}); } catch (e) { mutated = false; }
        const b = api.snapshot();
        return {frozen: Object.isFrozen(a) && Object.isFrozen(a.player) && Object.isFrozen(a.enemyShots),
                detachedLives: b.lives, mutated};
    """)
    assert result["frozen"], "snapshots must be deep-frozen"
    assert result["detachedLives"] == 3, "mutating a snapshot must never reach the engine"


def test_invalid_inputs_are_rejected_without_state_change(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('enemy-hit'); api.start(); for (let i = 0; i < 10; i++) api.step();
        const before = JSON.stringify(api.snapshot());
        api.reset; // no-op reference
        api.setDamageMode('chaotic');
        api.setVerticalMovementEnabled('yes');
        api.pause('coffee-break');
        api.resume('coffee-break');
        api.input('warp', true);
        const after = JSON.stringify(api.snapshot());
        const badFixture = api.reset('not-a-fixture');
        return {unchanged: before === after, fallbackFixture: badFixture.fixture};
    """)
    assert result["unchanged"], "an invalid call corrupted engine state"
    assert result["fallbackFixture"] == "enemy-hit", (
        "an unknown fixture must fall back to the current one, not explode or blank the game"
    )


# --------------------------------------------------------------------- world mechanics


def test_threats_originate_at_the_top_and_travel_downward(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('play'); api.start();
        let spawnedEnemies = [], spawnedRocks = [];
        for (let i = 0; i < 900; i++) {
            const s = api.step();
            for (const e of s.enemies) if (!spawnedEnemies.find(x => x.id === e.id)) spawnedEnemies.push(e);
            for (const a of s.asteroids) if (!spawnedRocks.find(x => x.id === a.id)) spawnedRocks.push(a);
        }
        const shots = api.snapshot().enemyShots;
        return {
            enemyBirthYs: spawnedEnemies.map(e => e.y), enemyVys: spawnedEnemies.map(e => e.vy),
            rockBirthYs: spawnedRocks.map(a => a.y), rockVys: [...new Set(spawnedRocks.map(a => a.vy))].sort((x, y) => x - y),
            shotVys: shots.map(p => p.vy),
        };
    """)
    assert result["enemyBirthYs"] and result["rockBirthYs"], "the play fixture must spawn threats"
    assert all(y < 60 for y in result["enemyBirthYs"]), "enemies must originate near the top"
    assert all(vy > 0 for vy in result["enemyVys"]), "enemies must descend"
    assert all(y < 40 for y in result["rockBirthYs"]), "asteroids must originate at the top"
    assert result["rockVys"] == [60, 105], (
        f"asteroids must fall at exactly the two seeded speeds; saw {result['rockVys']}"
    )
    assert all(vy > 0 for vy in result["shotVys"]), "enemy shots must travel downward"


def test_player_is_bounded_and_fires_upward(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        // enemy-hit, not play: thirty simulated seconds parked at a wall inside the live
        // fixture gets the player killed by seeded spawns, which is correct behavior but
        // not this test's subject. The quiet fixture's only threats stay in the x=180 column.
        api.reset('enemy-hit'); api.setDamageMode('fixed'); api.start();
        api.input('left', true);
        for (let i = 0; i < 900; i++) api.step();
        const leftX = api.snapshot().player.x;
        api.input('left', false); api.input('right', true);
        for (let i = 0; i < 1800; i++) api.step();
        const rightX = api.snapshot().player.x;
        api.input('right', false); api.input('fire', true);
        api.step();
        const shot = api.snapshot().playerShots[0];
        api.input('fire', false);
        return {leftX, rightX, shotVy: shot.vy, shotY: shot.y, playerY: api.snapshot().player.y};
    """)
    assert result["leftX"] == 14 and result["rightX"] == 346, "horizontal clamp failed"
    assert result["shotVy"] < 0, "player shots must travel upward"
    assert result["shotY"] < result["playerY"], "shots leave from the nose"


def test_player_shot_destroys_one_target_and_scores_once(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('enemy-hit'); api.setDamageMode('fixed'); api.start();
        api.input('fire', true); api.step(); api.input('fire', false);
        let s = api.snapshot(), n = 0;
        while (s.enemies.length && n++ < 400) s = api.step();
        return {enemiesLeft: s.enemies.length, score: s.score, booms: s.explosions.length,
                shotConsumed: s.playerShots.length === 0};
    """)
    assert result["enemiesLeft"] == 0, "the shot must destroy the seeded enemy"
    assert result["score"] == 100, "exactly one score increment per resolution"
    assert result["shotConsumed"], "a resolving projectile is consumed"


# ------------------------------------------------------------------------ damage rules


def test_buggy_mode_first_enemy_hit_is_terminal_with_lives_intact(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('enemy-hit'); api.setDamageMode('buggy'); api.start();
        let s = api.snapshot(), n = 0;
        while (s.lifecycle !== 'destroyed' && n++ < 500) s = api.step();
        return {ticks: n, lives: s.lives, lifecycle: s.lifecycle, booms: s.explosions.length};
    """)
    assert result["lifecycle"] == "destroyed"
    assert result["lives"] == 3, "the seeded bug never spends a life; the ship just dies"
    assert result["booms"] == 1, "exactly one explosion"
    assert result["ticks"] < 120, "the pre-placed shot must land deterministically early"


def test_fixed_mode_walks_lives_three_to_zero_with_invulnerability(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('enemy-hit'); api.setDamageMode('fixed'); api.start();
        const livesSeen = [3]; let invulnAfterFirst = null, guard = 0;
        while (api.snapshot().lifecycle !== 'destroyed' && guard++ < 4000) {
            const s = api.step();
            if (s.lives !== livesSeen[livesSeen.length - 1]) {
                livesSeen.push(s.lives);
                if (livesSeen.length === 2) invulnAfterFirst = s.player.invulnerableTicks;
            }
        }
        const end = api.snapshot();
        return {livesSeen, invulnAfterFirst, lifecycle: end.lifecycle, booms: end.explosions.length};
    """)
    assert result["livesSeen"] == [3, 2, 1, 0], f"lives must walk 3->2->1->0; saw {result['livesSeen']}"
    assert result["invulnAfterFirst"] == 90, "a non-fatal hit grants the 90-tick window"
    assert result["lifecycle"] == "destroyed"
    assert result["booms"] == 1, "the third hit creates exactly one explosion"


def test_asteroid_contact_is_always_fatal_with_one_explosion(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('asteroid-hit'); api.setDamageMode('fixed'); api.start();
        let s = api.snapshot(), n = 0;
        while (s.lifecycle !== 'destroyed' && n++ < 500) s = api.step();
        return {lives: s.lives, booms: s.explosions.length, lifecycle: s.lifecycle};
    """)
    assert result["lifecycle"] == "destroyed"
    assert result["lives"] == 3, "asteroid fatality bypasses the lives system entirely"
    assert result["booms"] == 1


def test_destroyed_is_terminal_until_reset_or_restart(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('asteroid-hit'); api.start();
        let n = 0; while (api.snapshot().lifecycle !== 'destroyed' && n++ < 500) api.step();
        const deadTick = api.snapshot().tick;
        api.resume('manual'); api.pause('manual'); api.resume('manual');
        const afterPause = api.snapshot().lifecycle;
        api.step();
        const afterStep = api.snapshot().tick;
        const revived = api.restart();
        return {afterPause, stepHeld: afterStep === deadTick,
                revived: revived.lifecycle, revivedLives: revived.lives,
                newGeneration: revived.generation};
    """)
    assert result["afterPause"] == "destroyed", "pause/resume must not leave destroyed"
    assert result["stepHeld"], "step must be refused after destruction"
    assert result["revived"] == "running" and result["revivedLives"] == 3


# ------------------------------------------------------------------------ feature flag


def test_vertical_movement_is_gated_then_clamped(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('play'); api.setVerticalMovementEnabled(false); api.start();
        api.input('up', true);
        for (let i = 0; i < 60; i++) api.step();
        const gatedY = api.snapshot().player.y;
        api.setVerticalMovementEnabled(true);
        for (let i = 0; i < 120; i++) api.step();
        const topY = api.snapshot().player.y;
        api.input('up', false); api.input('down', true);
        for (let i = 0; i < 240; i++) api.step();
        const bottomY = api.snapshot().player.y;
        api.input('down', false);
        return {gatedY, topY, bottomY};
    """)
    assert result["gatedY"] == 440, "vertical input must be ignored before the feature"
    assert result["topY"] == 360, "upward travel clamps at the band top"
    assert result["bottomY"] == 460, "downward travel clamps at the band bottom"


# ------------------------------------------------------------------- lifecycle wiring


def test_idle_holds_the_world_until_click_to_start(page_ctx) -> None:
    page, _ = page_ctx
    run_js(page, "api.reset('enemy-hit');")
    page.wait_for_timeout(350)
    snap = page.evaluate("window.NexusShooter.snapshot()")
    assert snap["lifecycle"] == "idle" and snap["tick"] == 0, "idle must not advance"
    start = page.locator("[data-arcade-start]")
    assert start.is_visible(), "the start overlay button must be a real visible control"
    assert start.text_content().strip() == "Click to start"
    start.click()
    page.wait_for_timeout(120)
    after = page.evaluate("window.NexusShooter.snapshot()")
    assert after["lifecycle"] in ("running", "paused"), "starting must leave idle"
    assert page.evaluate("document.activeElement.hasAttribute('data-arcade-game')"), (
        "starting must focus the game so it owns gameplay keys"
    )


def test_pause_reasons_compose_without_cross_clearing(page_ctx) -> None:
    page, _ = page_ctx
    result = run_js(page, """
        api.reset('play'); api.start();
        api.pause('manual'); api.pause('hidden');
        const both = api.snapshot().pauseReasons;
        api.resume('manual');
        const one = api.snapshot();
        api.resume('hidden');
        const none = api.snapshot();
        return {both, oneReasons: one.pauseReasons, oneState: one.lifecycle, noneState: none.lifecycle};
    """)
    assert result["both"] == ["hidden", "manual"]
    assert result["oneReasons"] == ["hidden"] and result["oneState"] == "paused", (
        "resuming one reason must not clear another"
    )
    assert result["noneState"] == "running"


def test_focused_game_owns_keys_and_escape_releases_them(page_ctx) -> None:
    page, _ = page_ctx
    page.locator("[data-arcade-start]").click()
    page.wait_for_timeout(100)
    hash_before = page.evaluate("location.hash")
    x0 = page.evaluate("window.NexusShooter.snapshot().player.x")
    page.keyboard.down("ArrowLeft")
    page.wait_for_timeout(250)
    page.keyboard.up("ArrowLeft")
    moved = page.evaluate("window.NexusShooter.snapshot().player.x")
    assert page.evaluate("location.hash") == hash_before, (
        "arrows inside the focused game must not drive page navigation"
    )
    # Under normal motion the frame loop ran; under any pause the position is unchanged
    # but ownership still holds, so assert on ownership, not distance.
    page.keyboard.press("Escape")
    page.wait_for_timeout(100)
    snap = page.evaluate("window.NexusShooter.snapshot()")
    assert "manual" in snap["pauseReasons"], "Escape must pause"
    focused = page.evaluate("document.activeElement.getAttribute('data-arcade-action')")
    assert focused == "toggle", "Escape must move focus to the visible resume control"
    assert moved <= x0, "ArrowLeft may only move the player left"


def test_modified_shortcuts_are_never_intercepted(page_ctx) -> None:
    page, _ = page_ctx
    page.locator("[data-arcade-start]").click()
    page.wait_for_timeout(100)
    intercepted = page.evaluate("""
        () => new Promise(resolve => {
            const game = document.querySelector('[data-arcade-game]');
            game.focus();
            const probe = new KeyboardEvent('keydown', {key: 'ArrowLeft', ctrlKey: true, cancelable: true, bubbles: true});
            game.dispatchEvent(probe);
            resolve(probe.defaultPrevented);
        })
    """)
    assert intercepted is False, "Ctrl-modified keys belong to the browser, not the game"


def test_resize_and_dpr_repaint_without_touching_world_state(page_ctx) -> None:
    page, _ = page_ctx
    before = run_js(page, """
        api.reset('enemy-hit'); api.start();
        for (let i = 0; i < 30; i++) api.step();
        api.pause('manual');
        const s = api.snapshot(); return JSON.parse(JSON.stringify(s));
    """)
    page.set_viewport_size({"width": 700, "height": 900})
    page.wait_for_timeout(200)
    after = page.evaluate("window.NexusShooter.snapshot()")
    assert json.dumps(before, sort_keys=True) == json.dumps(after, sort_keys=True), (
        "a resize changed world state; it may only repaint"
    )


def test_live_region_announces_changes_not_frames(page_ctx) -> None:
    page, _ = page_ctx
    result = page.evaluate("""
        () => new Promise(resolve => {
            const api = window.NexusShooter;
            const region = document.querySelector('[data-arcade-live-status]');
            api.reset('enemy-hit'); api.setDamageMode('fixed'); api.start();
            let mutations = 0;
            new MutationObserver(() => { mutations += 1; }).observe(region, {childList: true, characterData: true, subtree: true});
            let guard = 0;
            while (api.snapshot().lifecycle !== 'destroyed' && guard++ < 4000) api.step();
            setTimeout(() => resolve({mutations, text: region.textContent}), 50);
        })
    """)
    # 3->2, 2->1, 1->0+destroyed: a handful of announcements across four thousand ticks.
    assert 0 < result["mutations"] <= 8, (
        f"the live region announced {result['mutations']} times; it must announce changes, not frames"
    )
    assert "destroyed" in result["text"].lower() or "reset" in result["text"].lower()


def test_hud_shows_authoritative_lives_and_mode(page_ctx) -> None:
    page, _ = page_ctx
    run_js(page, "api.reset('enemy-hit'); api.setDamageMode('fixed'); api.start(); let g=0; while (api.snapshot().lives === 3 && g++ < 500) api.step();")
    page.wait_for_timeout(100)
    lives_text = page.locator("[data-arcade-lives]").text_content()
    assert lives_text == "2", f"the HUD must render the authoritative lives value; saw {lives_text!r}"
    mode_text = page.locator('[data-arcade="mode"]').text_content()
    assert mode_text == "damage fixed"


def test_pure_logic_seams_are_exposed_for_unit_assertions(page_ctx) -> None:
    page, _ = page_ctx
    result = page.evaluate("""
        () => {
            const L = window.NexusShooter.logic;
            return {
                touching: L.collides({x: 0, y: 0, r: 5}, {x: 8, y: 0, r: 3}),
                apart: L.collides({x: 0, y: 0, r: 5}, {x: 20, y: 0, r: 3}),
                buggy: L.damageOutcome('buggy', 3),
                fixedMid: L.damageOutcome('fixed', 3),
                fixedLast: L.damageOutcome('fixed', 1),
            };
        }
    """)
    assert result["touching"] is True and result["apart"] is False
    assert result["buggy"]["destroyed"] is True and result["buggy"]["lives"] == 3
    assert result["fixedMid"] == {"lives": 2, "destroyed": False, "reason": "hit"}
    assert result["fixedLast"] == {"lives": 0, "destroyed": True, "reason": "no-lives"}


# ------------------------------------------------------------------ reduced motion


def test_reduced_motion_pauses_and_manual_step_advances_one_tick(playwright_mod) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 940}, reduced_motion="reduce")
        try:
            page.goto(GUIDE.as_uri() + "#training/describe")
            page.wait_for_function("window.NexusShooter")
            page.locator("[data-arcade-start]").click()
            page.wait_for_timeout(200)
            before = page.evaluate("window.NexusShooter.snapshot()")
            assert "reduced-motion" in before["pauseReasons"]
            assert before["lifecycle"] == "paused"
            page.wait_for_timeout(250)
            held = page.evaluate("window.NexusShooter.snapshot().tick")
            assert held == before["tick"], "reduced motion must stop autonomous ticks"
            step = page.locator("[data-arcade-step]")
            assert step.is_visible() and step.is_enabled()
            step.click()
            stepped = page.evaluate("window.NexusShooter.snapshot()")
            assert stepped["tick"] == before["tick"] + 1, "Advance one step is exactly one tick"
            assert stepped["lifecycle"] == "paused", "stepping must not resume the game"
        finally:
            browser.close()


# ---------------------------------------------------------------- fallback + routes


def test_canvas_fallback_states_the_game_state_in_text(page_ctx) -> None:
    """The fallback path cannot be triggered in Chromium, so assert its contract in code:
    the fallback names lives, damage, and feature state, and unusable controls leave the
    Tab order. A structural check here plus the engine's guarded getContext is the honest
    coverage available without a canvas-less browser."""
    page, _ = page_ctx
    guide_text = GUIDE.read_text(encoding="utf-8")
    assert "This browser cannot draw the game canvas" in guide_text
    assert 'setAttribute("tabindex", "-1")' in guide_text
    assert "lives, seeded damage bug active, vertical movement disabled" in guide_text
    assert page.locator("[data-arcade-fallback]").count() == 1


@pytest.mark.parametrize("route", ROUTES)
def test_every_training_route_initializes_the_migrated_game(playwright_mod, route: str) -> None:
    with playwright_mod() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 940})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            page.goto(GUIDE.as_uri() + f"#training/{route}")
            page.wait_for_function("window.NexusShooter && window.NexusTraining")
            snap = page.evaluate("window.NexusTraining.snapshot()")
            engine = page.evaluate("window.NexusShooter.snapshot()")
        finally:
            browser.close()
    assert not errors, f"{route}: {errors}"
    assert snap["sceneId"] == route
    assert set(snap["game"]) == {"damageMode", "verticalMovementEnabled", "fixture"}
    assert engine["damageMode"] == snap["game"]["damageMode"]
    assert engine["verticalMovementEnabled"] == snap["game"]["verticalMovementEnabled"]
    assert engine["fixture"] == snap["game"]["fixture"]
