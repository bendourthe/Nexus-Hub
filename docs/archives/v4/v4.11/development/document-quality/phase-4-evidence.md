# Phase 4 Evidence - Deck Integrity Gates

**Project**: Nexus-Hub
**Plan**: [v4.11.2 document and deck quality](../../../../../archives/v4/v4.11/plans/v4.11.2-adoption-document-and-deck-quality.md)
**Phase**: 4 of 7
**Branch**: `feat/v4.11.2-document-deck-quality`
**Date**: 2026-09-13
**Status**: complete

## Model routing

Plan recommends frontier at max effort; ran on Opus 5 (strong tier), delta recorded.

## Delivered

`DECK_INTEGRITY`, a probe evaluated against ONE slide while that slide is
current, wired into the existing per-slide walk at the `final` state after the
animation window closes.

| Rule | Defect |
|---|---|
| `slide-overflow` | content beyond the fixed canvas, which a slide cannot scroll to reach |
| `invisible-after-animation` | an element left at effective opacity 0 by a fill-mode collision |
| `clone-reference-escapes-slide` | a cloned figure whose reference resolves only against the original |
| `empty-clone-holder` | a clone holder that resolved to nothing |

Rules written into `references/dual-view-handbooks.md`.

## The plan's premise was wrong, and the measurement corrected it

The plan predicted that measuring every slide at the end would OVER-report:
"a probe that checks all slides at the end reports everything hidden". I wrote
the test asserting exactly that, and it failed.

Measured on this fixture, the naive walk does something different and worse:

```
NAIVE (all slides at the end)        WHILE CURRENT
  s-clean       -                      s-clean       -
  s-overflow    -                      s-overflow    [slide-overflow]
  s-invisible   [invisible...]         s-invisible   [invisible...]
  s-dangling    [clone-ref...]         s-dangling    [clone-ref...]
```

`getBoundingClientRect` returns zeros for an element inside a `display:none`
slide, so the naive walk finds NO overflow at all and calls the deck clean. The
defect is not over-reported; it is invisible to that measurement.

**A false alarm gets investigated. A silent miss ships.** That is a stronger
argument for the per-slide walk than the one the plan made, and the test now
asserts the measured behaviour rather than the predicted behaviour.

### A secondary finding worth keeping

The same comparison shows the opacity and reference checks agree either way,
because neither depends on rects. Only the GEOMETRY check is timing-sensitive.
That is now asserted, so a future change making another check rect-dependent
breaks the assertion instead of silently inheriting the trap.

## The fixture

Four slides, one defect each, in a deck that shows one slide at a time exactly
as a real deck does.

`s-dangling` points at a marker DEFINED ON `s-clean`. It renders correctly while
the original is in the document and breaks the moment it is not, which is the
worst possible failure schedule and the reason the check resolves references
within the slide rather than document-wide.

## Verification

```
python -m pytest tests/skills/test_deck_integrity.py -q
  7 passed in 1.96s

python -m pytest tests/skills/test_presentify_measure_handbook.py -q
  47 passed in 116.66s

python scripts/ci/run.py --profile fast
  PASS: 14 passed, 0 failed, 0 skipped, 0 advisory in 161.8s
```

The 47 existing measurement tests passing unchanged is the evidence that wiring
a new probe into the per-slide loop did not disturb what that loop already
measured.

### Negative controls

| Assertion | Control |
|---|---|
| each slide reports exactly its own rule | the other three slides stay silent on it |
| the per-slide walk is load-bearing | the naive walk misses `slide-overflow` entirely, asserted directly |
| the clean slide is clean | it owns the marker `s-dangling` fails to resolve, and reports nothing |

## CI impact

Recorded against `cicd-architect`; no pipeline file edited.

- **New test path**: `tests/skills/test_deck_integrity.py`, covered by the existing `repo-tests` glob.
- **One new fixture**; static HTML.
- **No new dependency.** The probe adds one `page.evaluate` per slide at the final state only, so cost scales with slide count rather than with viewports.
- **Behaviour change for consumers**: a deck with an overflowing slide, an element invisible after its animation, or a clone whose references escape the slide now FAILS. All three previously passed every structural check.

## Phase 4 exit checklist

- [x] Every deck gate measured while its slide is current.
- [x] Overflow, invisibility and dangling-clone fixtures each fail.
- [x] Every gate negative-controlled.
- [x] Exactly one scoped local commit; no push.
