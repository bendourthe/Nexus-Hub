# v4.13.1 Training tab rebuild - design

Design spec for the complete rebuild of the Training tab in `guides/website/nexus-hub-guide.html`. Covers two subsystems: a production-quality canvas arcade engine (instance-per-element factory, enemy archetypes, procedural asteroids, futuristic player ship, wide device-pixel-ratio arena) and a narrative restructure (presentation mode removed, single-slide deck replaced by seven headed sections walking the Nexus-Hub command loop). Read this before implementing the v4.13.1 plan, and when changing anything under the `nht-` or `nag-` prefixes. Key topics: arcade factory refactor, RNG stream discipline, the `damageOutcome` invariant, the scene data model, presentation-mode removal, and accessibility carryover.

## Status

Approved in brainstorming on 2026-09-22. Implementation is governed by `docs/releases/v4/v4.13/plans/v4.13.1-guide-training-rebuild.md`.

## Context: what the Training tab is today

The Training tab is not a static page. It is a data-driven single-slide deck with a presentation mode:

- One slide shell in markup, carrying empty placeholders that the driver fills: `data-nht="title"`, `"intent"`, `"command"`, `"output"`, `"artifact-path"`, `"gate-status"`, and others.
- A JSON block `#nh-training-scenes` of about 17 KB, with an `initial` object and 8 `scenes`. Each scene carries `id`, `command`, `title`, `intent`, `output`, `tools`, `artifact`, `gate`, `files`, `focus_file`, `game`, `stage`, and `takeaway`.
- A presentation mode keyed on `.nht.is-present`, comprising about 76 CSS rules plus a fullscreen entry and exit path (`inPresent`, `finishPresent`, and a `fullscreenchange` listener). This is the source of the fixed three-column grid and of the layout boundaries this rebuild removes.
- An arcade engine of roughly 875 lines. It is deterministic by design: `mulberry32` seeding, two separate RNG streams, three named fixtures (`enemy-hit`, `asteroid-hit`, `play`), and an "Advance one step" control.
- A training driver of roughly 600 lines that swaps scene data into the single shell and maintains a cumulative file explorer.

The 8 current scenes are `/describe full`, `/review`, `/plan feature`, `/implement`, `/compare`, `/test unit`, `/update changelog`, and `/presentify`.

## Goals

- Replace the deck and its presentation mode with plainly headed sections, one per step of the command loop, so the page reads top to bottom with no layout boundaries imposed by a slide frame.
- Raise the arcade game to production quality: a futuristic player ship, asteroids that differ in size, speed, trajectory and silhouette, and enemy ships that differ in style, size, speed, trajectory and projectile behavior.
- Keep every section interactive. The runnable terminal, the tools panel, the artifact and gate panel, and the cumulative file explorer all survive the restructure.
- Keep the seeded damage bug reproducible, so the teaching narrative still has a defect it can point at on demand.

## Non-goals

- No change to any other tab. Home, Foundations, Cheatsheets and the shared shell are out of scope.
- No change to the commands themselves, to `catalog/`, or to any registry under `data/`.
- No new third-party dependency. The guide is a single self-contained HTML file and stays that way.

## Decisions

These were settled during brainstorming and are not reopened during implementation.

| # | Decision | Rationale |
|---|---|---|
| D1 | Every section stays interactive | The page is a demonstration, not a description. The existing driver is refitted rather than rewritten. |
| D2 | Random free play, seeded bug demo | Procedural variety in normal play, and a fixed seed for the bug demo so the first-hit defect reproduces on cue and step-through keeps its teaching value. |
| D3 | Game built before narrative | The game's look is the headline and the part most likely to need visual iteration. The sections are then built around a finished artifact. |
| D4 | Plan and implement content authored from real repository conventions | The section text mirrors how `/plan` and `/implement` genuinely behave here, including tier and effort vocabulary and the release gates. |
| D5 | `/test` and `/update changelog` fold into the implement final phase; `/presentify` survives as a second bonus | Matches the requested loop narrative while keeping the briefing step reachable. |
| D6 | Wide full-width arena at device pixel ratio | A narrow portrait column hides trajectory variety, which is the entire point of the archetypes. |
| D7 | Spec, then phased plan, then phase-by-phase implementation | Matches this repository's documented plan lifecycle and gives review gates before the diff grows large. |
| D8 | Version slot v4.13.1 | Follows the v4.4.1 through v4.4.6 precedent of shipping guide rebuilds as patch versions. No queued plan needs renumbering, since every queued plan already carries a higher number. |

## Subsystem A: the arcade engine

### A1. Instance-per-element factory

The engine currently resolves its element with `document.querySelector("[data-arcade-game]")`, singular, and holds `state`, `held`, `generation`, `accumulator` and `canvas` at module scope. The rebuild needs three playable instances on one page, so the engine becomes a factory.

- `createArcade(rootElement)` returns an instance object owning its own state, input map, RNG streams, canvas context and animation handle.
- A registry iterates every `[data-arcade-game]` element and constructs one instance each.
- Module scope retains only pure helpers: `mulberry32`, `collides`, `damageOutcome`, the archetype tables, and the painters.
- Each instance animates only while it is in the viewport and not paused. The existing pause-on-leave behavior generalizes to a per-instance `IntersectionObserver`, so three canvases never animate at once off-screen.

This is the largest non-visual change in the rebuild, and every other item in Subsystem A depends on it.

### A2. The `damageOutcome` invariant

`damageOutcome(mode, lives)` is a pure function and is the entire seeded bug. The whole training narrative hangs off it. The rebuild routes around it and does not alter its signature or its behavior. Any change here invalidates the teaching content in sections 2 through 5.

### A3. RNG stream discipline

The engine already splits one seed into two streams, with an existing comment recording why: `rng` drives the teaching beats (stars, the pre-placed enemy cadence, the play fixture timers) and `rngSpawn` drives spawn decisions, so adding spawns cannot shift a draw the beats depend on.

All new variety draws from `rngSpawn`, never from `Math.random`. This is what lets D2 hold with no new determinism machinery: free play looks procedural, and the seeded fixtures stay reproducible.

### A4. Enemy archetypes

A data table replaces the single enemy shape. Each archetype declares its own painter, hitbox radius, speed band, movement pattern and projectile behavior.

| Archetype | Size | Movement | Projectile |
|---|---|---|---|
| Interceptor | small | fast diagonal darts, re-aims on a timer | rapid single bolts |
| Gunship | medium | steady descent with lateral strafing | three-way spread |
| Lancer | large | slow and deliberate, holds a firing line | charged beam with a visible tell |
| Drone | tiny | erratic weave, never fires | rams the player |

Archetype selection at spawn draws from `rngSpawn`, weighted so that early waves favor Interceptors and later waves mix in Lancers.

### A5. Per-entity look seed

Asteroid silhouettes are currently derived from the radius itself, via `0.82 + 0.18 * sin(k * 2.7 + a.r)`. Two rocks of equal radius are therefore pixel-identical, which is why the field reads as repetitive.

Each asteroid and enemy stores a `look` seed captured at spawn. Silhouette vertices, plating, crater placement and panel lines all derive from that seed, so appearance is stable across an entity's lifetime and differs between entities of the same size. Asteroids additionally gain an independent `vx` drift, an independent spin rate, and three size classes, where the two larger classes fragment into smaller ones when destroyed.

### A6. Player ship

Rebuilt as a layered futuristic hull: a plated fuselage with panel seams, a glowing intake, an afterburner whose length and color respond to thrust, and a banking roll when strafing. The existing invulnerability flicker after a hit is preserved, since it is the visible proof that the fixed damage mode works.

### A7. Arena and resolution

The canvas moves from 360x480 logical pixels in a narrow column to a full-width stage at roughly 16:10, with a backing store scaled to `devicePixelRatio` and a CSS size that stays fluid. Drawing coordinates stay in logical units, so collision math and the fixtures are unaffected by the resolution change.

## Subsystem B: the narrative

### B1. Removals

- The roughly 76 `.nht.is-present` CSS rules.
- The fullscreen button `#nhtPresent` and its `data-nht="exit-present"` binding.
- `inPresent`, `finishPresent`, the `fullscreenchange` listener, and the fallback exit path.
- Deck navigation: the previous and next controls, and the step-number affordance that only made sense inside a deck.

### B2. Section structure

The single slide shell becomes seven stacked sections, each with its own `h2` and its own bound widgets.

| # | Heading intent | Commands | Game instance |
|---|---|---|---|
| 1 | The game: what it is, how to play, what is broken | none | buggy: `damageMode: "buggy"`, vertical movement off |
| 2 | Map it, then turn the symptom into a finding | `/describe`, `/review` | none |
| 3 | Make the repair planned and testable | `/plan` | none |
| 4 | Run the whole plan in one command | `/implement` | none |
| 5 | The fixed game | none | fixed: `damageMode: "fixed"`, vertical movement off |
| 6 | Bonus: add a feature the same way | `/compare` | fixed plus vertical movement enabled |
| 7 | Bonus: turn the evidence into a briefing | `/presentify` | none |

Section 3 renders a plan summary: every phase in order, each with its recommended model tier (`frontier`, `strong`, `standard`, `fast`) and its effort level. Section 4 renders the final-phase sequence explicitly: automatic review, known-gaps reconciliation, tests built and iterated until green, then the `/update release` sequence and what that entails.

### B3. Scene data model

`#nh-training-scenes` is rewritten from 8 deck scenes to 7 section records. Changes to the per-record shape:

- `command` becomes `commands`, an array, so section 2 can carry both `/describe` and `/review`.
- A new optional `phases` array on the `/plan` record, each entry carrying `name`, `tier`, `effort` and `summary`, so the plan summary renders from data rather than from prose.
- A new optional `finalPhase` object on the `/implement` record, carrying the ordered gate beats.
- `stage` is dropped. It existed to position content inside the presentation grid and has no meaning once sections stack.

### B4. File explorer

The cumulative file tree survives. Its accumulation key moves from deck step index to section index, so scrolling forward reveals files as the loop produces them, and scrolling back does not destroy state.

## Accessibility and motion

These are existing behaviors that the rebuild carries over rather than rediscovers.

- A per-instance `aria-label` on each canvas, and the visually hidden `aria-live` region that announces lives and lifecycle changes. The region stays boot-silent: page load is not a change.
- Touch control buttons for left, right, up, down and fire, with accurate labels per instance.
- `prefers-reduced-motion` support. With motion reduced, each instance renders a settled frame rather than animating, and the new archetype and asteroid variety must still be visible in that static frame.
- Keyboard operation: the start control is reachable and operable by keyboard, and leaving the arena pauses.
- Every heading is a real `h2` in document order with no level skipping, so the page outline matches the visible structure.

## Testing

- Reuse the repository's existing guide checks under `tests/verification/`, extending the fixture set to cover the new section structure.
- Headless render assertions: seven sections present in order, each with an `h2`; zero `.nht.is-present` rules remaining; three arcade instances constructed; no console errors.
- Determinism check: the seeded bug fixture produces an identical entity sequence across two runs with the same seed, proving D2 still holds after the archetype work.
- Invariant check: `damageOutcome` behavior is unchanged for both modes, asserted directly.
- Responsive check: no horizontal overflow at 420 px, per the repository's responsive-layout rule.
- Visual self-verification: every phase renders the edited region headless and inspects the capture, per `catalog/rules/html/visual-self-verification.md`.

## Risks

- The factory refactor touches the whole engine at once. Mitigation: it is its own phase, landed and verified before any visual work begins, so a regression is attributable to it.
- Three animating canvases could cost frame budget on weak hardware. Mitigation: per-instance viewport gating, and in practice only one instance is visible at a time given section spacing.
- Rewriting the scene JSON risks losing content that is currently expressed only there. Mitigation: the old JSON is preserved in the phase evidence before the rewrite.
- A wider arena changes the coordinate space the fixtures were tuned against. Mitigation: fixtures are expressed in logical units and are re-verified in the same phase that changes the arena.

## Alternatives considered

- **Keep presentation mode and add headings inside it.** Rejected: the layout boundaries at issue come from the presentation grid itself, so retaining it does not deliver the request.
- **A fully random engine with no fixtures.** Rejected: the bug becomes intermittent and "Advance one step" loses its teaching value. D2 keeps both properties.
- **Static illustrated panels instead of live terminals.** Rejected under D1: it would turn a demonstration into documentation.
- **One game instance toggled between states by the narrative.** Rejected: sections 1, 5 and 6 need to be comparable as the reader scrolls, and a single toggled instance forces the reader to lose the buggy behavior in order to see the fixed one.
- **Generating the plan section from a real plan file under `docs/releases/`.** Rejected under D4: it ties the training page to an unrelated plan and drifts as that plan changes.
