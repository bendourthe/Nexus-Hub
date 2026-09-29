"""v4.13.4 Phase 2: spawned entities vary without shifting seeded beats."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"
ARCHETYPES = {"interceptor", "gunship", "lancer", "drone"}


def _sync_playwright():
    """Import Playwright, skipping (or failing under NEXUS_REQUIRE_RENDER=1) when it is absent."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    return sync_playwright


@pytest.fixture()
def page():
    sync_playwright = _sync_playwright()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page(viewport={"width": 1440, "height": 940})
        pg.goto(GUIDE.as_uri() + "#training")
        pg.wait_for_function("window.NexusShooter && window.NexusShooter.logic.spawnSample")
        yield pg
        browser.close()


def _sample(pg, ticks=2400, seed=20260901):
    return pg.evaluate(
        "([t, s]) => window.NexusShooter.logic.spawnSample('play', s, t)", [ticks, seed]
    )


def test_every_archetype_appears(page):
    sample = _sample(page)
    seen = {enemy["archetype"] for enemy in sample["enemies"]}
    assert seen == ARCHETYPES, f"missing archetypes: {ARCHETYPES - seen}"


def test_enemy_radius_varies_by_archetype(page):
    sample = _sample(page)
    radii = {enemy["archetype"]: enemy["r"] for enemy in sample["enemies"]}
    assert len(set(radii.values())) >= 3
    assert radii["drone"] < radii["interceptor"] < radii["gunship"] < radii["lancer"]


def test_spawn_sample_is_deterministic(page):
    assert _sample(page) == _sample(page)


def test_trajectories_differ_by_pattern(page):
    sample = _sample(page)
    drift = {}
    for track in sample["tracks"]:
        drift.setdefault(track["archetype"], []).append(abs(track["xDrift"]))
    avg = {kind: sum(values) / len(values) for kind, values in drift.items()}
    assert avg["lancer"] < avg["gunship"]
    assert avg["drone"] > avg["lancer"]


def test_projectile_styles_are_distinct(page):
    sample = _sample(page)
    styles = {shot["style"] for shot in sample["shots"]}
    assert {"bolt", "spread", "beam"} <= styles


def test_asteroids_drift_laterally(page):
    sample = _sample(page)
    vxs = [rock["vx"] for rock in sample["asteroids"]]
    assert any(abs(value) > 4 for value in vxs)


def test_same_radius_asteroids_differ_in_silhouette(page):
    sample = _sample(page, ticks=4800)
    buckets = {}
    for rock in sample["asteroids"]:
        buckets.setdefault(round(rock["r"]), []).append(tuple(rock["shape"]))
    repeated = {radius: shapes for radius, shapes in buckets.items() if len(shapes) >= 2}
    assert repeated
    for radius, shapes in repeated.items():
        assert len(set(shapes)) > 1, f"all asteroids of radius {radius} share one silhouette"


def test_lancers_become_more_common_after_early_wave(page):
    early = _sample(page, ticks=900)["enemies"]
    late = _sample(page, ticks=2400)["enemies"][len(early) :]
    early_share = sum(enemy["archetype"] == "lancer" for enemy in early) / len(early)
    late_share = sum(enemy["archetype"] == "lancer" for enemy in late) / len(late)
    assert late_share > early_share


def _run_model_probe(tmp_path, body):
    sync_playwright = _sync_playwright()

    source = GUIDE.read_text(encoding="utf-8")
    marker = "  var registry = [];"
    assert source.count(marker) == 1
    guide_copy = tmp_path / "model-probe.html"
    guide_copy.write_text(
        source.replace(marker, "  window.__modelProbe = function () {\n" + body + "\n  };\n" + marker, 1),
        encoding="utf-8",
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page()
        errors: list[str] = []
        pg.on("pageerror", lambda error: errors.append(str(error)))
        pg.goto(guide_copy.as_uri() + "#training")
        result = pg.evaluate("() => window.__modelProbe()")
        assert not errors, f"page errors: {errors}"
        browser.close()
    return result


def test_beam_tell_is_safe_active_interval_hits_and_expiry_removes(tmp_path):
    result = _run_model_probe(
        tmp_path,
        """
        function state() {
          var s = fixtureState('play', DEFAULT_SEED);
          s.lifecycle = 'running'; s.damageMode = 'fixed';
          s.enemyShots = [{id:'beam-test',style:'beam',sourceId:'none',x:320,y:300,
            r:0,width:10,length:180,vy:1,tell:2,active:2,resolved:false}];
          return s;
        }
        var s = state();
        movementStep(s); collisionStep(s);
        var tellSafe = s.lives === 3;
        movementStep(s); collisionStep(s);
        var activeHits = s.lives === 2;
        var expired = state(); expired.enemyShots[0].tell = 0; expired.enemyShots[0].active = 1;
        movementStep(expired); collisionStep(expired); cleanupStep(expired);
        return {tellSafe:tellSafe,activeHits:activeHits,
          expirySafe:expired.lives === 3 && expired.enemyShots.length === 0};
        """,
    )
    assert result == {"tellSafe": True, "activeHits": True, "expirySafe": True}


def test_large_asteroid_fragments_with_distinct_look_seeds(tmp_path):
    result = _run_model_probe(
        tmp_path,
        """
        var s = fixtureState('play', DEFAULT_SEED);
        s.asteroids = [{id:'parent',x:180,y:200,r:20,vx:0,vy:75,tier:2,
          spin:0,face:0,look:1,shape:asteroidSilhouette(1,13),resolved:false}];
        s.playerShots = [{id:'player-shot',x:180,y:200,r:4,vy:-240,life:1,resolved:false}];
        collisionStep(s); cleanupStep(s);
        return {tiers:s.asteroids.map(function(a){return a.tier;}),
          looks:s.asteroids.map(function(a){return a.look;})};
        """,
    )
    assert result["tiers"] == [1, 1]
    assert len(set(result["looks"])) == 2
