"""The v4.13.10 R33 balance harness for the Nexus Defenders engine (code name Sky Sentinel).

It drives the real engine on the Training page deterministically (seed 7, ``SkySentinel.manual(true)``,
``step(n)`` only) and measures, for every ship, with no upgrade and with each weapon upgrade:

- ``single``: sustained damage per second against one target 170 px above the ship (mid-range);
- ``wave``: damage per second against a spread wave of ten targets (five columns 60 px apart, two
  rows 130 px and 230 px above the ship);
- ``reach``: the furthest distance above the ship at which the weapon still deals damage;
- ``bossDps`` and ``boss``: (R40: over a 60 s window only, so ``boss`` is None unless the boss falls in 60 s,
  which the shielded 1,625-point boss never does) the ship is held still at the front of its R33 zone (55 percent of the
  arena height; R35 lets a ship fly the whole arena, and the pilots keep this standoff so the table
  stays comparable), on the centre line the boss sways across, and fires (level 3, the Sentinel form, the ship
  made immune so only the weapon decides; a timed upgrade is renewed every 5 s). ``bossDps`` is the
  damage per second it deals to the boss over the first 60 s; ``boss`` is the seconds to destroy the
  boss, or None when a ship held still does not finish it within 150 s. From below, the boss's
  armour leaves its two upper nodes open only along a narrow outer strip, so a ship that never
  moves finishes it only by chance, and these two values mostly show which weapons reach past the
  shielded core.
- ``hunt``: seconds to destroy the boss with a simple pilot that stays at the front of its zone and
  slides under the lowest live node (then lines its outermost gun up on the open outer edge of an
  upper node, at a standoff of 0, 12, or 24 px, keeping the best of the three, then goes under the
  core), firing all the time. R40: while a shield layer stands, the pilot stays under the boss's centre,
  because the shield bubble is the whole target; the hunt is capped at 200 s. The ship's speed counts here. This is the boss measure the band checks.

Targets are balance dummies (``spawnDummy``): pinned, never firing, never dying. Damage is read
from ``state().dealt``. The band and the rules it checks are in :data:`BAND`; the table and its
reading are in docs/releases/v4/v4.13/development/v4.13.10-game-design.md, "Revision 9 (R33)
balance". Run ``python tests/guides/tools/game_balance.py`` to print the table.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TRAINING = ROOT / "guides" / "website" / "training.html"

SHIPS = ["vanguard", "warden", "specter", "talon", "raptor"]
#: the weapon upgrades; Shield, Repair, Time slow, and Magnet do not touch the weapon
WEAPON_UPGRADES = ["weapon", "spread", "rapid", "pierce", "missiles", "wingman"]
UPGRADE_NAMES = {"weapon": "Twin", "spread": "Spread", "rapid": "Rapid", "pierce": "Pierce",
                 "missiles": "Missiles", "wingman": "Wingman"}

#: The band. Base sustained single-target DPS within 20 percent of the five-ship mean; base
#: wave DPS within 40 percent of its mean (weapons differ most in coverage, by design); the hunt
#: kill time within 35 percent of its mean; each ship's power index (the mean of its single, wave,
#: reach, boss speed (1 / hunt), hull, and speed, each divided by the five-ship mean) within 10
#: percent of 1, so a strength in one axis is paid for in another; and every weapon upgrade moves at
#: least one measured value (single, wave, reach, boss DPS, or hunt time) by at least 15 percent on
#: every ship.
BAND = {"single": 0.20, "wave": 0.40, "hunt": 0.35, "power": 0.10, "upgrade": 0.15}
POWER_AXES = ["single", "wave", "reach", "bossRate", "hull", "speed"]

BALANCE_JS = r"""
(args) => {
  const g = SkySentinel.get('fixed');
  const SINGLE_AT = 170, WARM = 60, WINDOW = 300;
  const setup = (ship, up, extra) => {
    g.configure(Object.assign({ defects: {}, seed: 7, threats: false, level: 1, progression: false, boss: false, immune: true }, extra || {}));
    g.chooseShip(ship); g.start(); g.pause('balance'); g.step(5);
    if (up) { g.dropPowerUp(up); g.step(2); }
    return g.state();
  };
  /* R35: the ship may now fly the whole arena; the boss pilots hold the R33 standoff line (55 percent
     of the arena height, where the old zone ended) so the table stays comparable with R33 */
  const front = () => g.state().world.h * 0.55;
  /* wait out the boss wormhole and the boss's entrance, steering to the standoff line */
  const arrive = () => { let s = g.state(), n = 0; while (!(s.boss && s.boss.entered) && n++ < 20000) { g.input({ up: s.player.y > front() + 3 }); s = g.step(1); } g.input({ up: false }); return s; };
  const run = (ticks) => { g.input({ fire: true }); g.step(WARM); const d0 = g.state().dealt; g.step(ticks); const d = g.state().dealt - d0; g.input({ fire: false }); return d; };
  const single = (ship, up) => { const s = setup(ship, up); g.spawnDummy(s.player.x, s.player.y - SINGLE_AT, 22); return run(WINDOW) / (WINDOW / 60); };
  const wave = (ship, up) => {
    const s = setup(ship, up);
    for (const dy of [130, 230]) for (const dx of [-120, -60, 0, 60, 120]) g.spawnDummy(s.player.x + dx, s.player.y - dy, 22);
    return run(WINDOW) / (WINDOW / 60);
  };
  const reach = (ship, up) => {
    let best = 0;
    for (let d = 60; ; d += 20) {
      const s = setup(ship, up);
      if (s.player.y - d < 12) break;
      g.spawnDummy(s.player.x, s.player.y - d, 22);
      g.input({ fire: true }); g.step(120); g.input({ fire: false });
      if (g.state().dealt > 0) best = d;
    }
    return best;
  };
  const boss = (ship, up) => {
    setup(ship, null, { level: 3, progression: true, boss: true, bossNow: true });
    let s = arrive();
    let t = 0, d0 = s.dealt, dps = null;
    g.input({ fire: true });
    while (s.state !== 'over' && t < 3600) {
      if (up && t % 300 === 0) g.dropPowerUp(up);
      s = g.step(10); t += 10;
      if (t === 3600) dps = (s.dealt - d0) / 60;
    }
    g.input({ fire: false });
    if (dps === null) dps = g.bossPlan().total / (t / 60);
    return { dps, kill: s.victory ? t / 60 : null };
  };
  const hunt1 = (ship, up, standoff) => {
    setup(ship, null, { level: 3, progression: true, boss: true, bossNow: true });
    let s = arrive();
    let t = 0, lanes = [0];
    while (s.state !== 'over' && t < 12000) {
      if (up && t % 300 === 0) g.dropPowerUp(up);
      const geo = g.bossGeometry(), al = s.boss.alive, R = 34 * geo.scale;
      /* the gun lanes, read from the rounds just fired, so the pilot favours no gun layout */
      /* (only the main guns: wingman rounds, missiles, and Spread side shots sit further out) */
      const fresh = s.playerShots.filter(x => x.y > s.player.y - 40 && x.kind !== 'missile' && x.kind !== 'round').map(x => x.x - s.player.x).filter(d => Math.abs(d) <= 16);
      if (fresh.length) lanes = fresh;
      let ax = geo.centre[0];
      /* R40: while a shield layer stands it is the whole target: stay under the centre */
      if (s.boss.shieldsUp > 0) ax = geo.centre[0];
      else if (al[2] || al[3]) ax = geo.nodes[al[2] ? 2 : 3][0];
      /* an upper node is open from below only along its outer edge: put the outermost lane there */
      else if (al[0] || al[1]) ax = al[0] ? geo.nodes[0][0] - R + 3 - standoff - Math.min(...lanes) : geo.nodes[1][0] + R - 3 + standoff - Math.max(...lanes);
      const dx = ax - s.player.x;
      g.input({ fire: true, up: s.player.y > front() + 3, left: dx < -3, right: dx > 3 });
      s = g.step(1); t += 1;
    }
    g.input({ fire: false, up: false, left: false, right: false });
    return s.victory ? t / 60 : null;
  };
  /* three standoffs for the upper nodes (homing rounds need room to curve in); the best counts */
  const hunt = (ship, up) => {
    const times = [0, 12, 24].map(k => hunt1(ship, up, k)).filter(x => x !== null);
    return times.length ? Math.min(...times) : null;
  };
  const out = {};
  for (const ship of args.ships) {
    out[ship] = {};
    for (const up of [null].concat(args.upgrades)) {
      const b = args.boss ? boss(ship, up) : { dps: null, kill: null };
      out[ship][up || 'base'] = { single: single(ship, up), wave: wave(ship, up), reach: reach(ship, up), bossDps: b.dps, boss: b.kill, hunt: args.boss ? hunt(ship, up) : null };
    }
  }
  g.configure({ immune: false }); g.chooseShip('vanguard');
  return out;
}
"""


def measure(page, ships: list[str] | None = None, upgrades: list[str] | None = None, boss: bool = True) -> dict:
    """Measure every ship (or the ones named) on a page that has the Training game loaded."""
    page.evaluate("SkySentinel.manual(true)")
    return page.evaluate(BALANCE_JS, {"ships": ships or SHIPS, "upgrades": WEAPON_UPGRADES if upgrades is None else upgrades, "boss": boss})


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def changed(base: dict, other: dict) -> float:
    """The largest relative change across the four measures (boss time compared as a speed-up)."""
    best = 0.0
    for key in ("single", "wave", "reach", "bossDps"):
        if base.get(key):
            best = max(best, abs((other.get(key) or 0) - base[key]) / base[key])
        elif other.get(key):
            best = max(best, 1.0)
    if base.get("hunt") and other.get("hunt"):
        best = max(best, (base["hunt"] - other["hunt"]) / base["hunt"])
    return best


def power(data: dict, stats: dict) -> dict:
    """Each ship's power index: the mean of its axes, each divided by the five-ship mean."""
    vals = {s: dict(data[s]["base"], hull=stats[s][0], speed=stats[s][1], bossRate=1 / data[s]["base"]["hunt"]) for s in SHIPS}
    means = {a: mean([vals[s][a] for s in SHIPS]) for a in POWER_AXES}
    return {s: mean([vals[s][a] / means[a] for a in POWER_AXES]) for s in SHIPS}


def table(data: dict) -> str:
    """The Markdown table the design doc records."""
    rows = ["| Ship | Hull | Speed | Upgrade | Single DPS | Wave DPS | Reach (px) | Parked boss DPS | Parked kill (s) | Hunt kill (s) |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    stats = data.get("_stats", {})
    for ship in SHIPS:
        if ship not in data:
            continue
        for up, m in data[ship].items():
            hull, speed = stats.get(ship, ("", ""))
            boss = "-" if m["boss"] is None else f"{m['boss']:.1f}"
            name = "none" if up == "base" else UPGRADE_NAMES[up]
            hunt = "-" if m.get("hunt") is None else f"{m['hunt']:.1f}"
            rows.append(f"| {ship.title()} | {hull} | {speed} | {name} | {m['single']:.1f} | {m['wave']:.1f} | {m['reach']} | {m['bossDps']:.2f} | {boss} | {hunt} |")
    return "\n".join(rows)


def main() -> int:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(TRAINING.as_uri() + "#play-fixed")
        page.wait_for_function("window.SkySentinel && SkySentinel.get('fixed')")
        data = measure(page)
        data["_stats"] = {s["id"]: (s["hull"], s["speed"]) for s in page.evaluate("SkySentinel.get('fixed').ships()")}
        browser.close()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=1))
    else:
        print(table(data))
        for key in ("single", "wave", "hunt"):
            vals = {s: data[s]["base"][key] for s in SHIPS}
            m = mean([v for v in vals.values() if v])
            print(key, "mean", round(m, 2), {s: (round(v / m - 1, 3) if v else None) for s, v in vals.items()})
        for s in SHIPS:
            print(s, {u: round(changed(data[s]["base"], data[s][u]), 2) for u in WEAPON_UPGRADES})
        print("power", {k: round(v, 3) for k, v in power(data, data["_stats"]).items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
