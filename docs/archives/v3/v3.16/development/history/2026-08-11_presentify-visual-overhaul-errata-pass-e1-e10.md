# Session History - v3.16.5 errata pass (render-session lessons E1-E10)

**Date**: 2026-08-11
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md](../../plans/v3.16.5-presentify-visual-overhaul.md), the `## Errata: render-session lessons` section
**Scope**: not a plan phase. An errata pass executed immediately after Phase 3, because E1-E5 correct artifacts Phases 1 and 2 had already committed and the plan directs them to run inside Phase 3.
**Branch**: `feat/v3.16.5-presentify-visual-overhaul` (worktree)
**Model**: Opus 5
**Maintainer decisions**: sequence E1+E3 -> E2+E4 -> E5 -> E6-E9; adopt the repo-root fixture as canonical; where the scorer and the fixture disagree, the fixture wins; accept moved floor numbers; fix new 2560-capture defects per the contracts rather than relaxing checks; record everything against BG-E1.

## How this pass started

Phase 3's commit was already written when `git status` showed the plan file modified by a hand other than mine. The `## Errata` section recorded a four-round render session at 2560x1300 and 1920x1080 that overturned two prescriptions Phases 1 and 2 had shipped. Rather than commit Phase 3 as though the contracts were unchanged, the mechanism was committed on its own (`01f679a6`) with the supersession stated in its message, and the corrections taken as a separate unit - so "the render loop now exists" stays reviewable apart from "the contracts changed".

The decisive datapoint came from running the Phase 3 scorer against the maintainer's reference fixture: 16 font-floor failures, all false. E3 had predicted exactly that.

## What each item required

| Item | Change |
|---|---|
| **E1** | `responsive-typography.md` rule 3 rewritten: scaling goes on the ROOT in one declaration, not per element. Both replaced failure modes recorded. |
| **E1 corollary** | Found while executing it, and absent from the errata: root scaling does nothing below the root clamp's minimum. Now stated in the contract. |
| **E2** | Rule 2's example became `minmax(0, 2fr) minmax(16rem, 1fr)` with notes adjacent; the precedence (window-filling beats line-length caps on wide screens) is explicit. |
| **E3** | `root_font_px()` parses the `html` rule; every rem/ch resolves against it; `rem` counts as fluid when the root is; band math re-derived at the scaled root. |
| **E4** | Rotation stated as a readability defect, with the widen-viewBox + `tspan` replacement, a Verification item, and a rationalization row. |
| **E5** | Documented as rule 7 and given the `render-only-defects` check, with both directions tested including the near-misses. |
| **E6-E8** | Instant scroll + settle, a REQUIRED 2560x1300 capture, computed-metric probes per iteration; the rubric explains why both ends of the range are mandatory. |
| **E9** | Key-value cells as bullet lists with concrete values; neutral control colors distinct from data series. |
| **E10** | Noted - Playwright was already provisioned, so fixture work was verification. |

## The finding that mattered most

E1's corollary. Root scaling lifts type on large displays, but with `clamp(1rem, 0.5vw + 0.55rem, 1.6rem)` the root pins at 16px for every viewport at or below 1366px - so every `rem`-based small size bottoms out exactly where it did before. The reference fixture, verified at 2560 and 1920 where scaling was fully engaged, carried **14 distinct sub-floor element classes at 1366px**.

This is Phase 1 rule 4's lesson ("check at the clamp minimum") re-applied one level up, and it is precisely the blind spot a render session inherits from choosing its viewports. The two ends of the range catch different defects, which is why E7's 2560 requirement and the 1366 leg are both mandatory rather than alternatives.

## Fixed in the page, versus fixed in the check

The maintainer's two notes point in opposite directions and both applied, to different findings.

**Fixed in the page** (note 3 - never relax a check to make a page pass):

- The 14 sub-floor classes: secondary to `.8125rem` (13px at a 16px root), interactive to `.75rem` (12px).
- `code{font-size:.9em}` rendering at 12.53px, floored with `max(.9em, 0.8125rem)`. A fractional `em` is unresolvable statically (WN-3), so only the render caught it.
- The gutter cap `2.75rem -> 2.6rem`, so the full-width contract holds at the scaled root: 0.947 -> 0.950.
- `#mOn`, a marker defined for the highlighted flow state but never referenced, wired via `.flow.on{marker-end:url(#mOn)}`. Without it the accent-stroked connector kept the dim arrowhead - the same marker non-inheritance trap Phase 2 documented, left half-built in the fixture.

**Fixed in the check** (note 1 - where they disagree, the fixture wins): `svg-viewport-fit` demanded a literal `max-height`. The fixture uses `height: calc(100vh - 7.5rem); width: auto; max-width: 100%`, which pins the graphic to its slot AND prevents the horizontal overflow that deriving width from a capped height can cause. That is strictly better, so the check accepts either form and rule 4 documents the preferred one.

## A false pass is worse than a false failure

E3 produced one of each, and the asymmetry is worth recording. The 16 false FAILURES were loud, obviously wrong, and fixed within the hour. The single false PASS - a band fraction the check inflated from 0.947 to 0.954, across its own 0.95 threshold - had been sitting inside a green run since Phase 1 and would have shipped. A checker's errors are not symmetric, and the direction that costs you is the quiet one.

## Test-design correction

The fixture swap drifted all seven mutation-test string anchors at once. The `assert seeded != clean, "anchor drifted"` line caught it, which is why it was written - but a test that must be re-anchored whenever the page is re-authored is testing the wrong layer. Mutations now target `(selector, property)` pairs through a rule-aware helper, with only the two genuinely structural cases (an SVG path, an inline style attribute) staying literal. Expected severity also became per-case, after a single fixed macro dimension (MEDIUM by policy) failed a test asserting HIGH for everything - loosening the policy to satisfy the test would have inverted the relationship between them.

Two bugs in that helper are worth noting because both were invisible: `[^{}]+` reaches back through a preceding CSS comment, and for the first rule in a stylesheet it reaches through the `<style>` tag itself. `css_rules()` avoids both by extracting style-block contents first.

## Verification evidence

| Check | Result |
|---|---|
| Visual-QA suite | 70 passed (from 59) |
| Full presentify surface | 572 passed, 0 skipped |
| Lint (CI's target) | `ruff check --ignore RUF100` clean |
| Validators | all ten pass; orphan-bundle audit 0 warnings |
| Scorer on the canonical fixture | PASS, 0 high-severity across 13 structural criteria |
| Scorer vs live render | band fraction matches to four decimals at 2560 / 1920 / 1366 (0.9536 / 0.9473 / 0.9356); root font size exact (21.6 / 18.4 / 16.0) |
| Rendered floors, 4 viewports | secondary >= 13px and interactive >= 12px at 2560 / 1920 / 1366 / 390; no horizontal overflow at any width |
| E5 rules, rendered at 2560 | two sticky layers at distinct offsets; every anchor target has `scroll-margin-top`; 0 of 5 `pre` blocks clip |

## Deviations

- **The fixture was replaced wholesale**, not merged. Per E10 and the maintainer's decision; the ~3291-line diff is recorded in the docs-cleanup audit so a later reader is not left guessing.
- **E2 required no code change**, only contract text: the canonical fixture already implements fractional columns, and no deterministic check governs the measure inside a multi-column zone (it needs rendered geometry). Noted rather than silently skipped.

## Next steps

1. **Phase 4 - intake redesign** (imagery question + content-aware color schemes), unblocked and prerequisite-free.
2. Phase 5's placement pass closes the remaining half of v3.15 MT-2 inside the loop Phase 3 built.
3. Phase 7 owns MT-1's location half and will reconcile BG-E1 alongside the rest of v3.16.
