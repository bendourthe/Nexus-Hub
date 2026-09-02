# Arcade-Shooter Scenario -- the v4.4.1 Training game contract

**Plan**: [v4.4.1-guide-visual-and-arcade-rebuild.md](../plans/v4.4.1-guide-visual-and-arcade-rebuild.md), Phase 5
**Supersedes**: [`asteroids-scenario.md`](asteroids-scenario.md), which is preserved unchanged as the v4.4.0 historical contract
**Status**: authoritative for v4.4.1 from Phase 5 onward

This document is the single source of truth for the Training game: the engine in
`guides/website/nexus-hub-guide.html`, the scene data in
`guides/website/example/training-scenes.json` (and its verified inline copy), and the
suite in `tests/guides/test_arcade_shooter_game.py` all implement THIS contract. A
behavior in code that is not in this document is a defect in one of the two.

## 1. World and simulation

| Constant | Value | Note |
|---|---:|---|
| Logical world | 360 x 480 | portrait 3:4; painting scales, world never does |
| Fixed tick | 1/60 s | accumulator-driven; a paint frame may run 0..N ticks |
| Default seed | 20260901 | every fixture may override; equal seed + equal inputs = deep-equal snapshots |
| Starting lives | 3 | |
| Invulnerability window | 90 ticks | fixed damage mode only, after a non-fatal hit |
| Player spawn | (180, 440) | bottom centre |
| Player horizontal speed | 160 px/s | Left/Right or A/D |
| Player vertical speed | 120 px/s | Up/Down or W/S, ONLY when the feature is enabled |
| Lower play band | y in [360, 460] | vertical movement clamps here after the feature |
| Player shot | vy -240 px/s, r 3, 2.5 s life | fires upward from the nose |
| Enemy shot | vy +150 px/s, r 3.5 | travels straight down |
| Enemy descent | vy in [55, 80] px/s seeded | ships enter at y = -14 and move DOWN |
| Asteroid speeds | vy 60 or 105 px/s | exactly two seeded tiers, both downward |
| Asteroid radius | 12..22 seeded | |
| Score per destroyed target | +100 | one increment per resolution, deterministic |

The random stream is one mulberry32-style generator seeded at reset. Anything random
(spawn times, x positions, speeds, radii) draws from that stream in a fixed order, which
is what makes two runs with one seed identical.

## 2. Lifecycle and pause composition

States: `idle -> running <-> paused -> destroyed`, plus `reset`/`restart` from anywhere.

- **idle**: the game renders its first frame behind a real `Click to start` button. Ticks
  do not advance, entities do not move, and page-level arrow/Space behavior is untouched.
- **running**: the accumulator advances the world at the fixed tick.
- **paused**: a SET of reasons, not a boolean: `manual`, `blur`, `hidden`, `offscreen`,
  `reduced-motion`. Resuming one reason never clears another; the game runs only when the
  set is empty. Manual stepping (`step()`) is legal while paused and advances exactly one tick.
- **destroyed**: TERMINAL. `pause`/`resume` can neither enter nor leave it; a stale frame
  or held key cannot mutate it (each reset bumps a generation counter that stale callbacks
  check). Only `reset(fixture?)` or `restart()` creates a new playable generation.

Update order inside one tick, always: **input, spawn, movement, collision, cleanup, render**.

## 3. Damage rules

| Mode | Enemy projectile hits player | Asteroid touches player |
|---|---|---|
| `buggy` | FIRST hit enters terminal `destroyed` immediately -- lives read 3 and then the ship is gone, which is the seeded teaching defect | one explosion, terminal `destroyed` |
| `fixed` | lives decrement 3 -> 2 -> 1 -> 0 with a 90-tick invulnerability window between hits; the third hit spawns exactly one explosion and enters `destroyed` | one explosion, terminal `destroyed`, regardless of lives or invulnerability |

Collision precedence within one tick: asteroid/player fatality resolves first, then enemy
projectile/player, then player projectile/target. An entity resolved once this tick cannot
resolve again (no double hit, no double score, no double life loss). A player projectile
destroys exactly one enemy OR one asteroid, then is consumed.

## 4. Feature flag

`verticalMovementEnabled` defaults to `false`. While false, Up/Down input is read but
IGNORED: the player's y never changes. Once true, vertical input moves the ship at
120 px/s, clamped to the lower play band. The flag never adds a ninth scene: `/compare`
records its follow-on plan and implement inside the comparison step, as v4.4.0 did for
splitting.

## 5. Fixtures

| Fixture | Purpose | Contents |
|---|---|---|
| `enemy-hit` | prove the damage rule | no autonomous spawning; one enemy at (180, 80) descending slowly and re-firing on a deterministic cadence (first re-fire at tick 130, then every 90..150 seeded ticks), plus one pre-placed enemy shot at (180, 240) falling at 150 px/s. The pre-placed shot lands around tick 75; in fixed mode the re-fires land after each invulnerability window expires, so the fixture demonstrates the full 3 -> 2 -> 1 -> 0 sequence |
| `asteroid-hit` | prove asteroid fatality | no autonomous spawning; one radius-16 asteroid at (180, 200) falling at 105 px/s into the stationary player |
| `play` | the full game | seeded autonomous enemy and asteroid spawning, both asteroid speed tiers present |

## 6. Scene mapping -- the same eight command IDs

| Scene | damageMode | verticalMovementEnabled | fixture |
|---|---|---|---|
| `describe` | buggy | false | enemy-hit |
| `review` | buggy | false | enemy-hit |
| `plan` | buggy | false | enemy-hit |
| `implement` | **fixed** | false | enemy-hit |
| `compare` | fixed | **true** | play |
| `test` | fixed | true | play |
| `update` | fixed | true | play |
| `presentify` | fixed | true | play |

`/implement` fixes the damage handling; `/compare` adopts vertical movement through its
recorded follow-on plan/implement. Earlier scenes demonstrate the bug; later scenes keep
both corrections. The scene JSON carries exactly these three fields under `game`; Phase 6
owns rewriting the surrounding prose, simulated files, and artifacts to the shooter story.

## 7. Public browser API

`window.NexusShooter` is frozen and stable for tests and the Training runtime:

| Member | Contract |
|---|---|
| `snapshot()` | returns a DEEP-FROZEN detached object: `seed, tick, generation, lifecycle, lives, score, damageMode, verticalMovementEnabled, pauseReasons` (sorted array), `player {x, y, invulnerableTicks}`, and deterministic entity projections `enemies[], enemyShots[], asteroids[], playerShots[], explosions[]` (each `{id, x, y, r, vy}` rounded to 3 decimals) |
| `reset(fixture?)` | new generation from the named fixture (default: the current one); returns a snapshot |
| `restart()` | `reset()` plus immediate `running` |
| `start()` | leaves `idle`; no-op elsewhere |
| `step()` | advances exactly one tick even while paused; refused (no-op) in `idle` and `destroyed` |
| `pause(reason)` / `resume(reason)` | add/remove one composable reason; invalid reasons are rejected without state change; cannot enter or leave `destroyed` |
| `setDamageMode(mode)` | `'buggy'` or `'fixed'`; anything else rejected without state change |
| `setVerticalMovementEnabled(v)` | boolean coerced strictly; non-boolean rejected |
| `input(name, pressed)` | `'left','right','up','down','fire'`; unknown names rejected |
| `logic` | frozen pure seams for unit assertions: `collides(a, b)`, `damageOutcome(mode, lives)` |

Invalid seeds, fixtures, deltas, or inputs are rejected or normalized deterministically
and never corrupt current state; the rejection is observable (`snapshot()` unchanged).

## 8. Rendering, HUD, and accessibility

- All art is procedural canvas painting: layered ship hull with cockpit and wing detail,
  engine-trail particles, irregular cratered asteroids, glowing projectiles, particle
  explosions, and a decorative downward starfield. No placeholder primitive stands alone.
- The persistent HUD lives OUTSIDE the canvas: score, lives (authoritative state, shown
  `3, 2, 1, 0`), damage-mode tag, and lifecycle. An `aria-live="polite"` status announces
  lives and lifecycle CHANGES only, never per-frame.
- A real overlay `<button>` labelled `Click to start` owns activation (pointer, Enter, or
  Space). Before it, the page keeps its own arrow/Space behavior.
- While the focused game is active: Left/Right or A/D move, Space fires, Up/Down or W/S
  obey the feature flag. Escape pauses, clears held keys, releases key ownership, and
  moves focus to the visible Resume control. Modified shortcuts (Ctrl/Alt/Meta) are never
  intercepted. Labelled touch controls mirror every key.
- Reduced motion: no autonomous ticks, stars, or spawns; `Advance one step` performs one
  deterministic tick while the `reduced-motion` pause reason stays set.
- Canvas unavailable: the region shows a text fallback stating lives, damage mode, and
  feature state, and removes unusable canvas controls from the Tab order.
- Resize and devicePixelRatio changes repaint; they never touch world state.

## 9. Migration notes (Phase 5 scope only)

Phase 5 renames the public seam (`NexusAsteroids` -> `NexusShooter`), replaces the wrap
and splitting setters with `setDamageMode` / `setVerticalMovementEnabled`, migrates the
per-scene `game` fields in BOTH copies of the scene data to the section 6 schema, and
keeps all eight Training routes initializing through the migrated `configureGame`. The
scene prose, simulated files, artifacts, gates, and takeaways still tell the v4.4.0
Asteroids story; rewriting them is Phase 6's deliverable, not Phase 5's.
