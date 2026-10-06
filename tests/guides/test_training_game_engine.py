"""v4.13.10: the Sky Sentinel engine on the Training page.

Every test drives the simulation only through ``step(n)`` with a fixed seed and
``SkySentinel.manual(true)``, so no test waits on real time to move the game. Design and
rules: docs/releases/v4/v4.13/development/v4.13.10-game-design.md. Phase R10 replaced lives
with a health bar: each source deals its own damage, a shield adds a second bar that absorbs
damage first, and the ``firstHitFatal`` defect turns any hit into instant destruction.
Phase R14 (the game is now shown to players as "Nexus Defenders") added a start screen with
four ships and an upgrade key, ten upgrades carried by glowing enemies and asteroids, density
that grows through each level, and a fatal hit that shows its real damage while the hull drains.
Phase R16 gave both games one start screen that fits the arena with no scroll bar, made every
damage path (and the self-test blast) fatal in the buggy build, and gave each ship its own
weapon: twin cannons, a burst rifle, a lance beam, and splitting plasma orbs.
Phase R18 aimed every enemy weapon at the ship (``aimLog()`` records each shot's origin, heading,
and the ship's position when it fired), centred the end card in the arena, added a fifth ship
(the green Warden and its flak cone) with one main colour per ship and an animated weapon preview
on each card, and added ``SkySentinel.demo()``, a scripted scene drawn by the real renderer.

Skipped when Playwright or Chromium is missing; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import colorsys
import math
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
            const expected = g.damageFor(source, detail); g.forceHit(source, detail); return Object.assign(g.state(), { expected }); }""",
        [source, detail],
    )
    assert s["state"] == "over" and s["overReason"] == "first-hit"
    # R14 supersedes R10's full bars: the hit shows its real damage while hull and shield empty.
    assert s["health"] == 0 and s["shieldHp"] == 0, "a small hit emptied a full hull and shield: that is the bug"
    assert s["lastDamage"]["amount"] == s["expected"] < s["healthMax"]
    assert {"text": f"-{s['expected']}", "color": "#fca5a5", "big": True} in s["popups"], "the real damage floats over the ship"
    assert s["overText"] == f"Destroyed by a single hit: {text}"
    assert s["lastDamage"]["source"] == source


def test_first_hit_fatal_kills_on_every_run_not_only_the_first(page) -> None:
    reasons = _js(page, """const out = [];
        for (let run = 0; run < 3; run++) {
            g.configure({ defects: { firstHitFatal: true }, seed: 5 + run, threats: false }); g.start(); g.pause('t'); g.step(20);
            g.forceHit(run === 2 ? 'asteroid' : 'shot', run === 2 ? 'small' : undefined); const s = g.state(); out.push([s.state, s.overReason, s.health]);
        }
        return out;""")
    assert reasons == [["over", "first-hit", 0]] * 3


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


def test_a_lancer_lines_up_on_the_ship_then_charges_and_fires_a_beam_column(page) -> None:
    """R18: a lancer due to fire first slides onto the ship's column; only then does it charge."""
    _quiet(page, level=3, pad=GRACE + 10)
    out = _js(page, """const p = g.state().player; g.spawn('lancer', p.x - 150, 80);
        let n = 0; while (!g.view().beams.length && n < 200) { g.step(1); n++; }
        return { n, view: g.view(), s: g.state(), px: p.x };""")
    view, px = out["view"], out["px"]
    assert out["n"] > 20, "it had to travel to line up first"
    assert out["s"]["shotKinds"] == [], "the charge is a tell: no shot yet"
    assert view["beams"] and view["beams"][0]["charging"] > 0 and abs(view["beams"][0]["x"] - px) < 0.5, "it charges on the ship's column"
    assert sum(1 for t in view["threats"] if abs(t["x"] - px) < 8 and t["vx"] == 0 and t["vy"] == 8) >= 10, "the charging column is a threat"
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
    assert base[0] == 2 and spread[0] == 4, f"the Vanguard's twin cannons gain two side shots: {base} {spread}"
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


# ---------------------------------------------------------------- R14: ships, upgrades, carriers, density

SHIP_IDS = ["vanguard", "warden", "specter", "talon", "raptor"]
SHIP_COLOURS = {"vanguard": "blue", "warden": "green", "specter": "orange", "talon": "yellow", "raptor": "red"}
UPGRADES = ["shield", "repair", "weapon", "spread", "rapid", "pierce", "missiles", "wingman", "slow", "magnet"]


def test_the_start_screen_offers_five_ships_and_the_full_upgrade_key(page) -> None:
    _quiet(page)
    page.evaluate("(() => { const g = SkySentinel.get('fixed'); g.configure({ defects: {}, seed: 7 }); })()")
    host = ".ss-host[data-ss-id=fixed]"
    assert page.locator(f"{host} .ss-brand").text_content() == "Nexus Defenders"
    cards = page.locator(f"{host} .ss-hangar [role=radio]")
    assert cards.count() == 5
    assert page.get_attribute(f"{host} .ss-hangar", "role") == "radiogroup"
    labels = cards.evaluate_all("els => els.map(e => [e.dataset.ship, e.getAttribute('aria-checked'), e.getAttribute('aria-label')])")
    assert [x[0] for x in labels] == SHIP_IDS
    assert [x[1] for x in labels] == ["true", "false", "false", "false", "false"], "the default ship is preselected"
    assert all("Hull" in x[2] and "speed" in x[2] for x in labels), "each card names its stats"
    items = page.locator(f"{host} .ss-key-item").evaluate_all(
        "els => els.map(e => [e.dataset.upgrade, getComputedStyle(e).getPropertyValue('--ss-up').trim(), e.innerText])")
    api = page.evaluate("SkySentinel.get('fixed').upgrades()")
    assert sorted(x[0] for x in items) == sorted(UPGRADES) == sorted(u["kind"] for u in api)
    colours = {u["kind"]: u["color"] for u in api}
    assert all(x[1] == colours[x[0]] for x in items), "the key shows each upgrade in its own colour"
    assert len(set(colours.values())) == len(colours), "no two upgrades share a colour"
    assert all(len(x[2].split("\n")) >= 2 for x in items), "each entry has a name and a one-line effect"
    assert page.locator(f"{host} .ss-start").inner_text() == "Start game"


def test_both_games_share_one_start_screen(page) -> None:
    """R16 maintainer review: the buggy game's start screen differed from the fixed one (no key)."""
    shot = page.evaluate("""['buggy', 'fixed'].map(id => { const h = document.querySelector('.ss-host[data-ss-id=' + id + ']');
        SkySentinel.get(id).reset();
        return { key: h.querySelector('.ss-key').hidden, text: [...h.querySelectorAll('.ss-ship, .ss-key-item, .ss-key-title, .ss-start')].map(e => e.innerText) }; })""")
    assert shot[0]["key"] is False and shot[1]["key"] is False, "both games show the upgrade key"
    assert shot[0]["text"] == shot[1]["text"], "the same ships, key, and Start button in both games"


@pytest.mark.parametrize("ship", SHIP_IDS)
def test_choosing_a_ship_changes_the_state_and_the_rendered_form(page, ship: str) -> None:
    out = _js(page, f"""g.configure({{ defects: {{}}, seed: 7, threats: false, level: 1 }});
        const ok = g.chooseShip('{ship}'); const s = g.state(); const spec = g.ships().find(x => x.id === '{ship}');
        g.start(); g.pause('t'); g.step(2); const lit = g.render();
        const card = document.querySelector('.ss-host[data-ss-id=fixed] [data-ship={ship}]').getAttribute('aria-checked');
        g.chooseShip('vanguard');
        return {{ ok, s, spec, lit, card }};""")
    s, spec = out["s"], out["spec"]
    assert out["ok"] is True and s["ship"] == ship and s["shipMesh"] == f"{ship}1" and out["card"] == "true"
    assert s["healthMax"] == spec["hull"] == s["health"], "the ship's hull sets the bar"
    assert out["lit"] == "webgl"


def test_ships_differ_in_shape_colour_and_stats(page) -> None:
    ships = page.evaluate("SkySentinel.get('fixed').ships()")
    assert [s["id"] for s in ships] == SHIP_IDS and ships[0]["hull"] == 100 and ships[0]["speed"] == 1 and ships[0]["fire"] == 1
    assert len({(s["hull"], s["speed"], s["fire"]) for s in ships}) == 5, "every ship trades something"
    assert len({s["accent"] for s in ships}) == 5, "every ship has its own colour scheme"
    forms = _js(page, """const out = {};
        for (const id of ['vanguard', 'warden', 'specter', 'talon', 'raptor']) for (const lv of [1, 2, 3]) {
            g.configure({ defects: {}, seed: 7, threats: false, level: lv }); g.chooseShip(id); out[id + lv] = g.state().shipMesh; }
        g.chooseShip('vanguard'); return out;""")
    assert sorted(forms.values()) == sorted(f"{i}{n}" for i in SHIP_IDS for n in (1, 2, 3)), "three forms per ship"


def test_a_faster_ship_moves_further_and_unknown_ships_are_refused(page) -> None:
    def moved(ship: str) -> float:
        return _js(page, f"""g.configure({{ defects: {{}}, seed: 7, threats: false }}); g.chooseShip('{ship}'); g.start(); g.pause('t');
            const x0 = g.state().player.x; g.input({{ left: true }}); const x1 = g.step(10).player.x; g.input({{ left: false }});
            g.chooseShip('vanguard'); return x0 - x1;""")
    assert moved("talon") > moved("vanguard") > moved("specter")
    assert page.evaluate("SkySentinel.get('fixed').chooseShip('zeppelin')") is False


def test_cards_select_by_click_and_arrow_keys(page) -> None:
    page.evaluate("(() => { const g = SkySentinel.get('fixed'); g.configure({ defects: {}, seed: 7 }); g.chooseShip('vanguard'); })()")
    host = ".ss-host[data-ss-id=fixed]"
    page.locator(f"{host} [data-ship=talon]").click()
    assert page.evaluate("SkySentinel.get('fixed').state().ship") == "talon"
    page.locator(f"{host} [data-ship=talon]").focus()
    page.keyboard.press("ArrowRight")
    assert page.evaluate("SkySentinel.get('fixed').state().ship") == "raptor"
    assert page.evaluate("document.activeElement.dataset.ship") == "raptor", "focus follows the choice"
    page.keyboard.press("ArrowRight")
    assert page.evaluate("SkySentinel.get('fixed').state().ship") == "vanguard", "the choice wraps around"
    page.evaluate("SkySentinel.get('fixed').chooseShip('vanguard')")


@pytest.mark.parametrize("kind", UPGRADES)
def test_every_upgrade_kind_is_collected_and_takes_effect(page, kind: str) -> None:
    _quiet(page, pad=GRACE + 10)
    s = _js(page, f"""g.forceHit('beam'); g.step({INVULN}); const before = g.state();
        g.dropPowerUp('{kind}'); return Object.assign(g.step(2), {{ before }});""")
    assert s["collected"][-1]["kind"] == kind
    if kind == "shield":
        assert s["shieldHp"] == SHIELD
    elif kind == "repair":
        assert s["health"] == min(s["healthMax"], s["before"]["health"] + 35) > s["before"]["health"]
    else:
        assert s["player"][kind] > 0 and kind in [u["kind"] for u in s["upgrades"]], "a timed upgrade shows in the HUD list"


def test_a_piercing_shot_passes_through_every_target(page) -> None:
    def kills(pierce: bool) -> int:
        _quiet(page, pad=10)
        return _js(page, f"""{"g.dropPowerUp('pierce'); g.step(2);" if pierce else ""}
            const p = g.state().player; g.spawn('interceptor', p.x, p.y - 160); g.spawn('interceptor', p.x, p.y - 260); g.spawn('interceptor', p.x, p.y - 360);
            g.input({{ fire: true }}); g.step(1); g.input({{ fire: false }}); return 3 - g.step(50).enemies;""")
    assert kills(False) < 3 and kills(True) == 3


def test_time_slow_halves_the_enemy_side(page) -> None:
    def fall(slow: bool) -> float:
        _quiet(page, pad=10)
        return _js(page, f"""{"g.dropPowerUp('slow'); g.step(2);" if slow else ""}
            g.spawnAsteroid('large', 100, 100, 0, 2, 'repair'); const y0 = g.state().carriers[0].y; return g.step(40).carriers[0].y - y0;""")
    normal, slowed = fall(False), fall(True)
    assert normal == 80 and slowed == 40


def test_the_magnet_reels_in_a_far_upgrade(page) -> None:
    def got(magnet: bool) -> list:
        _quiet(page, pad=10)
        return _js(page, f"""{"g.dropPowerUp('magnet'); g.step(2);" if magnet else ""}
            const p = g.state().player; g.spawnAsteroid('small', p.x, p.y - 300, 0, 0, 'shield');
            g.input({{ fire: true }}); g.step(20); g.input({{ fire: false }});
            return g.step(70).collected.map(c => c.kind);""")
    assert "shield" not in got(False)
    assert "shield" in got(True)


@pytest.mark.parametrize("what", ["enemy", "asteroid"])
def test_a_carrier_drops_exactly_the_upgrade_it_glows_with(page, what: str) -> None:
    _quiet(page, pad=10)
    spawn = "g.spawn('gunship', p.x, p.y - 220, 'magnet')" if what == "enemy" else "g.spawnAsteroid('medium', p.x, p.y - 220, 0, 0, 'magnet')"
    s = _js(page, f"""const p = g.state().player; {spawn}; const c = g.state().carriers;
        g.input({{ fire: true }}); const s = g.step(60); g.input({{ fire: false }}); return Object.assign(s, {{ c }});""")
    assert s["c"] == [{**s["c"][0], "what": what, "upgrade": "magnet"}]
    assert s["drops"] and s["drops"][0]["upgrade"] == "magnet"
    assert s["drops"][0]["from"] == ("gunship" if what == "enemy" else "medium asteroid")
    assert "magnet" in s["powerUpKinds"] or s["collected"][-1]["kind"] == "magnet"


def test_carriers_appear_in_play_with_valid_upgrades_and_drop_often(page) -> None:
    out = _js(page, """g.configure({ defects: {}, seed: 8, threats: true, level: 1 }); g.start(); g.pause('t');
        const seen = new Map(); g.input({ fire: true });
        for (let i = 0; i < 80; i++) { const s = g.step(30); s.carriers.forEach(c => seen.set(c.what + c.type + Math.round(c.x), c.upgrade)); if (s.state === 'over') break; }
        g.input({ fire: false }); const s = g.state();
        return { kinds: [...seen.values()], drops: s.drops, spawned: s.spawned, state: s.state };""")
    assert len(out["kinds"]) >= 5, out
    assert set(out["kinds"]) <= set(UPGRADES) and len(set(out["kinds"])) >= 3, "carriers hold a variety of upgrades"
    assert len(out["drops"]) >= 3, "destroyed carriers release their upgrades"


def test_the_buggy_game_has_no_carriers(page) -> None:
    counts = page.evaluate("""(() => { const g = SkySentinel.get('buggy'); g.configure({ defects: {}, seed: 8, threats: true }); g.start(); g.pause('t');
        const n = []; for (let i = 0; i < 20; i++) n.push(g.step(60).carriers.length);
        g.configure({ defects: { firstHitFatal: true, randomExplosion: true }, seed: 4242 }); return n; })()""")
    assert counts == [0] * 20


def test_density_grows_through_a_level(page) -> None:
    early = _js(page, "g.configure({ defects: {}, seed: 7, threats: false, level: 1 }); g.start(); g.pause('t'); return g.step(300);")
    late = _js(page, "return g.step(4800);")
    assert 0 < early["levelProgress"] < 0.1 < 0.9 < late["levelProgress"] < 1
    assert early["spawnInterval"] > late["spawnInterval"] * 1.6, "enemies arrive far more often late in a level"
    assert early["enemyCap"] < late["enemyCap"] and early["rockInterval"] > late["rockInterval"] * 2
    # R18: aimed fire finds a ship that never dodges, so repair drops (outside the spawn stream) keep it alive
    counts = _js(page, """g.configure({ defects: {}, seed: 8, threats: true, level: 1 }); g.start(); g.pause('t'); g.input({ fire: true });
        const run = (n) => { let s; for (let k = 0; k < n; k += 100) { g.dropPowerUp('repair'); s = g.step(Math.min(100, n - k)); } return s; };
        const a = run(1500); const b = run(2400); const c = run(1300); g.input({ fire: false });
        return { first: a.spawned, last: c.spawned - b.spawned, rocksFirst: a.breaks.length, state: c.state };""")
    assert counts["state"] != "over", counts
    assert counts["last"] > counts["first"] * 1.4, f"the last 1,300 ticks send more enemies than the first 1,500: {counts}"


def test_the_buggy_fatal_hit_shows_its_damage_and_drains_the_bar(page) -> None:
    out = page.evaluate("""(() => { const g = SkySentinel.get('buggy'); g.configure({ defects: { firstHitFatal: true, randomExplosion: true }, seed: 4242, threats: false });
        g.start(); g.pause('t'); g.step(30); g.forceHit('needle'); const s = g.state();
        const said = document.querySelector('.ss-host[data-ss-id=buggy] .ss-live').textContent;
        g.configure({ threats: true }); return { s, said }; })()""")
    s = out["s"]
    assert s["health"] == 0 and s["lastDamage"]["amount"] == 6 and s["overText"] == "Destroyed by a single hit: an interceptor dart"
    assert s["popups"] == [{"text": "-6", "color": "#fca5a5", "big": True}]
    assert "6-point hit emptied a hull of 100" in out["said"]


# ---------------------------------------------------------------- R16: the start screen fits the arena

FIT_VIEWPORTS = [(1280, 900), (1440, 900), (1920, 1080), (1366, 768), (1280, 720), (390, 844)]

FIT_PROBE = """(id) => {
  const host = document.querySelector('.ss-host[data-ss-id=' + id + ']');
  const ov = host.querySelector('.ss-overlay'), box = ov.getBoundingClientRect();
  const shown = (e) => e.getClientRects().length > 0;
  const inside = (e) => { const r = e.getBoundingClientRect(); return r.left >= box.left - 0.5 && r.right <= box.right + 0.5 && r.top >= box.top - 0.5 && r.bottom <= box.bottom + 0.5; };
  const items = [...host.querySelectorAll('.ss-ship, .ss-start, .ss-key-item, .ss-brand, .ss-keybtn, .ss-ship-note, .ss-hint')].filter(shown);
  const clipped = [...host.querySelectorAll('.ss-ship-name, .ss-ship-weapon, .ss-key-text b, .ss-key-text span')].filter(shown).filter(e => e.scrollWidth > e.clientWidth + 1 || !inside(e));
  return { overflow: getComputedStyle(ov).overflowY, sh: ov.scrollHeight, ch: ov.clientHeight, sw: ov.scrollWidth, cw: ov.clientWidth,
           outside: items.filter(e => !inside(e)).map(e => e.className), clipped: clipped.map(e => e.textContent),
           ships: [...host.querySelectorAll('.ss-ship')].filter(shown).length, keys: [...host.querySelectorAll('.ss-key-item')].filter(shown).length,
           start: shown(host.querySelector('.ss-start')), toggle: shown(host.querySelector('.ss-keybtn')) };
}"""


@pytest.mark.parametrize("viewport", FIT_VIEWPORTS, ids=lambda v: f"{v[0]}x{v[1]}")
def test_the_start_screen_fits_the_arena_with_no_scroll_bar(browser, viewport: tuple[int, int]) -> None:
    """R16 maintainer review: the start screen overflowed the arena behind a scroll bar."""
    pg = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
    try:
        pg.goto(TRAINING.as_uri() + "#play-buggy")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        for gid in ("buggy", "fixed"):
            pg.locator(f".ss-host[data-ss-id={gid}] .ss-stage").scroll_into_view_if_needed()
            pg.wait_for_timeout(150)
            panels = [pg.evaluate(FIT_PROBE, gid)]
            if panels[0]["toggle"]:
                # a narrow arena shows ships and the key one at a time; both panels must fit
                pg.locator(f".ss-host[data-ss-id={gid}] .ss-keybtn").click()
                panels.append(pg.evaluate(FIT_PROBE, gid))
                pg.locator(f".ss-host[data-ss-id={gid}] .ss-keybtn").click()
            for m in panels:
                assert m["overflow"] == "hidden", "the overlay never scrolls"
                assert m["sh"] <= m["ch"] and m["sw"] <= m["cw"], f"{gid} {viewport}: content overflows the arena: {m}"
                assert m["outside"] == [] and m["clipped"] == [], f"{gid} {viewport}: {m}"
                assert m["start"], "the Start button always shows"
            assert max(m["ships"] for m in panels) == 5 and max(m["keys"] for m in panels) == 10, panels
    finally:
        pg.close()


# ---------------------------------------------------------------- R16: every damage path is fatal in the buggy build

BUGGY = "{ firstHitFatal: true, randomExplosion: true }"

# Each source is the real hazard placed against a parked ship in the buggy game; the run then
# steps through the real loop (no forceHit) until the hit lands.
REAL_HAZARDS = [
    ("shot", None, "g.spawn('gunship', p.x, p.y - 330);", {}),
    ("needle", None, "g.spawn('interceptor', p.x, p.y - 330);", {}),
    ("beam", None, "g.spawn('lancer', p.x, p.y - 330);", {"progression": True, "level": 2}),
    ("blast", "bomber", "g.spawn('bomber', p.x, p.y - 330);", {"progression": True, "level": 2}),
    ("collision", "gunship", "g.spawn('gunship', p.x, p.y);", {}),
    ("collision", "interceptor", "g.spawn('interceptor', p.x, p.y);", {}),
    ("collision", "lancer", "g.spawn('lancer', p.x, p.y);", {}),
    ("collision", "bomber", "g.spawn('bomber', p.x, p.y);", {}),
    ("asteroid", "large", "g.spawnAsteroid('large', p.x, p.y - 120, 0, 3);", {}),
    ("asteroid", "medium", "g.spawnAsteroid('medium', p.x, p.y - 120, 0, 3);", {}),
    ("asteroid", "small", "g.spawnAsteroid('small', p.x, p.y - 120, 0, 3);", {}),
    ("asteroid", "small", "g.spawnAsteroid('small', p.x + 22, p.y - 120, 0, 3);", {}),
    ("bossShot", None, "", {"progression": True, "boss": True, "level": 3, "bossNow": True}),
]


@pytest.mark.parametrize("source, detail, place, extra", REAL_HAZARDS, ids=lambda v: str(v)[:24] if isinstance(v, str) else None)
def test_the_buggy_build_dies_on_the_first_real_hit_from_every_source(page, source: str, detail, place: str, extra: dict) -> None:
    out = page.evaluate(
        """([place, extra]) => { const g = SkySentinel.get('buggy');
            g.configure(Object.assign({ defects: """ + BUGGY + """, seed: 4242, threats: false }, extra)); g.start(); g.pause('t');
            g.step(""" + str(GRACE) + """); g.dropPowerUp('shield'); g.step(2);
            const p = g.state().player; const shield = g.state().shieldHp; if (place) new Function('g', 'p', place)(g, p);
            let s = g.state(); for (let i = 0; i < 1200 && s.state !== 'over' && !s.hitTicks.length; i++) s = g.step(1);
            g.configure({ defects: """ + BUGGY + """, seed: 4242, threats: true, progression: false, boss: false, level: 1 });
            return Object.assign(s, { shieldBefore: shield }); }""",
        [place, extra],
    )
    assert out["hitTicks"], f"{source}: the hazard never reached the ship"
    assert out["state"] == "over" and out["overReason"] == "first-hit", f"{source} {detail}: {out['state']} {out['overReason']}"
    assert out["health"] == 0 and out["shieldHp"] == 0, "the first hit empties hull and shield"
    assert out["lastDamage"]["source"] == source and len(out["hitTicks"]) == 1
    assert any(u["big"] and u["text"] == f"-{out['lastDamage']['amount']}" for u in out["popups"]), "the real damage shows"


def test_a_wing_graze_is_a_hit_because_the_hit_shape_follows_the_drawn_ship(page) -> None:
    """R16 root cause: a bolt could visibly strike a wing and pass through an 18 px hit circle."""
    out = page.evaluate("""(() => { const g = SkySentinel.get('buggy');
        const fresh = () => { g.configure({ defects: """ + BUGGY + """, seed: 4242, threats: false }); g.start(); g.pause('t'); g.step(10); };
        fresh(); const p = g.view().player; g.spawnAsteroid('small', 40, 40, 0, 0); const rr = g.view().threats.slice(-1)[0].r;
        // the same seed draws the same rock again: place it past the old circle's reach, inside the wing
        const off = p.hw + rr - 8; fresh(); g.spawnAsteroid('small', p.x + off, p.y - 100, 0, 3);
        const s = g.step(60); g.configure({ threats: true }); return { s, hw: p.hw, r: p.r, off, oldReach: p.r + rr - 6 }; })()""")
    assert out["hw"] > out["r"] and out["off"] > out["oldReach"], f"the rock passes outside the old 18 px circle: {out['off']} > {out['oldReach']}"
    assert out["s"]["overReason"] == "first-hit", "it strikes the drawn wing, so it is a hit"


def test_the_buggy_build_ignores_the_invulnerability_window(page) -> None:
    out = page.evaluate("""(() => { const g = SkySentinel.get('buggy');
        g.configure({ defects: { firstHitFatal: true }, seed: 4242, threats: false }); g.start(); g.pause('t'); g.step(5);
        const before = g.state().player.invuln; g.forceHit('needle'); const s = g.state();
        g.configure({ defects: """ + BUGGY + """, threats: true }); return { before, s }; })()""")
    assert out["s"]["overReason"] == "first-hit"


def test_the_self_test_blast_is_fatal_too_in_the_buggy_build(page) -> None:
    """R16 root cause: a dodging player lived past 20 s and the 40-point self-test blast left the
    ship alive with a damage number over it, which read as a hit the bug failed to punish."""
    s = page.evaluate("""(() => { const g = SkySentinel.get('buggy');
        g.configure({ defects: """ + BUGGY + """, seed: 4242, threats: false }); g.start(); g.pause('t');
        const s = g.step(""" + str(EARLIEST + 700) + """); g.configure({ threats: true }); return s; })()""")
    assert s["explodeTicks"] and s["state"] == "over" and s["overReason"] == "explode"
    assert s["health"] == 0 and s["lastDamage"]["amount"] == 40 and s["hitTicks"] == []
    assert s["overText"] == "The ship blew itself up, with no hit"


@pytest.mark.parametrize("ship", SHIP_IDS)
def test_the_buggy_build_stays_fatal_after_play_again_and_a_ship_change(page, ship: str) -> None:
    out = page.evaluate("""(ship) => { const g = SkySentinel.get('buggy');
        g.configure({ defects: """ + BUGGY + """, seed: 4242, threats: false }); g.start(); g.pause('t'); g.step(20); g.forceHit('needle');
        const first = g.state().overReason;
        document.querySelector('.ss-host[data-ss-id=buggy] .ss-change').click(); g.chooseShip(ship);
        g.start(); g.pause('t'); g.step(20); const p = g.state().player; g.spawnAsteroid('small', p.x, p.y - 80, 0, 3);
        const second = g.step(60);
        g.start(); g.pause('t'); g.step(20); const q = g.state().player; g.spawn('interceptor', q.x, q.y);
        const third = g.step(2);
        g.chooseShip('vanguard'); g.configure({ threats: true }); return { first, second, third }; }""", ship)
    assert out["first"] == "first-hit"
    assert out["second"]["ship"] == ship and out["second"]["overReason"] == "first-hit", "after a ship change"
    assert out["third"]["overReason"] == "first-hit" and out["third"]["tick"] < 30, "after Play again"


@pytest.mark.parametrize("ship", SHIP_IDS)
def test_the_buggy_game_dies_on_its_first_hit_through_the_real_ui(browser, ship: str) -> None:
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    try:
        pg.goto(TRAINING.as_uri() + "#play-buggy")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('buggy')")
        host = ".ss-host[data-ss-id=buggy]"
        pg.locator(f"{host} .ss-stage").scroll_into_view_if_needed()
        pg.locator(f"{host} [data-ship={ship}]").click()
        pg.locator(f"{host} .ss-start").click()
        assert pg.evaluate("SkySentinel.get('buggy').state().state") == "running"
        pg.evaluate("(() => { const g = SkySentinel.get('buggy'); const p = g.state().player; g.spawnAsteroid('medium', p.x, p.y - 140, 0, 4); })()")
        pg.wait_for_function("SkySentinel.get('buggy').state().state === 'over'", timeout=15000)
        s = pg.evaluate("SkySentinel.get('buggy').state()")
        assert s["ship"] == ship and s["overReason"] == "first-hit" and len(s["hitTicks"]) == 1
        assert pg.locator(f"{host} .ss-over-title").inner_text().startswith("Destroyed by a single hit")
    finally:
        pg.close()


# ---------------------------------------------------------------- R16: each ship has its own weapon

def test_each_ship_fires_its_own_weapon(page) -> None:
    out = _js(page, """const out = {};
        for (const id of ['vanguard', 'warden', 'specter', 'talon', 'raptor']) {
            g.configure({ defects: {}, seed: 7, threats: false, level: 1 }); g.chooseShip(id); g.start(); g.pause('t'); g.step(5);
            const y0 = g.state().player.y;
            g.input({ fire: true }); const a = g.step(1); const b = g.step(6); g.input({ fire: false }); const c = g.step(40);
            out[id] = { weapon: a.weapon, first: a.playerShots, later: b.playerShots, y0, gone: c.playerShots };
        }
        g.chooseShip('vanguard'); return out;""")
    kinds = {k: v["weapon"]["kind"] for k, v in out.items()}
    assert kinds == {"vanguard": "cannon", "warden": "flak", "specter": "orb", "talon": "lance", "raptor": "burst"}
    assert len({v["weapon"]["name"] for v in out.values()}) == 5
    for ship, v in out.items():
        assert {s["kind"] for s in v["first"]} == {kinds[ship]}, f"{ship} fires its own rounds"
    assert len(out["vanguard"]["first"]) == 2 and out["vanguard"]["first"][0]["dmg"] == 2, "two heavy rounds side by side"
    assert len(out["raptor"]["first"]) == 1 and len(out["raptor"]["later"]) == 3, "a three-round burst from one pull"
    assert out["talon"]["first"][0]["len"] > 150 and out["talon"]["first"][0]["pierce"], "a ray that cuts through"
    assert len(out["specter"]["first"]) == 1 and out["specter"]["first"][0]["dmg"] == 2
    flak = out["warden"]
    xs = sorted(p["x"] for p in flak["first"])
    assert len(flak["first"]) == 5 and xs[-1] - xs[0] > 4, "a cone of five pellets that spread"
    assert not any(p["kind"] == "flak" for p in flak["gone"]), "flak is short-range: every pellet fades out"
    cards = page.locator(".ss-host[data-ss-id=fixed] .ss-ship").evaluate_all(
        "els => els.map(e => [e.querySelector('.ss-ship-weapon').textContent, e.querySelector('.ss-ship-desc').textContent])")
    api = page.evaluate("SkySentinel.get('fixed').ships()")
    assert cards == [[s["weaponName"], s["weaponNote"]] for s in api], "each card names its weapon and what it does"


def test_the_lance_cuts_every_target_in_its_reach_and_orbs_split(page) -> None:
    lance = _js(page, """g.configure({ defects: {}, seed: 7, threats: false }); g.chooseShip('talon'); g.start(); g.pause('t'); g.step(5);
        const p = g.state().player; g.spawn('interceptor', p.x, p.y - 80); g.spawn('interceptor', p.x, p.y - 150);
        g.input({ fire: true }); const s = g.step(3); g.input({ fire: false }); g.chooseShip('vanguard'); return s.enemies;""")
    assert lance == 0, "one lance pull cuts both interceptors in its column"
    orbs = _js(page, """g.configure({ defects: {}, seed: 7, threats: false }); g.chooseShip('specter'); g.start(); g.pause('t'); g.step(5);
        const p = g.state().player; g.spawnAsteroid('large', p.x, p.y - 200, 0, 0);
        g.input({ fire: true }); let s = g.state(), most = 0; for (let i = 0; i < 40; i++) { s = g.step(1); most = Math.max(most, s.playerShots.filter(x => x.kind === 'orb' && x.dmg === 1).length); }
        g.input({ fire: false }); g.chooseShip('vanguard'); return most;""")
    assert orbs >= 2, "an orb that hits splits into two smaller orbs"


@pytest.mark.parametrize("ship", SHIP_IDS)
def test_upgrades_stack_on_every_weapon(page, ship: str) -> None:
    out = _js(page, f"""const v = (kind) => {{ g.configure({{ defects: {{}}, seed: 7, threats: false }}); g.chooseShip('{ship}'); g.start(); g.pause('t'); g.step(5);
            if (kind) {{ g.dropPowerUp(kind); g.step(2); }}
            g.input({{ fire: true }}); const n = g.step(1).playerShots.length; const many = g.step(59); g.input({{ fire: false }});
            return [n, many.playerShots.length, many.weapon.cooldown]; }};
        const out = {{ base: v(null), twin: v('weapon'), spread: v('spread') }}; g.chooseShip('vanguard'); return out;""")
    assert out["twin"][0] == out["base"][0] * 2, f"{ship}: Twin doubles the barrels {out}"
    assert out["spread"][0] == out["base"][0] + 2, f"{ship}: Spread adds two side shots {out}"


# ---------------------------------------------------------------- R18: aimed enemy fire

AIM_CLASSES = ["gunship", "interceptor", "lancer", "bomber"]


def _miss(a: dict) -> float:
    """How far a logged shot's line passes from where the ship was when it fired (px)."""
    if a["kind"] == "beam":
        return abs(a["x"] - a["px"])
    if a["kind"] == "bomb":
        return math.hypot(a["tx"] - a["px"], a["ty"] - a["py"])
    dx, dy, vx, vy = a["px"] - a["x"], a["py"] - a["y"], a["vx"], a["vy"]
    assert dx * vx + dy * vy > 0, f"the shot flies toward the ship: {a}"
    return abs(dx * vy - dy * vx) / math.hypot(vx, vy)


@pytest.mark.parametrize("cls", AIM_CLASSES)
def test_every_enemy_weapon_aims_at_the_ship_where_it_is_when_it_fires(page, cls: str) -> None:
    """R18 maintainer review: enemy fire was not aimed at the ship, which made the game too easy."""
    _quiet(page, level=3, pad=GRACE + 10)
    seen = _js(page, f"""g.dropPowerUp('shield'); g.step(2);
        const cls = '{cls}', p0 = g.state().player, mine = () => g.aimLog().filter(a => a.cls === cls);
        g.spawn(cls, cls === 'lancer' ? p0.x - 200 : p0.x + 260, 90);
        const seen = [];
        for (const move of ['left', 'right', 'left']) {{
            g.input({{ [move]: true }}); g.step(12); g.input({{ left: false, right: false }});
            const before = mine().length;
            for (let n = 0; n < 700 && mine().length === before && g.state().state !== 'over'; n++) g.step(1);
            if (mine().length > before) seen.push(mine()[before]);
        }}
        return seen;""")
    assert len(seen) == 3, f"{cls} fired three times: {seen}"
    assert len({round(a["px"]) for a in seen}) >= 2, "the ship moved between shots"
    errors = [_miss(a) for a in seen]
    assert max(errors) < 0.5, f"{cls} aim errors {errors}"


@pytest.mark.parametrize("enemy, source", [("gunship", "shot"), ("interceptor", "needle")])
def test_a_shot_from_far_to_the_side_still_hits_a_parked_ship(page, enemy: str, source: str) -> None:
    _quiet(page, level=1, pad=GRACE + 10)
    s = _js(page, f"""const p = g.state().player; g.spawn('{enemy}', p.x + 300, p.y - 330);
        let s = g.state(); for (let i = 0; i < 400 && !s.lastDamage; i++) s = g.step(1); return s;""")
    assert s["lastDamage"] and s["lastDamage"]["source"] == source, "an aimed shot finds a ship that does not move"


def test_the_boss_aims_its_bolts_at_the_ship(page) -> None:
    page.evaluate("""(() => { const g = SkySentinel.get('fixed');
        g.configure({ defects: {}, seed: 7, threats: false, level: 3, progression: true, boss: true, bossNow: true }); g.start(); g.pause('t'); })()""")
    log = _js(page, "g.dropPowerUp('shield'); g.step(700); return g.aimLog().filter(a => a.cls === 'boss');")
    _js(page, "g.configure({ progression: true, boss: true, level: 1 });")
    assert len(log) >= 4 and max(_miss(a) for a in log) < 0.5


# ---------------------------------------------------------------- R18: the end card is centred

CARD_PROBE = """(id) => {
  const h = document.querySelector('.ss-host[data-ss-id=' + id + ']'), g = SkySentinel.get(id);
  g.render();
  const ov = h.querySelector('.ss-overlay').getBoundingClientRect(), pn = h.querySelector('.ss-panel').getBoundingClientRect();
  const cv = h.querySelector('.ss-canvas').getBoundingClientRect();
  const parts = [...h.querySelectorAll('.ss-over-title, .ss-start, .ss-change, .ss-hint')].filter(e => e.getClientRects().length)
    .map(e => { const r = e.getBoundingClientRect(); return r.left >= pn.left - 0.5 && r.right <= pn.right + 0.5 && r.top >= pn.top - 0.5 && r.bottom <= pn.bottom + 0.5; });
  const pops = g.state().popupBoxes.map(b => ({ x: b.x + cv.left, y: b.y + cv.top }));
  return { dx: (pn.left + pn.right) / 2 - (ov.left + ov.right) / 2, dy: (pn.top + pn.bottom) / 2 - (ov.top + ov.bottom) / 2,
           inside: pn.top >= ov.top - 0.5 && pn.bottom <= ov.bottom + 0.5 && pn.left >= ov.left - 0.5 && pn.right <= ov.right + 0.5,
           parts, pops, covered: pops.filter(p => p.x > pn.left && p.x < pn.right && p.y > pn.top && p.y < pn.bottom).length,
           shown: pops.filter(p => p.x > cv.left && p.x < cv.right && p.y > cv.top && p.y < cv.bottom).length,
           title: h.querySelector('.ss-over-title').textContent };
}"""


@pytest.mark.parametrize("viewport", [(1440, 900), (1280, 720), (390, 844)], ids=lambda v: f"{v[0]}x{v[1]}")
def test_the_end_card_sits_in_the_centre_of_the_arena(browser, viewport: tuple[int, int]) -> None:
    """R18 maintainer review: the game-over message sat near the top of the arena."""
    pg = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
    try:
        pg.goto(TRAINING.as_uri() + "#play-buggy")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        pg.evaluate("SkySentinel.manual(true)")
        cards = {}
        for gid in ("buggy", "fixed"):
            pg.locator(f".ss-host[data-ss-id={gid}] .ss-stage").scroll_into_view_if_needed()
            # a death with the ship parked high in its band, right where a centred card could hide the number
            pg.evaluate("""(id) => { const g = SkySentinel.get(id);
                g.configure({ defects: { firstHitFatal: true }, seed: 7, threats: false, level: 1 }); g.start(); g.pause('t');
                g.input({ up: true }); g.step(40); g.input({ up: false }); g.forceHit('shot'); }""", gid)
            cards[gid + " death"] = pg.evaluate(CARD_PROBE, gid)
        pg.evaluate("""() => { const g = SkySentinel.get('fixed');
            g.configure({ defects: {}, seed: 7, threats: false, level: 3, progression: true, boss: true, bossNow: true }); g.start(); g.pause('t'); g.step(600);
            for (let i = 0; i < 4; i++) g.hitBoss('node' + i, 8); g.hitBoss('core', 24); }""")
        cards["fixed victory"] = pg.evaluate(CARD_PROBE, "fixed")
        assert cards["fixed victory"]["title"] == "The Nexus megaship is down"
        for name, m in cards.items():
            assert abs(m["dx"]) < 2 and abs(m["dy"]) < 2, f"{name} {viewport}: the card is centred {m}"
            assert m["inside"] and all(m["parts"]), f"{name} {viewport}: title, buttons, and hint sit in the card {m}"
            if "death" in name:
                assert m["shown"] >= 1 and m["covered"] == 0, f"{name} {viewport}: the damage number stays visible {m}"
    finally:
        pg.close()


# ---------------------------------------------------------------- R18: five colours, animated previews

def _hue(hex_colour: str) -> float:
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


HUES = {"red": (-15, 15), "orange": (15, 38), "yellow": (38, 65), "green": (90, 160), "blue": (200, 240)}


def test_each_ship_owns_one_main_colour(page) -> None:
    ships = page.evaluate("SkySentinel.get('fixed').ships()")
    assert {s["id"]: s["colour"] for s in ships} == SHIP_COLOURS
    for s in ships:
        lo, hi = HUES[s["colour"]]
        for c in (s["accent"], s["weaponColor"]):
            h = _hue(c)
            h = h - 360 if h > 180 + hi else h
            assert lo <= h <= hi, f"{s['id']} {c} reads as {s['colour']}"


PREVIEW_GRAB = "id => [...document.querySelectorAll('.ss-host[data-ss-id=' + id + '] .ss-ship-pic')].map(c => c.toDataURL())"


def test_each_card_animates_its_weapon_and_stops_when_hidden(browser) -> None:
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    try:
        pg.goto(TRAINING.as_uri() + "#play-fixed")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        pg.locator(".ss-host[data-ss-id=fixed] .ss-stage").scroll_into_view_if_needed()
        pg.wait_for_function("SkySentinel.get('fixed').previewing()")
        a = pg.evaluate(PREVIEW_GRAB, "fixed")
        pg.wait_for_timeout(250)
        b = pg.evaluate(PREVIEW_GRAB, "fixed")
        assert len(a) == 5 and len(set(a)) == 5, "five different scenes"
        assert all(x != y for x, y in zip(a, b, strict=True)), "every card is moving"
        pg.evaluate("SkySentinel.get('fixed').start()")
        pg.wait_for_timeout(120)
        assert pg.evaluate("SkySentinel.get('fixed').previewing()") is False, "the previews stop while the game runs"
        pg.evaluate("SkySentinel.get('fixed').pause('t'); SkySentinel.get('fixed').reset()")
        pg.wait_for_function("SkySentinel.get('fixed').previewing()")
        pg.evaluate("window.scrollTo(0, 0)")
        pg.wait_for_timeout(200)
        assert pg.evaluate("SkySentinel.get('fixed').previewing()") is False, "the previews stop off screen"
    finally:
        pg.close()


def test_reduced_motion_shows_still_previews(browser) -> None:
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    try:
        pg = ctx.new_page()
        pg.goto(TRAINING.as_uri() + "#play-fixed")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        pg.locator(".ss-host[data-ss-id=fixed] .ss-stage").scroll_into_view_if_needed()
        pg.wait_for_timeout(200)
        a = pg.evaluate(PREVIEW_GRAB, "fixed")
        pg.wait_for_timeout(250)
        assert pg.evaluate("SkySentinel.get('fixed').previewing()") is False
        assert pg.evaluate(PREVIEW_GRAB, "fixed") == a and len(set(a)) == 5, "five still frames, each its own weapon"
    finally:
        ctx.close()


# ---------------------------------------------------------------- R18 (T086): demo mode

MK_DEMO = """window.mkDemo = (variant, opts) => {
  const d = document.createElement('div'); d.className = 'demo-host'; d.style.cssText = 'width:560px;height:350px';
  document.body.prepend(d);
  const c = SkySentinel.demo(d, Object.assign({ variant }, opts || {}));
  c.ev = []; c.on('hit', e => c.ev.push(['hit', e])); c.on('end', e => c.ev.push(['end', e]));
  return c;
};"""


@pytest.fixture(scope="module")
def demo_page(browser):
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    pg.goto(TRAINING.as_uri())
    pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
    pg.evaluate(MK_DEMO)
    yield pg
    pg.close()


def _demo(pg, variant: str, opts: dict | None = None, ms: int = 4000) -> dict:
    return pg.evaluate("""([v, opts, ms]) => { const c = mkDemo(v, opts); c.seek(ms);
        const out = { info: c.info, ev: c.ev, st: c.state(),
                      buttons: document.querySelector('.demo-host').querySelectorAll('button, .ss-overlay').length,
                      role: document.querySelector('.demo-host canvas').getAttribute('role'), ids: SkySentinel.ids() };
        c.destroy(); document.querySelector('.demo-host').remove(); return out; }""", [variant, opts or {}, ms])


def test_the_buggy_demo_is_destroyed_by_its_one_hit(demo_page) -> None:
    out = _demo(demo_page, "buggy")
    info, ev, st = out["info"], out["ev"], out["st"]
    assert [e[0] for e in ev] == ["hit", "end"]
    hit, end = ev[0][1], ev[1][1]
    assert (hit["source"], hit["amount"], hit["fatal"], hit["health"]) == ("shot", 10, True, 0), "a 10-point gunship bolt empties the hull"
    assert end["destroyed"] is True and end["health"] == 0
    assert info == {"source": "shot", "sourceText": "a gunship bolt", "amount": 10, "hitMs": hit["ms"], "hullBefore": 100, "hullAfter": 0, "destroyed": True}
    assert st["destroyed"] and st["ended"] and st["renderer"] == "webgl" and st["popups"] == ["-10"]
    assert out["ids"] == ["buggy", "fixed"], "a demo is not a game"
    assert out["buttons"] == 0 and out["role"] == "img", "no start screen, no buttons, not interactive"


def test_the_fixed_demo_takes_the_damage_and_flies_on(demo_page) -> None:
    out = _demo(demo_page, "fixed")
    info, ev, st = out["info"], out["ev"], out["st"]
    assert [e[0] for e in ev] == ["hit", "end"]
    hit, end = ev[0][1], ev[1][1]
    assert (hit["source"], hit["amount"], hit["fatal"], hit["health"]) == ("shot", 10, False, 90)
    assert end["destroyed"] is False and end["health"] == 90 == info["hullAfter"] == info["hullBefore"] - info["amount"]
    assert st["renderer"] == "webgl" and not st["destroyed"] and st["enemies"] == 0, "it flies on and shoots the gunship down"
    assert len(st["aimLog"]) == 1 and _miss(st["aimLog"][0]) < 0.5, "one aimed bolt"


def test_a_demo_is_deterministic_and_seekable(demo_page) -> None:
    a = _demo(demo_page, "fixed", ms=2500)["st"]
    b = _demo(demo_page, "fixed", ms=2500)["st"]
    assert a == b
    hit_ms = a["hit"]["ms"]
    assert 1000 < hit_ms < 3000
    assert _demo(demo_page, "fixed", ms=hit_ms - 50)["st"]["hit"] is None
    assert _demo(demo_page, "fixed", ms=hit_ms + 20)["st"]["hit"]["amount"] == 10


@pytest.mark.parametrize("opts, health, renderer", [({"ship": "raptor"}, 80, "webgl"), ({"renderer": "2d"}, 90, "2d")])
def test_demo_options_pick_the_ship_and_the_renderer(demo_page, opts: dict, health: int, renderer: str) -> None:
    st = _demo(demo_page, "fixed", opts)["st"]
    assert st["health"] == health and st["renderer"] == renderer and st["ship"] == opts.get("ship", "vanguard")


def test_a_demo_plays_in_real_time_pauses_off_screen_and_ends(demo_page) -> None:
    demo_page.evaluate("window.live = mkDemo('buggy'); live.play();")
    demo_page.wait_for_function("live.state().ms > 300", timeout=5000)
    demo_page.evaluate("window.scrollTo(0, 5000)")
    demo_page.wait_for_timeout(200)
    t0 = demo_page.evaluate("live.state().ms")
    demo_page.wait_for_timeout(400)
    assert demo_page.evaluate("live.state().ms") == t0, "an off-screen demo waits"
    demo_page.evaluate("window.scrollTo(0, 0)")
    demo_page.wait_for_function("live.state().ended", timeout=8000)
    out = demo_page.evaluate("(() => { const r = { ev: live.ev.map(e => e[0]), st: live.state() }; live.destroy(); const h = document.querySelector('.demo-host'); const empty = h.innerHTML === ''; h.remove(); r.empty = empty; return r; })()")
    assert out["ev"] == ["hit", "end"] and out["st"]["destroyed"] and out["empty"]


def test_a_demo_under_reduced_motion_shows_its_final_frame(browser) -> None:
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    try:
        pg = ctx.new_page()
        pg.goto(TRAINING.as_uri())
        pg.wait_for_function("window.SkySentinel")
        pg.evaluate(MK_DEMO)
        st = pg.evaluate("(() => { const c = mkDemo('buggy'); c.play(); return c.state(); })()")
        assert st["ended"] and st["ms"] == 4000 and st["destroyed"] and not st["playing"]
    finally:
        ctx.close()
