"""v4.13.10: the Sky Sentinel engine on the Training page.

Every test drives the simulation only through ``step(n)`` with a fixed seed and
``SkySentinel.manual(true)``, so no test waits on real time to move the game. Design and
rules: docs/releases/v4/v4.13/development/v4.13.10-game-design.md. Phase R10 replaced lives
with a health bar: each source deals its own damage, a shield adds a second bar that absorbs
damage first, and the ``firstHitFatal`` defect turns any hit into instant destruction.

Skipped when Playwright or Chromium is missing; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

GRACE, CLEARANCE, EARLIEST, GAP, INVULN = 180, 300, 1200, 900, 60
HEALTH, SHIELD, BLAST_RADIUS = 100, 50, 84

# Damage at Easy (level 1); every level multiplies it.
DAMAGE_TABLE = [
    ("needle", None, 6),
    ("shot", None, 10),
    ("bossShot", None, 14),
    ("beam", None, 32),
    ("blast", 0, 34),
    ("collision", "interceptor", 14),
    ("collision", "gunship", 22),
    ("collision", "lancer", 26),
    ("collision", "bomber", 30),
    ("collision", "boss", 45),
    ("asteroid", "large", 28),
    ("asteroid", "medium", 16),
    ("asteroid", "small", 7),
]


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


def _quiet(page, level: int = 1, defects: dict | None = None, pad: int = 10) -> None:
    """A quiet game: nothing spawns, so each test places what it needs."""
    page.evaluate(
        """([level, defects, pad]) => { const g = SkySentinel.get('fixed');
            g.configure({ defects, seed: 7, threats: false, level }); g.start(); g.pause('test'); g.step(pad); }""",
        [level, defects or {}, pad],
    )


def _js(page, body: str):
    return page.evaluate(f"(() => {{ const g = SkySentinel.get('fixed'); {body} }})()")


def test_a_seeded_run_is_identical_every_time(page) -> None:
    keys = ("tick", "score", "health", "shieldHp", "enemies", "enemyShots", "asteroids", "firstShotTick", "hitTicks", "player", "damageLog")
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


# ---------------------------------------------------------------- the health model


def test_the_ship_starts_with_a_full_hull_and_no_shield(page) -> None:
    s = _run(page, {}, 5, 1, threats=False)
    assert (s["health"], s["healthMax"], s["shieldHp"], s["shieldMax"]) == (HEALTH, HEALTH, 0, SHIELD)
    assert s["lastDamage"] is None and "lives" not in s


@pytest.mark.parametrize("source, detail, amount", DAMAGE_TABLE)
def test_each_source_deals_its_own_damage(page, source: str, detail, amount: int) -> None:
    _quiet(page)
    out = page.evaluate(
        """([source, detail]) => { const g = SkySentinel.get('fixed'); const hit = g.forceHit(source, detail);
            return { hit, s: g.state() }; }""",
        [source, detail],
    )
    s = out["s"]
    assert out["hit"] is True and s["state"] != "over"
    assert s["health"] == HEALTH - amount, f"{source} {detail}: {HEALTH - s['health']} damage"
    assert s["lastDamage"]["source"] == source and s["lastDamage"]["amount"] == amount


def test_smaller_asteroids_hurt_less(page) -> None:
    amounts = {}
    for size in ("large", "medium", "small"):
        _quiet(page)
        amounts[size] = HEALTH - _js(page, f"g.forceHit('asteroid', '{size}'); return g.state().health;")
    assert amounts["large"] > amounts["medium"] > amounts["small"] > 0, amounts


def test_a_real_asteroid_collision_costs_damage_by_size_and_breaks_the_rock(page) -> None:
    _quiet(page)
    s = _js(page, """const p = g.state().player; g.spawnAsteroid('medium', p.x, p.y - 60, 0, 3); return g.step(40);""")
    assert s["lastDamage"]["source"] == "asteroid" and s["lastDamage"]["detail"] == "medium"
    assert s["health"] == HEALTH - 16 and s["state"] != "over"
    assert s["breaks"] and s["breaks"][0]["size"] == "medium", "the rock breaks on the ship"


def test_fixed_damage_has_a_short_invulnerability_window_and_ends_at_zero(page) -> None:
    _quiet(page)
    out = _js(page, f"""const first = g.forceHit('beam'); const a = g.state();
        const during = g.forceHit('beam'); g.step({INVULN}); const again = g.forceHit('beam'); const b = g.state();
        for (let i = 0; i < 4; i++) {{ g.step({INVULN}); g.forceHit('beam'); }}
        return {{ first, a, during, again, b, end: g.state() }};""")
    assert out["first"] is True and out["a"]["health"] == HEALTH - 32 and out["a"]["player"]["invuln"] == INVULN
    assert out["during"] is False, "a hit during the window costs nothing"
    assert out["again"] is True and out["b"]["health"] == HEALTH - 64
    end = out["end"]
    assert end["health"] == 0 and end["state"] == "over" and end["overReason"] == "hit"
    assert end["overText"] == "Hull destroyed by a laser beam"


def test_the_shield_is_a_second_bar_that_absorbs_damage_first(page) -> None:
    _quiet(page)
    out = _js(page, f"""g.dropPowerUp('shield'); const up = g.step(2);
        g.forceHit('beam'); const a = g.state(); g.step({INVULN}); g.forceHit('beam'); const b = g.state();
        return {{ up, a, b }};""")
    assert out["up"]["shieldHp"] == SHIELD and out["up"]["player"]["shield"] == SHIELD
    assert (out["a"]["health"], out["a"]["shieldHp"]) == (HEALTH, SHIELD - 32), "the shield takes the first hit whole"
    assert out["a"]["lastDamage"]["absorbed"] == 32
    assert (out["b"]["health"], out["b"]["shieldHp"]) == (HEALTH - (32 - (SHIELD - 32)), 0), "the overflow reaches the hull"


def test_repair_restores_hull_up_to_the_maximum(page) -> None:
    _quiet(page)
    out = _js(page, f"""g.forceHit('beam'); g.step({INVULN}); g.forceHit('shot'); const hurt = g.state().health;
        g.dropPowerUp('repair'); const one = g.step(2).health; g.dropPowerUp('ship'); const two = g.step(2).health;
        return {{ hurt, one, two }};""")
    assert out["hurt"] == HEALTH - 42
    assert out["one"] == out["hurt"] + 35, "a repair kit restores 35"
    assert out["two"] == HEALTH, "repairs cap at the hull maximum (the old extra-ship name maps to repair)"


def test_damage_rises_with_the_level(page) -> None:
    taken = []
    for level in (1, 2, 3):
        _quiet(page, level=level)
        taken.append(HEALTH - _js(page, "g.forceHit('shot'); return g.state().health;"))
    assert taken[0] < taken[1] < taken[2], taken


# ---------------------------------------------------------------- the two defects


FATAL_SOURCES = [
    ("shot", None, "a gunship bolt"),
    ("needle", None, "an interceptor dart"),
    ("beam", None, "a laser beam"),
    ("blast", 70, "a bomb blast"),
    ("collision", "interceptor", "a collision with an interceptor"),
    ("collision", "bomber", "a collision with a bomber"),
    ("asteroid", "large", "a large asteroid"),
    ("asteroid", "small", "a small asteroid chunk"),
    ("collision", "boss", "the megaship"),
    ("bossShot", None, "a megaship bolt"),
]


@pytest.mark.parametrize("source, detail, text", FATAL_SOURCES)
def test_first_hit_fatal_destroys_the_ship_on_any_hit_from_any_source(page, source: str, detail, text: str) -> None:
    _quiet(page, defects={"firstHitFatal": True})
    s = page.evaluate(
        """([source, detail]) => { const g = SkySentinel.get('fixed'); g.dropPowerUp('shield'); g.step(2);
            g.forceHit(source, detail); return g.state(); }""",
        [source, detail],
    )
    assert s["state"] == "over" and s["overReason"] == "first-hit"
    assert s["health"] == s["healthMax"] and s["shieldHp"] == s["shieldMax"], "destroyed with the hull and shield still full: that is the bug"
    assert s["overText"] == f"Destroyed by a single hit: {text}"
    assert s["lastDamage"]["source"] == source


def test_first_hit_fatal_kills_on_every_run_not_only_the_first(page) -> None:
    reasons = _js(page, """const out = [];
        for (let run = 0; run < 3; run++) {
            g.configure({ defects: { firstHitFatal: true }, seed: 5 + run, threats: false }); g.start(); g.pause('t'); g.step(20);
            g.forceHit(run === 2 ? 'asteroid' : 'shot', run === 2 ? 'small' : undefined); const s = g.state(); out.push([s.state, s.overReason, s.health]);
        }
        return out;""")
    assert reasons == [["over", "first-hit", 100]] * 3


def test_first_hit_fatal_kills_on_a_real_chunk_collision(page) -> None:
    _quiet(page, defects={"firstHitFatal": True})
    s = _js(page, "const p = g.state().player; g.spawnAsteroid('small', p.x, p.y - 40, 0, 3); return g.step(30);")
    assert s["state"] == "over" and s["overReason"] == "first-hit"
    assert s["overText"] == "Destroyed by a single hit: a small asteroid chunk"


def test_the_over_overlay_names_the_single_hit(page) -> None:
    _quiet(page, defects={"firstHitFatal": True})
    _js(page, "g.forceHit('needle');")
    title = page.locator(".ss-host[data-ss-id=fixed] .ss-over-title").inner_text()
    assert title == "Destroyed by a single hit: an interceptor dart"


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
    assert [d["source"] for d in state["damageLog"]] == ["explode"] * len(ticks)
    assert state["damageLog"][0]["amount"] == 40


def test_random_explosion_ignores_the_shield(page) -> None:
    _quiet(page, defects={"randomExplosion": True})
    s = _js(page, f"g.dropPowerUp('shield'); g.step(2); return g.step({EARLIEST + 600});")
    assert s["explodeTicks"], "an explosion happened"
    assert s["shieldHp"] == SHIELD and s["health"] == HEALTH - 40, "the self-test blows up inside the shield"


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


# ---------------------------------------------------------------- controls, sizing, renderers


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
        hud = pg.evaluate("(() => { const h = document.querySelector('[data-ss-id=buggy] .ss-hudcanvas'); return [h.width, h.height]; })()")
        assert hud == [c["width"], c["height"]], "the HUD canvas matches the WebGL canvas pixel for pixel"
        content = pg.evaluate(
            """() => { const box = document.querySelector('[data-stage="play-buggy"] .container'); const cs = getComputedStyle(box);
                return box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight); }"""
        )
        assert c["cssWidth"] >= content - 4, "the arena spans the content width (inside its 1 px border)"
    finally:
        pg.close()


def test_chromium_draws_with_webgl(page) -> None:
    s = _run(page, {}, 3, 60)
    assert s["renderer"] == "webgl"
    assert page.get_attribute(".ss-host[data-ss-id=fixed]", "data-ss-renderer-active") == "webgl"
    assert page.locator(".ss-host[data-ss-id=fixed] .ss-hudcanvas").count() == 1
    lit = page.evaluate(
        """() => { const g = SkySentinel.get('fixed'); g.render();
            const c = document.querySelector('.ss-host[data-ss-id=fixed] .ss-canvas'); const gl = c.getContext('webgl');
            const px = new Uint8Array(4 * 64 * 64); gl.readPixels(Math.floor(c.width / 2) - 32, 0, 64, 64, gl.RGBA, gl.UNSIGNED_BYTE, px);
            let sum = 0; for (let i = 0; i < px.length; i += 4) sum += px[i] + px[i + 1] + px[i + 2]; return sum; }"""
    )
    assert lit > 0, "the WebGL canvas drew the scene"


@pytest.mark.parametrize("how", ["global", "attribute"])
def test_the_2d_renderer_can_be_forced_and_plays(browser, how: str) -> None:
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    if how == "global":
        pg.add_init_script("window.SKY_SENTINEL_RENDERER = '2d';")
    else:
        # Mark each host as the parser inserts it, before the page script creates the games.
        pg.add_init_script(
            "new MutationObserver(() => document.querySelectorAll('.ss-host:not([data-ss-renderer])')"
            ".forEach(h => h.setAttribute('data-ss-renderer', '2d'))).observe(document, { childList: true, subtree: true });"
        )
    try:
        pg.goto(TRAINING.as_uri() + "#play-fixed")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        s = pg.evaluate(
            """() => { SkySentinel.manual(true); const g = SkySentinel.get('fixed');
                g.configure({ defects: {}, seed: 9, level: 3 }); g.start(); g.pause('t'); g.input({ fire: true });
                const s = g.step(600); g.dropPowerUp('shield'); g.step(2); g.render(); return s; }"""
        )
        assert s["renderer"] == "2d" and s["tick"] > 0
        assert pg.locator(".ss-host[data-ss-id=fixed] .ss-hudcanvas").count() == 0
        painted = pg.evaluate(
            """() => { const c = document.querySelector('.ss-host[data-ss-id=fixed] .ss-canvas');
                const d = c.getContext('2d').getImageData(0, 0, c.width, 60).data; let n = 0;
                for (let i = 0; i < d.length; i += 4) if (d[i + 1] > 120) n++; return n; }"""
        )
        assert painted > 50, "the 2D path draws the scene and its HUD bars"
        assert not errors, errors
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
        assert pg.evaluate("SkySentinel.get('buggy').state().renderer") == "none"
        assert pg.evaluate("NexusTrainingPage.stage()") == "play-buggy", "the story still works"
    finally:
        pg.close()


def test_without_webgl_the_game_falls_back_to_2d(browser) -> None:
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    pg.add_init_script(
        "const orig = HTMLCanvasElement.prototype.getContext;"
        "HTMLCanvasElement.prototype.getContext = function (kind, o) { return /webgl/.test(kind) ? null : orig.call(this, kind, o); };"
    )
    try:
        pg.goto(TRAINING.as_uri() + "#play-buggy")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('buggy')")
        assert pg.evaluate("SkySentinel.get('buggy').state().renderer") == "2d"
        assert not pg.locator(".ss-host[data-ss-id=buggy] .ss-fallback").is_visible()
    finally:
        pg.close()


# ---------------------------------------------------------------- enemy weapons, asteroids, power-ups


@pytest.mark.parametrize("enemy, kind", [("gunship", "bolt"), ("interceptor", "needle"), ("bomber", "bomb")])
def test_each_enemy_class_fires_its_own_weapon(page, enemy: str, kind: str) -> None:
    _quiet(page, level=3, pad=GRACE + 10)
    page.evaluate(f"SkySentinel.get('fixed').spawn('{enemy}', 120, 80)")
    kinds = page.evaluate("SkySentinel.get('fixed').step(2).shotKinds")
    assert kinds and set(kinds) == {kind}, f"{enemy} fired {kinds}"


def test_a_lancer_charges_then_fires_a_beam_column(page) -> None:
    _quiet(page, level=3, pad=GRACE + 10)
    page.evaluate("SkySentinel.get('fixed').spawn('lancer', 120, 80)")
    charging = page.evaluate("SkySentinel.get('fixed').step(2)")
    assert charging["shotKinds"] == [], "the charge is a tell: no shot yet"
    view = page.evaluate("SkySentinel.get('fixed').view()")
    assert sum(1 for t in view["threats"] if abs(t["x"] - 120) < 8 and t["vx"] == 0 and t["vy"] == 8) >= 10, "the charging column is a threat"
    assert view["beams"] and view["beams"][0]["charging"] > 0
    fired = page.evaluate("SkySentinel.get('fixed').step(55)")
    assert "beam" in fired["shotKinds"]


def test_a_beam_down_the_ships_column_deals_beam_damage(page) -> None:
    _quiet(page, level=1, pad=GRACE + 10)
    s = _js(page, "const p = g.state().player; g.spawn('lancer', p.x, 80); return g.step(70);")
    assert s["lastDamage"] and s["lastDamage"]["source"] == "beam" and s["lastDamage"]["amount"] == 32
    assert s["health"] == HEALTH - 32, "one beam counts once, thanks to the invulnerability window"


def test_a_bomb_arms_near_the_ship_shows_its_blast_zone_and_bursts(page) -> None:
    _quiet(page, level=1, pad=GRACE + 10)
    out = _js(page, f"""const p = g.state().player; g.spawn('bomber', p.x, 120);
        let armed = null;
        for (let i = 0; i < 400 && !armed; i++) {{ g.step(1); const v = g.view(); if (v.blasts.length) armed = v.blasts[0]; }}
        const before = g.state().health;
        g.step({40});
        return {{ armed, before, s: g.state() }};""")
    assert out["armed"] is not None and out["armed"]["r"] == BLAST_RADIUS, "the armed bomb is a visible blast-zone threat"
    s = out["s"]
    assert s["lastDamage"]["source"] == "blast"
    assert 6 <= s["lastDamage"]["amount"] <= 34 and s["health"] < out["before"]


def test_bomb_blast_damage_falls_off_with_distance(page) -> None:
    amounts = []
    for dist in (0, 21, 42, 63, 83):
        _quiet(page)
        amounts.append(HEALTH - page.evaluate(f"(() => {{ const g = SkySentinel.get('fixed'); g.forceHit('blast', {dist}); return g.state().health; }})()"))
    assert amounts[0] == 34 and amounts == sorted(amounts, reverse=True) and len(set(amounts)) == len(amounts), amounts
    assert amounts[-1] >= 6, "a blast still hurts at the rim"
    _quiet(page)
    assert _js(page, f"return g.forceHit('blast', {BLAST_RADIUS + 1});") is False, "outside the radius it does nothing"


def test_shooting_a_bomb_in_flight_detonates_it_early(page) -> None:
    _quiet(page, level=1, pad=GRACE + 10)
    s = _js(page, """const p = g.state().player; g.spawn('bomber', p.x, 100); g.step(2);
        g.input({ fire: true }); const s = g.step(25); g.input({ fire: false }); return s;""")
    assert "bomb" not in s["shotKinds"] and s["health"] == HEALTH, "the bomb burst far from the ship"


def test_asteroids_split_into_smaller_chunks_then_dust(page) -> None:
    _quiet(page)
    out = _js(page, """const p = g.state().player; g.spawnAsteroid('large', p.x, p.y - 260, 0, 0);
        g.input({ fire: true }); const s1 = g.step(60); g.input({ fire: false });
        const seen = new Set(); let s = g.state(); s.asteroidSizes.forEach(x => seen.add(x));
        return { s1, seen: [...seen] };""")
    breaks = out["s1"]["breaks"]
    assert breaks and breaks[0]["size"] == "large" and breaks[0]["into"] in (2, 3), breaks
    assert "medium" in out["s1"]["asteroidSizes"] or any(b["size"] == "medium" for b in breaks)
    # break every size in turn by spawning one of each in the line of fire
    sizes = _js(page, """const out = []; for (const size of ['medium', 'small']) {
            g.configure({ defects: {}, seed: 7, threats: false }); g.start(); g.pause('t'); g.step(5);
            const p = g.state().player; g.spawnAsteroid(size, p.x, p.y - 260, 0, 0);
            g.input({ fire: true }); const s = g.step(45); g.input({ fire: false }); out.push(s.breaks[0]); }
        return out;""")
    assert sizes[0]["size"] == "medium" and sizes[0]["into"] in (2, 3)
    assert sizes[1]["size"] == "small" and sizes[1]["into"] == 0, "a small chunk turns to dust"


@pytest.mark.parametrize("kind, seconds", [("spread", 10), ("rapid", 10), ("missiles", 9), ("wingman", 15)])
def test_timed_upgrades_are_collected_and_expire(page, kind: str, seconds: int) -> None:
    _quiet(page, pad=GRACE + 10)
    page.evaluate(f"SkySentinel.get('fixed').dropPowerUp('{kind}')")
    got = page.evaluate("SkySentinel.get('fixed').step(2)")
    assert got["collected"][-1]["kind"] == kind
    assert seconds * 60 - 5 <= got["player"][kind] <= seconds * 60
    gone = page.evaluate(f"SkySentinel.get('fixed').step({seconds * 60})")
    assert gone["player"][kind] == 0, f"{kind} expires"


def test_spread_and_rapid_change_the_guns(page) -> None:
    def volley(kind: str | None) -> tuple[int, int]:
        _quiet(page, pad=GRACE + 10)
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
    _quiet(page)
    ok = page.evaluate("['shield','weapon','repair','spread','rapid','missiles','wingman','ship'].map(k => SkySentinel.get('fixed').dropPowerUp(k))")
    assert ok == [True] * 8
    assert page.evaluate("SkySentinel.get('fixed').dropPowerUp('laser')") is False


def test_the_hud_goal_names_the_next_level_and_tracks_progress(page) -> None:
    _quiet(page, pad=GRACE + 10)
    first = page.evaluate("SkySentinel.get('fixed').state().goal")
    assert first["text"].startswith("Survive ") and first["text"].endswith("to reach level 2")
    later = page.evaluate("SkySentinel.get('fixed').step(600).goal")
    assert 0 < first["k"] < later["k"] < 1
    _quiet(page, level=3, pad=GRACE + 10)
    assert page.evaluate("SkySentinel.get('fixed').state().goal.text").startswith("Something big arrives in")


def test_the_accessible_hud_reads_hull_and_difficulty(page) -> None:
    _quiet(page, level=2)
    _js(page, "g.forceHit('shot');")
    items = page.locator(".ss-host[data-ss-id=fixed] .ss-hud-item").all_inner_texts()
    assert "Hull 88 of 100" in items, items
    assert any(t.startswith("Level 2 (Medium)") for t in items), items


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


def test_the_explosion_plays_out_after_a_buggy_death(page) -> None:
    """Goal review (revision 2): the death explosion kept animating instead of freezing on its first frame."""
    _quiet(page, defects={"firstHitFatal": True})
    s = _js(page, "g.forceHit('shot'); return { over: g.state().state, animating: g.animating() };")
    assert s == {"over": "over", "animating": True}
