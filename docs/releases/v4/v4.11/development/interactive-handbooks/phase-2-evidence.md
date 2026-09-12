# v4.11.0 interactive handbooks - Phase 2 evidence

The shared offline runtime manages one active deck, retained reading position and focus, automatic builds and independent authored slide state. It is exercised through inline browser output and both real installer paths. This is runtime qualification; production assembly and visual design qualification remain in Phases 3 and 6.

## Observed runtime behavior

- `python -m pytest tests/skills/test_presentify_dual_view_runtime.py -q`: 17 passed. All six slides tested at 1366x768, 1280x720, 1536x784, 1920x850, 1920x851 and 390x844. The long source heading is used; desktop slides have no overflow and compact reflow is explicit.
- Title/global entry resets to slide 1; chapter entry targets slide 4; Back/Next/Home/End and history share state. Invalid hashes preserve the reading page. Closing restores the saved reading position and opener focus.
- Real Chromium fullscreen entry includes usable controls and a nested modal. Native exit returns to reading; the explicit fullscreen toggle keeps fitted mode. Denial remains usable. A delayed rejected/interrupted request cannot reopen a closed deck.
- Input and declared chart/directory regions keep native keys; Tab remains in the deck; nested Escape closes details first in fitted mode. Touch swipe advances once and native input gestures do not advance. Empty storyboards fail visibly; the 48-slide fixture retains bounded controls.
- Process delays are 0 and 260 ms for steps 0 and 2; comparison marks begin together. At 100 ms the later process step is hidden and marks are partially revealed. Replay retains four managed animations rather than duplicating them. Reduced motion shows complete content instantly. Hidden documents and inactive slides have zero runtime animation work. Reading animations pause while the deck is open and resume on exit.
- No JavaScript retains reading content with unavailable presentation controls hidden. Print emits the reading page once. Detached local-file open records no outbound requests.

## Coverage, lint and rendered inspection

V8 precise block ranges mapped to the first code position of each nonblank code line: 186/205 lines, 90.73%. [Retained coverage](phase-2-runtime-coverage.json) binds this measurement to the runtime SHA-256. This is a V8 range-based metric, not an Istanbul branch-coverage claim; separate native-fullscreen tests exercise paths absent from the denial-based coverage probe.

`node --check catalog/skills/specialized-domains/document-to-interactive-html/assets/dual-view-runtime.js` passed. Ruff checks passed on both new test modules. Bundle audit: 336 skills, 0 errors, 64 existing advisory warnings.

The real runtime screenshot was inspected; it is a deliberately plain behavior harness rather than a production-design specimen. Native control text was enlarged to inherit the runtime text size. `detect_visual_defects.py` on the detached runtime artifact at fragment slide-1 and widths 390/1366 passed with 0 findings and 2 scoped exceptions. The exact exception is retained in `tests/fixtures/interactive-handbooks/runtime-visual-exceptions.json`: the intentionally scrolling directory child exceeds its viewport. Desktop stage overflow remains forbidden and tested independently.

## Corrections and negative evidence

The initial visual probe found absent hash-target IDs; the runtime now supplies slide-N IDs when authors omit them. The second probe found reading content still painted behind the modal and a fixed paragraph width; the page now hides while presented and the fixed limit was removed. A new test stalled because its Playwright setup returned an unresolved promise; the test setup now returns void. The stalled run was interrupted and the corrected suite passed. These are resolved failures, not first-build passes.

## Distribution and CI impact

`python -m pytest tests/skills/test_presentify_dual_view_distribution.py -q`: 2 passed on Windows, running Git Bash and Windows PowerShell installers into independent temporary Claude workspaces with the specialized-domains module. Installed runtime/CSS/reference bytes match the source bundle; installed inline output enters, advances and exits with no browser errors. `python scripts/check_installer_parity.py`: PASS. No live user configuration was used as an install target. Native Linux/macOS execution remains part of the final platform matrix.

Existing tests/skills discovery covers these tests; the slow marker makes the two installer exercises explicit. No dependency, secret, external service, pipeline file or remote CI run was added. Phase 7 owns terminal CI reconciliation. Browser availability is required by these runtime assertions, not a silent skip.

## Post-phase sequence

Gitignore: 0 patterns added; runtime artifacts stay in temporary directories. Final post-phase review: 292 tests passed, 2 slow tests deselected and separately passed; Ruff and git diff --check passed. The shared reference links both new assets. Documentation audit retains the new records in the active release tree, with no deletion or archive move. Product version remains 4.9.0 pending the later release workflow.
