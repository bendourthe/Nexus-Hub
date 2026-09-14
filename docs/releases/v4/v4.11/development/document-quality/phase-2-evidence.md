# Phase 2 Evidence - Type Roles and the SVG Render Ratio

**Project**: Nexus-Hub
**Plan**: [v4.11.2 document and deck quality](../../plans/v4.11.2-adoption-document-and-deck-quality.md)
**Phase**: 2 of 7
**Branch**: `feat/v4.11.2-document-deck-quality`
**Date**: 2026-09-13
**Status**: complete

## Model routing

Plan recommends frontier at max effort; this phase ran on Opus 5 (strong tier),
per the standing preference to continue and record the delta.

## Delivered

- `references/responsive-typography.md` section 12: the named role inventory, the inheritance rule, and the render-ratio derivation.
- `measure_handbook.py`: rendered-size CEILINGS per named role, and a role-coverage walk.
- Six negative-controlled tests in `tests/skills/test_presentify_measure_handbook.py`.

## The gate that was one-sided

The font pass enforced floors only. Text rendering far ABOVE the document scale
passed silently, and that is exactly how the SVG scaling trap escapes: an SVG
multiplies every authored length, `font-size` included, by
`css width / viewBox width`. A `14px` label in a 120-unit viewBox laid out at
600px renders at **70px** while the source looks entirely ordinary. The larger
the ratio, the more invisible the defect is in the source.

## Ceilings calibrated against real output, not chosen

The repository's own handbooks were measured BEFORE any ceiling was written:

```
role            n   max px
title           2     68.3
heading-1      10     41.0
body           42     20.0
interactive     6     18.0
caption        10     14.0
```

Each ceiling sits well above its observed maximum (title 96, heading-1 56,
body 28, interactive 28, caption 22) and far below what the trap produces.
Choosing numbers first and checking later is how a gate either fails legitimate
design or never fires.

## Two corrections, both forced by the tests

### The role-coverage gate could not fire at all

First implementation resolved `typeRole` inside the floor-gate loop, which
iterates a fixed selector list: `h1,h2,h3,p,li,td,th,figcaption,svg text,label,
button,a,input,select,textarea`. Every member of that list maps to a role, so
`typeRole` could never be null, and a bare `<span>` was never visited at all.

`test_an_unassignable_text_node_fails_with_its_text_and_selector` failed, which
is the test doing its job: the gate would otherwise have shipped permanently
green. Coverage now runs its own walk over every element owning visible text,
deliberately separate from the floor pass so the floor gate's scope is
unchanged.

### Then the walk was too broad

The wider walk reported **30 unresolved nodes per handbook**, every one a
`<strong>` or `<span>` inside prose. An inline element inherits the role of the
block containing it; reporting those buries the single case worth catching.

A node now fails only when nothing in its ancestor chain resolves a role. Real
output returned to 0 unresolved, and the orphan test still fails correctly -
both halves proven rather than one.

## Verification

```
python -m pytest tests/skills/test_presentify_measure_handbook.py -q
  47 passed in 109.27s

python scripts/ci/run.py --profile fast
  PASS: 14 passed, 0 failed, 0 skipped, 0 advisory in 159.0s

real output, coverage walk:
  overview       unresolved: 0
  distribution   unresolved: 0
```

### Negative controls

| Assertion | Control |
|---|---|
| 60px body fails the 28px ceiling | declaring `type_ceilings: {body: 200}` silences exactly that error |
| 20px body passes | same document, same gate, only the size differs |
| an orphan `<span>` fails with its text | adding `data-type-role="annotation"` silences it |

## CI impact

Recorded against `cicd-architect`; no pipeline file edited.

- **No new test path**: the six tests extend an existing file already in the `repo-tests` group.
- **No new dependency**; runtime unchanged (the coverage walk adds one DOM pass).
- **Behaviour change for consumers**: a handbook whose text renders above a role ceiling, or carries an unassignable text node, now FAILS where it previously passed. Both are real defects, and `type_ceilings` in the inventory is the declared escape hatch for a document with a deliberately larger scale.

## Phase 2 exit checklist

- [x] Oversized type fails; correctly derived type passes.
- [x] Every text node resolves to exactly one named role.
- [x] Both gates negative-controlled.
- [x] Exactly one scoped local commit; no push.
