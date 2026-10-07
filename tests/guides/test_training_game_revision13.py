"""v4.13.10 plan revision 13 (R41 and R42): one retry per level in the fixed game, and the supernova
and wormhole passage from level 3 into the Nexus dimension.

Like the other engine tests, every test drives the simulation through ``step(n)`` with a fixed seed
and ``SkySentinel.manual(true)``; no test waits a fixed real time for a frame-counted sequence.
Design: docs/releases/v4/v4.13/development/v4.13.10-game-design.md, "Revision 13".
Skipped without Playwright or Chromium; fail-closed under NEXUS_REQUIRE_RENDER=1.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "guides" / "website" / "training.html"
ENGINE = ROOT / "guides" / "website" / "src" / "sky-sentinel.js"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"

HOST = ".ss-host[data-ss-id=fixed]"
NOVA_STAGES = ["swell", "collapse", "burst", "tear", "travel", "emerge"]
NOVA_TAGS = {"nova-star", "supernova-flash", "shock-ring", "ejecta", "nova-tunnel", "tunnel-walls", "nexus-arrival"}
WORMHOLE_ONLY = {"wormhole-disc", "wormhole-arms", "star-streaks"}
FINALE_ONLY = {"chain-blast", "flash", "rift", "light-bleed", "event-horizon", "accretion-disk", "photon-ring", "lensing",
               "infall-debris", "stretched-ship", "new-universe", "prize-card"}
NOVA_START, BOSS_AT = 3000, 3600          # ticks into level 3: the passage, then the boss's arrival
STILL_START = 3300                        # the reduced-motion passage is 300 ticks


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
            g.configure(Object.assign({ defects: {}, seed: 31, threats: false, level: 1, progression: true, boss: true, immune: false }, cfg)); g.start(); g.pause('test'); }""",
        [game, cfg],
    )


LOSE = "for (let i = 0; i < 60 && g.state().state !== 'over'; i++) { g.forceHit('beam'); g.step(80); }"
CARD = f"""const q = s => document.querySelector('{HOST} ' + s);
  const card = {{ title: q('.ss-over-title').textContent, retry: !q('.ss-retry').hidden, note: q('.ss-retry-note').hidden ? null : q('.ss-retry-note').textContent,
    start: !q('.ss-start').hidden, change: !q('.ss-change').hidden, live: q('.ss-live').textContent, overlay: !q('.ss-overlay').hidden }};"""


# ---------------------------------------------------------------- R41 (T123): one retry per level

def test_the_first_loss_on_a_level_offers_its_one_retry(page) -> None:
    _fresh(page, level=2)
    out = _js(page, f"""const ev = []; g.on('destroyed', e => ev.push([e.retry, e.level])); g.step(120); {LOSE}
        const s = g.state(); {CARD} return {{ s, card, ev }};""")
    s, card = out["s"], out["card"]
    assert s["state"] == "over" and s["retryOffer"] is True and s["overReason"] == "hit"
    assert card["overlay"] and card["title"] == "Ship Lost" and card["retry"] and card["note"] == "Retries left: 0"
    assert not card["start"] and not card["change"], "the retry card offers only the retry"
    assert "Ship lost" in card["live"] and "Retry level" in card["live"], "the live region announces the loss and the retry"
    assert out["ev"][-1] == [True, 2]


def test_a_retry_restarts_the_level_with_a_full_hull_the_same_ship_and_the_level_start_score(page) -> None:
    """Score rule (decision): a retry restores the score the level began with."""
    _fresh(page, level=1, threats=True, immune=True)
    out = _js(page, f"""g.input({{ fire: true }}); let s = g.step(5400 + 260); const atStart = s.levelScore;
        s = g.step(900); g.input({{ fire: false }}); g.dropPowerUp('spread'); g.step(2); g.configure({{ immune: false, reset: false }});
        const before = g.state(); {LOSE} const lost = g.state();
        const took = g.retry(); g.pause('t'); const after = g.state(); return {{ atStart, before, lost, took, after }};""")
    b, lost, a = out["before"], out["lost"], out["after"]
    assert b["level"] == 2 and out["atStart"] > 0 and b["score"] > out["atStart"], "points were earned before and during level 2"
    assert any(u["kind"] == "spread" for u in b["upgrades"]), "an upgrade was running before the loss"
    assert lost["retryOffer"] and out["took"] is True
    assert a["state"] == "paused" and a["level"] == 2 and a["map"] == "Violet Halo" and a["health"] == a["healthMax"]
    assert a["ship"] == b["ship"] and a["upgrades"] == [] and a["downgrades"] == [] and a["shieldHp"] == 0, "the chosen ship, no upgrades"
    assert a["score"] == out["atStart"] == a["levelScore"], "the score returns to what the level began with"
    assert a["levelProgress"] == 0 and a["spawnRate"] == pytest.approx(0.64, abs=0.01), "the level's starting difficulty"
    assert a["spawnRate"] < b["spawnRate"], "lower than where the lost attempt had climbed to"
    assert a["enemies"] == a["enemyShots"] == a["asteroids"] == 0
    assert a["retryLog"][-1]["level"] == 2 and a["retries"]["2"] == 0


def test_a_second_loss_on_the_same_level_ends_the_run(page) -> None:
    _fresh(page, level=1)
    out = _js(page, f"""const ev = []; g.on('destroyed', e => ev.push(e.retry)); g.step(60); {LOSE} g.retry(); g.pause('t'); g.step(60); {LOSE}
        const s = g.state(); g.render(); {CARD} return {{ s, card, again: g.retry(), ev: ev.slice(-2) }};""")
    s, card = out["s"], out["card"]
    assert s["state"] == "over" and s["retryOffer"] is False and out["again"] is False
    assert card["title"] == s["overText"] and card["start"] and card["change"] and not card["retry"], "the normal end card"
    assert card["note"] == "Retries left: 0" and "No retries left" in card["live"]
    assert out["ev"] == [True, False]


def test_each_new_level_grants_its_own_retry(page) -> None:
    _fresh(page, level=1)
    out = _js(page, f"""g.step(60); {LOSE} g.retry(); g.pause('t'); g.configure({{ immune: true, reset: false }});
        const l1 = g.state(); let s = g.step(5400 + 220); g.configure({{ immune: false, reset: false }}); const l2 = g.state(); {LOSE} const lost2 = g.state();
        return {{ l1, l2, lost2 }};""")
    assert out["l1"]["retries"]["1"] == 0 and out["l1"]["retriesLeft"] == 0
    assert out["l2"]["level"] == 2 and out["l2"]["retriesLeft"] == 1 and out["l2"]["retries"]["2"] == 1, "level 2 brings a fresh retry"
    assert out["lost2"]["retryOffer"] is True


def test_the_boss_level_retry_restarts_the_fight_with_its_entrance(page) -> None:
    _fresh(page, level=3, bossNow=True)
    out = _js(page, f"""let s = g.state(); while (!(s.boss && s.boss.entered)) s = g.step(5);
        g.breakShields(); g.hitBoss('node0', 9999); const hurt = g.state(); g.step(100); {LOSE} const lost = g.state();
        g.retry(); g.pause('t'); const after = g.state(); let t = after; while (!t.boss.entered) t = g.step(5);
        return {{ hurt, lost, after, entered: t }};""")
    hurt, lost, a = out["hurt"], out["lost"], out["after"]
    assert hurt["boss"]["hp"] < hurt["boss"]["hpMax"] and hurt["bossLevel"] is True
    assert lost["retryOffer"] is True and lost["retries"]["4"] == 1, "the boss fight is a level of its own"
    assert a["boss"] is not None and a["boss"]["entered"] is False and a["boss"]["intro"]["t"] <= 1, "the megaship arrives again"
    assert a["boss"]["hp"] == a["boss"]["hpMax"] and a["boss"]["shieldsUp"] == 3, "a fresh boss"
    assert a["map"] == "The Nexus Storm" and a["health"] == a["healthMax"] and a["score"] == a["levelScore"] == lost["levelScore"]
    assert out["entered"]["boss"]["entered"] is True and a["retries"]["4"] == 0


def test_the_buggy_game_never_offers_a_retry(page) -> None:
    out = _js(page, f"""g.configure({{ seed: 31, threats: false }}); g.start(); g.pause('t'); g.step(30); g.forceHit('shot'); const s = g.state(); g.render();
        const q = sel => document.querySelector('.ss-host[data-ss-id=buggy] ' + sel);
        return {{ s: g.state(), took: g.retry(), retry: !q('.ss-retry').hidden, title: q('.ss-over-title').textContent }};""", game="buggy")
    s = out["s"]
    assert s["state"] == "over" and s["overReason"] == "first-hit", "the first hit still ends the buggy game"
    assert s["retriesOn"] is False and s["retryOffer"] is False and out["took"] is False and not out["retry"]
    assert out["title"] != "Ship Lost" and s["hud"]["retry"] is None
    # a fixed game with a defect switched on is a demonstration of that defect, so it offers none either
    _fresh(page, defects={"firstHitFatal": True})
    fixed = _js(page, "g.step(30); g.forceHit('shot'); return g.state();")
    _fresh(page)
    assert fixed["overReason"] == "first-hit" and fixed["retryOffer"] is False and fixed["retriesOn"] is False


def test_the_hud_shows_the_retries_left_on_this_level(any_page) -> None:
    _fresh(any_page, level=1)
    out = _js(any_page, f"""g.step(30); g.render(); const a = g.state().hud.retry; {LOSE} g.render(); const b = g.state().hud.retry;
        g.retry(); g.pause('t'); g.render(); const c = g.state().hud.retry;
        const dom = document.querySelectorAll('{HOST} .ss-hud-item')[2].textContent; return {{ a, b, c, dom, w: g.state().canvas.cssWidth }};""")
    assert out["a"]["text"] == "Retries left: 1" and out["a"]["left"] == 1
    assert out["b"]["text"] == "Retries left: 0", "the offered retry counts as spent, as the card says"
    assert out["c"]["text"] == "Retries left: 0"
    assert out["a"]["y"] < 60 and out["a"]["x"] > out["w"] * 0.8, "small, top right, under the score"
    assert "Retries left: 0" in out["dom"], "screen readers get the count with the level"


def test_the_retry_button_works_from_the_keyboard(page) -> None:
    _fresh(page, level=1)
    _js(page, f"g.step(30); g.render(); {LOSE} return 0;")
    focused = page.evaluate(f"document.activeElement === document.querySelector('{HOST} .ss-retry')")
    page.locator(HOST + " .ss-retry").focus()
    page.keyboard.press("Enter")
    s = _js(page, "const s = g.state(); g.pause('t'); return s;")
    live = page.evaluate(f"document.querySelector('{HOST} .ss-live').textContent")
    assert focused, "the card moves focus to the retry button"
    assert s["state"] == "running" and s["health"] == s["healthMax"] and s["retryLog"], "Enter on the button retries"
    assert "Retrying level 1" in live


# ---------------------------------------------------------------- R42 (T124): the supernova and the wormhole

def _nova_frames(page, every: int = 10) -> dict:
    _fresh(page, level=3, threats=True, immune=True, seed=7)
    return _js(page, f"""let arrive = null; g.on('bossArrive', e => {{ arrive = e.tick; }}); let s = g.step({NOVA_START - 1}); const before = s; const frames = [];
        while (!s.boss) {{ s = g.step({every}); g.render(); frames.push({{ tick: s.tick, stage: s.nova && s.nova.stage, tags: g.frameTags(), map: s.map, kind: s.transitionInfo && s.transitionInfo.kind,
          live: document.querySelector('{HOST} .ss-live').textContent, enemies: s.enemies }}); }}
        return {{ before, frames, end: s, arrive }};""")


@pytest.mark.parametrize("renderer", ["webgl", "2d"])
def test_clearing_level_three_plays_the_supernova_passage_in_order_into_the_boss_entrance(browser, renderer: str) -> None:
    ctx, pg, errors = _open(browser, renderer=None if renderer == "webgl" else "2d")
    try:
        out = _nova_frames(pg)
        seen = []
        for f in out["frames"]:
            if f["stage"] and (not seen or seen[-1] != f["stage"]):
                seen.append(f["stage"])
        assert out["before"]["transition"] is False and out["before"]["map"] == "Ember Belt"
        assert seen == NOVA_STAGES, seen
        log = out["end"]["novaLog"]
        assert [x["stage"] for x in log] == NOVA_STAGES and log[0]["tick"] == NOVA_START
        by = {st: [f for f in out["frames"] if f["stage"] == st] for st in seen}
        assert all(f["kind"] == "nova" for st in seen for f in by[st])
        assert all("nova-star" in f["tags"] for f in by["swell"] + by["collapse"]), "the star swells, then collapses"
        assert any({"supernova-flash", "shock-ring", "ejecta"} <= set(f["tags"]) for f in by["burst"]), "flash, shock ring, ejecta"
        assert any("nova-tunnel" in f["tags"] for f in by["tear"]) and all({"nova-tunnel", "tunnel-walls"} <= set(f["tags"]) for f in by["travel"])
        assert any("nexus-arrival" in f["tags"] for f in by["emerge"]) and all(f["map"] == "The Nexus Storm" for f in by["emerge"])
        assert all(f["map"] == "Ember Belt" for f in by["travel"]), "the map changes only as the tunnel opens onto the storm"
        assert any("Supernova" in f["live"] for f in by["burst"]), "the live region names the stages"
        assert by["emerge"][-1]["enemies"] == 0, "the shock wave cleared the arena"
        end = out["end"]
        assert out["arrive"] == BOSS_AT and end["boss"]["entered"] is False and end["boss"]["intro"]["t"] <= 10, "it ends in the boss entrance, on time"
        assert 8 <= (BOSS_AT - NOVA_START) / 60 <= 12
    finally:
        assert not errors, errors
        ctx.close()


def _transition_tags(page, level: int) -> set[str]:
    _fresh(page, level=level, boss=False, immune=True, seed=7)
    return set(_js(page, f"""const tags = new Set(); const at = {5400 if level == 1 else 6600}; g.step(at - 1);
        for (let i = 0; i < 22; i++) {{ const s = g.step(10); g.render(); g.frameTags().forEach(t => tags.add(t)); if (s.transitionInfo) tags.add('kind:' + s.transitionInfo.kind); }}
        return [...tags];"""))


def _finale_tags(page) -> set[str]:
    _fresh(page, level=3, bossNow=True, seed=7)
    return set(_js(page, """let s = g.state(); while (!(s.boss && s.boss.entered)) s = g.step(5); g.defeatBoss(); s = g.state(); const tags = new Set();
        while (!s.finale.done) { s = g.step(10); g.render(); g.frameTags().forEach(t => tags.add(t)); } return [...tags];"""))


@pytest.mark.parametrize("renderer", ["webgl", "2d"])
def test_the_passage_shares_no_element_with_the_level_wormholes_or_the_finale(browser, renderer: str) -> None:
    ctx, pg, errors = _open(browser, renderer=None if renderer == "webgl" else "2d")
    try:
        nova = set()
        for f in _nova_frames(pg, every=6)["frames"]:
            nova.update(f["tags"])
        worm12, worm23, fin = _transition_tags(pg, 1), _transition_tags(pg, 2), _finale_tags(pg)
        assert NOVA_TAGS <= nova, nova
        for worm in (worm12, worm23):
            assert "kind:level" in worm and WORMHOLE_ONLY <= worm, "the level transitions are unchanged"
            assert not (worm & NOVA_TAGS) and not (nova & WORMHOLE_ONLY), f"shared with a level wormhole: {worm & nova}"
        assert not (fin & NOVA_TAGS) and not (nova & FINALE_ONLY), f"shared with the finale: {fin & nova}"
    finally:
        assert not errors, errors
        ctx.close()


def test_the_passage_palette_is_its_own() -> None:
    """Each of the passage's colours appears once in the engine, in NOVA_LOOK: no other draw path uses it."""
    src = ENGINE.read_text(encoding="utf-8")
    look = re.search(r"var NOVA_LOOK = \{(.*?)\};", src, re.S)
    assert look, "NOVA_LOOK is defined"
    colours = re.findall(r"#[0-9a-fA-F]{6}", look.group(1))
    assert len(colours) == 9
    for c in colours:
        assert src.lower().count(c.lower()) == 1, f"{c} is used outside NOVA_LOOK"


ARENA = """() => { const g = SkySentinel.get('fixed'); g.render(); const c = document.querySelector('.ss-host[data-ss-id=fixed] .ss-canvas'), gl = c.getContext('webgl');
  const px = new Uint8Array(4 * c.width * c.height); gl.readPixels(0, 0, c.width, c.height, gl.RGBA, gl.UNSIGNED_BYTE, px);
  let n = 0, tunnel = 0, dark = 0, sum = [0, 0, 0];
  for (let y = 4; y < c.height; y += 9) for (let x = 4; x < c.width; x += 9) { const i = 4 * (y * c.width + x), r = px[i], gg = px[i + 1], b = px[i + 2];
    const mx = Math.max(r, gg, b), mn = Math.min(r, gg, b), mean = (r + gg + b) / 3; n++; sum[0] += r; sum[1] += gg; sum[2] += b;
    if (mx - mn > 35 && mean > 40 && b > r) tunnel++; if (mean < 20) dark++; }
  return { tunnel: tunnel / n, dark: dark / n, mean: sum.map(v => v / n) }; }"""


def test_a_tunnel_frame_looks_unlike_a_level_wormhole_frame_and_a_finale_frame(page) -> None:
    """The tunnel fills the arena with violet and teal walls; the wormhole is a disc on dark space; the finale is a dark hole with a warm disk."""
    _fresh(page, level=3, seed=7)
    _js(page, f"g.step({NOVA_START} + 450); return 0;")
    tunnel = page.evaluate(ARENA)
    _fresh(page, level=3, seed=7)
    _js(page, f"g.step({NOVA_START} + 262); return 0;")
    burst = page.evaluate(ARENA)
    _fresh(page, level=1, boss=False, seed=7)
    _js(page, "g.step(5400 + 100); return 0;")
    worm = page.evaluate(ARENA)
    _fresh(page, level=3, bossNow=True, seed=7)
    _js(page, "let s = g.state(); while (!(s.boss && s.boss.entered)) s = g.step(5); g.defeatBoss(); g.step(470); return 0;")
    hole = page.evaluate(ARENA)
    assert tunnel["tunnel"] > 0.6 and tunnel["dark"] < 0.1, f"the tunnel fills the view: {tunnel}"
    assert worm["tunnel"] < 0.45 and worm["dark"] > 0.35, f"the level wormhole is a disc on dark space: {worm}"
    assert hole["tunnel"] < 0.1, f"the finale holds no violet-teal tunnel: {hole}"
    assert burst["mean"][2] > burst["mean"][0] + 10, f"the supernova's light is white-blue, not the finale's warm fire: {burst}"


def test_skipping_lands_on_the_arrival_then_starts_the_fight(page) -> None:
    _fresh(page, level=3, seed=7)
    out = _js(page, f"""g.step({NOVA_START} + 320); const tear = g.state().nova.stage; const a1 = g.skipNova(); const a = g.state();
        const b1 = g.skipNova(); const b = g.state(); return {{ tear, a1, a, b1, b, none: g.skipNova() }};""")
    a, b = out["a"], out["b"]
    assert out["tear"] == "tear" and out["a1"] is True
    assert a["nova"]["stage"] == "emerge" and a["map"] == "The Nexus Storm" and a["nova"]["skipped"] == 1 and a["boss"] is None
    assert out["b1"] is True and b["transition"] is False and b["boss"] is not None and b["boss"]["entered"] is False, "the second skip starts the entrance"
    assert out["none"] is False


def test_space_skips_the_passage_but_not_in_its_first_moments(page) -> None:
    _fresh(page, level=3, seed=7)
    _js(page, f"g.step({NOVA_START} + 10); g.start(); return 0;")
    page.locator(HOST + " .ss-canvas").focus()
    page.keyboard.press(" ")
    early = _js(page, "return g.state().nova.stage;")
    _js(page, "g.step(100); return 0;")
    page.keyboard.press(" ")
    first = _js(page, "return g.state().nova.stage;")
    page.keyboard.press("Enter")
    after = _js(page, "const s = g.state(); g.pause('t'); return s;")
    assert early == "swell", "a fire tap as level 3 ends does not skip it"
    assert first == "emerge" and after["boss"] is not None and after["transition"] is False


def test_reduced_motion_shows_one_still_frame_per_stage(browser) -> None:
    ctx, pg, errors = _open(browser, 1440, 900, motion="reduce")
    try:
        _fresh(pg, level=3, seed=7)
        out = _js(pg, f"""let s = g.step({STILL_START} - 1); const pre = s.transition; const seen = {{}};
            while (!s.boss) {{ s = g.step(1); if (!s.nova) continue; g.render(); const k = s.nova.stage;
              const look = JSON.stringify([s.nova.star, s.nova.shock, s.nova.flash, s.nova.ejecta, s.nova.tunnel]);
              (seen[k] = seen[k] || {{ looks: new Set(), tags: g.frameTags(), still: s.nova.still }}).looks.add(look); }}
            const stages = Object.keys(seen); return {{ pre, stages, looks: stages.map(k => seen[k].looks.size), still: stages.map(k => seen[k].still), tags: stages.map(k => seen[k].tags), tick: s.tick }};""")
        assert out["pre"] is False and out["stages"] == ["swell", "burst", "tear", "travel", "emerge"], out["stages"]
        assert out["looks"] == [1] * 5, "each stage is one still frame"
        assert all(out["still"]) and out["tick"] == BOSS_AT, "the boss still arrives on time"
        assert "nova-star" in out["tags"][0] and "shock-ring" in out["tags"][1] and "nova-tunnel" in out["tags"][3]
    finally:
        assert not errors, errors
        ctx.close()


def test_the_ship_cannot_be_hit_during_the_passage(page) -> None:
    _fresh(page, level=3, threats=True, immune=True, seed=7)
    out = _js(page, f"""let s = g.step({NOVA_START}); g.configure({{ immune: false, reset: false }}); s = g.state(); const d0 = s.damageTaken, h0 = s.health; const hits = []; const stages = [];
        while (!s.boss) {{ for (const src of ['shot', 'beam', 'collision', 'asteroid']) hits.push(g.forceHit(src, src === 'asteroid' ? 'large' : src === 'collision' ? 'gunship' : undefined));
          s = g.step(20); if (s.nova) stages.push(s.nova.stage); }}
        return {{ d0, h0, hits, d1: s.damageTaken, h1: s.health, stages: [...new Set(stages)] }};""")
    assert out["stages"] == NOVA_STAGES
    assert not any(out["hits"]), "every hit is refused in transit"
    assert out["d1"] == out["d0"] and out["h1"] == out["h0"]
