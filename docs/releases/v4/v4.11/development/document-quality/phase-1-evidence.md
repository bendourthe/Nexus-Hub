# Phase 1 Evidence - Geometric Audit Foundation

**Project**: Nexus-Hub
**Plan**: [v4.11.2 document and deck quality](../../../../../archives/v4/v4.11/plans/v4.11.2-adoption-document-and-deck-quality.md)
**Phase**: 1 of 7
**Branch**: `feat/v4.11.2-document-deck-quality`, from `develop` at `8ac5e325`
**Date**: 2026-09-13
**Status**: complete

## Model routing

The plan recommends frontier tier at max effort. This phase ran on Opus 5
(strong tier), per the standing preference to continue on the session model and
record the delta rather than switch. Recorded here because the plan's
recommendation and what actually ran should never be assumed identical.

## Delivered

- `catalog/skills/specialized-domains/document-to-interactive-html/scripts/geometric_audit.py` - six checks, all measured in screen space.
- Nine fixtures under `tests/fixtures/document-quality/` - one per defect class, a clean baseline, and the two false-positive defences.
- `tests/skills/test_geometric_audit.py` - 19 tests.
- A bundled-resources entry in the skill, which the orphan audit requires.

## The fixture matrix

Each broken fixture reports EXACTLY its own check. A second check on one
fixture would mean a check is over-broad, and an over-broad check hides the
missing one beside it.

```
clean                 pass  -
clipped-text          fail  [clipped-text]
label-overlap         fail  [label-overlap]
label-on-trace        fail  [label-on-trace]
legend-colour         fail  [legend-colour-collision]
oversized-type        fail  [oversized-type]
stroke-drift          fail  [stroke-drift]
rotated-axis-title    pass  -    <- defence A
label-beside-wiggle   pass  -    <- defence B
```

## Negative control

`--disable <check>` switches one check off. The suite asserts, per fixture,
that the check fires and then that disabling it silences the fixture. A check
that cannot be shown to be the thing producing a finding is not evidence,
however green the run looks.

```
python geometric_audit.py tests/fixtures/document-quality/label-on-trace.html --disable label-on-trace
  with check disabled -> pass []
```

The option exists for this purpose and is documented as such in the script and
in the skill entry, rather than being a debug flag nobody can account for.

## Three corrections, all caught by "fires on its own and on no other"

**1. A real bug: `clipped-text` could never fire.** An SVG defaults to
`overflow: hidden`, so the clip-walking helper intersected the text against the
very viewport that clipped it - circular reasoning that guarantees no finding.
The fixture passed when it had to fail. Check 1 now measures the text's RAW
rect against the SVG frame; clipping by ancestors outside the SVG is still
honoured in the overlap checks, where it belongs.

**2. `clean.html` was not clean.** Its axis tick labels sat on the lower
trace's endpoint, and `label-on-trace` correctly reported it. The fixture was
wrong, not the check. Traces now stay clear of the axis band.

**3. Defence B tested nothing.** The wiggle was a dense zigzag from y=40 to
y=280 every 40px, so the label genuinely sat on the ink and the fixture
asserted a false positive that was not false. It now hugs the bottom band with
one tall spike at the right edge: the bounding box still spans the label
(x 20-580, y 40-285) while the nearest ink is roughly 100px away. A
bounding-box test reports a collision here; sampling does not. That gap is the
entire point of the fixture.

A fourth, smaller one: the `oversized-type` fixture carried two defects,
because scaling the type up pushed its ascender 3px above the viewBox. The
baseline moved from y=12 to y=26 so it carries one.

## Against real generated output

The check that matters, because the source project's first audit produced
roughly 220 findings on real output and was abandoned for it:

```
overview.html       pass  svgs=5  -
distribution.html   pass  svgs=5  -
```

Zero findings across ten SVGs of genuine generated output.

## Verification

```
python -m pytest tests/skills/test_geometric_audit.py -q
  19 passed in 15.68s

python scripts/ci/run.py --profile fast
  PASS: 14 passed, 0 failed, 0 skipped, 0 advisory in 157.8s
```

## CI impact

Recorded against `cicd-architect`; no pipeline file edited in this phase, per
the plan lifecycle.

- **New test path**: `tests/skills/test_geometric_audit.py`. Already covered by the existing `repo-tests` group glob; no new job or path filter needed.
- **New fixtures**: `tests/fixtures/document-quality/`. Static HTML, no build step.
- **Dependency**: none added. The audit uses Playwright, which the render job already installs, and the suite guards on it with `importorskip` plus a `NEXUS_REQUIRE_RENDER=1` hard-fail so a render job cannot skip silently.
- **Runtime**: about 16s for the suite.
- **Not yet wired into a profile.** The audit is a bundled skill script, not a repository gate, and wiring it into the `docs` group is Phase 6's stated deliverable. Recorded here so the omission is deliberate rather than forgotten.

## Phase 1 exit checklist

- [x] Every check fires on its own fixture and on no other.
- [x] Both false-positive defences proven by fixtures that must stay silent.
- [x] Every new assertion negative-controlled.
- [x] Exactly one scoped local commit; no push, PR or remote CI.
