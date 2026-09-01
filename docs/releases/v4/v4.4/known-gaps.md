# Known Gaps - v4.4

**Project**: Nexus-Hub
**Status**: v4.4.0 finalized 2026-09-01 at `/update release`; v4.4.1 in progress on the same minor
**Last updated**: 2026-09-01 (v4.4.1 Phase 1)

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
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 2 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - The four Phase 4 output-media assets are not yet staged

- **Source phase**: Phase 1 - Contracts, asset provenance, and byte budget (sub-task 1.3).
- **Plan reference**: `docs/releases/v4/v4.4/plans/v4.4.1-guide-visual-and-arcade-rebuild.md` sub-task 1.3 / T003.
- **Reason**: The plan's Phase 1 stability gate permits each output-media candidate to be either staged now or "recorded as a Phase 4 blocker", and the maintainer approved the deferral. `model-output-image.svg`, `model-output-video.gif`, `model-output-video-poster.svg`, and `model-output-audio.wav` will be generated as ORIGINAL local media in the phase that consumes them, so no third-party media enters the ledger.
- **Impact**: Blocks Phase 4 only. Phase 2 and Phase 3 are unblocked, because they consume the five approved platform marks rather than output media.
- **Suggested next step**: In Phase 4, generate each asset locally, record its provenance and SHA-256 in `asset-provenance.md` section 3, and only then embed it. If the GIF exceeds its Phase 4 byte allocation, fall back to an animated inline SVG and record that substitution with its hash.

#### Warnings

##### WN-1 - Phase 1 ran one model tier below the plan's recommendation

- **Source phase**: Phase 1 routing pre-flight.
- **Plan reference**: Phase 1 `**Recommended model tier**: frontier` / `**Recommended effort level**: max`.
- **Reason**: The refreshed model map places the session's `claude-opus-5` at the `strong` tier, while the phase recommends `frontier` (`claude-fable-5`). Claude Code cannot switch models programmatically, so the delta was surfaced at the pre-flight and the maintainer chose to continue on Opus 5 at max effort rather than switch. This is a recorded decision, not a silent downshift, and no mid-phase downshift occurred.
- **Impact**: None observed. Every Phase 1 gate passed, including the fail-closed browser suite, and the two load-bearing outputs (the measured vector mark and the asset ledger) were independently verified by render and by hash.
- **Suggested next step**: Re-surface the tier recommendation at each subsequent phase pre-flight. Phases 3, 4, 5, and 7 are also rated frontier/max and carry more implementation risk than Phase 1, so the same choice should be made deliberately rather than inherited.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| BG-1 | The plan document leaked personal filesystem paths | Phase 1 | Sub-task 1.3 named the local Cursor candidates as absolute `C:/Users/<user>/Downloads/...` paths. `validate_no_personal_paths.py` reported 4 findings against the plan file, and that validator runs in `make validate` and CI, so the plan as authored would have failed the pipeline on commit. Redacted to a username-free `~/Downloads/...` form; the scanner is clean. |
| BG-2 | The plan's model map listed a Flash model as the Google frontier tier | Phase 1 | `## Current model map` carried `gemini-3.7-flash` in the frontier slot where the vendor documents `gemini-3.1-pro-preview`. The identical defect was corrected in `catalog/skills/ai-development/model-routing/references/last-known-model-map.json` during the v4.4.0 release, so the plan had inherited it. The plan's map is corrected and annotated, with the strong/standard split recorded as a maintainer judgment. |

> Not finalized. v4.4.1 is in progress; this section is appended per phase and reconciled at the plan's final phase.
