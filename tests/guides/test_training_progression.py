"""v4.13.10 Phase 6: levels, ship forms, power-ups, and the Nexus megaship boss.

Like the Phase 3 engine tests, every test drives the simulation through ``step(n)`` with a
fixed seed and ``SkySentinel.manual(true)``; nothing waits on real time. Progression and
the boss are switched on per game: the buggy game has neither, the partly fixed game has
progression, and the fixed game has both. Phase R10 gave each level a named difficulty
(Easy, Medium, Hard) that is measurably harder than the last. Phase R14 put a wormhole between
levels (no input, no damage) and gave each level, and the boss, its own map; the level number
and the timings are unchanged, so the transition plays during the first moments of each level.
Phase R16 gave each ship its own weapon; the default Vanguard fires twin cannons (two rounds per
pull), so the gun counts below are twice the old single gun's, and the dodging bot now reads
the ship's real hit width (``view().player.hw``), which follows the drawn wingspan.
Phase R18 aimed every enemy weapon at the ship, so shots converge on wherever it is; the bot now
sweeps each threat forward in time against its own path for nine candidate moves, and the
measurement tests that only hold fire keep the ship alive with repair drops (which never touch
the spawn stream).
Skipped without Playwright or Chromium; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

LEVEL2, LEVEL3, BOSS_AT = 5400, 12000, 15600
HEALTH, SHIELD = 100, 50


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


@pytest.fixture(scope="module")
def page(browser):
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    pg.goto(TRAINING.as_uri() + "#play-fixed")
    pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
    pg.evaluate("SkySentinel.manual(true)")
    yield pg
    pg.close()


def _fresh(page, game: str = "fixed", **cfg) -> None:
    page.evaluate(
        """([game, cfg]) => { const g = SkySentinel.get(game);
            g.configure(Object.assign({ defects: {}, seed: 31, threats: false, level: 1 }, cfg)); g.start(); g.pause('test'); }""",
        [game, cfg],
    )


def _js(page, body: str, game: str = "fixed"):
    return page.evaluate(f"(() => {{ const g = SkySentinel.get('{game}'); {body} }})()")


def test_games_carry_the_right_features(page) -> None:
    flags = page.evaluate("['buggy', 'fixed'].map(id => { const s = SkySentinel.get(id).state(); return [s.progression, s.bossEnabled, s.defects]; })")
    assert flags == [
        [False, False, {"firstHitFatal": True, "randomExplosion": True}],
        [True, True, {"firstHitFatal": False, "randomExplosion": False}],
    ]


def test_levels_and_ship_forms_follow_survival_time(page) -> None:
    _fresh(page)
    s = _js(page, f"return g.step({LEVEL2 - 1});")
    assert (s["level"], s["form"]) == (1, "Scout")
    s = _js(page, "return g.step(1);")
    assert (s["level"], s["form"]) == (2, "Fighter") and s["levelUps"] == [LEVEL2]
    s = _js(page, f"return g.step({LEVEL3 - LEVEL2});")
    assert (s["level"], s["form"]) == (3, "Sentinel") and s["levelUps"] == [LEVEL2, LEVEL3]


def test_the_boss_arrives_four_to_five_minutes_in(page) -> None:
    _fresh(page)
    s = _js(page, f"return g.step({BOSS_AT - 1});")
    assert s["boss"] is None
    s = _js(page, "return g.step(1);")
    assert s["boss"] is not None and s["boss"]["nodesAlive"] == 4
    assert 240 <= BOSS_AT / 60 <= 300, "a typical reader meets the boss after 4 to 5 minutes of play"


def test_progression_without_the_boss_levels_up_but_never_shows_it(page) -> None:
    _fresh(page, boss=False)
    s = _js(page, "const s = g.step(20000); g.configure({ boss: true }); return s;")
    assert s["level"] == 3 and s["boss"] is None and s["bossDue"] is None


def test_the_buggy_game_has_no_progression_or_power_ups(page) -> None:
    _fresh(page, game="buggy", threats=True, defects={})
    s = _js(page, "g.input({ fire: true }); const s = g.step(6000); g.input({ fire: false }); return s;", game="buggy")
    assert s["level"] == 1 and s["form"] == "Scout" and s["levelUps"] == []
    assert s["powerUps"] == 0 and s["collected"] == [], "power-ups never appear in the buggy game"
    assert set(s["enemyTypes"]) <= {"gunship", "interceptor"}
    assert s["difficulty"]["name"] == "Easy"


def _classes_seen(page, level: int) -> set[str]:
    _fresh(page, threats=True, level=level, seed=11)
    return set(_js(page, """const t = new Set(); g.input({ fire: true });
        for (let i = 0; i < 40 && g.state().state !== 'over'; i++) { g.dropPowerUp('repair'); g.step(60).enemyTypes.forEach(x => t.add(x)); }
        g.input({ fire: false }); return [...t];"""))


def test_enemy_variety_grows_with_the_level(page) -> None:
    assert _classes_seen(page, 1) <= {"gunship", "interceptor"}
    assert _classes_seen(page, 3) == {"gunship", "interceptor", "lancer", "bomber"}


@pytest.mark.parametrize("level, name", [(1, "Easy"), (2, "Medium"), (3, "Hard")])
def test_each_level_names_its_difficulty(page, level: int, name: str) -> None:
    _fresh(page, level=level)
    d = _js(page, "return g.state().difficulty;")
    assert d["level"] == level and d["name"] == name


def test_difficulty_rises_with_every_level(page) -> None:
    ds = []
    for level in (1, 2, 3):
        _fresh(page, level=level)
        ds.append(_js(page, "return g.state().difficulty;"))
    assert ds[0]["pace"] > ds[1]["pace"] > ds[2]["pace"], "enemies arrive more often"
    assert ds[0]["fire"] > ds[1]["fire"] > ds[2]["fire"], "they fire sooner"
    assert ds[0]["damage"] < ds[1]["damage"] < ds[2]["damage"], "they hit harder"
    assert ds[0]["cap"] < ds[1]["cap"] < ds[2]["cap"] and len(ds[0]["classes"]) < len(ds[1]["classes"]) <= len(ds[2]["classes"])


def test_harder_levels_send_more_enemies(page) -> None:
    rates = []
    for level in (1, 2, 3):
        _fresh(page, threats=True, level=level, seed=19)
        s = _js(page, "g.input({ fire: true }); const s = g.step(1500); g.input({ fire: false }); return s;")
        rates.append(s["spawned"] / s["tick"])
    assert rates[0] < rates[1] < rates[2], rates


# ---------------------------------------------------------------- R35 (T112): cadence, speed, health, shields

def test_cadence_speed_and_health_rise_by_a_measurable_step_each_level(page) -> None:
    """R39 (updated): each level's curve starts clearly above the last level's start (speed about 30
    percent up, spawn rate about 50 percent up), and every new enemy flies at the curve's speed for
    the moment it spawned, inside the level's range."""
    table = page.evaluate("SkySentinel.get('fixed').difficulty()")
    rate0, speed0, hp, shielded = ([d[k][0] if isinstance(d[k], list) else d[k] for d in table] for k in ("rate", "speed", "hp", "shielded"))
    for a, b in zip(speed0, speed0[1:]):
        assert 1.25 <= b / a <= 1.35, f"enemy speed rises 25 to 35 percent per level: {speed0}"
    for a, b in zip(rate0, rate0[1:]):
        assert 1.4 <= b / a <= 1.6, f"the spawn rate rises 40 to 60 percent per level: {rate0}"
    assert hp[0] < hp[1] < hp[2], hp
    assert shielded[0] == 0 < shielded[1] < shielded[2], "shields from level 2, more of them on level 3"
    measured = []
    for level in (1, 2, 3):
        _fresh(page, threats=True, level=level, seed=19)
        measured.append(_js(page, """const first = g.state().spawnInterval; const spd = new Set(); g.input({ fire: true });
            for (let i = 0; i < 30; i++) { g.dropPowerUp('repair'); g.step(40).foes.forEach(f => spd.add(f.spd)); }
            g.input({ fire: false }); return { first, spd: [...spd] };"""))
    assert measured[0]["first"] > measured[1]["first"] > measured[2]["first"], measured
    for level, m in zip((1, 2, 3), measured):
        lo, hi = table[level - 1]["speed"]
        assert m["spd"] and all(lo - 1e-9 <= v <= hi + 1e-9 for v in m["spd"]), f"level {level}: speeds on the level's curve {m}"


def test_shielded_ships_join_on_level_two_and_grow_on_level_three(page) -> None:
    """R39 (updated from the R35 last-level-only rule): none on level 1, about a fifth of the larger
    classes on level 2, about two fifths on level 3."""
    shares = []
    for level in (1, 2, 3):
        _fresh(page, threats=True, level=level, seed=23)
        shares.append(_js(page, """g.input({ fire: true }); let s;
            for (let i = 0; i < 80; i++) { g.dropPowerUp('repair'); s = g.step(40); }
            g.input({ fire: false }); return [s.shieldedSpawned, s.largeSpawned];"""))
    assert shares[0][0] == 0 and shares[0][1] > 0, shares
    s2, s3 = shares[1][0] / shares[1][1], shares[2][0] / shares[2][1]
    assert shares[1][1] >= 15 and 0.1 <= s2 <= 0.35, f"about 22 percent shielded on level 2: {shares}"
    assert shares[2][1] >= 20 and 0.28 <= s3 <= 0.62 and s3 > s2, f"about 42 percent shielded on level 3: {shares}"


def test_a_shield_ring_absorbs_hits_until_it_breaks_then_the_hull_takes_them(page) -> None:
    _fresh(page, level=3)
    out = _js(page, """g.step(5); const p = g.state().player; g.spawn('gunship', p.x, p.y - 200, null, { shield: true }); g.render();
        const bar = g.lifeBars()[0]; const trace = []; g.input({ fire: true });
        for (let i = 0; i < 90; i++) { const f = g.step(1).foes[0]; if (!f) break; trace.push([f.shield, f.hp, f.hpMax]); }
        g.input({ fire: false }); return { bar, trace, max: g.shieldHp };""")
    trace = out["trace"]
    assert out["bar"]["shield"] == out["max"] == 5, "the bar shows the shield on top of the hull"
    assert all(hp == hpm for sh, hp, hpm in trace if sh > 0), "the hull takes nothing while the shield holds"
    broke = next(i for i, t in enumerate(trace) if t[0] == 0)
    assert any(t[1] < t[2] for t in trace[broke:]) or len(trace) < 90, "once the shield breaks, hits reach the hull"


def test_a_level_up_announces_its_difficulty(page) -> None:
    _fresh(page)
    out = _js(page, f"""const seen = []; g.on('levelUp', e => seen.push([e.level, e.difficulty]));
        g.step({LEVEL3}); return {{ seen, s: g.state() }};""")
    assert out["seen"][-2:] == [[2, "Medium"], [3, "Hard"]]
    assert out["s"]["difficulty"]["name"] == "Hard"


def test_the_shield_bar_takes_hits_until_it_is_spent(page) -> None:
    _fresh(page)
    out = _js(page, """g.step(5); g.dropPowerUp('shield'); const a = g.step(2); const seen = [];
        for (let i = 0; i < 6; i++) { g.forceHit('shot'); const s = g.state(); seen.push([s.health, s.shieldHp]); g.step(61); }
        return { a, seen };""")
    assert out["a"]["shieldHp"] == SHIELD and out["a"]["collected"][0]["kind"] == "shield"
    assert out["seen"] == [[HEALTH, 40], [HEALTH, 30], [HEALTH, 20], [HEALTH, 10], [HEALTH, 0], [HEALTH - 10, 0]], out["seen"]


def test_weapon_gives_twin_shots_then_expires(page) -> None:
    _fresh(page)
    out = _js(page, """g.step(5); g.dropPowerUp('weapon'); g.step(2);
        g.input({ fire: true }); const twin = g.step(1).shots; g.input({ fire: false });
        g.step(620); g.input({ fire: true }); const single = g.step(10).shots; g.input({ fire: false });
        return { twin, single, weapon: g.state().player.weapon };""")
    assert out["twin"] == 4, "Twin doubles the Vanguard's two cannons"
    assert out["weapon"] == 0 and out["single"] == 2, "twin shot ends after 10 seconds"


def test_repairs_are_capped_at_a_full_hull(page) -> None:
    _fresh(page)
    health = _js(page, "g.step(5); g.forceHit('beam'); for (let i = 0; i < 4; i++) { g.dropPowerUp('repair'); g.step(2); } return g.state().health;")
    assert health == HEALTH


def test_two_power_ups_in_one_tick_both_apply(page) -> None:
    _fresh(page)
    s = _js(page, "g.step(5); g.dropPowerUp('shield'); g.dropPowerUp('weapon'); return g.step(2);")
    assert sorted(c["kind"] for c in s["collected"]) == ["shield", "weapon"]
    assert len({c["tick"] for c in s["collected"]}) == 1
    assert s["player"]["shield"] == SHIELD and s["player"]["weapon"] > 0


def test_a_power_up_expiring_across_a_level_change_leaves_nothing_stale(page) -> None:
    _fresh(page)
    s = _js(page, f"g.step({LEVEL2 - 300}); g.dropPowerUp('weapon'); g.step(2); return g.step(700);")
    assert s["level"] == 2 and s["player"]["weapon"] == 0
    shots = _js(page, "g.input({ fire: true }); const n = g.step(1).shots; g.input({ fire: false }); return n;")
    assert shots == 2, "the Fighter fires its own two cannons once twin shot has expired"


def test_the_sentinel_fires_twin_by_default_and_spread_with_the_weapon(page) -> None:
    _fresh(page, level=3)
    base = _js(page, "g.input({ fire: true }); const n = g.step(1).shots; g.input({ fire: false }); return n;")
    assert base == 4, "the Sentinel doubles the Vanguard's cannons by default"
    spread = _js(page, "g.step(20); g.dropPowerUp('weapon'); g.step(2); g.input({ fire: true }); const n = g.step(1).shots; g.input({ fire: false }); return n;")
    assert spread >= 6


def test_boss_nodes_fall_before_the_core_and_its_plates_block_shots(page) -> None:
    _fresh(page, level=3, bossNow=True)
    s = _js(page, "return g.step(600);")
    assert s["boss"]["entered"] and s["boss"]["nodesAlive"] == 4
    # R40: the shield layers stand first; a node and the core refuse damage until they fall
    assert _js(page, "return g.hitBoss('node0', 8);") is False and s["boss"]["stage"] == "shields"
    assert _js(page, "return g.breakShields();") is True
    geo = _js(page, "return g.bossGeometry();")
    plate = geo["plates"][0]
    cx = sum(p[0] for p in plate) / 3
    cy = sum(p[1] for p in plate) / 3
    assert page.evaluate(f"SkySentinel.get('fixed').shotAt({cx}, {cy})") is True, "a side plate absorbs a shot"
    assert _js(page, "return g.hitBoss('core', 5);") is False, "the core is shielded while any node lives"
    for i in range(4):
        assert _js(page, f"return g.hitBoss('node{i}', 999);") is True
    s = _js(page, "return g.state();")
    assert s["boss"]["nodesAlive"] == 0
    events = _js(page, "const seen = []; g.on('bossDefeated', e => seen.push(e)); g.hitBoss('core', 999); return seen.length;")
    assert events == 1
    s = _js(page, "return g.state();")
    assert s["victory"] and s["state"] == "over" and s["overReason"] == "victory" and s["boss"] is None


def test_jump_to_boss_starts_level_three_with_the_boss_moments_later(browser) -> None:
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    try:
        pg.goto(TRAINING.as_uri() + "#play-fixed")
        pg.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        pg.evaluate("SkySentinel.manual(true)")
        # Maintainer review: the boss is a surprise for players who clear every level, so the page
        # offers no visible shortcut; jumpToBoss() stays for tests.
        assert pg.locator('[data-stage="play-fixed"] .tr-jump-boss').count() == 0
        assert pg.evaluate("SkySentinel.get('fixed').jumpToBoss()") is True
        s = pg.evaluate("SkySentinel.get('fixed').state()")
        assert s["state"] == "running" and s["level"] == 3 and s["form"] == "Sentinel"
        s = pg.evaluate("SkySentinel.get('fixed').step(200)")
        assert s["boss"] is not None
    finally:
        pg.close()


DODGING_BOT = r"""
(seed) => {
  const g = SkySentinel.get('fixed');
  g.configure({ defects: {}, seed, threats: true, level: 1 });
  g.start(); g.pause('bot');
  // R18: enemy fire is aimed, so shots converge on wherever the ship is. The bot scores each of
  // nine moves by sweeping every threat forward in time against the ship's own path (it holds the
  // move for 12 ticks, then stops) and keeps the move with the least overlap.
  const sp = 7 * g.state().shipSpeed;
  const danger = (v, mx, my) => {
    const x0 = v.player.x, y0 = v.player.y, hw = v.player.hw, pr = v.player.r;
    let d = 0;
    const bx = x0 + mx * sp * 6, by = y0 + my * sp * 0.86 * 6;
    if (bx < 30 || bx > v.world.w - 30 || by < v.world.h * 0.55 || by > v.world.h - 24) return 1e9;
    for (const t of v.threats) {
      if (t.r > 60) {
        const x = x0 + mx * sp * 6, y = y0 + my * sp * 6;
        const gap = Math.hypot(t.x - x, t.y - y) - t.r - hw; if (gap < 30) d += (30 - gap) * 400; continue;
      }
      for (let tau = 0; tau <= 42; tau += 3) {
        const k = Math.min(tau, 12), x = x0 + mx * sp * k, y = y0 + my * sp * 0.86 * k;
        const tx = t.x + t.vx * tau, ty = t.y + t.vy * tau;
        const gx = Math.abs(tx - x) - t.r - hw, gy = Math.abs(ty - y) - t.r - pr;
        const gap = Math.max(gx, gy);
        if (gap < 24) d += (24 - gap) * (48 - tau);
      }
    }
    return d;
  };
  let s = g.state();
  while (s.state !== 'over' && !s.boss && s.tick < 17000) {
    const v = g.view();
    let best = [0, 0, danger(v, 0, 0)];
    if (best[2] > 0) for (const mx of [-1, 0, 1]) for (const my of [-1, 0, 1]) {
      const dd = danger(v, mx, my) + (mx || my ? 1 : 0);
      if (dd < best[2]) best = [mx, my, dd];
    }
    g.input({ fire: true, left: best[0] < 0, right: best[0] > 0, up: best[1] < 0, down: best[1] > 0 });
    s = g.step(3);
  }
  g.input({ fire: false, left: false, right: false, up: false, down: false });
  return { tick: s.tick, boss: !!s.boss, health: s.health, taken: s.damageTaken, sources: [...new Set(s.damageLog.map(d => d.source))] };
}
"""


@pytest.mark.parametrize("seed", [1, 7])
def test_a_dodging_player_reaches_the_boss_in_four_to_five_minutes(page, seed: int) -> None:
    """A simple bot that dodges and keeps firing reaches the boss; the run still costs hull on the way."""
    run = page.evaluate(DODGING_BOT, seed)
    assert run["boss"], f"seed {seed}: the bot died at tick {run['tick']} ({run['sources']})"
    assert 240 <= run["tick"] / 60 <= 300
    assert run["taken"] > 0, "the run costs something on the way"


def test_progression_keeps_the_defect_schedule_untouched(page) -> None:
    quiet = _js(page, "g.configure({ defects: { randomExplosion: true }, seed: 777, threats: false, progression: false }); g.start(); g.pause('t'); return g.step(1100).nextExplosion;")
    busy = _js(page, "g.configure({ defects: { randomExplosion: true }, seed: 777, threats: true, progression: true }); g.start(); g.pause('t'); g.input({ fire: true }); const n = g.step(1100).nextExplosion; g.input({ fire: false }); return n;")
    assert quiet == busy == page.evaluate("SkySentinel.defectSchedule(777, 5000)[0]")
    _js(page, "g.configure({ progression: true, boss: true });")


# ---------------------------------------------------------------- R14: the wormhole and the maps

MAP_NAMES = {1: "Cyan Reach", 2: "Violet Halo", 3: "Ember Belt", 4: "The Nexus Storm"}  # R40: the boss arena changed
TRANS, FLASH = 210, 120


def test_a_wormhole_carries_the_ship_between_levels_and_changes_the_map(page) -> None:
    _fresh(page)
    out = _js(page, f"""const ev = []; g.on('transition', e => ev.push([e.kind, e.to]));
        const before = g.step({LEVEL2 - 1}); const p0 = before.player;
        g.spawnAsteroid('large', 300, 200, 0, 0, 'shield'); g.spawn('gunship', 600, 150);
        const start = g.step(1);
        g.input({{ left: true, fire: true }}); const mid = g.step({FLASH - 2}); const hit = g.forceHit('beam');
        const flash = g.step(2); g.input({{ left: false, fire: false }});
        const after = g.step({TRANS - FLASH});
        return {{ before, start, mid, hit, flash, after, ev }};""")
    b, s, m, f, a = out["before"], out["start"], out["mid"], out["flash"], out["after"]
    assert (b["map"], b["transition"], b["level"]) == (MAP_NAMES[1], False, 1)
    assert s["transition"] is True and s["level"] == 2 and s["levelUps"] == [LEVEL2], "the level number still changes on time"
    assert out["ev"] == [["level", 2]]
    assert m["transition"] and m["map"] == MAP_NAMES[1] and m["shots"] == 0, "no firing inside the wormhole"
    assert m["enemies"] + m["asteroids"] <= 2, "the wormhole swallows what is left of the level"
    assert out["hit"] is False and m["health"] == HEALTH, "nothing can hurt the ship in transit"
    assert f["map"] == MAP_NAMES[2] and f["enemies"] == f["asteroids"] == 0, "the map changes at the flash"
    assert a["transition"] is False and a["map"] == MAP_NAMES[2] and a["player"]["x"] == a["world"]["w"] / 2
    assert a["state"] == "paused", "the run continues after the wormhole"


def test_each_level_and_the_boss_has_its_own_map(page) -> None:
    seen = []
    for level in (1, 2, 3):
        _fresh(page, level=level)
        seen.append(_js(page, "return g.state().map;"))
    _fresh(page, level=3, bossNow=True)
    boss = _js(page, "const a = g.step(20); const b = g.step(400); return [a.transition, a.transitionInfo && a.transitionInfo.kind, b.map, !!b.boss];")
    assert seen == [MAP_NAMES[1], MAP_NAMES[2], MAP_NAMES[3]]
    assert boss == [True, "boss", MAP_NAMES[4], True], "a short wormhole jumps into the boss arena"


def test_the_full_run_visits_every_map_in_order(page) -> None:
    _fresh(page)
    maps = _js(page, f"""const out = []; for (let t = 0; t < {BOSS_AT + 30}; t += 30) {{ const m = g.step(30).map; if (out[out.length - 1] !== m) out.push(m); }} return out;""")
    assert maps == [MAP_NAMES[1], MAP_NAMES[2], MAP_NAMES[3], MAP_NAMES[4]]
