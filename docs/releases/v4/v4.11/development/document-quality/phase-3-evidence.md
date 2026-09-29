# Phase 3 Evidence - Figure and Diagram Construction Gates

**Project**: Nexus-Hub
**Plan**: [v4.11.2 document and deck quality](../../../../../archives/v4/v4.11/plans/v4.11.2-adoption-document-and-deck-quality.md)
**Phase**: 3 of 7
**Branch**: `feat/v4.11.2-document-deck-quality`
**Date**: 2026-09-13
**Status**: complete

## Model routing

Plan recommends frontier at high effort; ran on Opus 5 (strong tier), delta
recorded per the standing preference.

## Delivered

Three checks added to `geometric_audit.py`, taking it from six to nine:

| Check | What it catches |
|---|---|
| `legend-entry-not-drawn` | a legend entry whose colour nothing in the figure paints |
| `tick-outside-range` | a tick claiming the axis reaches a value the data never does |
| `viewbox-dead-space` | a `viewBox` carrying empty space beyond its ink |

Plus the rules in their owning references: `figure-reconstruction.md` for legend
integrity, tick range and cropping; `svg-diagram-quality.md` for one-colour-per-
identity and stroke consistency.

## The fixture matrix

Thirteen fixtures. Nine carry exactly one defect; four must stay silent.

```
clean                 pass  -
clipped-text          fail  [clipped-text]
label-overlap         fail  [label-overlap]
label-on-trace        fail  [label-on-trace]
legend-colour         fail  [legend-colour-collision]
oversized-type        fail  [oversized-type]
stroke-drift          fail  [stroke-drift]
legend-not-drawn      fail  [legend-entry-not-drawn]
tick-outside-range    fail  [tick-outside-range]
viewbox-dead-space    fail  [viewbox-dead-space]
rotated-axis-title    pass  -    <- defence A
label-beside-wiggle   pass  -    <- defence B
viewbox-cropped       pass  -    <- the corrected counterpart
```

## The new check exposed fixture debt, including in both defences

Adding `viewbox-dead-space` immediately failed eight fixtures written in Phase
1, **including both false-positive defences**, which must stay silent to mean
anything. Their viewBoxes were `0 0 600 300` regardless of where their ink
actually sat.

This was fixture debt rather than a false positive, and the distinction was
settled by evidence rather than assumption: the real repository handbooks passed
throughout. Each fixture was re-cropped using the crop the check itself
suggested, restoring one-defect-per-fixture.

```
clipped-text        0 0 600 300  -> 0 84 600 182
label-on-trace      0 0 600 300  -> 0 94 600 172
oversized-type      0 0 120 60   -> 0 12.2 120 39
stroke-drift        0 0 600 300  -> 0 154 600 112
label-beside-wiggle 0 0 600 300  -> 0 34 600 257
```

## The suggestion is actionable, and that is asserted

`viewbox-dead-space.html` and `viewbox-cropped.html` are the same figure. The
cropped one carries, verbatim, the `viewBox` the check suggested for the other,
and it passes. `test_the_suggested_crop_is_actionable_not_advisory` asserts
exactly that, because a suggestion nobody can apply is a complaint.

My own first hand-written crop for that fixture was WRONG - it left 14% dead
space at the bottom and still failed. The check's suggestion was right and mine
was not, which is the most direct evidence that emitting a computed crop earns
its place.

## Verification

```
python -m pytest tests/skills/test_geometric_audit.py -q
  29 passed in 23.28s

python scripts/ci/run.py --profile fast
  PASS: 14 passed, 0 failed, 0 skipped, 0 advisory in 8.8s

real output:
  overview.html       pass  -
  distribution.html   pass  -
```

### Negative controls

| Assertion | Control |
|---|---|
| each of the nine checks fires on its fixture | `--disable <check>` silences exactly that fixture |
| dead space is reported at 8% | `--dead-space-fraction 0.95` silences it while the figure is unchanged |
| a legend entry matching a drawn colour is fine | the clean fixture's legend keys both entries to painted colours |

## A deliberate exception, stated

`viewbox-dead-space` uses `getBBox`, which the rest of this audit forbids. The
ban exists because `getBBox` ignores transforms and therefore disagrees with the
screen. Here the question is entirely in user space - content bounds against a
user-space `viewBox` - so transforms are not part of it. Everything judged
against the SCREEN still uses `getBoundingClientRect`. The exception is
commented at the call site so a later reader does not "fix" it.

## CI impact

Recorded against `cicd-architect`; no pipeline file edited.

- **No new test path**: the three checks extend `tests/skills/test_geometric_audit.py`, already in the `repo-tests` group.
- **Four new fixtures**; static HTML, no build step.
- **No new dependency**. Runtime up from about 16s to 23s for the suite.
- **Behaviour change for consumers**: a figure with dead space, a mismatched legend, or an out-of-range tick now fails where it previously passed. `--dead-space-fraction` is the declared escape hatch for a figure with deliberate margin.

## Phase 3 exit checklist

- [x] Each construction gate fails its own fixture and passes a corrected one.
- [x] No gate fires on a legitimate figure from the retained artifacts.
- [x] Every gate negative-controlled.
- [x] Exactly one scoped local commit; no push.
