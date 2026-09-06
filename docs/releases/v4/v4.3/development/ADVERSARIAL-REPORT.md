# v4.3.0 Adversarial Verification Report

**Date**: 2026-08-30
**Scope**: Functional-verification visual detector, responsive HTML guard parity, and installer postconditions
**Method**: Read-only inspection plus fresh execution of existing repository tests and fixtures; no new hostile inputs or implementation changes

## Verdict

**APPROVE** for the scoped v4.3.0 robustness gate. The three previously confirmed detector findings are fixed on the tested tree, the clean control remains clean, responsive-guard Bash/PowerShell parity passes, and installer postconditions remain intact. This verdict does not replace the plan's remaining CI, platform-contract, publication, or integration gates.

## Attack Surface

| # | Entry Point | Input Source | Trust Level | Data Type | Evidence Route |
|---|---|---|---|---|---|
| E-1 | Detector numeric CLI controls | Command-line arguments | Untrusted | Floating-point strings | Parameterized CLI regression tests and direct `--tolerance Infinity` invocation |
| E-2 | Rendered HTML and CSS declaration scan | Local HTML with embedded and inline CSS | Semi-trusted | DOM and CSSOM | Variable-cap regression fixture at 900 px |
| E-3 | Linked local stylesheet inspection | `file:` stylesheet loaded by the target HTML | Semi-trusted | Bounded UTF-8 CSS | Linked variable-cap route in the same regression fixture |
| E-4 | Visible geometry excluded from the accessibility tree | Rendered DOM carrying `aria-hidden="true"` | Semi-trusted | Element geometry and semantic text metadata | Aria-hidden visible-geometry fixture at 900 px |
| E-5 | Responsive HTML write guard | Tool JSON consumed by Bash and PowerShell hooks | Untrusted | JSON and HTML/CSS fragments | Dual-host hook behavior and sibling-parity tests |
| E-6 | Installed functional-verification and managed-hook surfaces | Installer materialization and upgrade paths | Trusted repository content crossing a packaging boundary | Files and hook registrations | Installer smoke and managed-upgrade postconditions |

## Fresh Command Receipts

| # | Command | Process Exit | Observed Result | Disposition |
|---|---|---:|---|---|
| R-1 | `python -m pytest -q tests/verification/test_visual_defect_detector.py` | 0 | `26 passed in 19.17s` | Detector-focused suite passed, including all six non-finite control cases and the three prior-finding regressions. |
| R-2 | `python catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py tests/verification/fixtures/visual/clean.html` | 0 | `PASS visual-defect detector: 0 finding(s), 0 allowlisted`; 420, 900, and 1440 px viewports all reported `page_pass: true`. | Clean control remained clean. |
| R-3 | `python catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py tests/verification/fixtures/visual/fixed-text-max-width-variable.html --viewports 900` | 1 | Expected gate failure with exactly 3 high `fixed-text-max-width` findings for `#embedded-variable-cap`, `#inline-variable-cap`, and `#linked-variable-cap`; every declaration recorded `resolved_value`. | All embedded, inline, and linked local CSS routes detected. |
| R-4 | `python catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py tests/verification/fixtures/visual/aria-hidden-visible.html --viewports 900` | 1 | Expected gate failure with exactly 1 high `horizontal-overflow` finding at `#aria-hidden-container`; no `font-size-floor` finding. | Visible pixels remained in geometry checks without decorative semantic-text noise. |
| R-5 | `python catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py tests/verification/fixtures/visual/clean.html --tolerance Infinity` | 2 | Argparse rejected the value with `must be a finite number zero or greater`; no detector JSON was emitted. | Non-finite tolerance cannot suppress findings. |
| R-6 | `python -m pytest -q catalog/hooks/tests/test_html_responsive_guard.py catalog/hooks/tests/test_hook_sibling_parity.py::test_blocking_hooks_agree_and_are_correct` | 0 | `47 passed in 16.47s`. | Existing responsive-guard behaviors and blocking-hook Bash/PowerShell parity passed. |
| R-7 | `python -m pytest -q tests/installer/test_managed_hook_upgrade.py tests/installer/test_installer_smoke_postconditions.py` | 0 | `20 passed in 28.04s`. | Managed-hook upgrade and installed-artifact postconditions passed. |

Expected detector gate exits of 1 in R-3 and R-4 are successful defect detections, not command failures. R-5's exit 2 is the expected CLI usage-error contract.

## Prior Finding Disposition

### AF-1: Non-finite numeric CLI controls

**Prior failure**: A non-finite tolerance could neutralize numeric comparisons and allow a broken page to pass.

**Observed correction**: The numeric parsers reject non-finite values before browser startup. The focused suite passed six existing cases spanning `Infinity` and `NaN` across tolerance, minimum text dimensions, font floor, and settle time. The direct tolerance invocation returned process exit 2 with a finite-number error.

**Status**: FIXED.

### AF-2: CSS custom-property text caps

**Prior failure**: `max-width: var(...)` could evade the fixed `px`/`ch` declaration rule, including linked local CSS that browser CSSOM access did not expose on a `file:` page.

**Observed correction**: The detector resolves custom-property chains against computed style and supplements inaccessible local linked CSS through bounded local reads without weakening browser file isolation. The existing regression fixture produced exactly three gate findings, one each for embedded, inline, and linked CSS, with the resolved `60ch`, `48ch`, and `640px` evidence recorded.

**Status**: FIXED.

### AF-3: Visible geometry under `aria-hidden="true"`

**Prior failure**: Treating `aria-hidden="true"` as visually hidden could exclude pixels that still overflow on screen.

**Observed correction**: The detector keeps aria-hidden elements in pixel-geometry analysis while excluding their decorative text from semantic size and font-floor rules. The existing fixture produced the intended horizontal-overflow finding and no font-floor noise.

**Status**: FIXED.

## Confirmed Findings on Corrected Tree

None in the scoped retest. No proof-of-failure remained after the existing regression fixtures and focused suites were executed against the corrected tree.

## Considered but Rejected

| # | Candidate | Counter-Hypothesis and Actual Routes | Observed Rejection Evidence |
|---|---|---|---|
| RJ-1 | Closed disclosure content may create false positive geometry or font findings. | The relevant route is a closed native `details` descendant in the clean fixture; the visible `summary` remains applicable while the collapsed descendant is not rendered. | R-1 passed the focused regression and R-2 reported zero findings across all three default viewports. |
| RJ-2 | Linked local CSS may remain invisible because `file:` CSSOM access can throw. | The actual routes are embedded rules, inline declarations, and linked local stylesheet text; linked HTTP CSS is not part of this local-only detector route. | R-3 produced one distinct high finding for every applicable route, including `#linked-variable-cap` with `640px` resolution evidence. |
| RJ-3 | Excluding aria-hidden text from semantic checks may also hide its visible layout defect. | The actual geometry route is the aria-hidden element's rendered overflow inside its visible container; the semantic font-floor route is intentionally not applicable to decorative text. | R-4 detected `horizontal-overflow` at the container and emitted no font-floor finding. |
| RJ-4 | Bash and PowerShell responsive guards may disagree at the blocking boundary. | The actual hook routes are the same existing JSON payload cases executed through both siblings. | R-6 passed all 47 behavior and targeted parity cases. |
| RJ-5 | Correct repository behavior may fail after installer materialization or managed upgrade. | The applicable routes are installer smoke materialization and managed-hook upgrade postconditions. | R-7 passed all 20 installer checks. |

## Needs Live Validation

None for the three prior findings within this local detector and installer scope. Remote CI, provider platform behavior, publication, and integration are separate plan gates and were not evaluated by this report.

## Untested Areas

| Area | Reason Not Tested | Risk Treatment |
|---|---|---|
| New adversarial strings or synthetic fixtures | The assigned retest explicitly limited execution to existing tests and fixtures. | No coverage claim beyond the enumerated routes. |
| Remote stylesheets and network-origin pages | The detector's tested workflow is local-only and blocks outbound requests. | Out of scope for this report. |
| Remote CI and platform discovery contracts | Owned by separate Phase 5 gates. | This approval is explicitly scoped and cannot close those gates. |
| Full repository suite | A prior full-suite run exists elsewhere in Phase 5 evidence, but this independent retest used the narrowest suites covering the corrected surfaces. | No fresh full-suite claim is made here. |

## Overall Assessment

**Verdict**: APPROVE

**Current confirmed vulnerabilities**: 0

**Recommendation**: Accept the corrected detector, responsive-guard parity, and installer postconditions for the scoped robustness gate, then continue the independent CI, platform-contract, publication, and integration gates before any release-level completion claim.
