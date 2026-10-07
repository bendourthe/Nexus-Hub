"""v4.13.10 plan revision 10 (R35 to R37): enemy health, full-arena movement, downgrades, a moving
background, the Nexus boss's entrance, agent ships, and the finale that hands off to the reward.

Like the other engine tests, every test drives the simulation through ``step(n)`` with a fixed seed
and ``SkySentinel.manual(true)``; nothing waits on real time to move the game. The finale is the one
part that also plays in real time on the page, and the hand-off test lets it do so once. Design and
the per-class and per-level tables: docs/releases/v4/v4.13/development/v4.13.10-game-design.md,
"Revision 10". The level-scaling tests (cadence, speed, shields) live in test_training_progression.py.
Skipped without Playwright or Chromium; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

SHIP_IDS = ["vanguard", "warden", "specter", "talon", "raptor"]
CLASSES = ["gunship", "interceptor", "lancer", "bomber", "agent"]
DOWNGRADES = ["mine", "freeze", "slowfire", "scramble"]
INTRO, FINALE_LEN = 270, 760  # R40: the black-hole finale runs 760 ticks


@pytest.fixture(scope="module")
def playwright_mod():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    return sync_playwright


@pytest.fixture(scope="module")
def browser(playwright_mod):
    with playwright_mod() as pw:
        try:
            b = pw.chromium.launch()
        except Exception as exc:  # pragma: no cover - environment dependent
            if REQUIRE_RENDER:
                pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
            pytest.skip(f"chromium is unavailable: {exc}")
        yield b
        b.close()


def _open(browser, width: int = 1280, height: int = 900, motion: str = "no-preference", renderer: str | None = None):
    ctx = browser.new_context(viewport={"width": width, "height": height}, reduced_motion=motion)
    if renderer:
        ctx.add_init_script(f"window.SKY_SENTINEL_RENDERER = '{renderer}';")
    pg = ctx.new_page()
    errors: list[str] = []
    pg.on("pageerror", lambda exc: errors.append(str(exc)))
    pg.goto(TRAINING.as_uri() + "#play-fixed")
    pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
    pg.evaluate("SkySentinel.manual(true)")
    return ctx, pg, errors


@pytest.fixture(scope="module")
def page(browser):
    ctx, pg, errors = _open(browser)
    yield pg
    assert not errors, errors
    ctx.close()


def _js(page, body: str):
    return page.evaluate(f"(() => {{ const g = SkySentinel.get('fixed'); {body} }})()")


def _quiet(page, level: int = 1, ship: str = "vanguard", pad: int = 10) -> None:
    _js(page, f"""g.configure({{ defects: {{}}, seed: 7, threats: false, level: {level}, progression: true, boss: true }});
        g.chooseShip('{ship}'); g.start(); g.pause('t'); g.step({pad}); return 0;""")


def _boss(page, threats: bool = False, ship: str = "vanguard") -> dict:
    """Level 3 with the boss on its way (a short wormhole first); returns the state when it spawns."""
    return _js(page, f"""g.configure({{ defects: {{}}, seed: 7, threats: {str(threats).lower()}, level: 3, progression: true, boss: true, bossNow: true }});
        g.chooseShip('{ship}'); g.start(); g.pause('t');
        let s = g.state(), n = 0; while (!s.boss && n++ < 1000) s = g.step(1); return s;""")


# ---------------------------------------------------------------- R35 (T110): enemy health and life bars

@pytest.mark.parametrize("level", [1, 2, 3])
def test_each_class_has_its_health_and_every_class_but_the_smallest_shows_a_life_bar(page, level: int) -> None:
    _quiet(page, level=level)
    out = _js(page, """const p = g.state().player;
        ['gunship', 'interceptor', 'lancer', 'bomber', 'agent'].forEach((t, i) => g.spawn(t, 120 + i * 160, 200));
        g.render(); return { foes: g.state().foes, bars: g.lifeBars(), classes: g.enemyClasses() };""")
    table = {c["type"]: c["hp"][level - 1] for c in out["classes"]}
    assert {f["type"]: f["hp"] for f in out["foes"]} == table, "each class spawns with its level's health"
    assert all(f["hp"] == f["hpMax"] for f in out["foes"])
    assert sorted(b["type"] for b in out["bars"]) == sorted(c for c in CLASSES if c != "interceptor"), out["bars"]
    assert all(b["frac"] == 1 and b["w"] > 10 for b in out["bars"]), "an unhurt enemy shows a full bar"
    # health grows with bulk (radius over cruise speed) among the four line classes
    line = sorted((c for c in out["classes"] if c["type"] != "agent"), key=lambda c: c["bulk"])
    assert [c["hp"][level - 1] for c in line] == sorted(c["hp"][level - 1] for c in line), line


def test_a_damaged_enemy_shows_a_shorter_bar(page) -> None:
    _quiet(page)
    out = _js(page, """const p = g.state().player; g.spawn('bomber', p.x, p.y - 200);
        g.input({ fire: true }); let s = g.state(), n = 0; while (s.dealt === 0 && n++ < 80) s = g.step(1); g.input({ fire: false });
        g.render(); return { foe: s.foes[0], bars: g.lifeBars() };""")
    foe, bar = out["foe"], out["bars"][0]
    assert foe["hp"] < foe["hpMax"] and bar["type"] == "bomber"
    assert bar["frac"] == pytest.approx(foe["hp"] / foe["hpMax"], abs=0.002) and bar["frac"] < 1


def test_no_class_but_the_smallest_dies_to_any_ships_strongest_single_round(page) -> None:
    """The heaviest round any ship fires, with any upgrade, stays below every class's health but the smallest."""
    out = _js(page, """const most = {};
        for (const id of ['vanguard', 'warden', 'specter', 'talon', 'raptor']) {
          let best = 0;
          for (const up of [null, 'weapon', 'spread', 'pierce', 'rapid', 'missiles']) {
            g.configure({ defects: {}, seed: 7, threats: false, level: 3, progression: true }); g.chooseShip(id); g.start(); g.pause('t'); g.step(5);
            if (up) { g.dropPowerUp(up); g.step(2); }
            g.input({ fire: true }); for (let i = 0; i < 60; i++) { const s = g.step(1); s.playerShots.forEach(x => { best = Math.max(best, x.dmg); }); } g.input({ fire: false });
          }
          most[id] = best;
        }
        g.chooseShip('vanguard'); return { most, classes: g.enemyClasses(), strongest: g.strongestRound };""")
    heaviest = max(out["most"].values())
    assert heaviest == out["strongest"], out["most"]
    for c in out["classes"]:
        for hp in c["hp"]:
            if c["type"] == "interceptor":
                assert hp == 1, "the smallest class still dies to a single round"
            else:
                assert hp > heaviest, f"{c['type']} must survive one hit of {heaviest}: {c}"


@pytest.mark.parametrize("ship", SHIP_IDS)
def test_one_trigger_pull_kills_an_interceptor_but_never_a_larger_class(page, ship: str) -> None:
    """Against every ship, at the balance harness's mid range: only the smallest class falls to one pull."""
    out = _js(page, f"""const r = {{}};
        for (const t of ['interceptor', 'gunship', 'lancer', 'bomber', 'agent']) {{
          g.configure({{ defects: {{}}, seed: 7, threats: false, level: 1, progression: true }}); g.chooseShip('{ship}'); g.start(); g.pause('t'); g.step(5);
          const p = g.state().player; g.spawn(t, p.x, p.y - 170);
          g.input({{ fire: true }}); g.step(1); g.input({{ fire: false }});
          let s = g.state(), n = 0; while (n++ < 70) s = g.step(1);
          r[t] = {{ left: s.foes.length, dealt: s.dealt }};
        }}
        g.chooseShip('vanguard'); return r;""")
    assert out["interceptor"]["left"] == 0, f"{ship}: one pull destroys an interceptor {out}"
    for t in ("gunship", "lancer", "bomber", "agent"):
        assert out[t]["dealt"] > 0 and out[t]["left"] == 1, f"{ship}: a {t} survives one pull {out}"


# ---------------------------------------------------------------- R35 (T111): full-arena movement

@pytest.mark.parametrize("viewport", [(1440, 900), (390, 844)], ids=lambda v: f"{v[0]}x{v[1]}")
def test_the_ship_reaches_all_four_edges_and_stops_short_of_the_hud(browser, viewport: tuple[int, int]) -> None:
    ctx, pg, errors = _open(browser, *viewport)
    try:
        pg.locator(".ss-host[data-ss-id=fixed] .ss-stage").scroll_into_view_if_needed()
        out = pg.evaluate("""() => { const g = SkySentinel.get('fixed');
            g.configure({ defects: {}, seed: 7, threats: false, level: 1 }); g.start(); g.pause('t');
            const go = (k) => { const i = {}; i[k] = true; g.input(i); const s = g.step(260); g.input({ [k]: false }); return s.player; };
            const left = go('left'), up = go('up'), right = go('right'), down = go('down');
            const s = g.state(), cv = s.canvas;
            return { left, up, right, down, w: s.world.w, h: s.world.h, hw: s.hitHalfWidth, cssPerUnit: cv.cssHeight / s.world.h, cssW: cv.cssWidth }; }""")
        assert out["left"]["x"] < out["hw"] * 1.6 and out["right"]["x"] > out["w"] - out["hw"] * 1.6, out
        assert out["down"]["y"] > out["h"] - 30, out
        assert out["up"]["y"] < out["h"] * 0.3, f"the ship flies far above the old half-height line: {out}"
        band = 98 if out["cssW"] < 520 else 66
        nose = (out["up"]["y"] - 18) * out["cssPerUnit"]
        assert nose >= band - 1, f"the ship stops below the HUD band: nose at {nose} css px, band {band}"
        assert out["up"]["top"] == out["up"]["y"]
    finally:
        assert not errors, errors
        ctx.close()


# ---------------------------------------------------------------- R36 (T113): downgrades

def test_freeze_holds_the_ship_still_until_its_timer_runs_out(page) -> None:
    _quiet(page, pad=200)
    out = _js(page, """g.dropPowerUp('freeze'); g.step(2); g.render(); const a = g.state();
        g.input({ left: true }); const b = g.step(60); const mid = g.state(); g.step(100); const c = g.step(20); g.input({ left: false });
        return { a, b: b.player, c: c.player, mid };""")
    a = out["a"]
    assert a["collected"][-1]["kind"] == "freeze" and a["player"]["freeze"] > 140
    assert {"kind": "freeze", "down": True, "seconds": 3} in a["chips"], a["chips"]
    assert out["b"]["x"] == a["player"]["x"], "frozen: left does nothing"
    assert out["mid"]["downgrades"][0]["kind"] == "freeze"
    assert out["c"]["freeze"] == 0 and out["c"]["x"] < a["player"]["x"], "the ship moves again once it thaws"


def test_slow_fire_halves_the_rate_of_fire_for_its_timer(page) -> None:
    def shots(slow: bool) -> int:
        _quiet(page, pad=200)
        return _js(page, f"""{"g.dropPowerUp('slowfire'); g.step(2);" if slow else ""}
            let n = 0, prev = 0; g.input({{ fire: true }});
            for (let i = 0; i < 240; i++) {{ const s = g.step(1); if (s.weapon.cooldown > prev) n += 1; prev = s.weapon.cooldown; }}
            g.input({{ fire: false }}); return n;""")
    base, slowed = shots(False), shots(True)
    assert slowed * 2 == pytest.approx(base, abs=1), (base, slowed)
    left = _js(page, "g.dropPowerUp('slowfire'); g.step(2); g.render(); return [g.state().player.slowfire, g.state().chips];")
    assert 290 <= left[0] <= 300 and any(c["kind"] == "slowfire" and c["down"] for c in left[1])
    assert _js(page, "return g.step(305).player.slowfire;") == 0


def test_scramble_swaps_left_and_right_for_its_timer(page) -> None:
    _quiet(page, pad=200)
    out = _js(page, """g.dropPowerUp('scramble'); const a = g.step(2).player;
        g.input({ left: true }); const b = g.step(30).player; g.input({ left: false }); g.step(240);
        g.input({ left: true }); const c = g.step(30).player; g.input({ left: false }); return { a, b, c };""")
    assert out["b"]["x"] > out["a"]["x"], "scrambled: left steers right"
    assert out["c"]["scramble"] == 0 and out["c"]["x"] < out["b"]["x"], "the controls come back"


def test_a_mine_bursts_on_contact_and_shooting_it_from_a_distance_is_safe(page) -> None:
    _quiet(page, level=1, pad=200)
    out = _js(page, """const p = g.state().player; g.spawnMine(p.x + 300, 150); g.render(); const shown = g.state();
        g.spawnMine(p.x, p.y - 40); let s = g.state(), n = 0; while (s.damageLog.length === 0 && n++ < 120) s = g.step(1);
        return { shown, s };""")
    assert out["shown"]["mines"] and any(c["kind"] == "mine" and c["down"] for c in out["shown"]["chips"]), "a mine shows a HUD timer"
    hit = out["s"]["damageLog"][-1]
    assert hit["source"] == "mine" and hit["amount"] == 20
    _quiet(page, level=1, pad=200)
    safe = _js(page, """const p = g.state().player; g.spawnMine(p.x, p.y - 260); g.input({ fire: true }); const s = g.step(40); g.input({ fire: false }); return s;""")
    assert safe["mines"] == [] and safe["damageTaken"] == 0, "a mine shot at range bursts harmlessly"


def test_a_mine_burns_out_on_its_timer(page) -> None:
    _quiet(page, pad=10)
    s = _js(page, "g.spawnMine(100, 100); const a = g.step(1).mines; const b = g.step(480).mines; return [a, b];")
    assert len(s[0]) == 1 and s[1] == []


@pytest.mark.parametrize("what", ["enemy", "asteroid"])
def test_a_hazard_carrier_drops_its_downgrade(page, what: str) -> None:
    """R39 (renamed): a hazard carrier no longer wears a marking; it still drops its downgrade."""
    _quiet(page, pad=10)
    spawn = "g.spawn('gunship', p.x, p.y - 220, 'freeze')" if what == "enemy" else "g.spawnAsteroid('medium', p.x, p.y - 220, 0, 0, 'freeze')"
    out = _js(page, f"""const p = g.state().player; {spawn}; const before = g.state();
        g.input({{ fire: true }}); let s = g.state(), n = 0; while (!s.downs.length && n++ < 120) s = g.step(1); g.input({{ fire: false }});
        return {{ before, s }};""")
    b, s = out["before"], out["s"]
    assert b["carriers"] == [] and b["hazards"][0]["downgrade"] == "freeze" and b["hazards"][0]["what"] == what
    assert s["downs"][0]["downgrade"] == "freeze" and s["drops"] == []
    assert "freeze" in s["powerUpKinds"] or s["collected"][-1]["kind"] == "freeze"


def test_the_magnet_never_pulls_a_downgrade(page) -> None:
    def got(kind: str) -> dict:
        _quiet(page, pad=10)
        return _js(page, f"""g.dropPowerUp('magnet'); g.step(2); const p = g.state().player;
            g.spawnAsteroid('small', p.x, p.y - 300, 0, 0, '{kind}');
            g.input({{ fire: true }}); g.step(20); g.input({{ fire: false }});
            const s = g.step(70); return {{ collected: s.collected.map(c => c.kind), left: s.powerUpKinds }};""")
    assert "shield" in got("shield")["collected"], "the magnet reels in an upgrade"
    hazard = got("slowfire")
    assert "slowfire" not in hazard["collected"] and "slowfire" in hazard["left"], "but never a downgrade"


def test_downgrades_drop_in_play_but_stay_rarer_than_upgrades(page) -> None:
    out = _js(page, """g.configure({ defects: {}, seed: 8, threats: true, level: 1, progression: true }); g.start(); g.pause('t');
        const hz = new Map(); g.input({ fire: true });
        for (let i = 0; i < 160; i++) { g.dropPowerUp('repair'); const s = g.step(30); s.hazards.forEach(c => hz.set(c.what + c.type + Math.round(c.x), c.downgrade)); if (s.state === 'over') break; }
        g.input({ fire: false }); const s = g.state();
        return { hazards: [...hz.values()], downs: s.downs.length, drops: s.drops.length, rates: g.dropRates() };""")
    assert out["hazards"] and set(out["hazards"]) <= set(DOWNGRADES), out
    assert out["downs"] >= 1, out
    assert out["drops"] > out["downs"] * 2, f"downgrades stay a risk, not a wall: {out}"
    assert out["rates"]["downShare"] < 0.5 and abs(sum(w for _, w in out["rates"]["downWeights"]) - 1) < 1e-9


def test_a_hazard_pickup_is_a_threat_to_a_reader_not_a_prize(page) -> None:
    """view() is what a player reads: a downgrade pickup falls among the threats, not the prizes."""
    _quiet(page, pad=10)
    out = _js(page, """const p = g.state().player; g.spawnAsteroid('small', p.x, p.y - 300, 0, 0, 'scramble');
        g.input({ fire: true }); let s = g.state(), n = 0; while (!s.powerUpKinds.length && n++ < 60) s = g.step(1); g.input({ fire: false });
        return { kinds: s.powerUpKinds, view: g.view() };""")
    assert out["kinds"] == ["scramble"]
    assert out["view"]["powerUps"] == []
    assert any(t["r"] == 14 for t in out["view"]["threats"]), out["view"]["threats"]


def test_the_start_screen_key_lists_the_downgrades_as_hazards(page) -> None:
    _js(page, "g.configure({ defects: {}, seed: 7 }); return 0;")
    host = ".ss-host[data-ss-id=fixed]"
    # R39: the full key, with names and effects, sits behind the Pickups button
    page.locator(f"{host} .ss-keybtn").click()
    items = page.locator(f"{host} .ss-down-item").evaluate_all(
        "els => els.map(e => [e.dataset.downgrade, getComputedStyle(e).getPropertyValue('--ss-up').trim(), e.innerText])")
    page.locator(f"{host} .ss-keybtn").click()
    api = _js(page, "return g.downgrades();")
    assert [x[0] for x in items] == DOWNGRADES == [d["kind"] for d in api]
    assert all(len(x[2].split("\n")) >= 2 for x in items), "a name and a one-line effect"
    assert page.locator(f"{host} .ss-down-title").inner_text().startswith("Hazards")
    upgrades = {u["color"] for u in _js(page, "return g.upgrades();")}
    assert len({d["color"] for d in api}) == 4 and not ({d["color"] for d in api} & upgrades), "hazards never share an upgrade's colour"


# ---------------------------------------------------------------- R36 (T114): the background moves

@pytest.mark.parametrize("renderer", ["webgl", "2d"])
def test_every_background_layer_moves_between_frames_on_every_map(browser, renderer: str) -> None:
    ctx, pg, errors = _open(browser, renderer=None if renderer == "webgl" else "2d")
    try:
        pg.locator(".ss-host[data-ss-id=fixed] .ss-stage").scroll_into_view_if_needed()
        out = pg.evaluate("""() => { const g = SkySentinel.get('fixed'); const out = [];
            for (const level of [1, 2, 3]) {
              g.configure({ defects: {}, seed: 7, threats: false, level, progression: true, boss: false }); g.start(); g.pause('t'); g.step(30);
              const a = g.background(); g.render(); const pa = g.state().renderer;
              g.step(120); const b = g.background();
              out.push({ level, a, b, renderer: pa, map: g.state().map });
            }
            return out; }""")
        for frame in out:
            a, b = frame["a"], frame["b"]
            assert frame["renderer"] == renderer
            assert all(x != y for x, y in zip(a["stars"], b["stars"])), f"star layers scroll: {frame}"
            for layer in ("nebula", "cloud", "planet"):
                moved = max(abs(x - y) for x, y in zip(a[layer], b[layer]))
                assert 0.5 < moved < 60, f"{layer} drifts slowly but visibly on {frame['map']}: {moved}"
            assert b["spin"] != a["spin"], "the station turns"
        # the motion loops: the layers come back within their period instead of running away
        loop = pg.evaluate("""() => { const g = SkySentinel.get('fixed'); g.configure({ defects: {}, seed: 7, threats: false, level: 1 }); g.start(); g.pause('t');
            let lo = 1e9, hi = -1e9; for (let i = 0; i < 60; i++) { const p = g.step(120).player; const b = g.background(); lo = Math.min(lo, b.planet[0]); hi = Math.max(hi, b.planet[0]); }
            return { lo, hi, w: g.state().world.w }; }""")
        assert loop["lo"] < 0 < loop["hi"] and loop["hi"] - loop["lo"] < loop["w"] * 0.13, loop
    finally:
        assert not errors, errors
        ctx.close()


# ---------------------------------------------------------------- R37 (T115): the boss's entrance, life bar, and agents

def test_the_boss_enters_with_a_title_card_and_cannot_hurt_or_be_hurt_meanwhile(page) -> None:
    s = _boss(page)
    assert s["boss"]["intro"]["len"] == INTRO and s["boss"]["intro"]["t"] <= 1 and s["boss"]["intro"]["title"] is False
    mid = _js(page, f"""const s = g.step({INTRO // 2}); g.render(); const geo = g.bossGeometry();
        return {{ s: g.state(), hit: g.forceHit('shot'), shot: g.shotAt(geo.nodes[2][0], geo.nodes[2][1]) }};""")
    st = mid["s"]
    assert st["boss"]["intro"]["title"] is True and st["hud"]["title"]["alpha"] > 0.5, "the title card shows mid-entrance"
    assert 0 < st["boss"]["intro"]["grow"] < 1, "the megaship is still growing out of its rift"
    assert mid["hit"] is False and st["health"] == st["healthMax"], "nothing hurts the ship during the entrance"
    assert mid["shot"] is False and st["boss"]["hp"] == st["boss"]["hpMax"], "shots pass through until it has arrived"
    done = _js(page, f"return g.step({INTRO});")
    assert done["boss"]["entered"] and done["boss"]["intro"] is None
    assert _js(page, "g.render(); return g.state().hud.title;") is None


def test_the_boss_has_its_own_life_bar_that_drains_node_by_node(page) -> None:
    """R40 (updated): the bar now totals the three shield layers, the four nodes, and the core."""
    _boss(page)
    out = _js(page, f"""g.step({INTRO + 5}); g.render(); const a = g.state(); const plan = g.bossPlan();
        g.breakShields(); g.hitBoss('node0', plan.nodeHp); g.render(); const b = g.state();
        for (let i = 1; i < 4; i++) g.hitBoss('node' + i, plan.nodeHp); g.hitBoss('core', plan.coreHp / 2); g.render(); const c = g.state();
        return {{ a, b, c, plan }};""")
    a, b, c, plan = out["a"], out["b"], out["c"], out["plan"]
    total = plan["total"]
    assert a["boss"]["hp"] == a["boss"]["hpMax"] == total and a["hud"]["bossBar"]["frac"] == 1
    left = 3 * plan["nodeHp"] + plan["coreHp"]
    assert b["boss"]["hp"] == left and b["hud"]["bossBar"]["frac"] == pytest.approx(left / total, abs=0.002)
    assert c["boss"]["hp"] == plan["coreHp"] / 2 and c["hud"]["bossBar"]["frac"] == pytest.approx(plan["coreHp"] / 2 / total, abs=0.002)
    bar = a["hud"]["bossBar"]
    assert bar["w"] > 300 and bar["y"] < 70, "a large bar across the top of the arena"


def test_the_boss_launches_agent_ships_that_attack_and_drop_pickups(page) -> None:
    _boss(page, threats=True)
    out = _js(page, f"""let s = g.step({INTRO + 10}); const t0 = s.tick; let n = 0;
        while (s.agentsLaunched < 4 && n++ < 1200) {{ g.dropPowerUp('repair'); s = g.step(1); }}
        const agents = s.foes.filter(f => f.type === 'agent');
        let fired = false; for (let i = 0; i < 300 && !fired; i++) {{ g.dropPowerUp('repair'); s = g.step(1); fired = g.aimLog().some(a => a.cls === 'agent'); }}
        return {{ launched: s.agentsLaunched, waited: s.tick - t0, agents, fired }};""")
    assert out["launched"] >= 4 and out["waited"] < 1000, out
    assert out["agents"] and all(a["hp"] == 7 for a in out["agents"]), "agent ships survive one hit"
    assert out["fired"], "agent ships fire aimed darts"
    for carry, key, field in (("rapid", "drops", "upgrade"), ("slowfire", "downs", "downgrade")):
        _quiet(page, pad=10)
        got = _js(page, f"""const p = g.state().player; g.spawn('agent', p.x, p.y - 200, '{carry}');
            g.input({{ fire: true }}); let s = g.state(), n = 0; while (!s.{key}.length && n++ < 200) s = g.step(1); g.input({{ fire: false }});
            return s.{key};""")
        assert got and got[0]["from"] == "agent" and got[0][field] == carry, got


def test_without_threats_the_boss_launches_no_agents(page) -> None:
    _boss(page, threats=False)
    s = _js(page, f"return g.step({INTRO + 900});")
    assert s["agentsLaunched"] == 0, "the balance harness measures the boss alone"


# ---------------------------------------------------------------- R37 (T116): the finale and the hand-off

def _kill_boss(page) -> dict:
    _boss(page)
    return _js(page, f"""g.step({INTRO + 5}); const ev = []; window.__ev = ev;
        g.on('rewardUnlocked', e => ev.push(['reward', e.tick])); g.on('bossDefeated', e => ev.push(['boss', e.tick]));
        g.defeatBoss(); return g.state();""")


def test_the_finale_plays_its_destruction_black_hole_and_prize_card_then_unlocks_the_reward(page) -> None:
    """R40 (updated): explode, tear, collapse, swallow, universe, prize, over 10 to 14 s."""
    s = _kill_boss(page)
    assert s["state"] == "over" and s["victory"] and s["boss"] is None
    assert s["finale"]["phase"] == "explode" and not s["finale"]["done"]
    assert page.evaluate("window.__ev") == [["boss", s["tick"]]], "the reward waits for the finale"
    assert page.locator(".ss-host[data-ss-id=fixed] .ss-overlay").is_hidden(), "no end card over the finale"
    seen, frames, best = [], {}, None
    for _ in range(FINALE_LEN // 10 + 2):
        st = _js(page, "const s = g.step(10); g.render(); return g.state();")
        ph = st["finale"]["phase"]
        if not seen or seen[-1] != ph:
            seen.append(ph)
        frames.setdefault(ph, st)
        if st["hud"]["prize"] and (best is None or st["hud"]["prize"]["alpha"] >= best["alpha"]):
            best = st["hud"]["prize"]
    assert seen == ["explode", "tear", "collapse", "swallow", "universe", "prize"], seen
    assert frames["explode"]["map"] == "The Nexus Storm" and frames["universe"]["map"] == "A New Universe", "past the black hole, a new universe"
    assert best and best["alpha"] == 1 and best["w"] > 300, f"the prize card fills the middle of the arena: {best}"
    end = _js(page, "return g.step(60);")
    assert end["finale"]["done"] and page.evaluate("window.__ev")[-1][0] == "reward"
    assert 10 <= FINALE_LEN / 60 <= 14, "the sequence lasts 10 to 14 s"
    over = page.locator(".ss-host[data-ss-id=fixed] .ss-over-prize")
    assert over.is_visible() and "Nexus AI Studio" in over.inner_text()


def test_one_skip_jumps_to_the_prize_card_and_a_second_ends_the_finale(page) -> None:
    _kill_boss(page)
    a = _js(page, "g.step(30); g.skipFinale(); g.render(); return g.state();")
    assert a["finale"]["phase"] == "prize" and a["finale"]["skipped"] == 1 and not a["finale"]["done"]
    assert a["hud"]["prize"]["alpha"] == 1, "the skip lands on the prize card, fully shown"
    b = _js(page, "g.skipFinale(); return g.state();")
    assert b["finale"]["done"] and page.evaluate("window.__ev")[-1][0] == "reward"


def test_a_click_or_a_key_on_the_arena_skips_the_finale(browser) -> None:
    ctx, pg, errors = _open(browser, 1440, 900)
    try:
        pg.locator(".ss-host[data-ss-id=fixed] .ss-stage").scroll_into_view_if_needed()
        pg.evaluate(f"""() => {{ const g = SkySentinel.get('fixed');
            g.configure({{ defects: {{}}, seed: 7, threats: false, level: 3, bossNow: true }}); g.start(); g.pause('t');
            let s = g.state(); while (!(s.boss && s.boss.entered)) s = g.step(5);
            g.defeatBoss(); }}""")
        pg.locator(".ss-host[data-ss-id=fixed] .ss-canvas").click()
        assert pg.evaluate("SkySentinel.get('fixed').state().finale.phase") == "prize"
        pg.locator(".ss-host[data-ss-id=fixed] .ss-canvas").focus()
        pg.keyboard.press("Space")
        st = pg.evaluate("SkySentinel.get('fixed').state()")
        assert st["finale"]["done"] and st["state"] == "over", "a key ends it; it never restarts the game"
        pg.wait_for_function("NexusTrainingPage.reward()", timeout=5000)
    finally:
        assert not errors, errors
        ctx.close()


def test_the_finale_hands_off_to_the_reward_panel_in_real_time(browser) -> None:
    ctx, pg, errors = _open(browser, 1440, 900)
    try:
        pg.evaluate(f"""() => {{ const g = SkySentinel.get('fixed');
            g.configure({{ level: 3, bossNow: true }}); g.start(); g.step(600);
            g.defeatBoss(); SkySentinel.manual(false); }}""")
        assert pg.evaluate("NexusTrainingPage.reward()") is False, "the panel waits for the finale"
        pg.wait_for_function("SkySentinel.get('fixed').state().finale.phase === 'prize'", timeout=15000)
        assert pg.evaluate("NexusTrainingPage.reward()") is False
        pg.wait_for_function("NexusTrainingPage.reward()", timeout=15000)
        assert pg.locator("#trReward").is_visible() and pg.evaluate("document.activeElement.id") == "trReward"
    finally:
        assert not errors, errors
        ctx.close()


def test_reduced_motion_shortens_the_entrance_and_the_finale_to_still_frames(browser) -> None:
    ctx, pg, errors = _open(browser, 1440, 900, motion="reduce")
    try:
        out = pg.evaluate("""() => { const g = SkySentinel.get('fixed');
            g.configure({ defects: {}, seed: 7, threats: false, level: 3, bossNow: true }); g.start(); g.pause('t');
            let s = g.state(); while (!s.boss) s = g.step(1);
            g.render(); const intro = g.state();
            let n = 0; while (!s.boss.entered) { s = g.step(1); n++; }
            g.defeatBoss();
            const phases = []; let f = g.state();
            while (!f.finale.done) { f = g.step(1); if (phases[phases.length - 1] !== f.finale.phase) phases.push(f.finale.phase); }
            return { intro, entrance: n, phases, finale: f.finale }; }""")
        assert out["intro"]["boss"]["intro"]["len"] == 90 and out["intro"]["boss"]["intro"]["grow"] == 1, "a still megaship with its title"
        assert out["intro"]["boss"]["intro"]["title"] is True
        assert out["entrance"] <= 90
        # R40 (updated): four still frames: the wreck, the black hole, the new universe, the prize
        assert out["phases"] == ["explode", "swallow", "universe", "prize"], out["phases"]
        assert out["finale"]["still"] and out["finale"]["len"] == 300
    finally:
        assert not errors, errors
        ctx.close()
