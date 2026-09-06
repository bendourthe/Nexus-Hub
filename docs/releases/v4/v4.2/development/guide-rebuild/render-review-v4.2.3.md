# Rendered QA review (v4.2.3 Phase 6)

**Date**: 2026-08-29
**Harness**: `python tests/guides/tools/render_guide.py --label v423-phase-6`
**Coverage**: 4 pages x 2 themes x 3 widths = 24 captures, plus per-phase sets and present-mode captures.

Every phase of this plan rendered before committing, continuing the practice v4.2.2 established to close its DF-1.

## Measurements

- **Contrast**: every text-bearing element in both themes - **242 unique text styles, 0 below WCAG AA**. One genuine regression was found and fixed: light-theme `--amber` (`#9a6b12`) scored 4.14 on the new "WITHOUT NEXUS-HUB" label at 11 px, and was darkened to `#8a5f0f` (4.99). The count rose from v4.2.2's 217 because this release added comparison rows, loop segments, usage terminals, and icon controls.
- **Keyboard**: **0 untabbable controls** across all four pages in both themes, re-checked after Training's controls moved in the DOM and after the copy buttons lost their visible chrome.
- **Reduced motion**: verified per page - reveals opaque, comparison rows opaque, pulses hidden. All four pages pass.
- **Overflow**: no page-level horizontal scrolling at 420 / 900 / 1440 in either theme, across all four pages (24 combinations). This is the standing risk of removing the text measure, so it is re-checked every phase.
- **Present mode**: the slide occupies 823 px of a 900 px viewport (91%), against a small centred block before.

## Defects rendering caught this release

Rendering found seven defects the markup tests could not see:

1. The Foundations H1 still read "edits your code" after the language pass - the vocabulary test was scoped to the section body and did not cover the page heading.
2. Scene 5's "a command" chip was 58 px against a label needing about 80, so the text spilled out of its shape.
3. Scene 5's outcome subtitle ran past the SVG viewBox edge.
4. Scene 5's "a guardrail stops it once" and "gate" captions collided.
5. The Training takeaway's rule stopped at 45% of the width - a leftover `78ch` cap that survived Phase 1's removal of `--measure`.
6. The Training terminal echoed the command a second time under a prompt line that already displayed it.
7. The present-mode booth stage was a tall empty box before any pose was captured.

## Verdict

**24 of 24 standard captures pass.** No capture was accepted with a known visual defect. The one contrast regression and all seven rendering defects were fixed in the phase that found them.

## Budget

Guide file: **397 KB** against the 500 KB budget. No runtime network references.

## Note on render evidence (v4.2.3 Phase 7 consolidation)

The per-phase render sets this file references were consolidated on 2026-08-29. Evidence had grown to 38.4 MB across twelve sets, against an 11.5 MB precedent in `assets/`, in a repository that users clone.

Kept: the final full sweep (`renders/v423-phase-6/`, 24 captures) and every capture that exists nowhere else - reduced motion, present mode before and after a run, and the diagram and command crops. Removed: the superseded standard 24-shot sweeps from earlier phases, including all six v4.2.2 sets, which document pages that v4.2.3 subsequently rewrote.

Nothing is lost: every pruned image remains in git history at the commit that added it. The written verdicts, measurements, and defect lists in this file and in `render-review-v4.2.3.md` are unaffected.
