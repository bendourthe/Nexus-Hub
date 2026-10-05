"""v4.13.10 Phase 3: the Sky Sentinel engine on the Training page.

Every test drives the simulation only through ``step(n)`` with a fixed seed and
``SkySentinel.manual(true)``, so no test waits on real time to move the game. Design and
rules: docs/releases/v4/v4.13/development/v4.13.10-game-design.md.

Skipped when Playwright or Chromium is missing; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

GRACE, CLEARANCE, EARLIEST, GAP, INVULN = 180, 300, 1200, 900, 120


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


@pytest.fixture(scope="module")
def browser(playwright_mod):
    with playwright_mod() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


@pytest.fixture(scope="module")
def page(browser):
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    pg.goto(TRAINING.as_uri() + "#play-fixed")
    pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
    pg.evaluate("SkySentinel.manual(true)")
    yield pg
    pg.close()


def _run(page, defects: dict, seed: int, ticks: int, threats: bool = True) -> dict:
    return page.evaluate(
        """([defects, seed, ticks, threats]) => {
            const g = SkySentinel.get('fixed');
            g.configure({ defects, seed, threats });
            g.start();
            g.pause('test');
            return g.step(ticks);
        }""",
        [defects, seed, ticks, threats],
    )


def test_a_seeded_run_is_identical_every_time(page) -> None:
    keys = ("tick", "score", "lives", "enemies", "enemyShots", "asteroids", "firstShotTick", "hitTicks", "player")
    a = _run(page, {}, 99, 900)
    b = _run(page, {}, 99, 900)
    assert {k: a[k] for k in keys} == {k: b[k] for k in keys}
    c = _run(page, {}, 100, 900)
    assert (c["score"], c["enemies"], c["firstShotTick"]) != (a["score"], a["enemies"], a["firstShotTick"]), "the seed changes the run"


@pytest.mark.parametrize("seed", [1, 7, 42, 4242, 90210])
def test_no_enemy_fires_during_the_start_grace(page, seed: int) -> None:
    early = _run(page, {}, seed, GRACE - 1)
    assert early["enemyShots"] == 0 and early["firstShotTick"] is None
    later = _run(page, {}, seed, 1200)
    assert later["firstShotTick"] is not None and later["firstShotTick"] >= GRACE
    assert later["firstShotGap"] >= CLEARANCE, "the first shot leaves from far enough away to dodge"


def test_first_hit_fatal_destroys_the_ship_with_lives_left(page) -> None:
    state = page.evaluate(
        """() => { const g = SkySentinel.get('fixed');
            g.configure({ defects: { firstHitFatal: true }, seed: 5 }); g.start(); g.pause('test'); g.step(30);
            g.forceHit('shot'); return g.state(); }"""
    )
    assert state["state"] == "over" and state["overReason"] == "first-hit" and state["lives"] == 0


def test_fixed_damage_costs_one_life_per_hit_with_invulnerability(page) -> None:
    out = page.evaluate(
        """() => { const g = SkySentinel.get('fixed');
            g.configure({ defects: {}, seed: 5, threats: false }); g.start(); g.pause('test'); g.step(10);
            const first = g.forceHit('shot'); const afterFirst = g.state();
            g.step(91); const respawned = g.state();
            const during = g.forceHit('shot');
            g.step(""" + str(INVULN + 1) + """);
            g.forceHit('shot'); g.step(91); g.step(""" + str(INVULN + 1) + """); g.forceHit('shot');
            return { first, afterFirst, respawned, during, end: g.state() }; }"""
    )
    assert out["first"] is True and out["afterFirst"]["lives"] == 2 and out["afterFirst"]["state"] != "over"
    assert out["respawned"]["player"]["invuln"] > 0, "the ship respawns with a short invulnerability window"
    assert out["during"] is False, "a hit during invulnerability costs nothing"
    assert out["end"]["lives"] == 0 and out["end"]["state"] == "over" and out["end"]["overReason"] == "hit"


def test_random_explosion_follows_the_pure_schedule_and_its_bounds(page) -> None:
    seed = 4242
    state = _run(page, {"randomExplosion": True}, seed, EARLIEST - 1, threats=False)
    assert state["explodeTicks"] == [], "never before 20 seconds of play"
    state = _run(page, {"randomExplosion": True}, seed, 6000, threats=False)
    ticks = state["explodeTicks"]
    assert ticks, "the defect shows up in a long enough run"
    assert ticks[0] >= EARLIEST
    assert all(b - a >= GAP for a, b in zip(ticks, ticks[1:])), "never twice within 15 seconds"
    nominal = page.evaluate(f"SkySentinel.defectSchedule({seed}, 6000)")
    assert ticks == nominal[: len(ticks)], "with nothing else happening, explosions land exactly on the schedule"
    assert state["hitTicks"] == [], "the explosion is not a hit"


def test_explosion_bounds_hold_across_many_seeds(page) -> None:
    bad = page.evaluate(
        f"""() => {{ const bad = [];
            for (let s = 1; s <= 400; s++) {{
                const t = SkySentinel.defectSchedule(s, 20000);
                if (!t.length || t[0] < {EARLIEST}) bad.push([s, 'first', t[0]]);
                for (let i = 1; i < t.length; i++) if (t[i] - t[i - 1] < {GAP}) bad.push([s, 'gap', t[i] - t[i - 1]]);
            }}
            return bad; }}"""
    )
    assert bad == []


def test_threats_do_not_shift_the_defect_schedule(page) -> None:
    seed = 777
    quiet = _run(page, {"randomExplosion": True}, seed, 1100, threats=False)
    busy = _run(page, {"randomExplosion": True}, seed, 1100, threats=True)
    assert quiet["nextExplosion"] == busy["nextExplosion"] == page.evaluate(f"SkySentinel.defectSchedule({seed}, 5000)[0]")


def test_both_flags_end_the_run_before_the_explosion_appears(page) -> None:
    state = page.evaluate(
        """() => { const g = SkySentinel.get('fixed');
            g.configure({ defects: { firstHitFatal: true, randomExplosion: true }, seed: 4242 }); g.start(); g.pause('test');
            return g.step(20000); }"""
    )
    assert state["state"] == "over" and state["overReason"] == "first-hit"
    assert state["explodeTicks"] == [] and state["tick"] < EARLIEST, (
        "with the first bug in place the run ends before the hidden one can show"
    )


def test_unknown_defect_is_rejected_without_change(page) -> None:
    out = page.evaluate(
        """() => { const g = SkySentinel.get('fixed');
            g.configure({ defects: { firstHitFatal: true }, seed: 3 });
            const warnings = []; const orig = console.warn; console.warn = (m) => warnings.push(String(m));
            const ok = g.configure({ defects: { teleport: true } });
            console.warn = orig;
            return { ok, warnings, defects: g.state().defects }; }"""
    )
    assert out["ok"] is False and out["warnings"] and "teleport" in out["warnings"][0]
    assert out["defects"] == {"firstHitFatal": True, "randomExplosion": False}


def test_keyboard_moves_fires_and_cancels(page) -> None:
    out = page.evaluate(
        """() => { const g = SkySentinel.get('fixed');
            g.configure({ defects: {}, seed: 11, threats: false }); g.start(); g.pause('test');
            const x0 = g.state().player.x;
            g.input({ left: true }); const x1 = g.step(20).player.x;
            g.input({ left: true, right: true }); const x2 = g.step(20).player.x;
            g.input({ left: false, right: false, fire: true }); const shots = g.step(5).shots;
            g.input({ fire: false });
            return { x0, x1, x2, shots }; }"""
    )
    assert out["x1"] < out["x0"], "left moves left"
    assert out["x2"] == out["x1"], "holding left and right together cancels"
    assert out["shots"] >= 1


def test_real_keys_start_move_and_pause(page) -> None:
    page.evaluate("SkySentinel.get('fixed').configure({ defects: {}, seed: 11, threats: false })")
    page.focus(".ss-host[data-ss-id=fixed] .ss-canvas")
    page.keyboard.press("Enter")
    assert page.evaluate("SkySentinel.get('fixed').state().state") == "running"
    x0 = page.evaluate("SkySentinel.get('fixed').state().player.x")
    page.keyboard.down("ArrowRight")
    page.evaluate("SkySentinel.get('fixed').step(15)")
    page.keyboard.up("ArrowRight")
    assert page.evaluate("SkySentinel.get('fixed').state().player.x") > x0
    page.keyboard.press("Escape")
    state = page.evaluate("SkySentinel.get('fixed').state()")
    assert state["state"] == "paused" and state["pausedBy"] == "escape"


def test_hidden_tab_pauses_and_releases_keys(page) -> None:
    out = page.evaluate(
        """() => { const g = SkySentinel.get('fixed');
            g.configure({ defects: {}, seed: 12, threats: false }); g.start();
            g.input({ left: true });
            Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true });
            document.dispatchEvent(new Event('visibilitychange'));
            const s = g.state();
            Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true });
            const x0 = s.player.x; const x1 = g.step(10).player.x;
            return { state: s.state, by: s.pausedBy, moved: x1 !== x0 }; }"""
    )
    assert out["state"] == "paused" and out["by"] == "hidden"
    assert out["moved"] is False, "pausing releases every held key"


def test_scrolling_the_arena_away_pauses(page) -> None:
    page.evaluate("const g = SkySentinel.get('fixed'); g.configure({ defects: {}, seed: 13, threats: false }); g.start();")
    page.evaluate(
        """() => { const spacer = document.createElement('div'); spacer.id = 'probe-spacer'; spacer.style.height = '3000px';
            document.querySelector('[data-stage="play-fixed"] .container').appendChild(spacer);
            window.scrollTo(0, document.body.scrollHeight); }"""
    )
    page.wait_for_function("SkySentinel.get('fixed').state().state === 'paused'", timeout=3000)
    assert page.evaluate("SkySentinel.get('fixed').state().pausedBy") == "offscreen"
    page.evaluate("document.getElementById('probe-spacer').remove(); window.scrollTo(0, 0)")


def test_resize_rescales_without_resetting(page) -> None:
    page.evaluate("const g = SkySentinel.get('fixed'); g.configure({ defects: {}, seed: 14 }); g.start(); g.pause('test'); g.step(300);")
    before = page.evaluate("SkySentinel.get('fixed').state()")
    page.set_viewport_size({"width": 900, "height": 800})
    page.wait_for_function(f"SkySentinel.get('fixed').state().canvas.cssWidth !== {before['canvas']['cssWidth']}")
    after = page.evaluate("SkySentinel.get('fixed').state()")
    page.set_viewport_size({"width": 1280, "height": 900})
    assert after["tick"] == before["tick"] and after["score"] == before["score"] and after["world"] == before["world"]


def test_device_pixel_ratio_backs_the_canvas(browser) -> None:
    pg = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
    try:
        pg.goto(TRAINING.as_uri() + "#play-buggy")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('buggy')")
        c = pg.evaluate("SkySentinel.get('buggy').state().canvas")
        assert abs(c["width"] - 2 * c["cssWidth"]) <= 2 and abs(c["height"] - 2 * c["cssHeight"]) <= 2
        content = pg.evaluate(
            """() => { const box = document.querySelector('[data-stage="play-buggy"] .container'); const cs = getComputedStyle(box);
                return box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight); }"""
        )
        assert c["cssWidth"] >= content - 4, "the arena spans the content width (inside its 1 px border)"
    finally:
        pg.close()


def test_touch_controls_start_and_move(browser) -> None:
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    pg = ctx.new_page()
    try:
        pg.goto(TRAINING.as_uri() + "#play-fixed")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        pg.evaluate("SkySentinel.manual(true); SkySentinel.get('fixed').configure({ defects: {}, seed: 21, threats: false })")
        left = pg.locator(".ss-host[data-ss-id=fixed] .ss-touch-left")
        assert left.is_visible()
        box = left.bounding_box()
        assert box["height"] >= 44 and box["width"] >= 44
        assert pg.evaluate("SkySentinel.get('fixed').state().world") == {"w": 720, "h": 960}, "phones get a portrait arena"
        x0 = pg.evaluate("SkySentinel.get('fixed').state().player.x")
        left.dispatch_event("pointerdown")
        pg.evaluate("SkySentinel.get('fixed').step(15)")
        left.dispatch_event("pointerup")
        state = pg.evaluate("SkySentinel.get('fixed').state()")
        assert state["state"] == "running" and state["player"]["x"] < x0
    finally:
        ctx.close()


def test_a_game_first_shown_on_a_phone_fills_the_width_in_portrait(browser) -> None:
    """A play stage is hidden at load, so the arena must re-choose its shape when it first appears."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    pg = ctx.new_page()
    try:
        pg.goto(TRAINING.as_uri() + "#intro")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        pg.evaluate("location.hash = '#play-fixed'")
        pg.wait_for_function("NexusTrainingPage.stage() === 'play-fixed'")
        pg.wait_for_function("SkySentinel.get('fixed').state().canvas.cssWidth > 300")
        s = pg.evaluate("SkySentinel.get('fixed').state()")
        assert s["world"] == {"w": 720, "h": 960}
        ratio = s["canvas"]["cssHeight"] / s["canvas"]["cssWidth"]
        assert abs(ratio - 960 / 720) < 0.02, "the canvas matches the portrait world, with no letterbox"
    finally:
        ctx.close()


def test_a_missing_canvas_context_shows_the_text_fallback(browser) -> None:
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    pg.add_init_script("HTMLCanvasElement.prototype.getContext = function () { return null; };")
    try:
        pg.goto(TRAINING.as_uri() + "#play-buggy")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('buggy')")
        assert pg.locator(".ss-host[data-ss-id=buggy] .ss-fallback").is_visible()
        assert pg.evaluate("NexusTrainingPage.stage()") == "play-buggy", "the story still works"
    finally:
        pg.close()


# ---------------------------------------------------------------- R5: weapons, upgrades, HUD, and bounds


def _armed(page, level: int = 3) -> None:
    """A quiet level past the start grace: nothing spawns, so each test places what it needs."""
    page.evaluate(
        """(level) => { const g = SkySentinel.get('fixed');
            g.configure({ defects: {}, seed: 7, threats: false, level }); g.start(); g.pause('test'); g.step(GRACE_PAD); }""".replace("GRACE_PAD", str(GRACE + 10)),
        level,
    )


@pytest.mark.parametrize("enemy, kind", [("drone", "bolt"), ("weaver", "orb"), ("bomber", "mine")])
def test_each_enemy_type_fires_its_own_weapon(page, enemy: str, kind: str) -> None:
    _armed(page)
    page.evaluate(f"SkySentinel.get('fixed').spawn('{enemy}', 120, 80)")
    kinds = page.evaluate("SkySentinel.get('fixed').step(2).shotKinds")
    assert kinds == [kind], f"{enemy} fired {kinds}"


def test_a_lancer_charges_then_fires_a_beam_column(page) -> None:
    _armed(page)
    page.evaluate("SkySentinel.get('fixed').spawn('lancer', 120, 80)")
    charging = page.evaluate("SkySentinel.get('fixed').step(2)")
    assert charging["shotKinds"] == [], "the charge is a tell: no shot yet"
    view = page.evaluate("SkySentinel.get('fixed').view()")
    assert sum(1 for t in view["threats"] if abs(t["x"] - 120) < 8 and t["vx"] == 0 and t["vy"] == 8) >= 10, "the charging column is a threat"
    fired = page.evaluate("SkySentinel.get('fixed').step(55)")
    assert "beam" in fired["shotKinds"]


def test_a_mine_bursts_into_six_bolts_when_its_fuse_runs_out(page) -> None:
    _armed(page)
    page.evaluate("SkySentinel.get('fixed').spawn('bomber', 120, 60)")
    assert page.evaluate("SkySentinel.get('fixed').step(2).shotKinds") == ["mine"]
    page.evaluate("(() => { const g = SkySentinel.get('fixed'); g.step(1); })()")
    after = page.evaluate("SkySentinel.get('fixed').step(80).shotKinds")
    assert "mine" not in after[:1] and after.count("bolt") >= 6


@pytest.mark.parametrize("kind, seconds", [("spread", 10), ("rapid", 10), ("missiles", 9), ("wingman", 15)])
def test_timed_upgrades_are_collected_and_expire(page, kind: str, seconds: int) -> None:
    _armed(page, level=1)
    page.evaluate(f"SkySentinel.get('fixed').dropPowerUp('{kind}')")
    got = page.evaluate("SkySentinel.get('fixed').step(2)")
    assert got["collected"][-1]["kind"] == kind
    assert seconds * 60 - 5 <= got["player"][kind] <= seconds * 60
    gone = page.evaluate(f"SkySentinel.get('fixed').step({seconds * 60})")
    assert gone["player"][kind] == 0, f"{kind} expires"


def test_spread_and_rapid_change_the_guns(page) -> None:
    def volley(kind: str | None) -> tuple[int, int]:
        _armed(page, level=1)
        if kind:
            page.evaluate(f"SkySentinel.get('fixed').dropPowerUp('{kind}')")
            page.evaluate("SkySentinel.get('fixed').step(2)")
        return page.evaluate("""(() => { const g = SkySentinel.get('fixed'); const s0 = g.state().shots;
            g.input({ fire: true }); const one = g.step(1).shots - s0; const sixty = g.step(59).shots;
            g.input({ fire: false }); return [one, sixty]; })()""")
    base, spread, rapid = volley(None), volley("spread"), volley("rapid")
    assert base[0] == 1 and spread[0] == 3, (base, spread)
    assert rapid[1] > base[1], f"rapid fire puts more shots in the air: {rapid} vs {base}"


def test_every_power_up_kind_is_droppable_and_unknown_is_refused(page) -> None:
    _armed(page, level=1)
    ok = page.evaluate("['shield','weapon','ship','spread','rapid','missiles','wingman'].map(k => SkySentinel.get('fixed').dropPowerUp(k))")
    assert ok == [True] * 7
    assert page.evaluate("SkySentinel.get('fixed').dropPowerUp('laser')") is False


def test_the_hud_goal_names_the_next_level_and_tracks_progress(page) -> None:
    _armed(page, level=1)
    first = page.evaluate("SkySentinel.get('fixed').state().goal")
    assert first["text"].startswith("Survive ") and first["text"].endswith("to reach level 2")
    later = page.evaluate("SkySentinel.get('fixed').step(600).goal")
    assert 0 < first["k"] < later["k"] < 1
    _armed(page, level=3)
    assert page.evaluate("SkySentinel.get('fixed').state().goal.text").startswith("Something big arrives in")


@pytest.mark.parametrize("viewport", [(1440, 900), (1280, 720), (1920, 1080), (1024, 1366)])
def test_the_world_fills_the_frame_with_no_side_bands(browser, viewport: tuple[int, int]) -> None:
    pg = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
    try:
        pg.goto(TRAINING.as_uri() + "#play-fixed")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        st = pg.evaluate("SkySentinel.get('fixed').state()")
        world, canvas = st["world"], st["canvas"]
        assert abs(world["w"] / world["h"] - canvas["cssWidth"] / canvas["cssHeight"]) < 0.03, (world, canvas)
    finally:
        pg.close()
