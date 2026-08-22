# Session History - presentify-fidelity-and-variety Phase 3: Site-wide interaction layer

**Date**: 2026-07-11
**Plan**: `docs/v3/v3.12/plans/v3.12.0-presentify-fidelity-and-variety.md`
**Phase**: 3 of 6 (non-final)
**Model**: Fable 5, medium effort per the plan's recommendation (no routing delta)

## What was done

- **3.1 Catalog + budget** (`references/interactive-features.md`): new "Site-wide interaction layer" section in the primary-path half - seven patterns, each with a vanilla-JS/CSS sketch and an accessibility note (scroll reveals via IntersectionObserver with `.js`-gating; active-nav tracking with `aria-current` + rAF-throttled progress; hover/`:focus-visible` affordance pairs; exact-value animated counters; the shared pan/zoom lightbox with dialog semantics, focus trap, Escape + restore - the same component as the figure-reconstruction enhanced-original viewer; native `details`/ARIA tabs; micro-transitions) - followed by the binary five-point MINIMUM INTERACTION BUDGET (~60 KB inline-JS cap, offline, reduced-motion-guarded) and the explicit rules "charts-only interactivity FAILS" / "a chart-free page still passes through this layer".
- **3.2 Enforcement**: SKILL.md authoring step gained the budget bullet naming all five points; two new Common Rationalizations rows ("mostly text, static is fine", "animations are risky, skip motion entirely"); two new binary Verification items (all five points observable; the 60 KB / offline / reduced-motion constraints); the Step 8 visual-QA screenshot states now include a mid-scroll reveal and an open lightbox. `catalog/commands/presentify.md` delegation names the budget in one clause.
- **3.3 Chart-free demo**: `budget_demo.py` (committed) authors `models/budget-demo.html` (gitignored) from `scanned_enriched.json` - a source with ZERO chart blocks: corrected OCR text, the verified table rendered both as a focusable table and as animated 42/37 KPI counters (signature interaction), both scanned pages as lightbox-wrapped figure buttons, warm-paper serif design (attractor avoided). `verify_budget_demo.py` (committed) asserts the budget structurally.

## Test results

- Budget demo verification: **11/11 PASS** - zero external references; interaction JS ~7 KB (cap 60 KB); P1 nav + `aria-current` + rootMargin tracking; P2 `.js`-gated reveals; P3 hover/focus pairs on cards, images, rows; P4 both images lightbox-wrapped with `role="dialog"`, `aria-modal`, Escape, wheel zoom, pointer pan, focus restore; P5 exact-final-value counters; reduced-motion CSS + JS guards; keyboard trap/tabindex/restore. One iteration: a check regex expected `class="imgbtn"` exactly while the markup has `class="imgbtn reveal"` - TEST-class fix to the verifier pattern.
- Validators: bundle audit 0 errors, unicode-safety 0 errors, ruff clean (1 autofix + format on the two new demo scripts).
- Degradation note (WN-3): no headless browser on this host, so the demo was verified by static structural review per the skill's documented degradation; rendering is checkpointed at the Phase 5 worked example.

## Deviations

- None. (The Phase 1 verifier was not re-run: this phase changed no extractor code.)

## Known-gaps delta

- Added WN-3 (static-only demo verification pending a browser-rendered pass at Phase 5). DF-1/2/3, WN-1/2, MT-1 unchanged.

## Next steps

- Phase 4: design-entropy engine (`scripts/design_seed.py` seeded axis-pool sampler, persisted run history with the 2-of-3-axes rejection rule, roll-then-adapt brainstorm rewrite) - the anti-repetition mechanics.
