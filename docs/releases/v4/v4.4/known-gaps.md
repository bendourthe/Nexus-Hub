# Known Gaps - v4.4

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-08-31

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
| MT-1 | Main CI does not enforce browser-backed guide verification | Phase 7 | Added the scoped `guide-render` job with Playwright Chromium and `NEXUS_REQUIRE_RENDER=1`, wired it into `ci-required`, passed 67 workflow contract tests, and ran the exact fail-closed guide and detector targets locally with 154 passed and one explicit optional portfolio-copy skip. Remote clean-runner execution remains a publication gate rather than claimed local evidence. |
| BG-1 | Training API accepted non-integer numeric scene indexes and corrupted exported state | Phase 7 | Restricted numeric navigation to in-range integers and added browser proof that `NaN` and fractional indexes preserve the current scene; the current focused Training explorer suite passed 3 tests. |
| BG-2 | Training presentation mode painted the game and terminal over later regions | Phase 7 | Restored natural grid height inside the scrollable presentation slide and added rectangle-separation checks at 1920x1080, 1440x900, 1024x768, and 900x900. |
| BG-3 | Training presentation mode allowed focus to escape and did not restore its invoker | Phase 7 | Added dialog semantics, background isolation, a Tab loop, early Escape handling, and post-fullscreen focus restoration; the current fail-closed Training explorer suite passed 3 tests in 21.22 seconds. |
| BG-4 | Denied-fullscreen presentation fallback survived route changes and left the destination inert | Phase 7 | Exit presentation when hash routing leaves Training, restore the recorded inert states, and prove that a rejected Fullscreen API followed by `#home` navigation leaves Home and the site header operable. |
| BG-5 | Presentation mode had no visible close control inside its isolated dialog | Phase 7 | Added an in-dialog `Exit presentation` control, preserved Escape behavior and invoker focus restoration, and exercised pointer exit through the focused browser suite. |
| QG-2 | Harness claim chips were omitted from the rendered label-containment inventory | Phase 7 | Promoted all five desktop and mobile claims to measurable nodes, retained readable font sizes, corrected chip geometry, and passed all 6 responsive widths in both motion modes. |
