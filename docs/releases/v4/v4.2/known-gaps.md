# Known Gaps - v4.2

**Project**: Nexus-Hub
**Status**: finalized 2026-08-31, at `/update release`; shipped within the v4.3.0 cut
**Note**: v4.2.0 through v4.2.3 were developed and documented as separate minors but were never tagged, so their work is published inside v4.3.0. Items still open below remain owned by THIS ledger and were deliberately not absorbed into v4.3's, matching the convention v4.1's ledger states; v4.3's Phase 5 reconciliation judged each on evidence and recorded why it stayed open.
**Last updated**: 2026-08-31 (v4.4.0 Phase 7 reconciliation)

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
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |

### Open Items

None. DF-1 and QG-1 were reconciled in the v4.2.2 last-phase close-out (2026-08-29); see Resolved.

### Superseded note

v4.2.1's UI was never published. The v4.2.2 plan (`plans/v4.2.2-guide-cinematic-rebuild.md`) re-engineered the guide from the ground up and is the first public cut. v4.2.1's phase work remains in git history; its publication step (T026) was never run, by maintainer decision on 2026-08-29.

### Resolved

#### Deferred

##### DF-1 - Last-phase Lighthouse Accessibility, rendered visual QA, and workshop 4-of-5 were not run

- **Source phase**: Phase 7 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md` T024
- **Reason**: This Cursor session had no browser automation. Structural tests in `tests/guides/test_nexus_hub_guide.py` pass (38 passed, 1 skipped). No five-person workshop cohort was available; do not invent one.
- **Suggested next step**: After merge, open `guides/website/nexus-hub-guide.html` and re-check the ten visual QA ledger items in light and dark at 1440x900, 1024x768, 390x844, and 1920x1080; run Lighthouse Accessibility in both themes (target >=90); confirm keyboard slideshow, reduced-motion Foundations, `file://` untrusted-origin warning, and Cheatsheets hash redirects. Record a bounded non-pass for workshop 4-of-5 if participants are unavailable.
- **Resolution**: v4.2.2 made rendered browser QA a per-phase gate rather than a last-phase hope. `tests/guides/tools/render_guide.py` produced 77 committed screenshots across six phase sets, each reviewed with a written verdict in `development/guide-rebuild/render-review.md`; rendering caught six defects that markup tests could not see. Contrast was measured on 217 unique text styles in both themes (0 below WCAG AA, four tokens corrected), and keyboard reachability, reduced motion, and animation gating were verified in-browser. The `file://` untrusted-origin warning item is void: the warning box was removed by maintainer decision. The five-person workshop remains genuinely un-run and is NOT claimed; it is carried to v4.2.2 as a bounded non-pass under human testing, since no cohort exists to run it.
- **Resolved in**: v4.2.2 Phase 7 close-out on 2026-08-29

#### Quality-Gate Gaps

##### QG-1 - Local full repo pytest suite did not finish in this last-phase session

- **Source phase**: Phase 7 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md` T025
- **Reason**: `python -m pytest --collect-only -q tests` collected 3534 tests. CI budgets `tests` at 4500s. A local run reached about 16 percent after eight minutes and was stopped. Focused `tests/guides/test_nexus_hub_guide.py` (38 passed, 1 skipped) and `python scripts/ci/run.py --profile fast` (12 passed) are green.
- **Suggested next step**: Treat the integration pull request `pytest tests` job as the full-suite proof. Do not merge on a red `ci-required`.
- **Resolution**: superseded by the v4.2.2 close-out, which runs the full local suite to completion before publication (see `development/last-phase-evidence.md`, "Full-suite testing and stabilization") and still gates the merge on a green `ci-required`.
- **Resolved in**: v4.2.2 Phase 7 close-out on 2026-08-29

### Inherited Ledger Review

- Closed v4.2.0 DF-1 and QG-1 stay under `## v4.2.0` as Resolved. This patch does not absorb v4.1 or v4.0 gaps.

## v4.2.2 - guide-cinematic-rebuild

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 1 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-2 - The five-person workshop validation was not run

- **Source phase**: Phase 7 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md` T027
- **Reason**: Inherited from v4.2.1 DF-1. No cohort of five participants exists to run a workshop against. Rendered QA, WCAG AA contrast, keyboard, and reduced-motion checks were all run and are recorded; the workshop specifically was not, and is not claimed.
- **Suggested next step**: When a cohort is available, run the eight-step Training walkthrough with five people and record where they stall. Until then this stays open rather than being marked satisfied by proxy evidence.

##### DF-1 - Unicode-safety validator does not scan `.html`, so the guide is outside the sanitize gate

- **Source phase**: Phase 1 - Design brief, design system, shell, and render harness
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md` T003
- **Reason**: `scripts/validate_unicode_safety.py` `TEXT_EXTENSIONS` excludes `.html`; the rebuilt guide relies on HTML entities and review instead. Extending the validator is outside this plan's changed-line scope.
- **Reconciliation evidence**: On 2026-08-31, `scripts/validate_unicode_safety.py` still omitted `.html` from `TEXT_EXTENSIONS`, so the visual HTML detector did not close this text-sanitization gap.
- **Suggested next step**: A future patch adds `.html` (or a guide-specific entity allowlist) to the validator and grandfathers existing archives.

### Resolved

#### Missing Tests

##### MT-1 - Render harness has an import test but no functional test

- **Source phase**: Phase 1 - Design brief, design system, shell, and render harness
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md` T002
- **Evidence at deferral**: `tests/guides/tools/render_guide.py` was exercised manually per phase, but no automated functional browser test existed.
- **Resolution**: v4.4.0 added `tests/guides/test_render_guide_tool.py::test_explicit_output_root_writes_local_browser_evidence`, which invokes the renderer through a real Chromium context and verifies a non-empty PNG in an isolated output root. A fresh fail-closed run with `NEXUS_REQUIRE_RENDER=1` returned `1 passed, 17 deselected`.
- **Resolved in**: v4.4.0 Phase 7 reconciliation on 2026-08-31

### Inherited Ledger Review

- v4.2.1 DF-1 (rendered visual QA) and QG-1 (full-suite proof) are resolved under `## v4.2.1` by the evidence recorded there.

## v4.2.3 - guide-refinement

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 1 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

DF-1 and DF-2 remain open from v4.2.2. MT-1 is resolved below by functional browser evidence added in v4.4.0.

#### Deferred

##### DF-1 - Unicode-safety validator does not scan `.html`, and misses wrong-script glyphs

- **Source phase**: carried from v4.2.2 DF-1; re-confirmed in v4.2.3 Phase 7
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.3-guide-refinement.md` T026
- **Reason**: `scripts/validate_unicode_safety.py` excludes `.html` from `TEXT_EXTENSIONS`, so the guide is outside the gate entirely. This cycle also showed the validator misses a second class in files it DOES scan: writing the v4.2.3 plan introduced a stray CJK character (U+6539) into a `.md` file, the validator scanned it and reported "repaired 0 files", and a separate scan caught it. The tool flags invisible characters and smart punctuation, not a valid-but-wrong-script glyph.
- **Reconciliation evidence**: On 2026-08-31, `.html` remained absent from `TEXT_EXTENSIONS` and no script-range check was present, so both parts of this gap remain open.
- **Suggested next step**: add `.html` to `TEXT_EXTENSIONS` (grandfathering existing archives), and add a script-range check that flags characters outside the expected scripts for an English document.

##### DF-2 - The five-person workshop validation was not run

- **Source phase**: carried from v4.2.2 DF-2
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.3-guide-refinement.md` T031
- **Reason**: no cohort of five participants exists. Rendered QA, WCAG AA contrast, keyboard, and reduced-motion checks were all run and recorded; the workshop specifically was not, and is not claimed.
- **Suggested next step**: when a cohort is available, run the eight-step Training walkthrough with five people and record where they stall.

### Resolved

#### Missing Tests

##### MT-1 - Render harness has an import test but no functional test

- **Source phase**: carried from v4.2.2 MT-1
- **Plan reference**: `docs/releases/v4/v4.2/plans/v4.2.3-guide-refinement.md` T026
- **Evidence at deferral**: `tests/guides/tools/render_guide.py` was exercised manually every phase, but no automated functional browser test existed.
- **Resolution**: v4.4.0 added `tests/guides/test_render_guide_tool.py::test_explicit_output_root_writes_local_browser_evidence`, which invokes the renderer through a real Chromium context and verifies a non-empty PNG in an isolated output root. A fresh fail-closed run with `NEXUS_REQUIRE_RENDER=1` returned `1 passed, 17 deselected`.
- **Resolved in**: v4.4.0 Phase 7 reconciliation on 2026-08-31

This release also resolved user-reported UI defects, which are tracked in the plan's Goal review rather than as known gaps.

### Inherited Ledger Review

- v4.2.1's DF-1 and QG-1 stay Resolved under `## v4.2.1`. The v4.1.0 and v4.1.1 DF-1 items remain open on their source ledger; v4.1.0 WN-1 and QG-1 were resolved during the v4.4.0 Phase 7 reconciliation.
