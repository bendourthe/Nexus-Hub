# Known Gaps - v4.4

**Project**: Nexus-Hub
**Status**: v4.4.0 finalized 2026-09-01 at `/update release`; v4.4.1 in progress on the same minor
**Last updated**: 2026-09-01 (v4.4.1 Phase 4)

## v4.4.0 - guide-depth-and-training-rebuild

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 5 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 1 |
| Quality-gate gaps (QG) | 0 | 2 |

### Open Items

#### Deferred

##### DF-1 - Three platform entries use text treatments pending approved standalone marks

- **Source phase**: Phase 1 - Home identity, platforms, installation, and comparison.
- **Plan reference**: `docs/releases/v4/v4.4/plans/v4.4.0-guide-depth-and-training-rebuild.md` sub-task 1.2 / T002.
- **Reason**: Current official assets provide a verified Claude icon, Cursor cube, and OpenCode logo. The OpenAI brand pack does not provide a ChatGPT-specific SVG, Gemini product-icon use requires documented partner approval, and current GitHub guidance does not support using the Copilot bot as a standalone hero mark. Phase 1 therefore uses labelled text treatments for ChatGPT, Gemini, and GitHub Copilot instead of inventing or misapplying trademark geometry.
- **Suggested next step**: Replace an individual text treatment only after its vendor publishes a distributable standalone product mark or grants documented permission, then add the exact asset provenance and rerun both-theme contrast and geometry tests.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| QG-1 | Visual detector could not activate hash-routed guide pages | Phase 2 | Added validated `--fragment` routing with visible-target proof, regression coverage, JSON provenance, and owning-skill usage guidance. |
| MT-1 | Main CI does not enforce browser-backed guide verification | Phase 7 | Added the scoped `guide-render` job with Playwright Chromium and `NEXUS_REQUIRE_RENDER=1`, wired it into `ci-required`, passed 67 workflow contract tests, and ran the exact fail-closed guide and detector targets locally with 154 passed and one explicit optional portfolio-copy skip. Remote clean-runner execution completed on pull request #150, where `guide-render` passed in 1m51s and `ci-required` aggregated green, closing the publication gate this entry named. |
| BG-1 | Training API accepted non-integer numeric scene indexes and corrupted exported state | Phase 7 | Restricted numeric navigation to in-range integers and added browser proof that `NaN` and fractional indexes preserve the current scene; the current focused Training explorer suite passed 3 tests. |
| BG-2 | Training presentation mode painted the game and terminal over later regions | Phase 7 | Restored natural grid height inside the scrollable presentation slide and added rectangle-separation checks at 1920x1080, 1440x900, 1024x768, and 900x900. |
| BG-3 | Training presentation mode allowed focus to escape and did not restore its invoker | Phase 7 | Added dialog semantics, background isolation, a Tab loop, early Escape handling, and post-fullscreen focus restoration; the current fail-closed Training explorer suite passed 3 tests in 21.22 seconds. |
| BG-4 | Denied-fullscreen presentation fallback survived route changes and left the destination inert | Phase 7 | Exit presentation when hash routing leaves Training, restore the recorded inert states, and prove that a rejected Fullscreen API followed by `#home` navigation leaves Home and the site header operable. |
| BG-5 | Presentation mode had no visible close control inside its isolated dialog | Phase 7 | Added an in-dialog `Exit presentation` control, preserved Escape behavior and invoker focus restoration, and exercised pointer exit through the focused browser suite. |
| QG-2 | Harness claim chips were omitted from the rendered label-containment inventory | Phase 7 | Promoted all five desktop and mobile claims to measurable nodes, retained readable font sizes, corrected chip geometry, and passed all 6 responsive widths in both motion modes. |

> Finalized on 2026-09-01 at the v4.4.0 publication. DF-1 remains open and owned by this ledger; it is a vendor-asset availability limit, not a defect, and will be ingested by the next `/plan`.

## v4.4.1 - guide-visual-and-arcade-rebuild

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 0 | 7 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Warnings

##### WN-1 - Phase 1 ran one model tier below the plan's recommendation

- **Source phase**: Phase 1 routing pre-flight.
- **Plan reference**: Phase 1 `**Recommended model tier**: frontier` / `**Recommended effort level**: max`.
- **Reason**: The refreshed model map places the session's `claude-opus-5` at the `strong` tier, while the phase recommends `frontier` (`claude-fable-5`). Claude Code cannot switch models programmatically, so the delta was surfaced at the pre-flight and the maintainer chose to continue on Opus 5 at max effort rather than switch. This is a recorded decision, not a silent downshift, and no mid-phase downshift occurred.
- **Impact**: None observed. Every Phase 1 gate passed, including the fail-closed browser suite, and the two load-bearing outputs (the measured vector mark and the asset ledger) were independently verified by render and by hash.
- **Suggested next step**: Re-surface the tier recommendation at each subsequent phase pre-flight. Phases 3, 4, 5, and 7 are also rated frontier/max and carry more implementation risk than Phase 1, so the same choice should be made deliberately rather than inherited.

##### WN-2 - The Phase 1 superseded-assertion register was incomplete

- **Source phase**: Phase 2 - Home identity, platform rail, and workflow loop.
- **Plan reference**: `docs/releases/v4/v4.4/development/guide-visual-and-arcade-rebuild/phase-1-contract.md` section 2.
- **Reason**: Phase 2 broke four assertions the register had not listed. Three pinned literal implementation strings (the exact hero markup, the exact text of a `querySelectorAll` selector, and a `data-logo-source` attribute selector inside a browser evaluation block) and are structurally invisible to a register built by reading requirements. The fourth was a measurement that became wrong rather than stale: `Range.getClientRects()` counts inline fragments, so a two-span title reported five "lines" on one visual line.
- **Impact**: None shipped. Every case was caught by running the suite, corrected in the same commit, and the two structural rows plus the generalized lesson were added to the register. The risk is to LATER phases, which edit the same shared markup and script.
- **Suggested next step**: Before Phases 3 through 6 change shared markup or shared script, grep the test suite for the literal strings being changed rather than trusting the register alone. Re-check at Phase 7 whether any register row was updated without a matching assertion change, or the reverse.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| BG-1 | The plan document leaked personal filesystem paths | Phase 1 | Sub-task 1.3 named the local Cursor candidates as absolute `C:/Users/<user>/Downloads/...` paths. `validate_no_personal_paths.py` reported 4 findings against the plan file, and that validator runs in `make validate` and CI, so the plan as authored would have failed the pipeline on commit. Redacted to a username-free `~/Downloads/...` form; the scanner is clean. |
| DF-1 | The four Phase 4 output-media assets were not yet staged | Phase 4 | All four generated as ORIGINAL local media (procedural balloon SVG, ten-frame Pillow sunrise GIF, a poster drawn from the same geometry constants, and a stdlib-synthesized two-note chime WAV), hashed into ledger section 3 as SETTLED, then embedded. `test_v441_phase4_foundations.py` decodes every embedded payload and hash-matches it against the staged file, so the approved-bytes-only rule is enforced, not assumed. |
| BG-7 | A dead animation primitive kept a reduced-motion check alive | Phase 3 | `fx-grow` lost its only consumer when the SVG context-budget diagram became an HTML node tree, leaving three orphan CSS rules and a reduced-motion assertion that failed on an empty element set. The CSS was deleted and the check made vacuously safe while staying strict for any element that exists, plus a guard asserting `fx-grow` is absent so a reintroduced consumer must restore its static state. |
| BG-6 | Tokens diagram caption text was clipped at the SVG viewBox edge | Phase 3 | Two caption lines ran past the 360-unit viewBox width and were cut mid-word. SVG text does not wrap, so the captions moved to an HTML paragraph below the diagram and the viewBox height was trimmed to match. |
| BG-5 | Unbalanced HTML re-parented the Training page out of `main` | Phase 3 | A two-step `<section>`-to-`<div>` conversion had its first step refused by a guard assertion, but the second step ran anyway, pairing `<section>` openings with `</div>` closings. The browser re-parented everything after the error, so `#page-training` became a direct child of `<body>` and presentation mode's inert walk never reached `.site-header`. A Training test caught a Foundations markup bug. Both opening tags were converted and the ancestor chains re-verified in the browser. |
| BG-4 | Narrow-screen layout overrides lost to source order | Phase 3 | The stacking rules for the new Foundations components were placed in a `@media` block ABOVE the base rules they override. A media query adds no specificity, so the later base rule won and `.fx-states` still computed three columns at 320 px, overflowing the viewport. The overrides were moved below their definitions with a comment recording why the position is load-bearing. |
| BG-3 | The hero heading's line box could not contain its own text | Phase 2 | `.hero-wordmark` used `line-height: 1`, making the h1 line box (68 px at 1440) shorter than its inline children's content boxes (90 px). The visual-defect detector reported 12 HIGH `parent-padding-escape` findings once Phase 2's two-span title gave it child elements to measure; the condition pre-dated Phase 2 and was simply unobservable with a bare text node. Raised to `line-height: 1.34`, which contains the font ascent and descent at every clamp size. Detector then passed both themes with 0 findings. |
| BG-2 | The plan's model map listed a Flash model as the Google frontier tier | Phase 1 | `## Current model map` carried `gemini-3.7-flash` in the frontier slot where the vendor documents `gemini-3.1-pro-preview`. The identical defect was corrected in `catalog/skills/ai-development/model-routing/references/last-known-model-map.json` during the v4.4.0 release, so the plan had inherited it. The plan's map is corrected and annotated, with the strong/standard split recorded as a maintainer judgment. |

> Not finalized. v4.4.1 is in progress; this section is appended per phase and reconciled at the plan's final phase.
