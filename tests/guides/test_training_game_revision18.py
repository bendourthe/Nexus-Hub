"""v4.13.10 plan revision 18 (R48): a clean, animated new universe after the finale, the end card's
score summary (per level and overall, destroyed over spawned), and the two rare pickups on a
schedule: one Atomic blast per level in its last third and one Revive per level in its second half
(boss fight: after the first shield layer falls, and below half health), larger and slower than the
other pickups, never carried, and the Revive valid only for its level.

Every test drives the simulation through ``step(n)`` with a fixed seed and ``SkySentinel.manual(true)``;
no test waits a fixed real time for a frame-counted sequence.
Design: docs/releases/v4/v4.13/development/v4.13.10-game-design.md, "Revision 18".
Skipped without Playwright or Chromium; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
HOST = ".ss-host[data-ss-id=fixed]"


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


def _open(browser, width: int = 1440, height: int = 900, motion: str = "no-preference", renderer: str | None = None):
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


def _fresh(page, **cfg) -> None:
    page.evaluate(
        """(cfg) => { const g = SkySentinel.get('fixed');
            g.configure(Object.assign({ defects: {}, seed: 31, threats: true, level: 1, progression: true, boss: true, immune: true }, cfg));
            g.chooseShip('vanguard'); g.start(); g.pause('test'); }""",
        cfg,
    )


WIN = """g.configure({ defects: {}, seed: 7, threats: true, level: 3, progression: true, boss: true, bossNow: true, immune: true });
    g.chooseShip('vanguard'); g.start(); g.pause('t'); g.input({ fire: true }); g.step(400);
    g.dropPowerUp('shield'); g.step(3); g.dropPowerUp('spread'); g.step(3); g.dropPowerUp('rapid'); g.step(3); g.defeatBoss(); g.input({ fire: false });"""
DONE = "g.input({ fire: false, left: false, right: false, up: false }); g.configure({ immune: false, level: 1, bossNow: false }); return 0;"
LOSE = "for (let i = 0; i < 80 && g.state().state !== 'over'; i++) { g.forceHit('beam'); g.step(80); }"
FIT = f"""(() => {{ const h = document.querySelector('{HOST}'), ov = h.querySelector('.ss-overlay'), pn = h.querySelector('.ss-panel'), t = h.querySelector('.ss-sum-table');
  const o = ov.getBoundingClientRect(), p = pn.getBoundingClientRect(), r = t.getBoundingClientRect();
  return {{ shown: !h.querySelector('.ss-summary').hidden, scroll: ov.scrollHeight - ov.clientHeight, hscroll: ov.scrollWidth - ov.clientWidth,
           inside: p.top >= o.top - 0.5 && p.bottom <= o.bottom + 0.5 && p.left >= o.left - 0.5 && p.right <= o.right + 0.5,
           table: r.width > 0 && r.left >= p.left - 0.5 && r.right <= p.right + 0.5, scale: pn.style.transform,
           rows: [...t.querySelectorAll('tbody tr')].map(tr => [tr.dataset.level, ...[...tr.cells].map(c => c.textContent)]),
           total: [...t.querySelectorAll('tfoot td')].map(c => c.textContent), score: h.querySelector('.ss-sum-score b').textContent,
           title: h.querySelector('.ss-over-title').textContent, prize: h.querySelector('.ss-over-prize').hidden ? null : h.querySelector('.ss-over-prize').textContent }}; }})()"""


def _stage_png(page) -> bytes:
    return page.locator(HOST + " .ss-stage").screenshot()


# ---------------------------------------------------------------- T132: the clean new universe

def test_after_the_swallow_nothing_of_the_battle_remains_and_the_universe_animates(any_page) -> None:
    out = _js(any_page, WIN + """const a = g.state(); const fl = g.finalePlan().flash; let s = a;
        while (s.finale.t < fl + 1) s = g.step(1); g.render();
        const b = g.state(); const tags = g.frameTags();
        return { a: { shots: a.shots, shield: a.shieldHp, ups: a.upgrades.length }, b, tags };""")
    a, b = out["a"], out["b"]
    assert a["shots"] > 0 and a["shield"] > 0 and a["ups"] > 0, f"the fight left shots, a shield, and upgrades running: {a}"
    assert b["finale"]["phase"] == "universe" and b["map"] == "A New Universe"
    assert b["shots"] == b["enemyShots"] == b["enemies"] == b["asteroids"] == b["powerUps"] == 0, b
    assert b["blast"] is None and b["popupCount"] == 0 and b["effects"] <= 1, "only the arrival's own flash"
    assert b["shieldHp"] == 0 and b["upgrades"] == [] and b["downgrades"] == [] and b["revive"] == 0, "no shield bubble, no running effect"
    assert b["chips"] == [], "no effect chip is left counting"
    assert b["hud"]["calm"] == {"title": "VICTORY", "map": "A New Universe", "bars": False, "chips": 0}, "the HUD drops the fight's bars"
    assert "new-universe" in out["tags"] and not any(t.startswith(("atomic", "revive")) for t in out["tags"])
    _js(any_page, "let s = g.state(); while (!s.finale.done) s = g.step(10); g.render(); return 0;")
    first = _stage_png(any_page)
    c0 = _js(any_page, "return g.state().calm;")
    _js(any_page, "g.step(150); g.render(); return 0;")
    second = _stage_png(any_page)
    assert _js(any_page, "return g.state().calm;") > c0, "the calm clock runs after the finale"
    assert first != second, "the new universe keeps turning behind the end card"
    assert _js(any_page, "return g.animating();") is True, "the page keeps animating it while it is on screen"
    _js(any_page, DONE)


# ---------------------------------------------------------------- T132: the score summary

def test_the_victory_summary_lists_each_level_with_tracked_percentages(page) -> None:
    _js(page, WIN + "let s = g.state(); while (!s.finale.done) s = g.step(20); return 0;")
    sm = _js(page, "return g.scoreSummary();")
    fit = page.evaluate(FIT)
    _js(page, DONE)
    assert fit["title"] == "Victory" and fit["prize"] == "Reward unlocked: Nexus AI Studio"
    assert fit["score"] == f"{sm['score']:,}" and sm["victory"] is True
    boss = [r for r in sm["rows"] if r["level"] == 4][0]
    assert boss["spawned"] >= 1 and boss["destroyed"] >= 1, "the megaship counts as one"
    for r in sm["rows"]:
        assert r["percent"] == (100 * r["destroyed"] // r["spawned"]), r
    assert sm["percent"] == 100 * sm["destroyed"] // sm["spawned"]
    assert sum(r["points"] for r in sm["rows"]) == sm["score"]
    shown = {row[0]: row for row in fit["rows"]}
    assert shown["4"][1] == "Nexus Boss" and shown["4"][3] == f"{boss['percent']}%{boss['destroyed']} of {boss['spawned']}"
    assert fit["total"][1] == f"{sm['percent']}%{sm['destroyed']} of {sm['spawned']}"


def test_a_level_counts_spawns_and_kills_including_fragments_and_closes_at_the_level_end(page) -> None:
    _fresh(page, seed=7)
    out = _js(page, """g.input({ fire: true }); let s = g.state(); while (s.level === 1) s = g.step(20);
        const sm = g.scoreSummary(); g.input({ fire: false });
        return { sm, breaks: s.breaks.reduce((n, b) => n + b.into, 0), levelScore: s.levelScore, spawned: s.spawned };""")
    row1 = out["sm"]["rows"][0]
    assert row1["level"] == 1 and not row1["current"] and row1["points"] == out["levelScore"], "level 1 closed at its end with its points"
    assert row1["spawned"] >= out["spawned"] + out["breaks"], "every ship, rock, and fragment counts as spawned"
    assert 0 < row1["destroyed"] <= row1["spawned"] and row1["percent"] == 100 * row1["destroyed"] // row1["spawned"]
    assert out["sm"]["rows"][1]["level"] == 2 and out["sm"]["rows"][1]["current"]


def test_a_retry_resets_the_level_counts_and_a_loss_shows_the_levels_reached(browser) -> None:
    for size in [(1440, 900), (390, 844)]:
        ctx, pg, errors = _open(browser, *size)
        try:
            _fresh(pg, level=2, seed=11)
            before = _js(pg, "g.input({ fire: true }); g.step(1500); g.input({ fire: false }); g.configure({ immune: false, reset: false }); return g.scoreSummary();")
            lost = _js(pg, LOSE + " return Object.assign(g.scoreSummary(), { offer: g.state().retryOffer, shown: !document.querySelector('" + HOST + " .ss-summary').hidden });")
            after = _js(pg, "g.retry(); g.pause('t'); return g.scoreSummary();")
            _js(pg, "g.configure({ immune: true, reset: false }); g.input({ fire: true }); g.step(600); g.input({ fire: false }); g.configure({ immune: false, reset: false });" + LOSE + " return 0;")
            final = _js(pg, "return g.scoreSummary();")
            fit = pg.evaluate(FIT)
            r0 = before["rows"][0]
            assert r0["level"] == 2 and r0["spawned"] > 0 and r0["destroyed"] > 0
            assert lost["offer"] and not lost["shown"], "the retry card shows no summary"
            assert after["rows"][0]["spawned"] == 0 and after["rows"][0]["destroyed"] == 0 and after["rows"][0]["points"] == 0, "the retry counts from zero"
            fr = final["rows"][0]
            assert fr["current"] and fr["spawned"] > 0 and fr["percent"] == 100 * fr["destroyed"] // fr["spawned"]
            assert fit["shown"] and fit["title"] != "Victory" and fit["prize"] is None
            assert fit["rows"][0][0] == "2" and fit["rows"][0][1].startswith("Level 2") and "so far" in fit["rows"][0][1]
            assert fit["scroll"] <= 0 and fit["hscroll"] <= 0 and fit["inside"] and fit["table"], f"{size}: no scroll {fit}"
        finally:
            _js(pg, DONE)
            assert not errors, errors
            ctx.close()


@pytest.mark.parametrize("size", [(1440, 900), (390, 844)], ids=lambda v: f"{v[0]}x{v[1]}")
def test_the_victory_summary_fits_without_a_scroll(browser, size: tuple[int, int]) -> None:
    ctx, pg, errors = _open(browser, *size)
    try:
        _js(pg, WIN + "let s = g.state(); while (!s.finale.done) s = g.step(20); return 0;")
        fit = pg.evaluate(FIT)
        assert fit["shown"] and fit["scroll"] <= 0 and fit["hscroll"] <= 0 and fit["inside"] and fit["table"], f"{size}: {fit}"
        for sel in (".ss-start", ".ss-change"):
            assert pg.locator(f"{HOST} {sel}").is_visible(), sel
    finally:
        _js(pg, DONE)
        assert not errors, errors
        ctx.close()


# ---------------------------------------------------------------- T133: the schedule

@pytest.fixture(scope="module")
def full_run(page):
    """One seeded run from level 1 to the boss with an immune, firing ship: the plans and spawns."""
    _fresh(page, seed=7)
    out = _js(page, """g.input({ fire: true }); const plans = { 1: g.rarePlan().plan }; let s = g.state();
        while (!s.boss && s.tick < 17000) { s = g.step(20); if (!plans[s.level]) plans[s.level] = g.rarePlan().plan; }
        g.input({ fire: false });
        return { plans, log: s.rareLog, drops: s.drops.map(d => d.upgrade), lengths: g.difficulty().map(d => d.seconds * 60) };""")
    _js(page, DONE)
    return out


@pytest.mark.parametrize("level", [1, 2, 3])
def test_exactly_one_blast_and_one_revive_per_level_inside_their_windows(full_run, level: int) -> None:
    log = [e for e in full_run["log"] if e["level"] == level]
    assert sorted(e["kind"] for e in log) == ["atomic", "revive"], log
    length = full_run["lengths"][level - 1]
    blast = [e for e in log if e["kind"] == "atomic"][0]
    revive = [e for e in log if e["kind"] == "revive"][0]
    assert length * 2 / 3 <= blast["levelTick"] < length, f"the blast arrives in the level's last third: {blast}"
    assert length / 2 <= revive["levelTick"] < length, f"the revive arrives in the second half: {revive}"
    plan = full_run["plans"][str(level)]
    assert blast["levelTick"] == plan["blastAt"] and revive["levelTick"] == plan["reviveAt"]


def test_carriers_never_drop_either_rare_pickup(page, full_run) -> None:
    assert full_run["drops"] and not {"atomic", "revive"} & set(full_run["drops"]), "a carrier released one"
    _fresh(page, seed=5)
    counts = _js(page, "return g.sampleDrops(40000);")
    assert "atomic" not in counts and "revive" not in counts
    assert 0.13 <= counts["repair"] / sum(counts.values()) <= 0.17, "their share drops a Repair, as before R43"


def test_the_boss_fight_brings_the_blast_after_the_first_layer_and_the_revive_below_half(page) -> None:
    out = _js(page, """g.configure({ defects: {}, seed: 7, threats: true, level: 3, progression: true, boss: true, bossNow: true, immune: true });
        g.chooseShip('vanguard'); g.start(); g.pause('t'); let s = g.state(); while (!(s.boss && s.boss.entered)) s = g.step(1);
        s = g.step(300); const a = s.rareLog.filter(e => e.level === 4).length;
        g.hitBoss('shield', 1e9); s = g.step(2); const b = s.rareLog.filter(e => e.level === 4);
        g.hitBoss('shield', 1e9); s = g.step(2); const c = s.rareLog.filter(e => e.level === 4).length;
        g.hitBoss('shield', 1e9); for (let i = 0; i < 4; i++) g.hitBoss('node' + i, 1e9); g.hitBoss('core', 300); s = g.step(2);
        return { a, b, c, d: s.rareLog.filter(e => e.level === 4), hp: s.boss.hp, max: s.boss.hpMax };""")
    _js(page, DONE)
    assert out["a"] == 0, "nothing before the first layer falls"
    assert [e["kind"] for e in out["b"]] == ["atomic"] and out["b"][0]["layer"] == 1
    assert out["c"] == 1, "one blast for the whole fight"
    revive = [e for e in out["d"] if e["kind"] == "revive"]
    assert len(revive) == 1 and revive[0]["bossHp"] < out["max"] / 2 and len(out["d"]) == 2


def test_rare_pickups_are_larger_and_slower_than_a_standard_one(any_page) -> None:
    _fresh(any_page, threats=False)
    out = _js(any_page, """const w = g.state().world.w; g.step(5);
        g.spawnRare('atomic', w * 0.25, 120); g.spawnRare('revive', w * 0.5, 120);
        const p = g.state().player; g.dropPowerUp('spread'); const plan = g.rarePlan();
        const std0 = g.state().pickups.find(u => !u.rare); const y0 = std0.y;
        g.spawnAsteroid('large', 10, -400, 0, 0);
        const a = g.state().pickups; g.step(30); g.render(); const b = g.state().pickups; const tags = g.frameTags();
        return { a, b, plan, tags };""")
    a, b, plan = out["a"], out["b"], out["plan"]
    rare = [u for u in a if u["rare"]]
    assert {u["kind"] for u in rare} == {"atomic", "revive"} and all(u["r"] == plan["r"] for u in rare)
    assert plan["r"] / plan["standardR"] == pytest.approx(1.4, abs=0.05) and plan["speed"] / plan["standardSpeed"] == pytest.approx(0.6)
    fall = {u["kind"]: bu["y"] - au["y"] for au, bu in zip(a, b) for u in [au] if au["rare"]}
    assert all(v == pytest.approx(30 * plan["speed"], abs=0.01) for v in fall.values()), fall
    assert {"rare-atomic", "rare-revive"} <= set(out["tags"]), out["tags"]
    look = {u["kind"]: u for u in _js(any_page, "return g.upgrades();")}
    assert look["atomic"]["color"] == "#7cfc3a" and look["revive"]["color"] == "#fde047"


# ---------------------------------------------------------------- T133: the Revive belongs to its level

def test_a_held_revive_expires_when_its_level_ends_and_never_stacks(page) -> None:
    _fresh(page, threats=False, immune=False)
    out = _js(page, """g.step(5250); g.forceHit('beam'); g.step(70); const hurt = g.state().health;
        g.dropPowerUp('revive'); g.step(3); g.dropPowerUp('revive'); g.step(3); g.render(); const a = g.state();
        let s = a; while (s.level === 1) s = g.step(5); g.step(260); g.render(); s = g.state();
        return { hurt, a: { revive: a.revive, health: a.health, chips: a.chips.map(c => c.kind) }, b: { level: s.level, revive: s.revive, expired: s.expired, chips: s.chips.map(c => c.kind), live: s.state } };""")
    assert out["a"]["revive"] == 1 and out["a"]["chips"][0] == "revive"
    assert out["a"]["health"] == min(100, out["hurt"] + 35), "a second one repairs instead of stacking"
    assert out["b"]["level"] == 2 and out["b"]["revive"] == 0 and len(out["b"]["expired"]) == 1 and out["b"]["expired"][0]["level"] == 1
    assert "revive" not in out["b"]["chips"], "the chip is gone in the next level"


def test_the_buggy_build_has_neither(page) -> None:
    out = _js(page, """g.configure({ defects: { firstHitFatal: true }, seed: 3, threats: true, level: 1, progression: true, immune: true });
        g.start(); g.pause('t'); const plan = g.rarePlan(); let s = g.step(5300);
        return { on: plan.on, plan: plan.plan, log: s.rareLog, atomic: g.dropPowerUp('atomic'), revive: g.dropPowerUp('revive'), rare: g.spawnRare('atomic', 100, 100) };""", game="buggy")
    _js(page, "g.configure({ defects: {}, immune: false }); return 0;", game="buggy")
    assert out["on"] is False and out["plan"] is None and out["log"] == []
    assert out["atomic"] is False and out["revive"] is False and out["rare"] is False


KEY_PROBE = f"""(() => {{ const h = document.querySelector('{HOST}'), ov = h.querySelector('.ss-overlay');
  const items = [...h.querySelectorAll('.ss-key-item')].map(li => {{ const r = li.getBoundingClientRect(), sp = li.querySelector('.ss-key-text span').getBoundingClientRect();
    return {{ kind: li.dataset.upgrade, text: li.innerText, spill: sp.right - r.right }}; }});
  return {{ scroll: ov.scrollHeight - ov.clientHeight, items }}; }})()"""


@pytest.mark.parametrize("size", [(1440, 900), (390, 844)], ids=lambda v: f"{v[0]}x{v[1]}")
def test_the_start_screen_names_the_schedule_and_still_fits(browser, size: tuple[int, int]) -> None:
    ctx, pg, errors = _open(browser, *size)
    try:
        pg.locator(f"{HOST} .ss-keybtn").click()
        out = pg.evaluate(KEY_PROBE)
        named = {i["kind"]: i for i in out["items"]}
        assert "Last third of each level" in named["atomic"]["text"]
        assert "2nd half; this level only" in named["revive"]["text"]
        assert out["scroll"] <= 0, out
        assert all(i["spill"] <= 1 for i in out["items"]), [i for i in out["items"] if i["spill"] > 1]
    finally:
        assert not errors, errors
        ctx.close()


# ---------------------------------------------------------------- reduced motion

def test_reduced_motion_shows_the_universe_and_the_summary_as_still_frames(browser) -> None:
    ctx, pg, errors = _open(browser, motion="reduce")
    try:
        _js(pg, WIN + "let s = g.state(); while (!s.finale.done) s = g.step(20); g.render(); return 0;")
        first = _stage_png(pg)
        out = _js(pg, "const c0 = g.state().calm; g.step(150); g.render(); return { c0, c1: g.state().calm, anim: g.animating() };")
        second = _stage_png(pg)
        fit = pg.evaluate(FIT)
        assert out["c0"] == out["c1"] and out["anim"] is False, out
        assert first == second, "one still frame"
        assert fit["shown"] and fit["scroll"] <= 0
    finally:
        _js(pg, DONE)
        assert not errors, errors
        ctx.close()
