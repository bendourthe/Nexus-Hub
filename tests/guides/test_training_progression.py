"""v4.13.10 Phase 6: levels, ship forms, power-ups, and the Nexus megaship boss.

Like the Phase 3 engine tests, every test drives the simulation through ``step(n)`` with a
fixed seed and ``SkySentinel.manual(true)``; nothing waits on real time. Progression and
the boss are switched on per game: the buggy game has neither, the partly fixed game has
progression, and the fixed game has both. Skipped without Playwright or Chromium;
fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

LEVEL2, LEVEL3, BOSS_AT = 5400, 12000, 15600


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
    flags = page.evaluate("['buggy', 'partial', 'fixed'].map(id => { const s = SkySentinel.get(id).state(); return [s.progression, s.bossEnabled]; })")
    assert flags == [[False, False], [True, False], [True, True]]


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


def test_the_partly_fixed_game_levels_up_but_never_shows_the_boss(page) -> None:
    _fresh(page, game="partial")
    s = _js(page, "return g.step(20000);", game="partial")
    assert s["level"] == 3 and s["boss"] is None and s["bossDue"] is None


def test_the_buggy_game_has_no_progression_or_power_ups(page) -> None:
    _fresh(page, game="buggy", threats=True, defects={})
    s = _js(page, "g.input({ fire: true }); const s = g.step(6000); g.input({ fire: false }); return s;", game="buggy")
    assert s["level"] == 1 and s["form"] == "Scout" and s["levelUps"] == []
    assert s["powerUps"] == 0 and s["collected"] == [], "power-ups never appear in the buggy game"
    assert set(s["enemyTypes"]) <= {"drone", "weaver"}


def test_enemy_variety_grows_with_the_level(page) -> None:
    _fresh(page, threats=True, level=3)
    s = _js(page, "g.input({ fire: false }); return g.step(900);")
    assert "lancer" in s["enemyTypes"] or s["enemies"] == 0
    seen = _js(page, "const t = new Set(); for (let i = 0; i < 40; i++) g.step(60).enemyTypes.forEach(x => t.add(x)); return [...t].sort();")
    assert {"drone", "weaver", "lancer"} <= set(seen)


def test_shield_absorbs_one_hit(page) -> None:
    _fresh(page)
    out = _js(page, """g.step(5); g.dropPowerUp('shield'); const a = g.step(2);
        const hit = g.forceHit('shot'); const b = g.state(); g.step(61); g.forceHit('shot'); return { a, hit, b, c: g.state() };""")
    assert out["a"]["player"]["shield"] == 1 and out["a"]["collected"][0]["kind"] == "shield"
    assert out["hit"] is True and out["b"]["lives"] == 3 and out["b"]["player"]["shield"] == 0, "the shield takes the hit, not a life"
    assert out["c"]["lives"] == 2, "the next hit costs a life"


def test_weapon_gives_twin_shots_then_expires(page) -> None:
    _fresh(page)
    out = _js(page, """g.step(5); g.dropPowerUp('weapon'); g.step(2);
        g.input({ fire: true }); const twin = g.step(1).shots; g.input({ fire: false });
        g.step(620); g.input({ fire: true }); const single = g.step(10).shots; g.input({ fire: false });
        return { twin, single, weapon: g.state().player.weapon };""")
    assert out["twin"] == 2
    assert out["weapon"] == 0 and out["single"] == 1, "twin shot ends after 10 seconds"


def test_extra_ships_are_capped(page) -> None:
    _fresh(page)
    lives = _js(page, "g.step(5); for (let i = 0; i < 4; i++) { g.dropPowerUp('ship'); g.step(2); } return g.state().lives;")
    assert lives == 5


def test_two_power_ups_in_one_tick_both_apply(page) -> None:
    _fresh(page)
    s = _js(page, "g.step(5); g.dropPowerUp('shield'); g.dropPowerUp('weapon'); return g.step(2);")
    assert sorted(c["kind"] for c in s["collected"]) == ["shield", "weapon"]
    assert len({c["tick"] for c in s["collected"]}) == 1
    assert s["player"]["shield"] == 1 and s["player"]["weapon"] > 0


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
  const danger = (v, x) => {
    let d = 0;
    for (const t of v.threats) {
      const dy = v.player.y - t.y;
      if (dy < -30 || dy > 260 || t.vy <= 0) continue;
      const at = t.x + t.vx * (dy / t.vy);
      const gap = Math.abs(at - x) - t.r - v.player.r;
      if (gap < 30) d += (30 - gap) * (300 - dy);
    }
    if (x < 30 || x > v.world.w - 30) d += 1e6;
    return d;
  };
  let s = g.state();
  while (s.state !== 'over' && !s.boss && s.tick < 17000) {
    const v = g.view();
    const here = danger(v, v.player.x), left = danger(v, v.player.x - 42), right = danger(v, v.player.x + 42);
    let move = here > 0 ? (left < right ? -1 : 1) : 0;
    if (here > 0 && Math.min(left, right) >= here) move = 0;
    g.input({ fire: true, left: move < 0, right: move > 0 });
    s = g.step(3);
  }
  g.input({ fire: false, left: false, right: false });
  return { tick: s.tick, boss: !!s.boss, lives: s.lives };
}
"""


@pytest.mark.parametrize("seed", [1, 7])
def test_a_dodging_player_reaches_the_boss_in_four_to_five_minutes(page, seed: int) -> None:
    """A simple bot that dodges and keeps firing reaches the boss; the run still costs lives on the way."""
    run = page.evaluate(DODGING_BOT, seed)
    assert run["boss"], f"seed {seed}: the bot died at tick {run['tick']}"
    assert 240 <= run["tick"] / 60 <= 300
    assert run["lives"] < 5, "the run costs something on the way"


def test_progression_keeps_the_defect_schedule_untouched(page) -> None:
    quiet = _js(page, "g.configure({ defects: { randomExplosion: true }, seed: 777, threats: false, progression: false }); g.start(); g.pause('t'); return g.step(1100).nextExplosion;")
    busy = _js(page, "g.configure({ defects: { randomExplosion: true }, seed: 777, threats: true, progression: true }); g.start(); g.pause('t'); g.input({ fire: true }); const n = g.step(1100).nextExplosion; g.input({ fire: false }); return n;")
    assert quiet == busy == page.evaluate("SkySentinel.defectSchedule(777, 5000)[0]")
    _js(page, "g.configure({ progression: true, boss: true });")
