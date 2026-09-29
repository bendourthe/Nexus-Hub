"""v4.13.4 Phase 3: canvas painters expose the simulated visual differences."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"


def _probe(tmp_path: Path, body: str):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    source = GUIDE.read_text(encoding="utf-8")
    marker = "  var registry = [];"
    assert source.count(marker) == 1
    copy = tmp_path / "painters.html"
    copy.write_text(
        source.replace(marker, "  window.__paintProbe = function () {\n" + body + "\n  };\n" + marker, 1),
        encoding="utf-8",
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(copy.as_uri() + "#training")
        result = page.evaluate("() => window.__paintProbe()")
        assert not errors, errors
        browser.close()
    return result


def test_archetypes_have_distinct_greyscale_silhouettes(tmp_path):
    masks = _probe(
        tmp_path,
        """
        return ['interceptor','gunship','lancer','drone'].map(function (archetype) {
          var c = document.createElement('canvas'); c.width = c.height = 64;
          var ctx = c.getContext('2d');
          paintEnemy(ctx, {x:32,y:32,r:10,archetype:archetype,look:7,fireIn:60});
          var rgba = ctx.getImageData(0,0,64,64).data, rows = [];
          for (var y=0; y<64; y++) {
            var row = '';
            for (var x=0; x<64; x++) row += rgba[(y*64+x)*4+3] > 80 ? '1' : '0';
            rows.push(row);
          }
          return rows.join('');
        });
        """,
    )
    assert len(set(masks)) == 4


def test_seed_changes_asteroid_outline(tmp_path):
    masks = _probe(
        tmp_path,
        """
        return [7,101].map(function (look) {
          var c = document.createElement('canvas'); c.width = c.height = 80;
          var ctx = c.getContext('2d');
          paintAsteroid(ctx,{x:40,y:40,r:20,face:0,look:look,
            shape:asteroidSilhouette(look,13)});
          var rgba=ctx.getImageData(0,0,80,80).data, mask='';
          for(var i=3;i<rgba.length;i+=4) mask += rgba[i]>80?'1':'0';
          return mask;
        });
        """,
    )
    assert masks[0] != masks[1]


def test_lancer_emitter_brightens_before_fire(tmp_path):
    values = _probe(
        tmp_path,
        """
        return [90,1].map(function (fireIn) {
          var c=document.createElement('canvas'); c.width=c.height=80;
          var ctx=c.getContext('2d');
          paintEnemy(ctx,{x:40,y:40,r:18,archetype:'lancer',look:3,fireIn:fireIn});
          var p=ctx.getImageData(40,58,1,1).data;
          return p[0]+p[1]+p[2];
        });
        """,
    )
    assert values[1] > values[0]


def test_beam_warns_before_active_stroke(tmp_path):
    pixels = _probe(
        tmp_path,
        """
        return [12,0].map(function (tell) {
          var c=document.createElement('canvas'); c.width=c.height=80;
          var ctx=c.getContext('2d');
          paintEnemyShot(ctx,{style:'beam',x:40,y:8,length:60,width:10,tell:tell});
          var p=ctx.getImageData(40,30,1,1).data;
          return p[3];
        });
        """,
    )
    assert pixels[0] < pixels[1]


def test_fixed_damage_invulnerability_keeps_visible_flicker(tmp_path):
    alpha = _probe(
        tmp_path,
        """
        return ['buggy','fixed'].map(function (damageMode) {
          var c=document.createElement('canvas'); c.width=c.height=80;
          var ctx=c.getContext('2d');
          paintShip(ctx,{x:40,y:40,bank:0,thrust:false,invulnerableTicks:30},
            {damageMode:damageMode,tick:2,lifecycle:'paused'});
          return ctx.getImageData(40,30,1,1).data[3];
        });
        """,
    )
    assert alpha[0] == 255
    assert 0 < alpha[1] < alpha[0]
