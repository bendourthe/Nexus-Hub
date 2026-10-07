"""v4.13.10 plan revision 12 (R39 and R40): a compact start screen, hidden carriers, visible missiles,
linear difficulty within each level and stepped starts between levels, the shielded Nexus boss with
its glowing core, rising agent launches, its own background, and the black-hole finale that is
distinct from the wormhole between levels.

Like the other engine tests, every test drives the simulation through ``step(n)`` with a fixed seed
and ``SkySentinel.manual(true)``. Design and the per-level, per-time table:
docs/releases/v4/v4.13/development/v4.13.10-game-design.md, "Revision 12".
Skipped without Playwright or Chromium; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

FIT_VIEWPORTS = [(1280, 900), (1440, 900), (1920, 1080), (1366, 768), (1280, 720), (390, 844)]
UPGRADES = 12   # R43 (T126): the Revive and the Atomic blast joined the key
HAZARDS = 4
INTRO = 270
WORMHOLE_ONLY = {"wormhole-disc", "wormhole-arms", "star-streaks"}
FINALE_ONLY = {"rift", "light-bleed", "event-horizon", "accretion-disk", "photon-ring", "lensing", "infall-debris", "stretched-ship", "new-universe"}


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
    pg.locator(".ss-host[data-ss-id=fixed] .ss-stage").scroll_into_view_if_needed()
    return ctx, pg, errors


@pytest.fixture(scope="module")
def page(browser):
    ctx, pg, errors = _open(browser)
    yield pg
    assert not errors, errors
    ctx.close()


@pytest.fixture(scope="module", params=["webgl", "2d"])
def any_page(browser, request):
    ctx, pg, errors = _open(browser, renderer=None if request.param == "webgl" else "2d")
    assert pg.evaluate("SkySentinel.get('fixed').state().renderer") == request.param
    yield pg
    assert not errors, errors
    ctx.close()


def _js(page, body: str):
    return page.evaluate(f"(() => {{ const g = SkySentinel.get('fixed'); {body} }})()")


def _boss_up(page, threats: bool = False, ship: str = "vanguard", immune: bool = True) -> dict:
    """Level 3 with the boss arrived and its entrance finished."""
    return _js(page, f"""g.configure({{ defects: {{}}, seed: 7, threats: {str(threats).lower()}, level: 3, progression: true, boss: true, bossNow: true, immune: {str(immune).lower()} }});
        g.chooseShip('{ship}'); g.start(); g.pause('t');
        let s = g.state(), n = 0; while (!(s.boss && s.boss.entered) && n++ < 3000) s = g.step(1); return s;""")


def _done(page) -> None:
    _js(page, "g.input({ fire: false, left: false, right: false, up: false, down: false }); g.configure({ immune: false }); g.chooseShip('vanguard'); return 0;")


# ---------------------------------------------------------------- R39 (T118): the compact start screen

STRIP_PROBE = """(id) => {
  const host = document.querySelector('.ss-host[data-ss-id=' + id + ']');
  const ov = host.querySelector('.ss-overlay'), box = ov.getBoundingClientRect();
  const shown = (e) => !!e && e.getClientRects().length > 0;
  const inside = (e) => { const r = e.getBoundingClientRect(); return r.left >= box.left - 0.5 && r.right <= box.right + 0.5 && r.top >= box.top - 0.5 && r.bottom <= box.bottom + 0.5; };
  const items = [...host.querySelectorAll('.ss-strip-item')].filter(shown);
  const tops = [...new Set(items.map(e => Math.round(e.getBoundingClientRect().top)))];
  return { panel: ov.getAttribute('data-panel'), items: items.map(e => [e.dataset.kind, e.getAttribute('title'), e.getAttribute('aria-label')]),
           inside: items.every(inside), rows: tops.length, sh: ov.scrollHeight, ch: ov.clientHeight,
           fullKey: [...host.querySelectorAll('.ss-key-item, .ss-down-item')].filter(shown).length,
           ships: [...host.querySelectorAll('.ss-ship')].filter(shown).length, toggle: shown(host.querySelector('.ss-keybtn')),
           toggleText: host.querySelector('.ss-keybtn').innerText, start: shown(host.querySelector('.ss-start')) };
}"""


@pytest.mark.parametrize("viewport", FIT_VIEWPORTS, ids=lambda v: f"{v[0]}x{v[1]}")
def test_the_start_screen_shows_a_compact_pickup_strip_that_fits(browser, viewport: tuple[int, int]) -> None:
    """The ships panel shows five ships and one strip of pickup icons; the full key waits behind Pickups."""
    ctx, pg, errors = _open(browser, *viewport)
    try:
        pg.wait_for_timeout(150)
        ships = pg.evaluate(STRIP_PROBE, "fixed")
        assert ships["panel"] == "ships" and ships["ships"] == 5 and ships["start"] and ships["toggle"], ships
        assert ships["fullKey"] == 0, "no name-and-effect key on the ships panel"
        assert len(ships["items"]) == UPGRADES + HAZARDS and ships["inside"], ships
        assert all(t and a for _, t, a in ships["items"]), "each icon names itself on hover and to a screen reader"
        assert ships["rows"] <= (2 if viewport[0] < 600 else 1), f"one row of icons: {ships}"
        assert ships["sh"] <= ships["ch"], f"no scroll bar: {ships}"
        pg.locator(".ss-host[data-ss-id=fixed] .ss-keybtn").click()
        key = pg.evaluate(STRIP_PROBE, "fixed")
        assert key["panel"] == "key" and key["fullKey"] == UPGRADES + HAZARDS and key["ships"] == 0 and key["toggleText"] == "Back to ships", key
        assert key["sh"] <= key["ch"], f"the key panel fits too: {key}"
    finally:
        assert not errors, errors
        ctx.close()


# ---------------------------------------------------------------- R39 (T118): hidden carriers

PIXELS = """() => { SkySentinel.get('fixed').render(); const host = document.querySelector('.ss-host[data-ss-id=fixed]');
  const c = host.querySelector('.ss-canvas'), hud = host.querySelector('.ss-hudcanvas'); let sum = 0, hash = 0;
  const add = (data) => { for (let i = 0; i < data.length; i += 7) { sum += data[i]; hash = (hash * 31 + data[i]) >>> 0; } };
  const gl = c.getContext('webgl');
  if (gl) { const px = new Uint8Array(4 * c.width * c.height); gl.readPixels(0, 0, c.width, c.height, gl.RGBA, gl.UNSIGNED_BYTE, px); add(px); }
  else add(c.getContext('2d').getImageData(0, 0, c.width, c.height).data);
  if (hud) add(hud.getContext('2d').getImageData(0, 0, hud.width, hud.height).data);
  return [sum, hash]; }"""


@pytest.mark.parametrize("carry", ["shield", "freeze"])
def test_a_carrier_is_drawn_exactly_like_any_other_enemy_and_rock(any_page, carry: str) -> None:
    """The same scene with and without a carrier renders the same pixels in both renderers."""
    frames = []
    for c in (None, carry):
        arg = "null" if c is None else f"'{c}'"
        _js(any_page, f"""g.configure({{ defects: {{}}, seed: 7, threats: false, level: 2, progression: true }}); g.start(); g.pause('t'); g.step(5);
            const p = g.state().player; g.spawn('gunship', p.x - 120, p.y - 260, {arg}); g.spawnAsteroid('medium', p.x + 120, p.y - 260, 0, 0, {arg});
            g.render(); return 0;""")
        frames.append([any_page.evaluate(PIXELS), _js(any_page, "return g.frameTags();"), _js(any_page, "return [g.state().carriers.length + g.state().hazards.length, g.lifeBars().length];")])
    plain, marked = frames
    assert marked[2][0] == 2 and plain[2][0] == 0, "the second scene really has two carriers"
    assert marked[0] == plain[0], f"a {carry} carrier changes no pixel: {plain[0]} vs {marked[0]}"
    assert marked[1] == plain[1], "and no extra element is drawn for it"


def test_a_dropped_pickup_keeps_its_upgrade_or_hazard_look(page) -> None:
    out = _js(page, """g.configure({ defects: {}, seed: 7, threats: false, level: 1, progression: true }); g.start(); g.pause('t'); g.step(5);
        g.dropPowerUp('rapid'); g.dropPowerUp('slowfire'); return [g.upgrades().find(u => u.kind === 'rapid').color, g.downgrades().find(d => d.kind === 'slowfire').color, g.state().powerUpKinds];""")
    assert out[2] == ["rapid", "slowfire"] and out[0] != out[1]


# ---------------------------------------------------------------- R39 (T122): visible missiles

def test_missiles_are_drawn_large_with_a_bright_head_and_a_trail(any_page) -> None:
    out = _js(any_page, """g.configure({ defects: {}, seed: 7, threats: false, level: 1, progression: true }); g.start(); g.pause('t'); g.step(5);
        g.dropPowerUp('missiles'); g.step(2); g.input({ fire: true }); const s = g.step(60); g.input({ fire: false }); g.render();
        return { marks: g.missileMarks(), tags: g.frameTags(), dmg: s.playerShots.filter(x => x.kind === 'missile').map(x => x.dmg) };""")
    marks = out["marks"]
    assert marks and "missile" in out["tags"], out
    assert all(m["len"] >= 20 and m["wid"] >= 6 and m["head"] >= 10 for m in marks), f"a body at least 20 long and a bright head: {marks}"
    assert max(m["trail"] for m in marks) >= 10, f"a smoke trail along the homing path: {marks}"
    assert set(out["dmg"]) == {2}, "the damage is unchanged"


# ---------------------------------------------------------------- R39 (T119): difficulty curves

def test_spawn_rate_and_speed_rise_linearly_within_each_level(page) -> None:
    out = _js(page, """const out = [];
        for (const level of [1, 2, 3]) {
          g.configure({ defects: {}, seed: 7, threats: false, level, progression: true, boss: true }); g.start(); g.pause('t');
          const len = level === 1 ? 5400 : level === 2 ? 6600 : 3600, pts = [];
          for (let q = 0; q <= 4; q++) { const s = g.state(); pts.push([s.levelProgress, s.spawnRate, s.enemySpeed, s.rockRate]); if (q < 4) g.step(len / 4 - (q === 3 ? 2 : 0)); }
          out.push(pts);
        }
        return { out, table: g.difficulty() };""")
    for level, pts in enumerate(out["out"], start=1):
        d = out["table"][level - 1]
        for k, rate, speed, rocks in pts:
            assert rate == pytest.approx(d["rate"][0] + (d["rate"][1] - d["rate"][0]) * k, abs=0.002), (level, pts)
            assert speed == pytest.approx(d["speed"][0] + (d["speed"][1] - d["speed"][0]) * k, abs=0.002), (level, pts)
            assert rocks == pytest.approx(d["rocks"][0] + (d["rocks"][1] - d["rocks"][0]) * k, abs=0.002), (level, pts)
        steps = [b[1] - a[1] for a, b in zip(pts, pts[1:])]
        assert all(s > 0 for s in steps) and max(steps) - min(steps) < 0.01, f"level {level}: equal steps, a straight line {steps}"


def test_more_enemies_arrive_late_in_a_level_than_early(page) -> None:
    counts = _js(page, """const out = [];
        for (const level of [1, 2]) {
          let first = 0, last = 0, skips = 0;
          for (let seed = 1; seed <= 6; seed++) {
            g.configure({ defects: {}, seed, threats: true, level, progression: true, boss: false, immune: true }); g.start(); g.pause('t'); g.input({ fire: true });
            const len = level === 1 ? 5400 : 6600, w = Math.round(len * 0.2);
            let s = g.step(w); first += s.spawned; s = g.step(len - 2 * w - 5); const mid = s.spawned; s = g.step(w); last += s.spawned - mid; skips += s.capSkips;
          }
          out.push([first, last, skips]);
        }
        g.input({ fire: false }); g.configure({ immune: false }); return out;""")
    # the rate's average over the last fifth is 1.37 to 1.5 times its average over the first fifth
    for first, last, skips in counts:
        assert last > first * 1.2, f"the last fifth of a level sends more enemies than the first: {counts}"
        assert skips <= 2, f"the enemy cap never flattens the curve: {counts}"


def test_each_level_starts_above_the_last_and_grows_its_enemies_shields_and_rocks(page) -> None:
    out = _js(page, """const out = [];
        for (const level of [1, 2, 3]) {
          g.configure({ defects: {}, seed: 7, threats: false, level, progression: true, boss: false }); g.start(); g.pause('t'); g.step(5);
          const s = g.state(); const p = s.player;
          g.spawn('bomber', p.x - 150, p.y - 300); g.spawn('gunship', p.x + 150, p.y - 300, null, { shield: true });
          g.spawnAsteroid('large', p.x, p.y - 420, 0, 0); g.render();
          out.push({ start: [s.spawnRate, s.enemySpeed, s.rockRate], foes: g.state().foes, bars: g.lifeBars(), rock: g.state().rocks[0], classes: g.enemyClasses() });
        }
        return { out, table: g.difficulty() };""")
    lv, table = out["out"], out["table"]
    for a, b, ta in zip(lv, lv[1:], table):
        assert b["start"][0] > a["start"][0] and b["start"][1] > a["start"][1] and b["start"][2] > a["start"][2], "every start is above the last level's"
        assert b["start"][1] >= ta["speed"][1], "a level starts at or above the last level's top speed"
        assert b["start"][0] >= ta["rate"][1] * 0.85, "and near the last level's end spawn rate"
        assert b["foes"][0]["hpMax"] > a["foes"][0]["hpMax"], "the same class has more health"
        assert b["bars"][0]["w"] > a["bars"][0]["w"] * 1.1, "and a visibly longer life bar"
        assert b["rock"]["r"] > a["rock"]["r"] * 1.1 and b["rock"]["hpMax"] > a["rock"]["hpMax"], "asteroids grow in size and health"
    assert [t["shielded"] for t in table][0] == 0 < table[1]["shielded"] < table[2]["shielded"]
    shield_bar = [b for b in lv[2]["bars"] if b["shield"] > 0][0]
    assert shield_bar["shieldH"] >= 3 and shield_bar["shieldColor"] == "#38bdf8" and shield_bar["shieldFrac"] == 1, f"a shield shows its own bar: {shield_bar}"


def test_shielded_enemies_spawn_with_the_levels_shield_strength(page) -> None:
    out = _js(page, """const out = [];
        for (const level of [2, 3]) {
          g.configure({ defects: {}, seed: 23, threats: true, level, progression: true, boss: false, immune: true }); g.start(); g.pause('t');
          const seen = new Set(); for (let i = 0; i < 60; i++) g.step(40).foes.forEach(f => { if (f.shieldMax) seen.add(f.shieldMax); });
          out.push([...seen]);
        }
        g.configure({ immune: false }); return { out, table: g.difficulty() };""")
    assert out["out"][0] == [out["table"][1]["shieldHp"]] and out["out"][1] == [out["table"][2]["shieldHp"]], out


# ---------------------------------------------------------------- R40 (T120): the shielded boss

def test_the_boss_shield_layers_fall_outermost_first_under_real_fire(page) -> None:
    s = _boss_up(page)
    assert s["boss"]["shieldsUp"] == 3 and s["boss"]["stage"] == "shields" and s["boss"]["layer"] == 0
    radii = [L["r"] for L in s["boss"]["shields"]]
    assert radii == sorted(radii, reverse=True) and len({L["color"] for L in s["boss"]["shields"]}) == 3, "three concentric layers, each its own colour"
    out = _js(page, """let s = g.state(), n = 0, layers = [];
        while (s.boss && s.boss.shieldsUp > 0 && n++ < 9000) { const dx = g.bossGeometry().centre[0] - s.player.x;
          g.input({ fire: true, left: dx < -3, right: dx > 3, up: s.player.y > s.world.h * 0.56 }); s = g.step(1);
          if (layers[layers.length - 1] !== s.boss.layer) layers.push(s.boss.layer); }
        g.input({ fire: false, left: false, right: false, up: false }); return { layers, broken: s.boss.broken.map(b => b.layer), alive: s.boss.nodesAlive, nodeHp: s.boss.nodeHp, stage: s.boss.stage };""")
    _done(page)
    assert out["layers"] == [0, 1, 2, -1] and out["broken"] == [0, 1, 2], out
    assert out["alive"] == 4 and len(set(out["nodeHp"])) == 1, "the nodes were untouched while the shields stood"
    assert out["stage"] == "nodes"


def test_node_damage_is_blocked_until_every_shield_falls(page) -> None:
    _boss_up(page)
    out = _js(page, """const geo = g.bossGeometry(), before = g.state().boss;
        const hook = g.hitBoss('node2', 10); const shot = g.shotAt(geo.nodes[2][0], geo.nodes[2][1]); const after = g.state().boss;
        g.breakShields(); const open = g.hitBoss('node2', 10); return { hook, shot, before, after, open, last: g.state().boss };""")
    _done(page)
    assert out["hook"] is False, "the test hook refuses a node while a shield stands"
    assert out["shot"] is True and out["after"]["nodeHp"] == out["before"]["nodeHp"], "a round aimed at a node is stopped by the shield"
    assert out["after"]["shields"][0]["hp"] < out["before"]["shields"][0]["hp"], "and the shield takes it"
    assert out["open"] is True and out["last"]["nodeHp"][2] < out["before"]["nodeHp"][2]


@pytest.mark.parametrize("renderer", ["webgl", "2d"])
def test_the_core_is_blocked_until_the_nodes_fall_then_glows(browser, renderer: str) -> None:
    ctx, pg, errors = _open(browser, renderer=None if renderer == "webgl" else "2d")
    try:
        _boss_up(pg)
        out = _js(pg, """g.breakShields(); const geo = g.bossGeometry(); const c0 = g.state().boss.coreHp;
            const hook = g.hitBoss('core', 10); const d0 = g.state().boss.deflects; const shot = g.shotAt(geo.centre[0], geo.centre[1]);
            const mid = g.state().boss; g.render(); const midTags = g.frameTags();
            for (let i = 0; i < 4; i++) g.hitBoss('node' + i, 9999); g.step(1); g.render();
            const glow = g.state().boss; const tags = g.frameTags(); const open = g.hitBoss('core', 10);
            return { c0, hook, d0, shot, mid, midTags, glow, tags, open, after: g.state().boss.coreHp };""")
        assert out["hook"] is False and out["shot"] is True and out["mid"]["coreHp"] == out["c0"], "the core takes nothing while a node lives"
        assert out["mid"]["deflects"] == out["d0"] + 1, "the round glances off visibly"
        assert out["mid"]["coreGlow"] is False and "core-glow" not in out["midTags"]
        assert out["glow"]["stage"] == "core" and out["glow"]["coreGlow"] is True and "core-glow" in out["tags"], "only the core is left: it glows"
        assert out["open"] is True and out["after"] < out["c0"]
    finally:
        assert not errors, errors
        ctx.close()


def test_agent_launches_speed_up_as_the_fight_goes_on(page) -> None:
    _boss_up(page, threats=True)
    out = _js(page, """let s = g.state(); for (let i = 0; i < 4200 && s.boss; i += 20) { g.dropPowerUp('repair'); s = g.step(20); }
        return { launches: s.boss.launches, every: s.boss.agentEvery, cap: s.boss.agentCap, plan: g.bossPlan() };""")
    _done(page)
    gaps = [b - a for a, b in zip(out["launches"], out["launches"][1:])]
    assert len(gaps) >= 8, out
    assert gaps[-1] < gaps[0] * 0.6 and all(b <= a for a, b in zip(gaps, gaps[1:])), f"launch gaps shrink: {gaps}"
    assert out["every"] == out["plan"]["agentEvery"][1] and out["cap"] == out["plan"]["agentCap"][1], "full rate and cap after the ramp"


def test_the_boss_level_has_its_own_background(browser) -> None:
    ctx, pg, errors = _open(browser)
    try:
        out = pg.evaluate("""() => { const g = SkySentinel.get('fixed'); const out = [];
            const read = () => { g.render(); const c = document.querySelector('.ss-host[data-ss-id=fixed] .ss-canvas'), gl = c.getContext('webgl');
              const w = Math.floor(c.width * 0.3), h = Math.floor(c.height * 0.25), px = new Uint8Array(4 * w * h);
              gl.readPixels(Math.floor(c.width * 0.02), Math.floor(c.height * 0.3), w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
              const m = [0, 0, 0]; for (let i = 0; i < px.length; i += 4) { m[0] += px[i]; m[1] += px[i + 1]; m[2] += px[i + 2]; } return m.map(v => v / (px.length / 4)); };
            for (const level of [1, 2, 3]) { g.configure({ defects: {}, seed: 7, threats: false, level, progression: true, boss: false }); g.start(); g.pause('t'); g.step(30);
              out.push({ map: g.state().map, mapId: g.state().mapId, rgb: read() }); }
            g.configure({ defects: {}, seed: 7, threats: false, level: 3, progression: true, boss: true, bossNow: true }); g.start(); g.pause('t');
            let s = g.state(); while (!(s.boss && s.boss.entered)) s = g.step(5);
            out.push({ map: s.map, mapId: s.mapId, rgb: read() });
            return out; }""")
        names = [o["map"] for o in out]
        assert names[-1] == "The Nexus Storm" and len(set(names)) == 4, names
        storm = out[-1]["rgb"]
        for other in out[:-1]:
            dist = sum((a - b) ** 2 for a, b in zip(storm, other["rgb"])) ** 0.5
            assert dist > 6, f"the storm reads differently from {other['map']}: {storm} vs {other['rgb']}"
        assert storm[1] > storm[2], f"the storm is green-gold, not the old teal station: {storm}"
    finally:
        assert not errors, errors
        ctx.close()


# ---------------------------------------------------------------- R40 (T121): the black-hole finale

def _finale_frames(page, every: int = 10) -> list[dict]:
    _boss_up(page, immune=False)
    return _js(page, f"""g.defeatBoss(); const out = []; let s = g.state();
        while (!s.finale.done) {{ s = g.step({every}); g.render(); out.push({{ t: s.finale.t, phase: s.finale.phase, tags: g.frameTags(), hole: s.finale.hole, rift: s.finale.rift, ship: s.finale.ship, map: s.map, prize: s.hud.prize }}); }}
        return out;""")


@pytest.mark.parametrize("renderer", ["webgl", "2d"])
def test_the_finale_plays_explosion_tear_black_hole_swallow_universe_and_prize_in_order(browser, renderer: str) -> None:
    ctx, pg, errors = _open(browser, renderer=None if renderer == "webgl" else "2d")
    try:
        seen = []
        _js(pg, "window.__rw = []; SkySentinel.get('fixed').on('rewardUnlocked', e => window.__rw.push(e.tick)); return 0;")
        frames = _finale_frames(pg)
        for f in frames:
            if not seen or seen[-1] != f["phase"]:
                seen.append(f["phase"])
        assert seen == ["explode", "tear", "collapse", "swallow", "universe", "prize"], seen
        by = {ph: [f for f in frames if f["phase"] == ph] for ph in seen}
        assert any("chain-blast" in f["tags"] for f in by["explode"])
        assert any({"rift", "light-bleed"} <= set(f["tags"]) for f in by["tear"]), "the rift tears open and bleeds light"
        assert any(f["rift"]["open"] > 0 and f["hole"] > 0 for f in by["collapse"]), "the rift collapses into the hole"
        assert all({"event-horizon", "accretion-disk", "photon-ring", "lensing"} <= set(f["tags"]) for f in by["swallow"])
        stretch = [f["ship"]["k"] for f in by["swallow"]]
        assert stretch == sorted(stretch) and stretch[-1] > 2.5 and any("stretched-ship" in f["tags"] for f in by["swallow"]), "the ship stretches as it is drawn in"
        assert all(f["map"] == "A New Universe" and "new-universe" in f["tags"] for f in by["universe"] + by["prize"])
        assert max(f["prize"]["alpha"] for f in by["prize"] if f["prize"]) == 1
        assert pg.evaluate("window.__rw").__len__() == 1, "the reward hand-off fires once, at the end"
        assert 10 <= frames[-1]["t"] / 60 <= 14, "10 to 14 s"
    finally:
        assert not errors, errors
        ctx.close()


@pytest.mark.parametrize("renderer", ["webgl", "2d"])
def test_the_finale_shares_no_element_with_the_wormhole_between_levels(browser, renderer: str) -> None:
    ctx, pg, errors = _open(browser, renderer=None if renderer == "webgl" else "2d")
    try:
        worm = pg.evaluate("""() => { const g = SkySentinel.get('fixed'); const tags = new Set();
            g.configure({ defects: {}, seed: 7, threats: false, level: 1, progression: true, boss: false }); g.start(); g.pause('t'); g.step(5399);
            for (let i = 0; i < 21; i++) { g.step(10); g.render(); g.frameTags().forEach(t => tags.add(t)); } return [...tags]; }""")
        fin = set()
        for f in _finale_frames(pg):
            fin.update(f["tags"])
        assert WORMHOLE_ONLY <= set(worm), worm
        assert FINALE_ONLY <= fin, fin
        assert not (fin & WORMHOLE_ONLY) and not (set(worm) & FINALE_ONLY), f"no shared element: {set(worm) & fin}"
    finally:
        assert not errors, errors
        ctx.close()


CENTRE = """([x, y]) => { const g = SkySentinel.get('fixed'); g.render(); const c = document.querySelector('.ss-host[data-ss-id=fixed] .ss-canvas'), gl = c.getContext('webgl');
  const s = g.state(), k = c.width / s.world.w, px = new Uint8Array(4 * 9 * 9), cx = Math.round(x * k), cy = Math.round(c.height - y * k);
  gl.readPixels(cx - 4, cy - 4, 9, 9, gl.RGBA, gl.UNSIGNED_BYTE, px); const m = [0, 0, 0];
  for (let i = 0; i < px.length; i += 4) { m[0] += px[i]; m[1] += px[i + 1]; m[2] += px[i + 2]; } return m.map(v => v / 81); }"""


def test_a_wormhole_frame_and_a_black_hole_frame_look_different(page) -> None:
    """The wormhole's heart is a bright cyan and violet swirl; the black hole's is a dark horizon ringed with a warm disk."""
    _js(page, "g.configure({ defects: {}, seed: 7, threats: false, level: 1, progression: true, boss: false }); g.start(); g.pause('t'); g.step(5400 + 100); return 0;")
    hole = _js(page, "const t = g.state().transitionInfo; return [g.state().world.w / 2, g.state().world.h * 0.3, t && t.kind];")
    assert hole[2] == "level"
    worm = page.evaluate(CENTRE, hole[:2])
    _boss_up(page, immune=False)
    hp = _js(page, "g.defeatBoss(); const s = g.step(470); const f = s.finale; return [f.phase, f.hole];")
    assert hp[0] == "swallow" and hp[1] >= 1
    spot = _js(page, "return g.holeAt();")
    assert spot and spot["R"] > 10, "the engine reports where the hole is"
    dark = page.evaluate(CENTRE, [spot["x"], spot["y"]])
    disk = page.evaluate(CENTRE, [spot["x"] - spot["R"] * 2.4, spot["y"]])
    assert sum(worm) / 3 > 120 and worm[2] >= worm[0], f"the wormhole's heart is bright and cool: {worm}"
    assert sum(dark) / 3 < 25, f"the black hole's heart is dark: {dark}"
    assert disk[0] > disk[2] and sum(disk) / 3 > 60, f"its disk is warm and bright: {disk}"


def test_skipping_from_the_rift_lands_on_the_prize_card_and_a_second_skip_ends_it(page) -> None:
    _boss_up(page, immune=False)
    out = _js(page, """g.defeatBoss(); g.step(230); const tear = g.state().finale.phase; g.skipFinale(); g.render(); const a = g.state();
        g.skipFinale(); const b = g.state(); return { tear, a, b };""")
    assert out["tear"] == "tear"
    assert out["a"]["finale"]["phase"] == "prize" and out["a"]["hud"]["prize"]["alpha"] == 1 and out["a"]["map"] == "A New Universe"
    assert out["b"]["finale"]["done"]


def test_reduced_motion_shows_the_black_hole_as_a_still_frame(browser) -> None:
    ctx, pg, errors = _open(browser, 1440, 900, motion="reduce")
    try:
        _boss_up(pg, immune=False)
        out = _js(pg, """g.defeatBoss(); const seen = []; let s = g.state();
            while (!s.finale.done) { s = g.step(1); g.render(); const last = seen[seen.length - 1];
              if (!last || last.phase !== s.finale.phase) seen.push({ phase: s.finale.phase, tags: g.frameTags(), t: s.finale.t }); }
            return seen;""")
        assert [x["phase"] for x in out] == ["explode", "swallow", "universe", "prize"]
        hole = [x for x in out if x["phase"] == "swallow"][0]
        assert {"event-horizon", "accretion-disk"} <= set(hole["tags"]) and "rift" not in hole["tags"], hole
    finally:
        assert not errors, errors
        ctx.close()
