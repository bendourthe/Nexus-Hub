# Session History - Presentify Slide Navigation Phase 3: Animation Adaptation Grammar

**Date**: 2026-08-22
**Branch**: `feat/presentify-slide-navigation`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.3-presentify-slide-navigation.md`](../../plans/v3.18.3-presentify-slide-navigation.md)
**Phase**: 3 - Animation adaptation grammar
**Environment**: Windows 11, Git Bash and PowerShell, Python 3.12.10, Node (syntax gate), pytest, Playwright headless Chromium; GNU Make unavailable, so `make validate` was executed as its constituent commands
**Outcome**: The three-way slide-mode animation grammar exists in `interactive-features.md` with a 14-row mapping table exhaustive over every pattern the reference names; `scroll-scrub.md` carries the "Cinematic without scroll" section (fragment-stepped camera, ambient holds, trigger-only delta); and `scroll-scrub-engine.js` gained the `driver: 'scroll' | 'step'` abstraction with a `goTo` API - during which one real engine bug (the initial layer never painting under the step driver) was found by the render checks and fixed. A three-slide demo deck passes 24 real headless checks across all three grammar classes, reduced motion, and the step driver.

## 1. Starting State

- **Starting commit**: `db898fb5` (Phase 2, same branch)
- **Worktree**: clean
- **Model routing**: the plan records `frontier / high`; the session is on the frontier tier, so the pre-flight agreed and no switch was made.

## 2. What Was Implemented

### 3.1 - The grammar in `interactive-features.md`

A "Slide-mode animation grammar (nav=slides)" subsection between the scrollytelling catalog and the design-direction section, plus a one-line tie-in from the interactivity spectrum's mapping summary. Its content:

- **Three trigger classes, and only three** (an author never invents a fourth): entry-triggered (once per activation, with the binary re-entry rule - re-run only if idempotent AND non-data-bearing; counters count up once and render settled thereafter), fragment-stepped (each discrete state one `data-fragment` step per the Phase 2 contract, with the scrollytelling STATE TABLE requirement carried over unchanged), and ambient loop (atmosphere-class only: running while the slide is active, paused when inactive, disabled entirely under reduced motion).
- **The data-bearing prohibition as a binary rule**: ambient conversion applies only to non-data-bearing, non-narrative animation; anything whose motion carries meaning is class 1 or 2, never a loop, because looping data motion fabricates the impression of live data. Amplitude discipline: background-layer subtlety, at most one ambient system per slide.
- **A 14-row mapping table** covering the five scrollytelling catalog patterns, the balanced-layer patterns (reveals, active-nav/progress bar, counters, micro-transitions), the budget's lightbox, hover/focus affordances, expand/collapse (bounded by the overflow rule: expansion that would overflow the stage becomes a declared scrollable region or a fragment), marquee/atmospheric texture, and the cinematic scrubbed stage (pointing at scroll-scrub.md's new section). The table's own claim - every pattern named in the reference has a row - was made true, not aspirational: rows for patterns 3 and 6 were added when a cross-check showed the claim exceeded the coverage.
- **The fallback rule (binary)**: an unmapped pattern defaults to entry-triggered-once (the class that can never fabricate data or loop a narrative) with a design-record note.
- **Restrained needs no adaptation** (it never had scroll-triggered motion), and the reduced-motion posture restated as one rule set: loops removed, fragment transitions instant, entry reveals visible-immediately.

### 3.2 - Cinematic without scroll (`scroll-scrub.md` section 8 + the engine)

- Section 8 states the trigger-only delta explicitly: keys instead of scroll position, with the size/cost gate, asset boundary, seam/pacing protocol, stills-only fallback, and accessibility floor applying unchanged and not restated. Each camera keyframe is one fragment; the transition tween uses the easing the scrub curve would have applied; holds carry at most one background-amplitude ambient drift (none under reduced motion); interrupted transitions fast-forward to the target keyframe; an autoplay refusal degrades to the poster still, never a black stage. One verification item added; the Related listing updated.
- **The engine did not support an external driver**, so per the plan's if-not clause it was extended: `driver: 'scroll'` (default, byte-for-byte the old behavior) attaches the scroll/resize listeners; `driver: 'step'` attaches none and exposes `goTo(sectionIndex, progress, opts)` - tween with ease-in-out-cubic over `stepDuration` (default 600ms), instant under `opts.instant` or reduced motion, fast-forward retargeting from the currently-shown state on interruption, section crossings handed to the existing seam crossfade, everything downstream (`_seek`, linger, video seek-coalescing, stills path) shared. Input ownership deliberately stays with the slide runtime - the engine never listens for keys, so the disengage-inside-interactive-regions rule cannot be violated by the stage. The header documents both drivers with a usage sketch.

### 3.3 - Demo deck and render checks

A three-slide demo deck (scratchpad test artifact) exercising one grammar class per slide: an entry-triggered reveal + count-up counter, a fragment-stepped three-bar chart build, and an ambient gradient-drift background gated on `.slide-active` via `animation-play-state`. The Playwright harness (`verify_grammar.py`) asserts **24 real checks**: arrows step fragments before slides; the counter counts up on first activation, shows its final value on re-entry, and renders settled immediately under reduced motion; the ambient loop runs only while its slide is active, is paused before and after, sits at background amplitude, and is removed (not slowed) under reduced motion; slide transitions are instant cuts under reduced motion; and the engine step driver mounts with layer 0 painted, tweens the stills path, crosses sections through the seam layers, lands instant jumps settled, and settles an interrupted tween at the LAST target.

## 3. Troubleshooting (three failures on the first run, each triaged to its true cause)

1. **A real engine bug, caught by the render check**: under the step driver, the initial `goTo(0, 0)` at mount never painted layer 0. `_shown.index` initializes to 0, so `crossing` was false, while `this.active` was still -1 - the class toggle was skipped and no layer carried `ss-on`. The scroll driver never hits this because `_update` compares against `active`. Fix: gate the toggle on `crossing || this.active !== index`, with a comment naming the mount case. This is the class of defect the plan's "verify in a local render" step exists to catch - `node --check` was green the whole time.
2. **A test-harness race**: a fixed 950ms sleep raced the 800ms count-up animation and read 1150 mid-count. Fixed by polling (`wait_for_function`) for the settled value - the same settle-then-assert rule Phase 2 recorded for screenshots, now applied to numeric animation.
3. **A CSSOM serialization false negative**: the interrupted-tween check expected the literal `1.0000` in the transform, but reading `style.transform` back re-serializes `scale(1.0000)` as `scale(1)`. The settled end state was correct; the assertion string was wrong. Fixed to assert exact equality with the serialized form.

One self-inflicted tautology (`or True` in a hedged check) was noticed and removed, so every printed PASS is a real assertion; the final harness is 24 checks, all green across two consecutive runs.

## 4. Verification

| Gate | Result |
|---|---|
| `make validate` (both suites, as constituent commands) | All green (orphan audit, placeholder lint, registries, contracts) |
| Unicode safety on both edited references | 0 repaired each; strict repo-wide pass |
| `node --check` on the extended engine | Clean |
| Targeted pytest (`-k "skill or workflow_policy"`) | 1043 passed, 8 skipped, 0 failed |
| Demo-deck render checks | 24/24 PASS (grammar classes, reduced motion, step driver) |
| Mapping-table exhaustiveness | Cross-checked: catalog 1-5, patterns 1-7, lightbox, marquee, cinematic stage - every named pattern has a row |
| CI | No change needed; unchanged from Phases 1-2 (no workflow-level paths filter; catalog/** classifies as relevant) |

## 5. Files Changed

| File | Change |
|---|---|
| `catalog/.../references/interactive-features.md` | The slide-mode animation grammar subsection (three classes, binary prohibitions, 14-row mapping table, fallback rule) + the spectrum tie-in line |
| `catalog/.../references/scroll-scrub.md` | Section 8 "Cinematic without scroll: slide mode", one verification item, Related listing update |
| `catalog/.../assets/scroll-scrub-engine.js` | The `driver: 'scroll' \| 'step'` abstraction, `goTo` tween API, header docs, destroy cleanup, and the initial-paint fix |
| `docs/v3/v3.18/known-gaps.md` | Phase 3 status and notes |
| `CHANGELOG.md` | Unreleased entries for the grammar and the engine driver |
| `docs/todos.md` | Phase 3 checked off; dashboard count |
| this file | Session history |

No registry edit (frontmatter unchanged); no installer edit (the skill tree is copied recursively).

## 6. Next Steps

Phase 4 (`strong` / `high`): slide-mode criteria in `visual-qa-rubric.md` (slide fit, fragment integrity, ambient-loop discipline, navigation chrome), the per-slide capture protocol in SKILL.md Step 9 (with the settle-then-capture rule Phases 2-3 recorded), and deterministic `data-nav` checks in `visual_qa_score.py` with a seeded-defect test per new check class.
