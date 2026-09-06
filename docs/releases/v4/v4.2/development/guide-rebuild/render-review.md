# Rendered QA review (v4.2.2 Phase 6)

**Date**: 2026-08-29
**Harness**: `python tests/guides/tools/render_guide.py --label phase-6` (Chromium via Playwright)
**Coverage**: 4 pages x 2 themes x 3 widths = 24 captures, plus reduced-motion and Present-mode captures.

This file exists because the v4.2.x visuals shipped without any rendered check (v4.2.1 known-gap DF-1). Every phase of this plan rendered before committing; this is the consolidated verdict.

## Verdict per capture

| Capture | Verdict | Note |
|---|---|---|
| home-dark-1440 | pass | Hero title and lead share one measure; install block Windows-first; loop strip and closing band read as one system. |
| home-dark-900 | pass | Comparison table keeps three columns; nothing crowds. |
| home-dark-420 | pass | Table scrolls inside its own container; page itself does not scroll sideways. |
| home-light-1440 | pass | Brand chip renders the glow mark against the light ground; GitHub octocat correct. |
| home-light-900 | pass | - |
| home-light-420 | pass | Nav collapses to the hamburger; controls stay reachable. |
| foundations-dark-1440 | pass | Five scenes, alternating sides, all diagrams complete after entry animation. |
| foundations-dark-900 | pass | Scene grid still two-column; diagrams scale by viewBox. |
| foundations-dark-420 | pass | Scenes stack text-above-diagram; labels stay legible. |
| foundations-light-1440 | pass | Same markup, both themes; arcs, cards, and lanes all carry theme tokens. |
| foundations-light-900 | pass | - |
| foundations-light-420 | pass | - |
| training-dark-1440 | pass | Booth, terminal, tools, artifact, gate, and takeaway all present in one screen. |
| training-dark-900 | pass | Two-column grid holds. |
| training-dark-420 | pass | Booth and terminal stack; pose buttons wrap. |
| training-light-1440 | pass | - |
| training-light-900 | pass | Reviewed in detail: booth tag "as shipped" reads red, counter shows the buggy 0/5 start, gate cards legible. |
| training-light-420 | pass | - |
| cheatsheets-dark-1440 | pass | Seven named sections; scope grid three-up; every scope has a description. |
| cheatsheets-dark-900 | pass | Scope grid reflows to two-up. |
| cheatsheets-dark-420 | pass | Scope grid single column; command headers wrap without clipping. |
| cheatsheets-light-1440 | pass | - |
| cheatsheets-light-900 | pass | - |
| cheatsheets-light-420 | pass | - |
| foundations-reduced-motion-dark-1440 | pass | Every diagram at final state, pulses hidden, no crushed-duration artifacts. |
| training-present-dark-1440 | pass | Present mode fills the viewport with a sticky control bar; booth and terminal stay interactive. |
| cs-explore-viewport-1440 | pass | Deep link lands the section 66px from the top, clear of the sticky header. |

**24 of 24 standard captures pass, plus 3 special captures.** No capture was accepted with a known visual defect.

## Defects found by rendering, and fixed in-phase

Rendering caught six defects that markup-parsing tests could not see. All were fixed in the phase that found them:

1. **Phase 1** - the GitHub octocat rendered as a crescent. Root cause: corrupted SVG path data inherited from v4.2.x, compounded by `.nav-links a` padding overriding the icon button. Fixed with the canonical path and a scoped `a.nav-gh` rule.
2. **Phase 1** - `--measure: 62ch` resolves per element font size, so the hero H1 and lead still wrapped differently. Changed to a px measure plus `text-wrap: balance`.
3. **Phase 2** - scroll-gated `.reveal` sections captured transparent (harness artifact, not a page bug); harness now forces the end state.
4. **Phase 2** - the sticky backdrop-filtered header stitched as a dark band in light-theme full-page shots. Verified against live computed styles and a viewport-only capture, then pinned the header static during capture so evidence is not misleading.
5. **Phase 3** - harness-ring arcs rendered broken because their endpoints were not on the circle. Recomputed onto r=132 about (260,156).
6. **Phase 3** - scene 5 was missing its gate station; added the gate diamond and widened the viewBox.

## Accessibility measurements (Phase 6)

- **Contrast**: every text-bearing element sampled in both themes - **217 unique text styles, 0 below WCAG AA**. Three tokens were corrected to get there: dark `--term-dim` (#5f7d84 -> #6d8d94, was 3.95), dark `--ink-faint` (#6f8990 -> #7e9aa1, was 3.76), light `--ink-faint` (#6b7c80 -> #586769, was 4.29), and dark `--red` (#e07070 -> #e88585, was 4.46 on the small booth tag).
- **Method note**: the first sweep reported 11 light-theme failures. That was a bug in the sweep script's background walk-up (it fell through to transparent and scored against black), not in the page. Re-measured against the real painted background before changing any token; the light theme was already passing at 6.2:1. Recorded here because a token changed on a mismeasurement would have been a silent regression.
- **Keyboard**: 24 + 4 + 17 + 38 = 83 visible controls across the four pages, **0 untabbable**. A global `:focus-visible` outline is defined.
- **Reduced motion**: pulses hidden, reveals and pops at full opacity, dash draws complete, terminal prints instantly.
- **Animation gating**: only 2 of 5 Foundations scenes carry `.live` at rest, so offscreen scenes run no animation.

## Budget

Guide file: **351 KB** against the 500 KB budget (`test_file_size_budget`). No runtime network references (`test_no_runtime_cdn_font_script_or_image`).

## Note on render evidence (v4.2.3 Phase 7 consolidation)

The per-phase render sets this file references were consolidated on 2026-08-29. Evidence had grown to 38.4 MB across twelve sets, against an 11.5 MB precedent in `assets/`, in a repository that users clone.

Kept: the final full sweep (`renders/v423-phase-6/`, 24 captures) and every capture that exists nowhere else - reduced motion, present mode before and after a run, and the diagram and command crops. Removed: the superseded standard 24-shot sweeps from earlier phases, including all six v4.2.2 sets, which document pages that v4.2.3 subsequently rewrote.

Nothing is lost: every pruned image remains in git history at the commit that added it. The written verdicts, measurements, and defect lists in this file and in `render-review-v4.2.3.md` are unaffected.
