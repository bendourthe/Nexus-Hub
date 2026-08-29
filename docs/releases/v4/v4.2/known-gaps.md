# Known Gaps - v4.2

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-08-29

## v4.2.0 - interactive-guide-redesign

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |

### Open Items

None. DF-1 and QG-1 closed in the v4.2.1 last-phase close-out.

### Resolved

#### Deferred

##### DF-1 - Phase 1 guide baseline has no rendered browser screenshots

- **Source phase**: Phase 1 - Baseline, content model, and UX contract
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md` T001
- **Evidence at deferral**: This implementation session had no browser tools. The plan said not to block: capture a static source audit and a hallmark-from-markup table, then record a known-gap that last-phase human testing must fill.
- **Resolution**: Maintainer screenshots that triggered the v4.2.1 visual-education plan exist (visual QA ledger dated 2026-08-29). Remaining Lighthouse Accessibility, last-phase rendered visual QA, and workshop 4-of-5 stay open as v4.2.1 DF-1 rather than as a claim that 4.2.0 had no pictures at all.
- **Resolved in**: v4.2.1 Phase 7 close-out on 2026-08-29

#### Quality-Gate Gaps

##### QG-1 - Local full repo pytest suite did not finish in the last-phase session

- **Source phase**: Phase 7 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md` T033
- **Evidence at deferral**: `python -m pytest --collect-only -q tests` collected 3526 tests. A local run reached about 16 percent after 11 minutes and was interrupted. Focused guide tests and `python scripts/ci/run.py --profile fast` were green.
- **Resolution**: Pull request [#145](https://github.com/bendourthe/Nexus-Hub/pull/145) merged to `develop` at `38a63ddc` with the `pytest tests` job as the full-suite proof named in the original next action.
- **Resolved in**: v4.2.1 Phase 7 close-out on 2026-08-29

### Inherited Ledger Review

- v4.1.0 DF-1 / WN-1 / QG-1 and v4.1.1 DF-1 stay on `docs/releases/v4/v4.1/known-gaps.md`. This plan does not absorb them.
- v4.0 DF-1 stays on `docs/releases/v4/v4.0/known-gaps.md`.
- No `## v3.20.0` section is appended to v3.16 or v3.20 ledgers.

## v4.2.1 - guide-visual-education

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |

### Open Items

#### Deferred

##### DF-1 - Last-phase Lighthouse Accessibility, rendered visual QA, and workshop 4-of-5 were not run

- **Source phase**: Phase 7 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md` T024
- **Reason**: This Cursor session had no browser automation. Structural tests in `tests/guides/test_nexus_hub_guide.py` pass (38 passed, 1 skipped). No five-person workshop cohort was available; do not invent one.
- **Suggested next step**: After merge, open `guides/website/nexus-hub-guide.html` and re-check the ten visual QA ledger items in light and dark at 1440x900, 1024x768, 390x844, and 1920x1080; run Lighthouse Accessibility in both themes (target >=90); confirm keyboard slideshow, reduced-motion Foundations, `file://` untrusted-origin warning, and Cheatsheets hash redirects. Record a bounded non-pass for workshop 4-of-5 if participants are unavailable.

#### Quality-Gate Gaps

##### QG-1 - Local full repo pytest suite did not finish in this last-phase session

- **Source phase**: Phase 7 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md` T025
- **Reason**: `python -m pytest --collect-only -q tests` collected 3534 tests. CI budgets `tests` at 4500s. A local run reached about 16 percent after eight minutes and was stopped. Focused `tests/guides/test_nexus_hub_guide.py` (38 passed, 1 skipped) and `python scripts/ci/run.py --profile fast` (12 passed) are green.
- **Suggested next step**: Treat the integration pull request `pytest tests` job as the full-suite proof. Do not merge on a red `ci-required`.

### Resolved

None yet.

### Inherited Ledger Review

- Closed v4.2.0 DF-1 and QG-1 stay under `## v4.2.0` as Resolved. This patch does not absorb v4.1 or v4.0 gaps.

## v4.2.2 - guide-cinematic-rebuild

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - Unicode-safety validator does not scan `.html`, so the guide is outside the sanitize gate

- **Source phase**: Phase 1 - Design brief, design system, shell, and render harness
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md` T003
- **Reason**: `scripts/validate_unicode_safety.py` `TEXT_EXTENSIONS` excludes `.html`; the rebuilt guide relies on HTML entities and review instead. Extending the validator is outside this plan's changed-line scope.
- **Suggested next step**: A future patch adds `.html` (or a guide-specific entity allowlist) to the validator and grandfathers existing archives.

#### Missing Tests

##### MT-1 - Render harness has an import test but no functional test

- **Source phase**: Phase 1 - Design brief, design system, shell, and render harness
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md` T002
- **Reason**: `tests/guides/tools/render_guide.py` is exercised manually per phase (24 screenshots per full sweep); an automated Playwright test would force a browser download in CI, which the offline-first pipeline deliberately avoids.
- **Suggested next step**: Keep manual; if CI ever gains a browser cache, add one smoke render behind an opt-in marker.

### Resolved

None yet.

### Inherited Ledger Review

- v4.2.1 DF-1 (rendered visual QA) and QG-1 (full-suite proof) remain open on the `## v4.2.1` section; this plan's Phase 7 reconciles both (per-phase render evidence closes the visual half; the integration PR's `pytest tests` job closes the suite half).
