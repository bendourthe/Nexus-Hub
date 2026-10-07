"""v4.13.10 plan revision 14 (R43): reachable boss nodes, correct singular and plural boss text, and
two rare pickups, the instant Revive and the Atomic blast.

Like the other engine tests, every test drives the simulation through ``step(n)`` with a fixed seed
and ``SkySentinel.manual(true)``; no test waits a fixed real time for a frame-counted sequence.
Design: docs/releases/v4/v4.13/development/v4.13.10-game-design.md, "Revision 14".
Skipped without Playwright or Chromium; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
import game_balance  # noqa: E402

HOST = ".ss-host[data-ss-id=fixed]"
REVIVE_INVULN = 120


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
    pg.locator(HOST + " .ss-stage").scroll_into_view_if_needed()
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


def _js(page, body: str, game: str = "fixed"):
    return page.evaluate(f"(() => {{ const g = SkySentinel.get('{game}'); {body} }})()")


def _fresh(page, game: str = "fixed", **cfg) -> None:
    page.evaluate(
        """([game, cfg]) => { const g = SkySentinel.get(game);
            g.configure(Object.assign({ defects: {}, seed: 31, threats: false, level: 1, progression: true, boss: true, immune: false }, cfg));
            g.chooseShip('vanguard'); g.start(); g.pause('test'); }""",
        [game, cfg],
    )


BOSS = """g.configure({ defects: {}, seed: 7, threats: false, level: 3, progression: true, boss: true, bossNow: true, immune: true });
    g.chooseShip('vanguard'); g.start(); g.pause('t'); let s = g.state(); while (!(s.boss && s.boss.entered)) s = g.step(1);"""
DONE = "g.input({ fire: false, left: false, right: false, up: false }); g.configure({ immune: false, level: 1, bossNow: false }); return 0;"
LIVE = f"document.querySelector('{HOST} .ss-live').textContent"


# ---------------------------------------------------------------- T125: every node is fairly reachable

@pytest.mark.parametrize("kill", [(), (2, 3), (0, 2, 3), (1, 2, 3)], ids=["all-four", "upper-two", "last-right", "last-left"])
def test_every_live_node_is_reachable_for_a_fair_share_of_the_node_stage(page, kill: tuple[int, ...]) -> None:
    """The maintainer could barely hit the last top nodes; the turning frame brings each one low."""
    out = game_balance.node_reach(page, kill)
    shares = [v for v in out["share"] if v is not None]
    assert len(shares) == 4 - len(kill)
    assert min(shares) >= game_balance.NODE_REACH_MIN, f"a node is out of reach too long: {out}"
    assert out["turns"] >= 6, f"the frame keeps turning through the minute: {out}"


@pytest.mark.parametrize("size", [(1280, 900), (1440, 900), (390, 844)], ids=lambda v: f"{v[0]}x{v[1]}")
def test_no_node_ever_sits_under_the_hud_or_the_boss_bar(browser, size: tuple[int, int]) -> None:
    ctx, pg, errors = _open(browser, *size)
    try:
        out = _js(pg, BOSS + """g.breakShields(); g.render(); let worst = 1e9, under = 0, turning = 0, bar = g.state().hud.bossBar;
            for (let t = 0; t < 1400; t++) { s = g.step(1); const geo = g.bossGeometry(); if (geo.turning) turning++;
              geo.nodes.forEach(p => { const gap = p[1] - geo.nodeR - geo.band; worst = Math.min(worst, gap); if (gap < 0) under++; }); }
            g.render(); const css = g.state().canvas.cssHeight / g.state().world.h, geo = g.bossGeometry();
            return { worst, under, turning, band: geo.band, barBottom: (bar.y + bar.h + 17) / css };""")
        assert out["turning"] > 200, "the sample covers several quarter turns"
        assert out["under"] == 0 and out["worst"] >= 0, f"a node reached into the boss bar's band: {out}"
        assert out["band"] >= out["barBottom"], f"the band covers the bar and its stage line: {out}"
    finally:
        _js(pg, DONE)
        assert not errors, errors
        ctx.close()


def test_the_frame_turns_a_quarter_at_a_time_and_hurries_when_no_node_is_low(page) -> None:
    out = _js(page, BOSS + """g.breakShields(); for (let i = 0; i < 1500; i++) g.step(1); const a = g.state().boss.turns.slice();
        while (g.bossGeometry().turning) g.step(1);
        let geo = g.bossGeometry(); const low = [0, 1, 2, 3].filter(i => geo.nodes[i][1] > geo.centre[1]);
        low.forEach(i => g.hitBoss('node' + i, 1e9)); const t0 = g.state().tick;
        const before = g.state().boss.turns.length; let n = 0; while (g.state().boss.turns.length === before && n++ < 900) g.step(1);
        const wait = g.state().tick - t0; while (g.bossGeometry().turning) g.step(1); geo = g.bossGeometry();
        const alive = g.state().boss.alive, lowAfter = [0, 1, 2, 3].filter(i => alive[i] && geo.nodes[i][1] > geo.centre[1]);
        return { a, low, wait, lowAfter };""")
    _js(page, DONE)
    assert all(abs(t["to"] - t["from"]) == 1 for t in out["a"]), "each turn is one quarter"
    gaps = [b["tick"] - a["tick"] for a, b in zip(out["a"], out["a"][1:])]
    assert gaps and all(g >= 420 for g in gaps), f"it rests between turns while a node sits low: {gaps}"
    assert len(out["low"]) == 2 and out["wait"] <= 61, f"with only the top nodes left it turns again at once: {out}"
    assert len(out["lowAfter"]) == 1, f"and the turn brings a live node down: {out}"


def test_the_armour_and_the_core_still_guard_while_a_node_lives_at_any_angle(page) -> None:
    out = _js(page, BOSS + """g.breakShields(); const res = [];
        for (let k = 0; k < 3; k++) {
          while (!g.bossGeometry().turning) g.step(1); g.step(45);
          for (const phase of ['mid', 'rest']) {
            if (phase === 'rest') while (g.bossGeometry().turning) g.step(1);
            const geo = g.bossGeometry(), c0 = g.state().boss.coreHp, d0 = g.state().boss.deflects, hp0 = g.state().boss.nodeHp.slice();
            const plate = geo.plates[0], cx = (plate[0][0] + plate[1][0] + plate[2][0]) / 3, cy = (plate[0][1] + plate[1][1] + plate[2][1]) / 3;
            const core = g.shotAt(geo.centre[0], geo.centre[1]), armour = g.shotAt(cx, cy), after = g.state().boss;
            res.push({ phase, rot: geo.rot, core, armour, coreHp: [c0, after.coreHp], deflect: after.deflects - d0, nodes: JSON.stringify(hp0) === JSON.stringify(after.nodeHp) });
          }
        }
        return res;""")
    _js(page, DONE)
    for r in out:
        assert r["core"] is True and r["coreHp"][0] == r["coreHp"][1] and r["deflect"] == 1, f"the core glances shots off while a node lives: {r}"
        assert r["armour"] is True and r["nodes"], f"a side plate absorbs a round at {r['phase']}: {r}"


def test_the_frame_settles_on_a_half_turn_once_only_the_core_is_left(page) -> None:
    out = _js(page, BOSS + """g.breakShields(); while (!g.bossGeometry().turning) g.step(1); while (g.bossGeometry().turning) g.step(1);
        const q0 = g.bossGeometry().quarter; for (let i = 0; i < 4; i++) g.hitBoss('node' + i, 1e9);
        let n = 0; while (n++ < 200) g.step(1); const geo = g.bossGeometry(); const t = g.state().boss.turns.length; g.step(800);
        return { q0, q: geo.quarter, turning: geo.turning, more: g.state().boss.turns.length - t };""")
    _js(page, DONE)
    assert out["q"] % 2 == 0 and not out["turning"] and out["more"] == 0, f"it stops with its plates at the sides: {out}"


# ---------------------------------------------------------------- T125: singular and plural boss text

def test_the_boss_text_reads_singular_for_the_last_node_and_layer(page) -> None:
    out = _js(page, BOSS + f"""g.render(); const t = [[g.state().goal.text, g.state().hud.bossBar.label]];
        g.hitBoss('shield', 1e9); g.hitBoss('shield', 1e9); g.step(1); g.render(); const live1 = {LIVE};
        t.push([g.state().goal.text, g.state().hud.bossBar.label]);
        g.hitBoss('shield', 1e9); g.step(1); g.render(); t.push([g.state().goal.text, g.state().hud.bossBar.label]);
        g.hitBoss('node0', 1e9); g.step(1); g.render(); t.push([g.state().goal.text, g.state().hud.bossBar.label]); const live3 = {LIVE};
        g.hitBoss('node1', 1e9); g.hitBoss('node2', 1e9); g.step(1); g.render(); t.push([g.state().goal.text, g.state().hud.bossBar.label]); const live1n = {LIVE};
        return {{ t, live1, live3, live1n }};""")
    _js(page, DONE)
    t = out["t"]
    assert t[0][0] == "Break the 3 shield layers, then the nodes"
    assert t[0][1] == "Outer shield: 3 of 3 layers left"
    assert t[1] == ["Break the last shield layer, then the nodes", "Inner shield: the last of 3 layers"]
    assert t[2] == ["Break the 4 glowing nodes, then the core", "Shields down: break the 4 nodes"]
    assert t[3] == ["Break the 3 glowing nodes, then the core", "Shields down: break the 3 nodes"]
    assert t[4] == ["Break the last glowing node, then the core", "Shields down: break the last node"]
    assert "1 shield layer left" in out["live1"] and "layers left" not in out["live1"]
    assert "3 nodes left" in out["live3"]
    assert "break the last node" in out["live1n"] and "1 nodes" not in out["live1n"]
    for pair in t:
        for text in pair:
            assert " 1 " not in f" {text} ", f"no count of one in the boss text: {text}"


def test_the_engine_builds_no_count_of_one_with_a_plural_noun() -> None:
    """A source sweep: every boss count string goes through count() or a last-one branch."""
    src = (ROOT / "guides" / "website" / "src" / "sky-sentinel.js").read_text(encoding="utf-8")
    for bare in ['nodesAlive(S.boss) + " nodes left."', 'nodesAlive(b) + " nodes"', '(b.shields.length - left) + " shield layers left."']:
        idx = src.find(bare)
        assert idx == -1 or "> 1 ?" in src[max(0, idx - 160):idx], f"a count string without its singular: {bare}"


# ---------------------------------------------------------------- T126: the Revive

def test_a_revive_is_held_one_at_a_time_and_shows_in_the_hud(page) -> None:
    _fresh(page)
    out = _js(page, """g.step(60); g.forceHit('beam'); g.step(80); const hurt = g.state().health;
        g.dropPowerUp('revive'); g.step(3); g.render(); const a = g.state();
        g.dropPowerUp('revive'); g.step(3); g.render(); const b = g.state();
        return { hurt, a: { revive: a.revive, chips: a.chips }, b: { revive: b.revive, health: b.health, collected: b.collected.map(c => c.kind) } };""")
    assert out["a"]["revive"] == 1
    assert out["a"]["chips"][0]["kind"] == "revive" and out["a"]["chips"][0]["label"] == "HELD", out["a"]["chips"]
    assert out["b"]["revive"] == 1, "never more than one held"
    assert out["b"]["health"] == min(100, out["hurt"] + 35), "a second revive repairs instead"


def test_a_revive_rebuilds_the_ship_in_place_with_a_full_hull_and_invulnerability(any_page) -> None:
    _fresh(any_page)
    out = _js(any_page, """g.step(600); g.dropPowerUp('revive'); g.step(3);
        const ex = g.state().player; g.spawnAsteroid('large', ex.x + 130, ex.y - 150, 0, 0);
        const seen = []; g.on('revive', e => seen.push(e));
        let n = 0; while (!g.state().revives.length && n++ < 60) { g.forceHit('beam'); if (g.state().revives.length) break; g.step(80); }
        const s = g.state(); g.render(); const tags0 = g.frameTags();
        const blocked = g.forceHit('beam'); g.step(20); g.render(); const tags1 = g.frameTags(); const mid = g.state();
        g.step(""" + str(REVIVE_INVULN) + """); g.render(); const tags2 = g.frameTags(); const after = g.state();
        return { s, seen, blocked, tags0, tags1, tags2, mid: { health: mid.health, look: mid.player.look }, after: { invuln: after.player.invuln, reviveT: after.reviveT },
                 hit: g.forceHit('beam') };""")
    s = out["s"]
    assert len(out["seen"]) == 1 and s["state"] == "paused" and s["overReason"] is None and not s["retryOffer"], "the run goes on (the test holds it paused)"
    assert s["health"] == s["healthMax"] and s["revive"] == 0, "a full hull; the revive is used up"
    assert s["player"]["invuln"] == REVIVE_INVULN, "two seconds of invulnerability"
    rv = s["revives"][0]
    assert abs(rv["x"] - s["player"]["x"]) < 1e-6 and abs(rv["y"] - s["player"]["y"]) < 1e-6, "rebuilt on the spot"
    assert s["asteroids"] == 1, "nothing near the ship is cleared"
    assert out["blocked"] is False and out["mid"]["health"] == s["healthMax"], "the protection holds"
    assert {"revive-burst", "revive-rebuild", "revive-shimmer"} <= set(out["tags0"]), out["tags0"]
    assert "revive-burst" not in out["tags1"] and 0.15 <= out["mid"]["look"] <= 1, "the ship grows back as the burst fades"
    assert "revive-shimmer" not in out["tags2"] and out["after"]["reviveT"] == -1
    assert out["hit"] is True, "once the shimmer ends, the ship can be hit again"


def test_a_held_revive_is_used_before_the_level_retry(page) -> None:
    _fresh(page, level=2)
    out = _js(page, """g.step(120); g.dropPowerUp('revive'); g.step(3);
        const lose = () => { for (let i = 0; i < 60; i++) { const r = g.state().revives.length; g.forceHit('beam'); if (g.state().state === 'over' || g.state().revives.length > r) return; g.step(80); } };
        lose(); const first = g.state(); g.step(""" + str(REVIVE_INVULN + 2) + """); lose(); const second = g.state();
        return { first: { state: first.state, retryOffer: first.retryOffer, retries: first.retries, revives: first.revives.length },
                 second: { state: second.state, retryOffer: second.retryOffer, revives: second.revives.length } };""")
    assert out["first"]["state"] == "paused" and out["first"]["retryOffer"] is False and out["first"]["revives"] == 1, "the revive, not the retry, answers the first loss"
    assert out["first"]["retries"]["2"] == 1, "the level's retry is still there"
    assert out["second"]["state"] == "over" and out["second"]["retryOffer"] is True and out["second"]["revives"] == 1


def test_there_is_no_revive_in_the_buggy_build(page) -> None:
    out = _js(page, """const counts = g.sampleDrops(20000); return { drop: g.dropPowerUp('revive'), counts };""", game="buggy")
    assert out["drop"] is False, "the buggy build refuses a revive"
    assert "revive" not in out["counts"] and out["counts"]["repair"] > 0, "its share drops a Repair instead"
    first = _js(page, """g.configure({ defects: { firstHitFatal: true }, seed: 3, threats: false, level: 1, progression: true }); g.start(); g.pause('t'); g.step(200);
        const drop = g.dropPowerUp('revive'); g.forceHit('shot'); return Object.assign(g.state(), { drop });""")
    assert first["drop"] is False and first["state"] == "over" and first["revives"] == [], "the first hit still ends a run with a defect"
    _js(page, "g.configure({ defects: {} }); return 0;")


# ---------------------------------------------------------------- T126: the Atomic blast

def _blast_scene(page):
    _fresh(page, immune=True)
    return _js(page, """g.step(200); const p = g.state().player;
        g.spawn('gunship', p.x, p.y - 150); g.spawn('agent', p.x - 60, p.y - 120); g.spawnAsteroid('large', p.x + 160, p.y - 90, 0, 0);
        g.spawnMine(p.x - 120, p.y - 60); g.spawn('bomber', 40, 40); g.spawnAsteroid('large', g.state().world.w - 50, 50, 0, 0);
        const score0 = g.state().score, seen = []; g.on('atomic', e => seen.push(e));
        g.dropPowerUp('atomic'); g.step(1);
        while (g.state().blast && g.state().blast.R < 200) g.step(1);
        const mid = g.state(); while (g.state().blast && !g.state().blast.done) g.step(1); const end = g.state();
        g.step(60); const later = g.state();
        return { score0, seen, mid: { R: mid.blast.R, enemies: mid.enemies, rocks: mid.asteroids, shots: mid.enemyShots },
                 end: { enemies: end.enemies, rocks: end.asteroids, shots: end.enemyShots, score: end.score, log: end.blastLog },
                 later: { blast: later.blast, log: later.blastLog.length } };""")


def test_the_atomic_blast_destroys_everything_its_front_passes_once(page) -> None:
    out = _blast_scene(page)
    assert len(out["seen"]) == 1
    assert out["mid"]["enemies"] == 1 and out["mid"]["rocks"] == 1, f"the near ones are gone, the far ones not yet: {out['mid']}"
    assert out["end"]["enemies"] == 0 and out["end"]["rocks"] == 0 and out["end"]["shots"] == 0, out["end"]
    log = out["end"]["log"][0]
    assert log["kills"] == 3 and log["rocks"] == 2 and log["shots"] >= 1, log
    assert out["end"]["score"] > out["score0"] + 150 + 200, "kills score normally"
    assert out["later"]["blast"] is None and out["later"]["log"] == 1, "one wave per pickup"


@pytest.mark.parametrize("stage", ["shields", "nodes", "core"])
def test_the_atomic_blast_never_kills_the_boss(page, stage: str) -> None:
    prep = {"shields": "", "nodes": "g.breakShields();", "core": "g.breakShields(); for (let i = 0; i < 4; i++) g.hitBoss('node' + i, 1e9);"}[stage]
    out = _js(page, BOSS + prep + """g.step(2); const b0 = g.state().boss; g.dropPowerUp('atomic'); g.step(1);
        while (g.state().blast && !g.state().blast.done) g.step(1); const b1 = g.state().boss;
        return { b0, b1, log: g.state().blastLog[0], plan: g.bossPlan() };""")
    _js(page, DONE)
    b0, b1 = out["b0"], out["b1"]
    assert b1 is not None and b1["coreHp"] == b0["coreHp"], "the core is never touched"
    assert out["log"]["boss"] == stage and b1["blasted"] == 1
    if stage == "shields":
        assert b0["layer"] == 0 and b1["layer"] == 1 and b1["shields"][0]["hp"] == 0 and b1["shields"][1]["hp"] == b1["shields"][1]["max"], "one layer breaks"
    if stage == "nodes":
        assert all(abs((h0 - h1) - out["plan"]["nodeHp"] * 0.4) < 1e-6 for h0, h1 in zip(b0["nodeHp"], b1["nodeHp"])), (b0["nodeHp"], b1["nodeHp"])
    if stage == "core":
        assert b1["hp"] == b0["hp"]


def test_the_atomic_blast_draws_its_flash_ring_and_shimmer(any_page) -> None:
    _fresh(any_page, immune=True)
    out = _js(any_page, """g.step(100); g.dropPowerUp('atomic'); g.step(2); g.render(); const t0 = g.frameTags();
        g.step(25); g.render(); const t1 = g.frameTags(); while (g.state().blast) g.step(1); g.render(); return { t0, t1, t2: g.frameTags() };""")
    assert {"atomic-flash", "atomic-ring", "atomic-shimmer"} <= set(out["t0"]), out["t0"]
    assert "atomic-flash" not in out["t1"] and "atomic-ring" in out["t1"]
    assert "atomic-ring" not in out["t2"]


# ---------------------------------------------------------------- T126: the start screen and the drop rates

def test_both_pickups_are_in_the_start_screen_key(page) -> None:
    page.evaluate("SkySentinel.get('fixed').reset()")
    strip = page.locator(f"{HOST} .ss-strip-item").evaluate_all("els => els.map(e => [e.dataset.kind, e.getAttribute('title')])")
    kinds = [k for k, _ in strip]
    assert kinds.index("revive") < kinds.index("mine") and kinds.index("atomic") < kinds.index("mine"), "with the upgrades, before the hazards"
    page.locator(f"{HOST} .ss-keybtn").click()
    items = page.locator(f"{HOST} .ss-key-item").evaluate_all("els => els.map(e => [e.dataset.upgrade, e.innerText])")
    page.locator(f"{HOST} .ss-keybtn").click()
    named = dict(items)
    assert named["revive"].startswith("Revive") and named["atomic"].startswith("Atomic blast")
    api = {u["kind"]: u for u in page.evaluate("SkySentinel.get('fixed').upgrades()")}
    assert api["revive"]["color"] != api["atomic"]["color"] and api["revive"]["seconds"] is None


def test_both_pickups_drop_rarely(page) -> None:
    _fresh(page, seed=5)
    counts = _js(page, "return g.sampleDrops(40000);")
    total = sum(counts.values())
    rates = page.evaluate("SkySentinel.get('fixed').dropRates()")
    for kind in ("revive", "atomic"):
        share = counts[kind] / total
        assert 0.01 <= share <= 0.03, f"{kind}: {share:.4f} of upgrade drops"
        # of all drops (a quarter of carriers, nearly half of agents, hold a hazard instead)
        assert 0.01 <= share * (1 - rates["downShare"]) <= 0.03
        assert 0.01 <= share * (1 - rates["downShareAgent"]) <= 0.03, "the boss fight's agents drop them too"
    assert {"revive", "atomic"} <= set(counts)


# ---------------------------------------------------------------- reduced motion: still frames

def test_reduced_motion_shows_still_frames_for_the_revive_and_the_blast(browser) -> None:
    ctx, pg, errors = _open(browser, motion="reduce")
    try:
        _fresh(pg, immune=True)
        blast = _js(pg, """g.step(100); g.dropPowerUp('atomic'); g.step(1); const rs = new Set();
            while (g.state().blast && !g.state().blast.done) { rs.add(Math.round(g.state().blast.R)); g.step(1); } return [...rs];""")
        assert 1 <= len(blast) <= 3, f"the front jumps in still steps: {blast}"
        _js(pg, "g.configure({ immune: false }); return 0;")
        _fresh(pg)
        looks = _js(pg, """g.step(100); g.dropPowerUp('revive'); g.step(3);
            for (let i = 0; i < 60 && !g.state().revives.length; i++) { g.forceHit('beam'); if (g.state().revives.length) break; g.step(80); }
            const out = []; for (let t = 0; t < 40; t++) { const s = g.state(); g.render(); out.push([s.player.look, g.frameTags().includes('revive-rebuild')]); g.step(1); } return out;""")
        assert all(look == 1 for look, _ in looks), "the ship is drawn whole: no growing animation"
        assert all(tag for _, tag in looks[:30]), "one still frame of the rebuild ring"
    finally:
        assert not errors, errors
        ctx.close()
