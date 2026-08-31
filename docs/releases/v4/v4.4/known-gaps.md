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
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |

### Open Items

#### Deferred

##### DF-1 - Three platform entries use text treatments pending approved standalone marks

- **Source phase**: Phase 1 - Home identity, platforms, installation, and comparison.
- **Plan reference**: `docs/releases/v4/v4.4/plans/v4.4.0-guide-depth-and-training-rebuild.md` sub-task 1.2 / T002.
- **Reason**: Current official assets provide a verified Claude icon, Cursor cube, and OpenCode logo. The OpenAI brand pack does not provide a ChatGPT-specific SVG, Gemini product-icon use requires documented partner approval, and current GitHub guidance does not support using the Copilot bot as a standalone hero mark. Phase 1 therefore uses labelled text treatments for ChatGPT, Gemini, and GitHub Copilot instead of inventing or misapplying trademark geometry.
- **Suggested next step**: Replace an individual text treatment only after its vendor publishes a distributable standalone product mark or grants documented permission, then add the exact asset provenance and rerun both-theme contrast and geometry tests.

#### Missing Tests / Coverage Gaps

##### MT-1 - Main CI does not enforce browser-backed guide verification

- **Source phase**: Phase 1 - Testing and stabilization.
- **Plan reference**: `docs/releases/v4/v4.4/plans/v4.4.0-guide-depth-and-training-rebuild.md` sub-task 1.5 / T005 and Phase 7 pipeline reconciliation.
- **Reason**: The full profile collects all guide and detector tests, but a clean GitHub Actions runner does not install Playwright or Chromium and does not set `NEXUS_REQUIRE_RENDER=1`. The real-browser render, console, geometry, theme, and contrast cases therefore skip remotely even though they pass fail-closed on the local Phase 1 host.
- **Suggested next step**: During Phase 7, compare the cost and gate value of installing Chromium in the integration pull-request gate versus a narrowly scoped browser job, then implement the approved option and require the browser cases to run rather than skip.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| QG-1 | Visual detector could not activate hash-routed guide pages | Phase 2 | Added validated `--fragment` routing with visible-target proof, regression coverage, JSON provenance, and owning-skill usage guidance. |
