# Session History - v3.16.5 Phase 2: SVG diagram-quality contract

**Date**: 2026-08-11
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md](../../plans/v3.16.5-presentify-visual-overhaul.md)
**Phase**: 2 of 7 (not the terminal phase)
**Branch**: `feat/v3.16.5-presentify-visual-overhaul`, worktree at `.claude/worktrees/v3.16.5-presentify`
**Model**: Opus 5. The plan recommends the **strong** tier at high effort for this phase; Opus 5 IS the strong tier in the plan's own model map, so the pre-flight agreed with the plan and no switch was needed.
**Prerequisite**: Phase 1, committed `c45fb90b`. Satisfied.

## Sub-tasks completed

### 2.1 - Author `references/svg-diagram-quality.md`

Five rules, each with a correct/incorrect snippet pair and an observable criterion: marker-based arrowheads, dash patterns clear of labels, connectors on node edges, viewport-fit for pinned graphics, and the numeric geometry self-check. Referenced from `SKILL.md` (a Step 6 bullet plus Bundled Resources).

This sub-task also repaid Phase 1's deliberate cross-reference debt. Phase 1 wrote two forward references to this file and then removed them so it could pass its own stability gate without a dangling link; both are now restored, so `responsive-typography.md` and `svg-diagram-quality.md` point at each other and the SVG-label-legibility exemption names the file that owns it.

### 2.2 - Extend the scorer and the rubric

Three checks (`svg-arrowhead`, `svg-viewport-fit`, `svg-marker-integrity`), a stdlib-XML SVG parser with an entity guard, a path-data tokenizer, a triangle discriminator, and real element-containment resolution. Rubric extended to eight criteria with criterion 8, `diagram integrity`.

### 2.3 - Rebuild the fixture's diagrams

Four marker definitions replacing three hand-placed triangles; arrowheads on all four pipeline connectors rather than only the first; the pinned graphic capped against its sticky offset; the loop-back viewBox widened 300 -> 330 so the rotated label clears its curve; every remaining hardcoded palette hex retargeted onto its token.

### 2.4 - Testing and stabilization

Three rationalization rows and one Verification item added to `SKILL.md`. Full sweep run.

## What the phase found that the plan did not anticipate

1. **The defect class is the triangle, not the dashed line.** The plan specified detecting "a `<path>` with `stroke-dasharray` that has no `marker-end` yet is followed by a sibling small filled triangle". But the pipeline's broken arrowhead sat on a SOLID line, so keying on the dash pattern would have caught one of the two instances and declared victory. The check detects the triangle itself, independent of the connector's style.
2. **Only one of four pipeline connectors had an arrowhead at all.** The maintainer's R5 mentioned "arrows between blocks misdrawn"; the actual state was that flows 1-3 had no head whatsoever, so the diagram silently lost its direction halfway down. This motivated the consistency check, which the plan did not ask for.
3. **The loop-back label and its curve overlapped, provably.** The label was centered at `(288, 248)` and the curve's cubic midpoint is `(286.5, 245)` - the same 2 user units. Rule 2 exists because that is invisible when reading the source and obvious on screen.
4. **Phase 1's contrast fix was being reverted at runtime** (BG-1). Five of six per-section accents, assigned to `--accent` from `data-accent` attributes by script, measured 3.20:1 to 4.36:1. Phase 1's check grades declared CSS properties and could not see them, so its gate passed truthfully on an incomplete view. Found only because this phase was retargeting hardcoded hexes in the SVGs and followed the pattern outward.
5. **Markers do not inherit from the element that references them.** The fixture's `.flow.on` state recolors the connector to the accent; a single marker cannot follow, because `currentColor` inside a marker resolves against the marker's own position in the DOM. Two markers swapped by CSS is the correct construction, and it forced both new checks to read CSS as well as attributes - otherwise the correct page reports as headless with two unused markers.

## Troubleshooting loop

One iteration, one failure, classified **IMPL**.

`test_scorer_ignores_a_sticky_container_that_holds_no_svg` failed on the first run. The viewport-fit check was looking a bounded 600 characters past a sticky container for an `<svg>`, which reports any diagram that merely FOLLOWS the container - so a sticky page nav with a chart later on the page produced a false HIGH. Replaced the window with real containment: walk the tag depth from the container's opening tag to its matching close and inspect the actual inner HTML. The near-miss test was written before the implementation was trusted, which is why the false positive surfaced in seconds rather than in a later phase's review.

## Verification evidence

| Check | Command | Result |
|---|---|---|
| Presentify visual-QA suite | `python -m pytest tests/skills/test_presentify_visual_qa.py -q` | 42 passed (from 29) |
| Full presentify surface | `python -m pytest tests/skills/ -q` | 541 passed, 3 skipped |
| Coverage of the changed module | `pytest --cov=.../scripts` | `visual_qa_score.py` 92% at 505 statements (was 92% at 328) |
| Lint | `python -m ruff check <scorer> <tests>` | All checks passed |
| Catalog + bundle validation | the ten `make validate` guards, run individually | all OK; orphan-bundle audit 0 warnings |
| Scorer against the fixture | `python scripts/visual_qa_score.py nexus-hub-unit-test-workflow.html` | PASS, 0 high-severity across 12 criteria, 4 markers all referenced |
| Rule-5 geometry self-check | ad-hoc numeric pass over both SVGs | all coordinates inside both viewBoxes; label clearance 15.25 and 23.0 user units |

## Security note

A `PostToolUse` hook flagged the stdlib `xml.etree.ElementTree` import for XXE and billion-laughs exposure. `defusedxml` is the standard remedy but is unavailable here: the scorer ships to users inside the skill bundle and is stdlib-only by contract, so adding an import would add an install requirement to every platform that receives the skill. `ElementTree` resolves no external entities and retrieves no DTDs, so the XXE class does not apply; the entity-expansion class requires an inline `<!ENTITY`, so `_parse_svg` now refuses any block carrying a DOCTYPE or ENTITY declaration before parsing it. That removes the surface the library would have guarded, with a test pinning the behavior.

## Deviations from the plan

- **The arrowhead check is broader than specified**, detecting the triangle rather than the dash-plus-triangle sequence. Narrower would have missed the pipeline instance.
- **An arrowhead-consistency check was added**, which the plan did not request. It exists because the fixture's actual state (1 of 4 connectors with a head) is a distinct defect from the detached head, and MEDIUM severity keeps it from blocking.
- **BG-1's fix touches non-SVG surfaces** (`data-accent` attributes, canvas literals) that belong to Phase 1's contrast domain. Justified by rule 5 of this phase's own contract, which mandates palette-token sourcing and names this exact failure mode; leaving it would mean calling the fixture a standing calibration artifact while five of six sections rendered sub-AA accents.

## Known gaps appended

Two new open, one closed, zero blockers. BG-1 closed (sub-AA runtime accents). WN-2 (the scorer cannot see script-assigned palette values) and NI-3 (SVG rules 2-3 not automated) both route to Phase 3. MT-1, NI-2, WN-1, DF-1 from Phase 1 unchanged. See [docs/releases/v3/v3.16/known-gaps.md](../../known-gaps.md).

## Next steps

1. **Phase 3 - the real render loop.** It is now carrying four routed items (Phase 1's NI-2 and WN-1, Phase 2's WN-2 and NI-3), and every one of them is the same shape: a static parser reaching the limit of what markup can tell it. A rendered screenshot answers all four directly. That is the argument for building Phase 3 rather than deepening the scorer further, and it is worth stating plainly before the next phase starts.
2. Phase 3 also re-verifies both rebuilt diagrams from real screenshots, and its acceptance test (deliberately re-breaking the loop-back arrow and confirming detection) now has a deterministic check to compare against.
3. Phase 7 still owns MT-1, the fixture's final location.
