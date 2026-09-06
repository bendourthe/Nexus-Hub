# Asteroids Training Scenario

## Status

Accepted for v4.4.0 Phase 4 and binding on the Phase 5 Training rebuild.

## Decision Summary

The seeded bug is `wrap-boundary-collision`: a bullet can cross the visibly wrapped part of an asteroid at one edge, but the game compares the bullet only with the asteroid's logical center at the opposite edge, so the hit is not registered. The later feature is `asteroid-splitting`: after the collision fix, a large asteroid hit produces two smaller fragments when the feature is enabled.

The teaching sequence uses the fixed `wrap-boundary` situation to prove the bug, its fix, and the later splitting feature without depending on random play. `ship-impact` remains available for the lives contract, and `play` restores free play after the learner has seen the controlled case.

## Goals

- Make the seeded bug observable within one shot and less than one second.
- Make correct aim undeniable through a visible and announced boundary-contact cue.
- Keep the collision and splitting logic pure enough to test without canvas rendering.
- Give Phase 5 one idempotent state seam that can jump directly to any walkthrough step.
- Make every source excerpt, diff, test, and file-explorer artifact agree with the embedded runtime.

## Non-Goals

- Simulating a full commercial Asteroids ruleset.
- Adding randomness to the two teaching situations.
- Making asteroid splitting part of the first bug-fix phase.
- Treating a canvas animation or a prose claim as verification of game logic.

## World and Entity Contract

The game uses the canvas's fixed logical world of 640 by 360 units and scales that world to its responsive display size. The ship and asteroids wrap. Bullets are short-lived and leave the world at its boundary; this makes the collision defect visible because a shot aimed at a wrapped asteroid silhouette can leave the screen before it ever approaches the asteroid's unwrapped center.

Every moving entity uses logical coordinates, pixels per second, and a collision radius:

```javascript
{
  id: "edge-rock",
  x: 8,
  y: 180,
  vx: 0,
  vy: 0,
  radius: 32,
  size: 2
}
```

The game state has this shape:

```javascript
{
  bounds: { width: 640, height: 360 },
  situation: "wrap-boundary",
  collisionMode: "buggy",
  splittingEnabled: false,
  running: false,
  frame: 0,
  pausedReasons: [],
  score: 0,
  lives: 3,
  ship: { x: 590, y: 180, vx: 0, vy: 0, angle: 0, radius: 10 },
  bullets: [
    { id: "seed-shot", x: 624, y: 180, vx: 80, vy: 0, radius: 3, life: 1.8 }
  ],
  asteroids: [
    { id: "edge-rock", x: 8, y: 180, vx: 0, vy: 0, radius: 32, size: 2 }
  ],
  missedWrapHits: 0,
  bugCue: false,
  cueText: "",
  lastDeltaSeconds: 0
}
```

Valid runtime-control values are deliberately closed:

- `collisionMode`: `buggy` or `fixed`.
- `splittingEnabled`: `false` or `true`.
- `situation`: `wrap-boundary`, `ship-impact`, or `play`.

## Seeded bug

### One-Sentence Explanation

The game draws wrapped asteroid copies but measures bullet distance only to the original center, so a shot visibly crossing an edge copy can be treated as a miss.

### Exact Buggy Code

The seeded version of `src/collision.js` uses direct Euclidean distance. The embedded runtime exposes the same pure function as `window.NexusAsteroids.logic.collides(a, b, bounds, wrapAware)`:

```javascript
export function collides(first, second, bounds, wrapAware) {
  const width = Number(bounds && bounds.width) || 640;
  const height = Number(bounds && bounds.height) || 360;
  const dx = Math.abs(Number(first.x) - Number(second.x)) % width;
  const dy = Math.abs(Number(first.y) - Number(second.y)) % height;
  const radius = (Number(first.radius) || 0) + (Number(second.radius) || 0);
  return dx * dx + dy * dy <= radius * radius;
}
```

The smallest pure regression fixture uses bounds of 100 by 100, a bullet at `(2, 50)` with radius 2, and an asteroid at `(98, 50)` with radius 5. Direct distance reports 96 horizontal units, so `logic.collides` returns `false` when `wrapAware` is `false`. Their wrapped distance is 4 units, so the same function returns `true` when `wrapAware` is `true`.

### Fixed Code

The fix uses the shortest signed distance on each wrapped axis:

```javascript
export function collides(first, second, bounds, wrapAware) {
  const width = Number(bounds && bounds.width) || 640;
  const height = Number(bounds && bounds.height) || 360;
  let dx = Math.abs(Number(first.x) - Number(second.x)) % width;
  let dy = Math.abs(Number(first.y) - Number(second.y)) % height;
  if (wrapAware) {
    dx = Math.min(dx, width - dx);
    dy = Math.min(dy, height - dy);
  }
  const radius = (Number(first.radius) || 0) + (Number(second.radius) || 0);
  return dx * dx + dy * dy <= radius * radius;
}
```

The Training runtime retains both paths so the walkthrough can switch between them without loading a second page. The active decision is exactly:

```javascript
const bounds = { width: WIDTH, height: HEIGHT };
const directHit = collides(shot, rock, bounds, false);
const wrapHit = collides(shot, rock, bounds, true);
const activeHit = state.collisionMode === "fixed" ? wrapHit : directHit;
```

The virtual project shown in Phase 5 does not pretend that the fourth argument fixed the seeded source by itself. Its displayed bug-fix diff adds the wrapped-axis branches, changes the game call from `false` to `true`, and adds the boundary regression test. The final embedded runtime keeps `wrapAware` selectable only because the lesson must reproduce before and after states on demand.

## Deterministic reproduction

The player reproduction takes 3 steps, and the observable cue appears less than 1 second after Fire. The reset also seeds a separate test probe so automated checks can prove the same path without input timing.

### `wrap-boundary` fixture

`reset("wrap-boundary")` restores score 0, lives 3, `collisionMode: "buggy"`, `splittingEnabled: false`, the fixed ship and asteroid positions, and a boundary bullet already placed at the visible contact seam. That seeded bullet is a test probe, not the player's shot: `reset("wrap-boundary")`, `pause("test")`, and `step(1 / 60)` prove both collision modes without depending on input timing. The player-facing Fire control creates a new bullet from the ship's nose through the same seam and collision path.

| Item | Exact state |
|------|-------------|
| World | 640 by 360 logical units |
| Collision oracle | Equivalent to bullet `(2, 50, r=2)` and asteroid `(98, 50, r=5)` in 100 by 100 bounds |
| Runtime reset | Seeds the same boundary relationship at canvas scale |
| Score, lives, frame | 0, 3, 0 |
| Split behavior | Off |

The asteroid renderer draws the original body at `x=8` on the left edge and its wrapped copy at the right edge. Dashed vertical boundary lines make the seam visible. The seeded test probe starts at `x=624`, `y=180` and moves right on the same horizontal line as the wrapped body. A newly fired player bullet follows that same line, so the learner does not steer and cannot reasonably blame the result on bad aim.

The exact keyboard map is Left Arrow or A to rotate left, Right Arrow or D to rotate right, Up Arrow or W to thrust, and Space to fire. The same four actions are exposed as named touch controls. In reduced-motion mode, a directional tap advances exactly one deterministic step so touch-only learners can operate the paused game.

### `ship-impact` fixture

`reset("ship-impact")` places the ship and `impact-rock` together at `(320, 180)`. The first step removes one life, announces `SHIP HIT - life lost`, and respawns the ship at the collision-free point `(320, 270)` with 1.4 seconds of invulnerability. The asteroid remains at `(320, 180)`; advancing past the invulnerability period without input leaves lives at 2, proving that respawn does not create a second automatic loss.

### Reproduce the Bug in Three Steps

1. Press `Reset bug demo`. The reset's seeded test probe immediately demonstrates the seam when autoplay advances; in reduced-motion mode, `Advance one step` advances that probe explicitly.
2. Press Space once, or tap the touch control named `Fire`, to repeat the path with a newly fired player bullet. Do not steer.
3. Within one second after Fire, watch the new bullet cross the wrapped silhouette. The red live cue reads `WRAP HIT MISSED - visual contact, score unchanged`, `bugCue` is `true`, `missedWrapHits` has increased, the asteroid remains, and the score stays at zero.

### Reproduce the Fix in Three Steps

1. Run `pause("walkthrough")`, `reset("wrap-boundary")`, `setCollisionMode("fixed")`, and `setSplittingEnabled(false)`, which is the state reached by the walkthrough's first `/implement` phase. Pausing prevents the seeded test probe from resolving before the player acts.
2. Press Space once, or tap `Fire`. Do not steer.
3. At the same contact point, the success cue reads `WRAP HIT COUNTED +100`, `bugCue` stays `false`, the asteroid is removed, and the score becomes 100.

## Unmistakable Hit-Registration Cue

The cue is teaching instrumentation and never decides the collision outcome. It compares the visible wrapped contact with the active gameplay result:

```javascript
const wrapHit = collides(shot, rock, { width: WIDTH, height: HEIGHT }, true);
const activeHit = collides(
  shot,
  rock,
  { width: WIDTH, height: HEIGHT },
  state.collisionMode === "fixed"
);

if (!activeHit && wrapHit) {
  shot.missedAsteroids[rock.id] = true;
  state.missedWrapHits += 1;
  setCue("miss", "WRAP HIT MISSED - visual contact, score unchanged");
}
```

The canvas draws a red 22-unit ring at `(628, 180)` for the buggy result. The visible `[data-asteroids-bug-cue]` element is visual only. A separate, persistent `[data-asteroids-live-status]` node uses `aria-live="polite"` and `aria-atomic="true"`, remains in the accessibility tree between updates, and announces the same message. The score and asteroid state provide two additional observable checks. A cue that says only `MISS` is not acceptable because it can still be interpreted as player error.

The cue fires once per bullet contact. It does not repeatedly announce on every frame, and it does not add score, remove the asteroid, or split it when the active collision path returns `false`.

## Added feature

The added feature is `asteroid-splitting`.

### Exact Feature Rule

When splitting is enabled, a registered hit on an asteroid with `size > 1` removes the parent and creates exactly two children. Each child has `size - 1`, radius `Math.max(10, parent.radius * 0.58)`, and opposing deterministic velocities. Size 1 asteroids disappear without children.

```javascript
function fragmentsFor(hit, enabled, firstId) {
  if (enabled !== true || hit.size <= 1) return [];
  const radius = Math.max(10, hit.radius * 0.58);
  const speed = 48 + hit.size * 8;
  return [
    asteroid(
      "fragment-" + firstId, hit.x, hit.y,
      radius, hit.size - 1, speed, -speed * 0.62
    ),
    asteroid(
      "fragment-" + (firstId + 1), hit.x, hit.y,
      radius, hit.size - 1, -speed, speed * 0.62
    )
  ];
}

function hitOutcome(hit, splittingEnabled, firstId, wrappedOnly) {
  const fragments = fragmentsFor(hit, splittingEnabled, firstId);
  return {
    scoreDelta: 100,
    fragments,
    cueText: (wrappedOnly ? "WRAP HIT" : "HIT") + " COUNTED +100"
      + (fragments.length ? " - asteroid split" : "")
  };
}
```

The hit-resolution diff is equally small and visible:

```diff
-state.asteroids.splice(ai, 1);
+const outcome = hitOutcome(
+  rock, state.splittingEnabled, nextEntityId, !directHit && wrapHit
+);
+const fragments = outcome.fragments;
+nextEntityId += fragments.length;
+state.asteroids.splice(ai, 1);
+Array.prototype.push.apply(state.asteroids, fragments);
-state.score += 100;
+state.score += outcome.scoreDelta;
+setCue("hit", outcome.cueText);
```

This function contains no randomness. `reset()` restores `nextEntityId` to 10, so the same reset and hit produce the same child IDs, positions, velocities, radii, sizes, and cue text on every replay. Only a wrapped-only registration says `WRAP HIT`; an ordinary direct collision says `HIT COUNTED +100`, so the teaching instrumentation does not mislabel normal gameplay.

### Splitting proof from the same fixture

The feature proof starts from `reset("wrap-boundary")`, then applies `setCollisionMode("fixed")` and selects whether `setSplittingEnabled` receives `false` or `true`. Reusing the same fixture prevents a change in aim, placement, or velocity from being mistaken for the feature.

| Item | Exact state |
|------|-------------|
| Reset | `reset("wrap-boundary")` |
| Collision | `setCollisionMode("fixed")` |
| Before feature | `setSplittingEnabled(false)` |
| After feature | `setSplittingEnabled(true)` |
| Score and lives | 0 and 3 before the shot |

With splitting off, the registered boundary shot removes the parent, adds 100 points, and leaves no asteroids. With splitting on, the same shot removes the size 2 parent and leaves exactly two size 1 fragments. For the 32-unit seeded asteroid, each fragment has radius 18.56. With the reset entity counter, their IDs are `fragment-10` and `fragment-11`; their velocities are `(64, -39.68)` and `(-64, 39.68)`. The success cue reads `WRAP HIT COUNTED +100 - asteroid split` and the live status announces the same result.

The before-feature and after-feature comparison therefore changes three observable facts, not merely a label:

- Before: the large asteroid disappears, the asteroid count becomes zero, and no split cue appears.
- After: the large asteroid disappears, the asteroid count becomes two, and the two smaller outlines move apart.
- In both states: the collision is registered, the score becomes 100, and the parent never remains behind the children.

## Observable states

| State | Canvas result | Cue | Numeric result |
|-------|---------------|-----|----------------|
| Seeded bug | Bullet crosses the right-edge wrapped silhouette; asteroid remains | Red ring and `WRAP HIT MISSED - visual contact, score unchanged` | Score 0, `missedWrapHits` 1, `bugCue` true |
| Collision fixed | Same shot removes the asteroid | `WRAP HIT COUNTED +100` | Score 100, `bugCue` false |
| Splitting absent | Boundary shot removes one size 2 asteroid; empty field remains | `WRAP HIT COUNTED +100` | Asteroid count 0 |
| Splitting added | Boundary shot replaces one size 2 asteroid with two diverging size 1 outlines | `WRAP HIT COUNTED +100 - asteroid split` | Asteroid count 2, both size 1 |

Color is redundant with ring shape, live text, score, and asteroid state. The splitting result visibly contains two moving bodies. Reduced-motion mode shows the same final frames and status text through explicit `Fire` and `Advance one step` actions without autoplay.

## Code seam

The guide exposes this exact API at `window.NexusAsteroids`:

```javascript
window.NexusAsteroids = Object.freeze({
  snapshot: snapshot,
  reset: reset,
  step: step,
  fire: fire,
  setCollisionMode: setCollisionMode,
  setSplittingEnabled: setSplittingEnabled,
  pause: pause,
  resume: resume,
  logic: Object.freeze({
    wrap: wrap,
    collides: collides,
    fragmentsFor: fragmentsFor,
    hitOutcome: hitOutcome
  })
});
```

- `reset(situation)` accepts `wrap-boundary`, `ship-impact`, or `play`; restores the named deterministic fixture; clears score, cue, frame, entities, transient input, and the entity ID counter; and returns the game to its declared baseline. Calling it twice with the same situation produces the same observable state.
- `setCollisionMode(mode)` accepts only `buggy` or `fixed` and changes which `logic.collides` path resolves gameplay hits.
- `setSplittingEnabled(enabled)` stores a strict boolean and changes only hit replacement behavior.
- `fire()` creates exactly one bullet when the current situation is ready and returns the new snapshot. Keyboard Space and the touch `Fire` control call this same function.
- `step(deltaSeconds)` advances the same update function used by `requestAnimationFrame`. It clamps one update to at most 0.05 seconds so the fixed collision cannot tunnel through the deterministic target. Tests and reduced-motion step-through use this seam.
- `pause(reason)` adds the named reason to `pausedReasons`; `resume(reason)` removes only that reason. Multiple pause causes therefore compose instead of resuming the loop prematurely.
- `snapshot()` returns a detached, JSON-safe copy containing `available`, `situation`, bounds, `collisionMode`, `splittingEnabled`, `running`, `frame`, `lastDeltaSeconds`, `pausedReasons`, score, lives, ship, bullets, asteroids, `missedWrapHits`, `bugCue`, and `cueText`. Consumers cannot mutate live state through the snapshot.
- `logic.wrap(value, size)` is the pure coordinate seam used by ship and asteroid movement and tested at both world boundaries.
- `logic.collides(a, b, bounds, wrapAware)` is the pure collision seam used by both the runtime and unit tests.
- `logic.fragmentsFor(asteroid, enabled, firstId)` is the pure splitting seam. It returns no children when splitting is disabled or the parent is size 1, and otherwise returns the same two detached fragments for the same inputs.
- `logic.hitOutcome(asteroid, splittingEnabled, firstId, wrappedOnly)` is the pure registered-hit seam used by gameplay. It always returns a 100-point score delta, delegates fragment creation to `logic.fragmentsFor`, and returns the exact ordinary or wrapped-only cue text.

The loop calls `pause("offscreen")` when the Training game leaves the observer threshold and `pause("document-hidden")` when the page is hidden, then removes only the matching reason when that condition clears. Every pause releases held keyboard and touch movement, so changing tabs cannot leave the ship thrusting or turning. Reduced motion adds `reduced-motion` and never autoplays; a live `matchMedia` change adds or removes that same reason without discarding the user's running intent. If canvas rendering is unavailable, the runtime removes the game root from the tab order, points `aria-describedby` to the state-aware static fallback, hides playable controls, and retains the read-only API state. Phase 5 applies a scene idempotently with the following order, not through synthetic key presses or replaying earlier commands:

```javascript
function applyGameState(game) {
  window.NexusAsteroids.reset(game.situation);
  window.NexusAsteroids.setCollisionMode(game.collisionMode);
  window.NexusAsteroids.setSplittingEnabled(game.splittingEnabled);
}
```

## Phase 5 Scene-State Contract

Every rewritten scene in `guides/website/example/training-scenes.json` carries this field:

```json
"game": {
  "collisionMode": "buggy",
  "splittingEnabled": false,
  "situation": "wrap-boundary"
}
```

The eight command scenes map to game state as follows:

| Scene | Collision | Splitting | Situation | Observable purpose |
|-------|-----------|-----------|-----------|--------------------|
| `describe` | Buggy | Off | `wrap-boundary` | Establish the wrapped world and pure-logic seams |
| `review` | Buggy | Off | `wrap-boundary` | Reproduce and rank the missed boundary hit |
| `plan` | Buggy | Off | `wrap-boundary` | Keep splitting explicitly outside the bug-fix phase |
| `implement` | Fixed | Off | `wrap-boundary` | Make the same shot register and prove the fix |
| `compare` | Fixed | Off | `wrap-boundary` | Show the fixed game before the reference feature is adopted |
| `test` | Fixed | On | `wrap-boundary` | Represent the completed follow-on plan and implementation, then prove splitting |
| `update` | Fixed | On | `play` | Record both shipped behaviors without inventing a release |
| `presentify` | Fixed | On | `play` | Close on the finished game and its evidence trail |

`/compare` remains read-only. It writes the gap analysis and a from-comparison plan; it does not silently edit the game. The existing eight-command lesson stays honest by making the `test` scene state that the same `/plan from-comparison` and `/implement` loop completed between scenes, exactly as the terminal output and cumulative files must state. There is no invented ninth command.

## Phase 5 Virtual Project and Diff Ownership

The file explorer uses these project paths as the authoritative source artifacts:

| Path | Required content |
|------|------------------|
| `src/collision.js` | The direct function before `/implement`, then the `minimumImage` version after it |
| `src/game.js` | Entity update and hit resolution; later modified to apply `hitOutcome` score and fragment results |
| `tests/collision.test.js` | Direct miss fixture, wrapped-hit regression, and unchanged ordinary collision cases |
| `tests/splitting.test.js` | Deterministic two-child, size, radius, ID, and no-child-at-size-1 assertions |
| `docs/v0.1.0/analysis.md` | Map of the real runtime units and input/render boundaries |
| `docs/v0.1.0/review.md` | Ranked wrap-collision finding with the exact `wrap-boundary` evidence |
| `docs/releases/v0.1/plans/fix-wrap-collision.md` | One bug-fix phase, tests, local commit, no splitting |
| `docs/v0.1.0/compare-asteroid-splitting.md` | Reference gap, adoption choice, rejected wholesale dependency, follow-on plan |
| `CHANGELOG.md` | Unreleased collision fix and splitting feature after their proofs exist |
| `asteroids-briefing.html` | Self-contained summary built from the real analysis, review, tests, and changelog |

Phase 5 must derive the displayed diff from the before and after file contents or copy the exact snippets in this document. It must not maintain a third, decorative version of the algorithm. The regression fixture uses the exact 100-unit `logic.collides` proof and the production `reset("wrap-boundary")` state, so prose, source, tests, game state, and visuals cannot drift independently.

## Verification Contract

Pure-logic tests must prove:

- The direct collision function returns `false` for the exact boundary fixture.
- The wrapped collision function returns `true` for that same fixture.
- An ordinary non-boundary hit returns `true` before and after the fix.
- An ordinary miss returns `false` before and after the fix.
- The fixed boundary hit removes the asteroid, increases the score once, and leaves `bugCue` false.
- Splitting off produces no children.
- Splitting on produces exactly two size 1 children with radius 18.56 and stable IDs `fragment-10` and `fragment-11`.
- Size 1 produces no children.
- Reapplying a situation yields a deep-equal snapshot.

Browser tests must prove:

- Space and the touch `Fire` control use the same fire path.
- Reduced-motion taps on Left, Right, and Thrust each advance one step, and a live preference change pauses or resumes through the `reduced-motion` reason.
- The wrap-boundary cue, live status, score, and asteroid state distinguish the bug from bad aim.
- The ship-impact fixture loses exactly one life and remains collision-free after invulnerability expires.
- The first `/implement` transition changes the same shot from an unregistered contact to a registered hit.
- The post-`/compare` follow-on state changes the same wrap-boundary hit from zero fragments to two.
- Jumping directly to any command produces its complete declared game state without replay.
- Re-running a command is idempotent.
- The loop pauses off screen and while the document is hidden.
- Game-focused keys do not scroll the page or invoke guide paging.
- Reduced motion has no autoplay and reaches the same documented final states through `Fire` and `Step`.
- Canvas absence produces a described static state rather than an empty region.

## Acceptance Decision

The scenario is accepted only if `reset("wrap-boundary")` produces the red unregistered-contact cue in buggy mode and a registered hit in fixed mode from the same initial state. The later feature is accepted only if that deterministic hit produces two smaller, stable fragments when enabled and none when disabled. Any implementation that relies on random asteroid placement, manual aim, prose-only state, or a diff that disagrees with the runtime fails this contract.
