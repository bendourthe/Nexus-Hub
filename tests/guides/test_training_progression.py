"""v4.13.10 Phase 6: levels, ship forms, power-ups, and the Nexus megaship boss.

Like the Phase 3 engine tests, every test drives the simulation through ``step(n)`` with a
fixed seed and ``SkySentinel.manual(true)``; nothing waits on real time. Progression and
the boss are switched on per game: the buggy game has neither, the partly fixed game has
progression, and the fixed game has both. Phase R10 gave each level a named difficulty
(Easy, Medium, Hard) that is measurably harder than the last. Skipped without Playwright or
Chromium; fail-closed under NEXUS_REQUIRE_RENDER=1.
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
        for (let i = 0; i < 40 && g.state().state !== 'over'; i++) g.step(60).enemyTypes.forEach(x => t.add(x));
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
    assert out["twin"] == 2
    assert out["weapon"] == 0 and out["single"] == 1, "twin shot ends after 10 seconds"


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
    assert shots == 1, "the Fighter fires a single shot once twin shot has expired"


def test_the_sentinel_fires_twin_by_default_and_spread_with_the_weapon(page) -> None:
    _fresh(page, level=3)
    base = _js(page, "g.input({ fire: true }); const n = g.step(1).shots; g.input({ fire: false }); return n;")
    assert base == 2
    spread = _js(page, "g.step(20); g.dropPowerUp('weapon'); g.step(2); g.input({ fire: true }); const n = g.step(1).shots; g.input({ fire: false }); return n;")
    assert spread >= 3


def test_boss_nodes_fall_before_the_core_and_its_plates_block_shots(page) -> None:
    _fresh(page, level=3, bossNow=True)
    s = _js(page, "return g.step(600);")
    assert s["boss"]["entered"] and s["boss"]["nodesAlive"] == 4
    geo = _js(page, "return g.bossGeometry();")
    plate = geo["plates"][0]
    cx = sum(p[0] for p in plate) / 3
    cy = sum(p[1] for p in plate) / 3
    assert page.evaluate(f"SkySentinel.get('fixed').shotAt({cx}, {cy})") is True, "a side plate absorbs a shot"
    assert _js(page, "return g.hitBoss('core', 5);") is False, "the core is shielded while any node lives"
    for i in range(4):
        assert _js(page, f"return g.hitBoss('node{i}', 8);") is True
    s = _js(page, "return g.state();")
    assert s["boss"]["nodesAlive"] == 0
    events = _js(page, "const seen = []; g.on('bossDefeated', e => seen.push(e)); g.hitBoss('core', 24); return seen.length;")
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
  // R10: bombs threaten an area, so the bot may also climb or drop out of a blast zone.
  const danger = (v, x, y) => {
    let d = 0;
    for (const t of v.threats) {
      if (t.r > 60) { const gap = Math.hypot(t.x - x, t.y - y) - t.r - v.player.r; if (gap < 30) d += (30 - gap) * 400; continue; }
      const dy = y - t.y;
      if (dy < -30 || dy > 260 || t.vy <= 0) continue;
      const at = t.x + t.vx * (dy / t.vy);
      const gap = Math.abs(at - x) - t.r - v.player.r;
      if (gap < 30) d += (30 - gap) * (300 - dy);
    }
    if (x < 30 || x > v.world.w - 30 || y < v.world.h * 0.55 || y > v.world.h - 24) d += 1e6;
    return d;
  };
  let s = g.state();
  while (s.state !== 'over' && !s.boss && s.tick < 17000) {
    const v = g.view();
    const x = v.player.x, y = v.player.y;
    const opts = [[0, 0, danger(v, x, y)], [-1, 0, danger(v, x - 42, y)], [1, 0, danger(v, x + 42, y)], [0, -1, danger(v, x, y - 36)], [0, 1, danger(v, x, y + 36)]];
    let best = opts[0];
    if (best[2] > 0) for (const o of opts) if (o[2] < best[2]) best = o;
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
