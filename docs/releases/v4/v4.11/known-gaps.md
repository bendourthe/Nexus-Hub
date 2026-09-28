# Known Gaps - v4.11

**Project**: Nexus-Hub
**Status**: released family with bounded open gaps. v4.11.0 was published at tag `v4.11.0` (`0f68fa1a`) and v4.11.2 at tag `v4.11.2` (`dfe302fb`). No v4.11.1 tag exists; its cache-and-diagram implementation merged into `develop` through PR #232 at `c54dbeb4`, completing T025 as historical closure inside the later released family. The v4.10.0 work shipped inside v4.11.0, so the missing v4.10.0 tag remains an intentional skipped number rather than an unpublished release. Open entries below remain explicit hosted-scan, feature-boundary, or manual-validation limitations.
**Last updated**: 2026-09-25

## Carried into v4.11.0 from earlier cycles - CodeQL backlog

#### SEC-1 - Eight CodeQL alerts newly visible to `main`, five of them high

- **Source**: PR #205 (`develop` -> `main`). CodeQL compares against `main`'s baseline, and `main` had not moved since v4.9.0, so every alert accumulated across the v4.9/v4.10/v4.11 work surfaced at once.
- **Not from this plan.** None originates in the interactive-handbooks work. Alerts 279-282 come from the v4.10 target-manifest git-trust fix, 278 and 283-284 from the v4.9.0 security-audit work, and 285 is a pre-existing cyclic import.
- **The five high alerts are `py/overly-permissive-file`, all test-only.** `tests/skills/test_target_manifest.py` (302, 384, 400, 417) chmods temporary fixtures so the code under test can execute them; `tests/skills/test_safe_artifact.py:390` sets `0o640` on a `tmp_path` file because the permission mode is the INPUT the test asserts `atomic_write_bytes` handles correctly. No shipped artifact, credential, or user-facing path is involved.
- **Deliberately NOT dismissed at release time.** CodeQL is not a required check for `main`, so these never blocked the release. Dismissing five high-severity alerts to clear a red mark during a release is how a real finding gets waved through beside four harmless ones; they are recorded here to be triaged on their own merits instead.
- **Next step**: triage each of the eight against the `used in tests` / false-positive / real-finding split, in a change that is not a release. Confirm in particular that `test_safe_artifact.py:390` is asserting behaviour rather than masking it.
- **Status**: remediation implemented 2026-09-22 and confirmed absent from both CodeQL analyses of PR #234's merge ref (`c858ca9a`); alerts 278-285 remain open against the older `main` baseline, so the hosted alert records are not claimed closed. Alerts 278-282 were deliberate test fixtures, but the current GitHub token lacks the administrative scope required to dismiss them. Their fixture modes now use owner-only execution or owner-read-only preservation, removing the flagged permissive modes without weakening the tests. Alerts 283-284 were removed by expressing the cleanup assertion through nested context managers, and alert 285 was removed by making the existing adapter/base import boundary lazy in both directions. The affected suite passes 138 tests with nine platform skips; the next `main` CodeQL analysis must confirm the alert-state transition.

## v4.11.2 - adoption-document-and-deck-quality
### WN-1 - Every release invalidates the distribution handbook

- **Status**: resolved 2026-09-22. The release workflow now refreshes mapped handbooks before version mutation and the version-upgrade skill, `/update`, and `/implement` all carry the pre-version handbook rule. This keeps the input-sensitive gate intact while moving the rebuild ahead of the pull request instead of discovering it as a CI failure.

- **Observed three times in two days**: v4.11.0's release PR, the plan_status.py registration (#207), and v4.11.2's release PR. Each time `check_handbooks` failed `validate`, each time the fix was identical, and each time the rebuilt output was BYTE-IDENTICAL.
- **Cause**: the `distribution` handbook declares `scripts/installer.sh` and `scripts/installer.ps1` as inputs, and every release bumps a version string in both. The gate hashes the builder and the inputs, not just the output, which is what makes "the same sources now describe different code" visible - so this is the gate working as designed, not a defect in it.
- **Cost**: a mandatory rebuild-and-refresh on every release and on every installer edit, discovered only after CI fails rather than before the PR opens.
- **Why it is recorded rather than fixed here**: the obvious fix - excluding the installers from the handbook's inputs - would blind the gate to the case it exists for, which is an installer change that really does make the handbook wrong. The version string is the only part that churns without changing meaning, and distinguishing it needs the gate to understand content rather than bytes.
- **Suggested next step**: have `/update release` rebuild mapped handbooks and refresh their evidence as a step BEFORE the release commit, in the same pass that regenerates `MANIFEST.sha256`. That converts a recurring CI failure into a routine regeneration, without weakening what the gate checks.
- **Status**: resolved 2026-09-22 by the pre-version handbook refresh rule described above.


**Status**: implementation complete, 7 of 7 phases. Nineteen checks across two
scripts, every one negative-controlled. Reconciled 2026-09-13.

### Summary

Six phases built gates; the seventh reconciled them. No check ships that has not
been observed to fail on a fixture built for it, and no fixture carries more
than one defect, so an over-broad check cannot hide a missing one beside it.

The repository's own handbooks pass every gate with zero findings, which is the
result the source project's audit could not reach - its first version produced
roughly 220 findings on real output and was abandoned.

### MT-5 - RESOLVED within the DOM-text measurement envelope

MT-5 was transferred into this plan from v4.11.0 on the expectation that Phase
5's provenance record would close it. It closes one half.

- **Closed**: a series with no computation behind it now fails `check_attestation.py`. That is the root cause of a fabricated value - a hardcoded list chosen to look right, indistinguishable from data until someone tries to reproduce it.
- **Still open**: a value that exists only in an intermediate animation frame. The attestation covers what the series IS; it does not observe what a chart displays mid-transition, which would need frame sampling during the animation window rather than after it.
- **Next step**: sample the rendered series at two or three points inside the animation window and assert every displayed value lies within the source data's range. The per-slide walk added in Phase 4 already establishes the timing discipline this needs.
- **Status**: resolved 2026-09-24 within the declared DOM-text envelope; canvas pixels and unmapped future values remain outside this check.

**Bounded temporal guard, 2026-09-23**: `measure_handbook.py` now watches DOM-text mutations and animation frames for exact source values named in its independent per-slide inventory. A brief wrong value between the settled samples, including one revealed by a style-only change, fails; absent mappings report `source_value_guard: unchecked`, and missing or ambiguous selectors are unverified. The [archived qualification](../../../archives/v4/v4.11/development/temporal-source-values/verification.md) records six focused controls and a 59-test module run. MT-5 remains open for actual handbook mappings and canvas-painted or otherwise unmapped numbers; a range-only check would not catch the observed in-range fabrication.

**Real-artifact closure, 2026-09-24**: The tracked five-slide presentation fixture supplies a native chart with East 10, Central 15 and West 20, plus a source sentence totaling 45. An [independent inventory](../../../archives/v4/v4.11/development/temporal-source-values/real-artifact-inventory.json) now maps its visible slide-4 total and count sentence. The unchanged retained first-build HTML produced 20 mapped observations at ten viewports and `source_value_guard: pass` with zero findings. Six focused controls, including brief wrong values, style-only revelation, absent mapping and unrelated layout failure, pass. The first build itself remains `fail` with 412 other errors; this is source-value sub-verdict proof, not presentation acceptance. The two current repository handbook sources contain no numeric source facts, so their `unchecked` status remains honest rather than receiving invented mappings. See the [frozen follow-up](../../../archives/v4/v4.11/development/temporal-source-values/real-artifact-verification.md) for hashes, derivation and limits. Future source-backed DOM numbers still require an independent mapping; canvas-painted and unmapped values are not certified.

### Deliberately attested rather than gated

Four tells from the source document have no mechanical check and are recorded as
attestations instead: emoji as section markers, heavy em-dash rhythm, sentences
that announce structure rather than delivering content, and every section
carrying exactly three bullets of similar length.

This is a decision, not an omission. Each needs a judgement about what the
document is FOR, and a check that guessed would be the beauty detector this plan
forbids. `check_attestation.py` fails a missing or empty `authorship` record, so
the review cannot be skipped silently - which is the failure mode that matters.

### No pipeline change was required

Recorded because "no change" and "not checked" look identical afterwards. This
plan added no script under `scripts/` (so neither installer needed an edit),
three skill-bundled scripts (auto-copied by both installers), and five test
files already covered by the existing `repo-tests` glob. `check_installer_parity.py`
passes.

### Carried from earlier cycles, unchanged by this plan

- **SEC-1**: eight CodeQL alerts, five high, all test-only. Untouched here; it belongs to a change that is not a release.
- **MT-9**: an inert control is still undetected. Needs CDP listener-chain inspection, which no phase of this plan attempted.

## v4.11.0 - interactive-handbooks-and-presentation-default

**Status**: COMPLETE AND RELEASED - 7/7 phases and 31/31 tasks. PR #202 merged into `develop` as `48bf552a`, and tag `v4.11.0` was published at `0f68fa1a`. The paragraphs below retain the mid-Phase-6 failure record rather than rewriting it as success; QG-2 closed as unmet and remains a bounded limitation. See [Phase 6 evidence](development/interactive-handbooks/phase-6-evidence.md) and the plan's current completion status.

### Summary

No new deferred item or waived requirement. Existing v4.9.0 gaps retain their owners.

The completed report retry is also a non-pass: native Word paints the source-appendix table beyond the page edge despite successful HTML/PDF/rebuild checks. The DOCX owner now keeps grid and header/body cell widths consistent and checks usable page width. Four new regressions and twelve affected DOCX/distribution/workflow checks pass. The diagnostic correction is excluded from qualification; a fresh bounded report invocation remains required.

The completed presentation retry opens normally and retains correct native chart values and process edges, but timed PowerPoint playback shows no automatic process or chart-series builds. The shared PPTX owner now includes a portable native fade helper, an explicit required-motion gate and a documented integration recipe. Seventeen affected checks pass with 96.59% helper coverage; both installers deliver matching helper bytes, and a separate diagnostic deck visibly executes eight overlapping process effects and one chart-series fade. Native PowerPoint also opens the corrected connector-only case without repair. The failed author output is unchanged, and a fresh presentation invocation is queued after the corrected report. No diagnostic edit is counted as qualification.

The repository final attempt timed out after 3,600.75 seconds without its final result record. Independent browser inspection reproduces two alternate-panel overflows at 2560x720; this remains a non-pass. The QA owner now requires alternate-panel inventory before first QA. The report run is active, the presentation run is queued, and a fresh repository case is queued with the same frozen input and three-correction ceiling under a predeclared 5,400-second limit. No result from an earlier skill revision or failed artifact is silently restamped.

The subsequent report-final invocation is independently accepted after three internal corrections in 3,247.39 seconds. Its final HTML, PDF and DOCX rebuild byte-identically; native Word renders two complete pages with correct Arial fonts and no outside-page text, and the PDF passes two rendering engines plus QPDF. Two hundred default states and 404 independent control/paint-order checks pass their recorded scopes. See [accepted report evidence](development/interactive-handbooks/phase-6-native-attempts/report-final/summary.json). The native authoring gate is 1/3 accepted; the active presentation and queued repository cases remain required. Earlier failed reports are not relabeled.

### Open items after the fresh presentation-readable and repo-semantic invocations - 2026-09-10

Both queued invocations completed and are non-passes, so the native authoring gate stays at 1 of 3 accepted and Phase 6 cannot close. Full context, evidence links and the confirmed mechanisms are in [Phase 6 evidence](development/interactive-handbooks/phase-6-evidence.md#fresh-presentation-readable-and-repo-semantic-invocations). The chart-title defect did not recur and is not relisted. Counts below apply to this plan's subsection only.

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 0 |
| BG | 0 | 5 |
| WN | 1 | 3 |
| MT | 2 | 5 |
| QG | 1 | 0 |

#### MT-3 - RESOLVED: rendered contrast is now measured by the owner that renders

- **Source phase**: Phase 6, T019.
- **Plan reference**: T019 contrast by owner, and light-only and dark-only validation over all slide types and child surfaces; R19 and R24.
- **What was wrong**: `visual_qa_score.py` pairs custom-property NAMES at root scope, so a block that redefines a token inside the same rule that consumes it resolves at computed-value time and scores clean. Twenty sub-AA rendered pairs at a worst ratio of 1.0 to 1 reached the delivered presentation bytes and were present already in the frozen first build.
- **Resolution**: `measure_handbook.py` now measures contrast on RENDERED computed colors during the pass that already walks every visible text element with a live browser, rather than teaching the static scorer to resolve cascades it cannot see. Ink comes from the computed `color` (or `fill` for SVG text), the backdrop is the first opaque painted ancestor background as the compositor resolves it, and the floor follows WCAG 1.4.3: 3.0 to 1 for large text at or above 24 pixels or bold at or above 18.66, otherwise 4.5 to 1. Fully transparent ink is skipped as an opacity concern rather than reported as a contrast one. Failures join the existing per-state error list, so an affected state fails its gate.
- **Proof**: run against the retained failing artifact, the check reports 21 sub-AA pairs with a worst ratio of exactly 1 to 1 (`rgb(23, 43, 59)` ink on an identical background), independently converging on the 20 pairs the runner found by screenshot inspection. Three tests cover the delivered token-redefinition shape, the large-text floor boundary at 4.00 to 1, and transparent ink; negative-controlled by disabling the reporting and confirming all three fail. The two living handbooks and every existing fixture still pass, so the check adds no false positives.
- **Residual**: the static token-pair check in `visual_qa_score.py` is unchanged and still useful for pre-render authoring feedback; it is no longer the gate for this class.

#### MT-4 - RESOLVED: label-versus-shape collisions are measured in the rendered pass

- **Source phase**: Phase 6, T019.
- **Plan reference**: T019 semantic-figure and SVG reference integrity; R17 and R21.
- **What was wrong**: the SVG checks were exactly `check_svg_arrowheads`, `check_svg_viewport_fit` and `check_svg_marker_integrity`. None compared a label against a shape and the module never called `getBBox`, so three edge labels painting across stage-card rectangles in the repository case passed every automated gate and were caught only by screenshot inspection.
- **Resolution**: `measure_handbook.py` now compares every rendered SVG `<text>` against every filled `<rect>`, `<circle>`, `<ellipse>` and `<polygon>` in the same figure. The discriminating rule is PARTIAL overlap: a label wholly inside a shape is correct node labelling and is ignored, a label clear of every shape is ignored, and a label straddling a shape's edge is a collision. A shape with `fill:none` is a stroke outline and cannot occlude, a label already inside the shape's own subtree is skipped, and an overlap covering under 8 percent of the label is treated as a grazing touch. Measuring in the browser means transforms, text length and font resolution are already applied rather than estimated.
- **Proof**: run against the retained failing SVG, the check reports exactly 3 collisions at 25, 33 and 36 percent label coverage, independently converging on the three edge labels the runner found by screenshot inspection, while the other 23 text elements in the same figure are correctly ignored. Four tests cover a straddling label, a wholly-inside label, a label clear of every shape, and an unfilled outline; negative-controlled by disabling the reporting and confirming the straddle test fails.
- **Residual**: this measures collision geometry only. Whether a diagram explains the right relationship remains a human or agent judgment, and no beauty or authorship detector was added.

#### BG-2 - RESOLVED: the reading offset is restored instantly rather than animated

- **Source phase**: Phase 6, T019, reported independently by two runners against Phase 2 output.
- **Plan reference**: R25 global reset and return-to-page behavior.
- **History**: first reported as a clamp to zero, then WITHDRAWN in this cycle after a synthetic harness restored correctly and the failure was traced to Playwright's `locator.click()` auto-scrolling its top-of-page target into view. That withdrawal was wrong. The auto-scroll was a genuine confound in that one harness, but a contaminated reproduction does not disprove the phenomenon, and a second runner then reported a partial shortfall that the auto-scroll explanation cannot produce.
- **Confirmed mechanism**: the page sets `html { scroll-behavior: smooth }`, which turns the restoring `window.scrollTo(0, scroll)` into an ANIMATION. The `origin.focus()` call on the next line cancels that animation mid-flight, stranding the reader wherever it had reached. Instrumenting the call on the retained real page shows the target and the document height were both already correct (5394 requested, 6384 tall) while `scrollY` immediately after the call was 0, settling later at 4663. The shortfall scales with depth because a short scroll completes before the cancellation: measured on the same page with the same sequence, 5394 lost 789 pixels and 3000 lost 140, while 1200 restored exactly. Layout timing, the mechanism proposed earlier in this cycle, was NOT the cause.
- **Resolution**: `assets/dual-view-runtime.js` restores with `window.scrollTo({top, left, behavior: 'instant'})`. Returning a reader to their place is a restoration, not a journey, so it opts out of the page-level smooth preference and cannot be cancelled.
- **Proof**: measured end to end on the retained first build with only the runtime swapped. Committed runtime: 5394 to 4605, 3000 to 2860, 1200 exact. Fixed runtime: all three exact. A regression test drives the documented open and close API on a fixture that sets `scroll-behavior: smooth` at depths 5394 and 3000; negative-controlled against the committed runtime, where both cases fail. The pre-existing `test_entry_reset_chapter_and_exit_restore_reading` still passes.
- **Why the earlier fixtures could not catch it**: none set `scroll-behavior: smooth`, so their restores were never animated and nothing could cancel them. A fixture that cannot fail proves nothing; the new one fails without the fix.

#### BG-3 - RESOLVED: an existing web page is now a first-class source

- **Source phase**: Phase 6, T020.
- **Plan reference**: T020 legacy HTML migration; R11 layout preservation.
- **What was wrong**: `scripts/extract_content.py` mapped roughly seventy-five extensions and `.html` was not among them, so the repository case ingested eight of nine files. The plan promised legacy HTML migration while the implementation could not read a web page, and the two disagreed silently. The run disclosed the omission on the delivered page rather than concealing it, which kept the result honest but did not close the gap.
- **Decision**: build the reader. The user chose the full capability over narrowing or dropping the promise, accepting a longer release.
- **Resolution**: `.html`, `.htm` and `.xhtml` now route to `_extract_html`, which reads a page into the shared section and block model using the standard library's `html.parser`. No dependency was added, so the reader cannot fail for a missing install. Headings open sections; paragraphs, blockquotes, definition terms and figure captions become paragraphs; lists become bullet blocks; tables keep header and body rows; `pre` becomes a code block; and an image contributes its `alt` text so a described visual is not silently lost. `title` supplies the document title, falling back to the first heading. Page chrome is dropped WHOLE rather than word by word: `nav`, `header`, `footer` and `aside` subtrees contribute nothing, and `script`, `style`, `noscript`, `template` and `svg` are skipped entirely, so navigation labels can never be presented as handbook prose. Malformed markup degrades rather than aborting, and a page with no readable content records its reason instead of passing.
- **Proof**: the frozen repository fixture now ingests 9 of 9 sources, and the legacy page yields both its headings with exact text, including the configuration values and the uncertainty statement the factual gate checks. 21 tests cover suffix recognition, the real fixture, heading and title resolution, lists, tables, preformatted text, image alt text, whitespace collapsing, each chrome and code tag, unclosed tags, an empty page and a chrome-only page; negative-controlled by unregistering the format and confirming four fail. 102 tests pass across the extractor-adjacent suites with no regression.
- **Residual**: reading a page and preserving its published URL and anchors are separate duties. This closes the reading half; the handbook-refresh rules continue to own address and anchor preservation, and a migration needs both.

#### BG-4 - RESOLVED: an invisible brand mark now fails its gate

- **Source phase**: Phase 6, T020, repository case.
- **Plan reference**: R26 brand fidelity and source-to-SVG comparison at actual sizes.
- **What was wrong**: every slide selected the opposite brand variant, leaving the wordmark invisible on both themes while the symbol still read. The selection code was correct and internally consistent; the CONTRACT was the defect, saying only that `brand_variants` "maps light/dark to supplied asset variants" without stating whether the key means the surface or the artwork's own colour.
- **Resolution**: `content-model.md` now states that the key is the SURFACE the lockup is drawn on, gives the concrete implication that `brand_variants.dark` is normally the light artwork, and names the consequence of reading it the other way. A rendered check measures every filled shape in a lockup against its actual backdrop and fails below 1.5 to 1. It is per-shape, so a legible symbol beside a vanished wordmark is still caught; the contrast pass could not see this because a lockup carries meaning in shapes rather than text.
- **Proof**: two tests, an invisible wordmark beside a legible symbol and a brand that reads against its surface, negative-controlled. The subsequent repository qualification found no mark below the floor at any of its 462 measured states.

#### BG-5 - RESOLVED: a deformed data mark now fails its gate

- **Source phase**: Phase 6, T020, repository case.
- **Plan reference**: R17 figure fidelity.
- **What was wrong**: `preserveAspectRatio="none"` stretched chart data points into ellipses. The attribute appears nowhere in this codebase, so it was authored, and nothing prevented it.
- **Resolution**: a rendered check flags non-uniform scaling on charts only, identified by `.dv-chart`, `[data-dv-chart]`, or any `svg` containing `[data-dv-mark]`. Decorative artwork may still stretch, because a background wave is a design choice while a deformed data mark is a misrepresentation.
- **Proof**: two tests, a deformed chart naming its mark count and decorative artwork that may stretch, negative-controlled.

#### WN-2 - RESOLVED: opening-screen content must be readable at first paint

- **Source phase**: Phase 6, T019, presentation case.
- **Plan reference**: R23 motion lifetime and reduced-motion behavior.
- **What was wrong**: a section already on screen at load rendered at opacity 0.45 from a scroll-driven reveal, so the opening screen shipped half-faded with nothing for the reader to scroll to trigger it.
- **Resolution**: the rendered pass now accumulates inherited opacity down the ancestor chain for every text-bearing element intersecting the initial viewport and fails below 0.95. Content below the fold may still start faded, because a reveal is legitimate for content the reader has to scroll to.
- **Proof**: four tests covering a faded opening screen, two stacked 0.7 ancestors compounding to 0.49, a fully opaque screen, and a legitimate below-the-fold reveal; negative-controlled. Independently, the later presentation run declined scroll-triggered reveals for exactly this reason and recorded it rather than shipping one.

#### WN-3 - CLOSED as authoring guidance: composition balance is not automatable

- **Source phase**: Phase 6, T020, repository case.
- **Plan reference**: R20 and R23 composition quality.
- **What was observed**: the chart pane left roughly half the slide empty. A later independent review recorded the same class as some empty space in a right-hand column.
- **Why this closes without a check**: the plan forbids an automatic beauty or authorship detector, and rightly. Empty space is a defect in one composition and deliberate in another, and no measurement separates them. Inventing a fill-ratio threshold would fail legitimate work and be gamed by padding, which the plan also names.
- **Resolution**: this stays a human or agent visual judgement, carried by the existing positive-design gate and the reference comparison. It is recorded here so a future reader does not mistake the absence of a check for an absence of review.

#### WN-4 - RESOLVED: the axis claim now matches what the runtime provides

- **Source phase**: Phase 6, T019.
- **Plan reference**: `SKILL.md` interactive-chart requirements.
- **What was wrong**: `SKILL.md` promised in two places that a reader can "adjust axis limits". `assets/dual-view-figures.js` implements reset, series toggle, region select, enlargement, zoom and pan, and no axis-limit control. The contract and the implementation disagreed.
- **Decision and reason**: the claim was corrected rather than implemented. A direct axis-limit control has to re-lay-out arbitrary authored SVG to an operator-chosen range, which is a charting engine, and this plan's `construction-debt` line forbids a second chart framework outright. The reader-facing value that claim was reaching for is already delivered by the auto-refit rule: toggling a series refits the axis so no value is silently clamped.
- **Resolution**: both claims now describe zoom, pan and series toggling with the axis refitting to whatever stays visible, and state plainly that there is no direct axis-limit control and why. The mixed-scale safety rule is untouched, including its binary statement that a flat-topped bar at the axis maximum is fabricated data.

#### BG-6 - RESOLVED: the reading view no longer hides content behind an undiscoverable scroll

- **Source phase**: Phase 6, T020, sixth qualification round, report case.
- **Plan reference**: R02 whole-source retention; R06 reading-view completeness.
- **What was wrong**: the assembler's own base stylesheet capped `.dv-directory` at 200 pixels with `overflow: auto`, in BOTH views. On the delivered report page that hid content in five separate blocks, the worst by 787 pixels, and `offsetWidth - clientWidth` was zero on every one, so no scrollbar was drawn. A reader saw a truncated table with nothing indicating more existed. The content was intact in the DOM, the PDF and the DOCX, so nothing was lost; it was simply unreachable in the view most readers use. This is a shipped default, not an authoring mistake, and two separate runners had to work around it.
- **Why it is the same shape as the print defect**: a default that behaves reasonably in the small case and quietly wrongly in the large one. With overlay scrollbars, "scrollable" and "truncated" are visually identical.
- **Resolution**: the cap is now scoped to slides only. The reading page has no stage to fit, so its directories are uncapped and content flows. The slide keeps the 200-pixel cap because it must fit a fixed stage, and it now sets `scrollbar-gutter: stable` so the scroll is visible rather than discovered.
- **Proof**: two tests build a thirty-row directory and assert the reading view hides at most two pixels while the slide retains its cap and its reserved gutter. Negative-controlled against the original declaration, where both fail. 39 measure tests pass.

#### MT-5 - No automated coverage for values fabricated mid-animation

- **Source phase**: Phase 6, T019 and T020, found by screenshot inspection in two independent runs.
- **Plan reference**: R16 source fidelity; T019 non-vacuous checks.
- **What was observed**: a count-up animation paints numbers the source does not contain. One run displayed 11 / 17 / 28 / 29 mid-flight where the true value was 31; another transiently painted a retry limit of 2, precisely the stale figure that refresh existed to correct. Both were caught only by looking at screenshots, and both runs independently repaired it the same way, by making the printed values static and animating a proportion bar instead.
- **Why no detector was added**: every gate in this system measures a settled frame, so the defect is invisible to all of them by construction. Catching it automatically needs temporal sampling of text content against the source model across the whole animation window, which is a new measurement architecture rather than an extension of the existing pass, and a naive version would fire on any legitimately animated non-sourced number.
- **What was done instead**: a binary authoring rule in `references/interactive-features.md` forbids animating the digits of a sourced value, requires the surrounding form to carry the motion, and permits animation of numbers the source does not contain. Guidance is the appropriate instrument here because both runners found and fixed the defect unaided once looking.
- **Suggested next step**: if this recurs after the rule ships, build the temporal sampler as its own scoped work with a fixture that animates a known-wrong intermediate value; do not bolt it onto the settled-frame pass.

#### MT-6 - RESOLVED: print contrast is measured against the surface that will actually paint

- **Source phase**: Phase 6, T020, third qualification round, repository case.
- **Plan reference**: T019 contrast by owner; R06 print behavior.
- **What was wrong**: Chromium defaults `print-color-adjust` to `economy` and drops background painting, so a dark band prints white while its light ink survives. The rendered contrast pass read `getComputedStyle().backgroundColor`, which print emulation does not change, so it read the declared dark surface and scored the pair clean. All THREE round-three artifacts carried the defect at 46, 52 and 35 failures; only one runner found it, by rasterising and looking, and the two that passed did so because nothing measured it. On that criterion round three was 0 of 3, not 2 of 3.
- **Resolution**: the existing print pass now resolves each text element's first opaque ancestor background and then decides whether that surface will actually PAINT, by walking for a computed `print-color-adjust: exact`. If it will not, contrast is computed against paper. Running under print emulation means an `@media print` palette remap has already applied, so both legitimate remedies pass and neither is mandated.
- **Proof**: reproduced the reported figures exactly on the retained artifact, 46 failures at worst 1.11 to 1. Four tests cover a bespoke dark band with no opt-in, `print-color-adjust: exact`, an `@media print` remap, and ordinary dark-on-light text; negative-controlled. An authoring rule in `responsive-typography.md` states the cause and both remedies.
- **Outcome in later rounds**: the three delivered artifacts went from 52, 35 and 46 failures to zero in a single round, entirely through guidance given up front, without any artifact failing the new gate in anger.

#### WN-5 - RESOLVED: an opaque out-of-flow layer occludes rather than collides

- **Source phase**: Phase 6, T020, third qualification round, report case.
- **Plan reference**: T019 non-vacuous checks.
- **Owner**: `catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py`, which belongs to `functional-verification` rather than to this skill.
- **What was observed**: a sticky global navigation produced 86 `text-overlap` errors across 7 of 8 sections, because its links overlap the prose beneath them once the reader scrolls. That is what a sticky nav is for. The runner removed the sticky behavior rather than silence the rule or edit the tooling, and recorded the disagreement with retained evidence. The delivered page is worse for it: a reader deep in the document must scroll to the top to reach navigation. The two installed tools disagreed on the same page, since `visual_qa_score.py`'s render-only-defects criterion passed the sticky version.
- **Why this matters beyond one page**: the same class was already adjudicated by hand during v4.9.0, whose evidence records that all 56 raw overlap warnings were opaque sticky-navigation occlusion. A false positive that is waived by a human every round is eventually obeyed instead, and this round it deleted a legitimate feature.
- **Resolution**: Phase 7, T022. The suggested step was applied in the owning skill's own script, exactly as scoped. `text-overlap` now skips a pair when exactly one side sits inside an out-of-flow layer that paints an opaque backdrop. The opacity condition is load-bearing and came from this entry: a transparent sticky bar does not occlude, so its collision is still reported.
- **Root cause**: the cluster had no rule-ownership table, which `AGENTS.md` requires for two skills covering adjacent territory. One gate required the navigation to compute as sticky (MT-7) while the other reported the consequence of it being sticky. A `## Rule ownership` table was added to the handbook skill naming one owner per concern.
- **Evidence**: negative-controlled in both directions. Disabling the exemption makes the opaque fixture report two findings instead of one; widening it to every sticky element makes the transparent fixture report none instead of one. Only the opacity-conditioned rule passes both. See the Architecture refactor section of [last-phase evidence](development/interactive-handbooks/last-phase-evidence.md).
- **Not done**: the two overlap implementations are not merged. They measure different things, and merging them to serve a false symmetry would give one script two responsibilities.

#### MT-7 - RESOLVED: a declared layout property must be the computed one

- **Source phase**: Phase 6, T020, fourth qualification round, presentation case.
- **Plan reference**: R25 navigation reachability; T019 non-vacuous checks.
- **What was wrong**: the navigation rail was authored `position: sticky`, but a later base rule at equal specificity won the cascade and it computed `static` everywhere, so global navigation was unreachable deep in the document. No gate saw it. This was the third appearance of one class in three rounds from three directions: round three DELETED a legitimate sticky nav because the overlap rule fired on it (WN-5), round four's presentation case authored one that never applied, and round four's repository case got it right only because its brief told it to verify the computed value.
- **Resolution**: the rendered pass now walks every stylesheet rule that declares `position: sticky` or `fixed`, skips rules whose media condition does not currently match, and reports any matching visible element whose computed position differs. A declaration is a request, not a fact; this reads what the engine resolved. A breakpoint that deliberately does not stick is not a finding, and a deliberate override should remove the losing declaration rather than leave a live rule that never applies.
- **Proof**: run against the retained presentation artifact it reports exactly one finding, `'.rail' declares position sticky but <header> computes static`, and reports zero on the other two round-four artifacts. Driven through the real measurement entry point the presentation case fails with that single layout error while the report case passes with none. Three tests cover a lost cascade, a declaration that applies, and a non-matching breakpoint; negative-controlled.

#### MT-8 - RESOLVED: focus restoration is now gated, and the reported defect was a harness artifact

- **Source phase**: Phase 6, T020, fourth qualification round, repository case.
- **Plan reference**: R25 return-to-page behavior, which names focus restoration beside scroll restoration.
- **What was reported**: closing Presentation Mode left focus on `body` rather than the control that opened the deck.
- **What reproduction showed**: the runtime is correct. Focus returns to the opening control on ALL THREE round-four artifacts when the control is genuinely focused first, as a real user click does. The failure appears only when the deck is opened with a programmatic `element.click()`, which does not move focus: the runtime then captures `body` as the origin and restoring to `body` is the right answer for that input. An earlier verification in this cycle repeated the reporting harness's mistake and wrongly confirmed the defect; that confirmation is withdrawn here rather than left standing. This is the same class as the BG-2 withdrawal, in the opposite direction: there a contaminated harness hid a real defect, here it invented one.
- **Why a check was still added**: R25 names focus restoration and nothing measured it, so a regression would have shipped silently. The gate now asserts that after close `document.activeElement` is within the control that opened the deck. It reads a value the contract already promises rather than inventing a requirement, and it currently passes everywhere, which is the correct outcome for a guard rather than evidence that it is useless.
- **Proof**: two tests, one asserting restoration on a sound fixture and one removing the opener before close so focus lands nowhere; negative-controlled. Driven through the real entry point, zero focus errors on all three round-four artifacts.

#### MT-9 - A control that exists but does nothing is not detected; the obvious check does not work

- **Source phase**: Phase 6, T020, fifth qualification round, repository case.
- **Plan reference**: R21 behavioral verification; T019 non-vacuous checks.
- **What was observed**: four stage buttons on presentation slide 4 are inert. A round-one restructure moved them outside the `<figure>` whose delegated listener handles them, so they render, focus and click with no effect. Independently reproduced: the four buttons exist, none is inside a `<figure>`, and clicking all four leaves the slide's DOM byte-identical.
- **Why no gate sees it**: every existing check measures whether something is DRAWN correctly. None asks whether it DOES anything, so a dead control passes contrast, geometry, floors, clipping and overlap perfectly.
- **An activate-and-observe check was built, tested and REJECTED**. It is recorded here so the next attempt does not repeat it. Three failures, in order: it was wired onto the page created with `java_script_enabled=False` for the no-JS check, where nothing is listening and every control reports dead; it did not reset state between probes, so the first control that opened the presentation made the reading page inert and every later control legitimately did nothing; and once both were fixed it still reported only false positives, because an idempotent control correctly changes nothing. `Reset chart` clicked in the default state, and `Replay the build`, both change no observable state and are working as designed. Worse, it MISSED the defect it was built for, because it opened only the first slide while the inert buttons are on the fourth.
- **What a correct check needs**: ask whether anything is LISTENING rather than whether something changed. Walk from the control up through its ancestors collecting click listeners through the Chrome DevTools Protocol, and report a control with no listener anywhere in its chain and no native form or anchor behavior. That distinguishes this defect exactly, since the moved buttons have no listening ancestor while working delegated controls do, and it is immune to idempotency. It must also iterate EVERY slide, not just the first.
- **Why it was not built now**: that is materially more machinery than the activate-and-observe sketch it replaces, and shipping the rejected version would have been worse than shipping nothing. A gate that fires on working reset buttons is how the `text-overlap` false positive (WN-5) came to delete working navigation three times.

**Follow-up, 2026-09-23**: The CDP suggestion above is insufficient for this runtime: document and deck both have broad click listeners, so a detached button still has listeners in its ancestor chain. A narrower [slide-series structure check](../../../archives/v4/v4.11/development/slide-series-control-qualification.md) now reports a series toggle outside its owning chart figure on every measured slide. A real Chromium click proves the detached button leaves plotted marks visible; the valid toggle hides them. The owning module passes 53 tests. MT-9 stays open for generic inert controls; the original four-button artifact is not retained here, so this fixture does not retroactively certify that exact artifact.

**Local follow-up, 2026-09-24**: An independent `control_behaviors` inventory now names a setup, precondition, action, and intended browser-visible result for each declared slide control. The [archived qualification](../../../archives/v4/v4.11/development/control-behavior-qualification.md) records a second-slide inert control caught, a working and an idempotent control accepted, and a chart mutation caught by unchanged plotted marks even though `aria-pressed` changed. No automatic inventory proves that all controls were mapped; the original four-button artifact is unretained, and protected publication is pending. MT-9 remains open.

**Retained-pilot qualification, 2026-09-24**: PR #297 published the declared-control guard through protected `develop`, and its post-merge smoke and provenance run passed. The [archived retained-pilot qualification](../../../archives/v4/v4.11/development/retained-pilot-control-qualification.md) now covers an exact live-DOM census of 34 initial controls plus both dynamically created image-close controls in the retained report pilot. Thirty-one Chromium tests pass, including an inert-stage negative control, and the standalone scorer reports three declared slide-control observations as `pass` with zero guard findings. The full-page scorer still reports 629 separate page errors, so this is not a visual-quality pass. The original four-button artifact remains unavailable and arbitrary future controls remain `unchecked` until declared. Keep MT-9 open until this follow-up is merged and post-merge verified.

**Closed after protected integration, 2026-09-25 UTC**: PR #298 passed 21 hosted checks with one expected skip, merged into `develop` as `1ae58ad5`, and post-merge run 36097633753 passed smoke and provenance on that merge commit. MT-9 is closed for the declared-control method qualified against the retained pilot's complete control census; this does not retroactively test the unavailable four-button artifact, certify an arbitrary future control without an inventory, or waive the pilot's separate whole-page findings.

#### MT-10 - No authored connector diagram has qualified the new geometry checks

**Source phase**: v4.11.1 Phase 5 (T013). **Plan reference**: v4.11.1 5.1.

**Original observation**: `check_svg_label_occlusion` and `check_svg_connector_routing` decide a narrow envelope: axis-aligned `rect`, `text` with numeric anchors, `line` and `polyline`/`polygon`, under `translate()` and `scale()` only. Scoring `docs/handbooks/distribution.html` returned `unchecked` for both checks across its five SVGs. A later corpus inspection showed those five SVGs are navigation/control icons, not diagrams; `docs/handbooks/overview.html` has the same five. The original inference that this proved zero coverage on hand-authored diagrams was too broad.

**Fresh evidence, 2026-09-23**: The real `docs/releases/v3/v3.9/development/worked-example/sample-deck.html` contains a bar-chart SVG with `rect`, `line`, and `text`. Both checks now decide it and pass. Initially routing reported three high-severity crossings because it mistook faint gridlines painted behind opaque bars for connectors; a red regression case and paint-order fix remove those false positives while the visible-connector crossing fixture still fails as intended. The 94-test visual-QA module passes. This establishes one real-artifact envelope exercise, not coverage of an authored connector diagram. The v4.11 pilot presentation and repository artifacts contain path-based SVGs whose diagram shapes remain unchecked when outside the envelope.

**Owner**: repository maintainer. **Status**: open, and deliberately not fixed here.

**Suggested next step**: qualify the checks on an actual authored connector diagram, then decide whether exact straight-line `<path>` segments (`M`/`L`/`H`/`V`) are needed or whether the diagram should use the declared shape vocabulary. Do not expand the envelope merely to score navigation icons, and do not approximate curves: a confident wrong verdict is worse than `unchecked`.

**Authored-diagram qualification, 2026-09-23**: The retained Phase 6 report pilot has two process-diagram layouts, each repeated once, with four labeled boxes, three straight `<path>` connectors, and one cubic return path. Both checks return `unchecked` with zero checked SVGs even when each diagram is scored alone. The [archived qualification](../../../archives/v4/v4.11/development/authored-connector-geometry-qualification.md) records the artifact and outcome. MT-10 remains open: supporting only exact straight paths would not decide either mixed-path diagram, so any extension first needs a truthful partial-coverage contract or exact full-path treatment with a negative crossing control. No curve approximation or pass claim follows from this result.

**Qualified locally 2026-09-23, publication pending**: A bounded `data-edge` path parser and conservative cubic control-hull test now decide both checks on each of the four retained authored diagrams. The whole pilot reports four routing SVGs checked; other path SVGs without connector identity remain `unchecked`. Inserting an unrelated node under the real return curve changes routing to `fail`; unsupported arcs, ambiguous tangencies, filled paths, malformed or unmarked paths, and non-finite geometry remain `unchecked`. The 112-test visual-QA module and the [archived follow-up](../../../archives/v4/v4.11/development/authored-connector-geometry-follow-up.md) record the exact boundary. Keep MT-10 open until protected merge and post-merge verification; this does not close MT-5 or MT-9.

**Closed after protected integration, 2026-09-24 UTC**: PR #269 passed 21 hosted checks with one expected skip, merged as `91617927`, and post-merge run 35940086752 passed smoke and provenance. MT-10 is closed within the explicit connector envelope; unsupported shapes and other SVGs retain honest `unchecked` coverage. MT-5 and MT-9 remain open.

#### QG-2 - CLOSED AS UNMET: two of three sustained across six rounds, carried forward

- **Source phase**: Phase 6, T020.
- **Plan reference**: T020 three of three final passes, with the repository family's repair budget amended from three to five on 2026-09-11.
- **Final state**: unmet. Six rounds never produced three simultaneous passes.

| Round | report | presentation | repository | Result |
|---|---|---|---|---|
| 2 | - | - | - | 1 of 3 |
| 3 | pass | pass | non-pass | 0 of 3, once print contrast became visible |
| 4 | pass | non-pass | qualified pass | 2 of 3 |
| 5 | pass | pass | non-pass | 2 of 3 |
| 6 | non-pass | non-pass | PASS | 1 of 3 |

- **What the budget amendment established**: it worked, and it moved the constraint rather than removing it. The repository case passed for the first time in round six, using all five corrections, with twelve deck controls independently probed across five slides and none inert. Its round-five failure was budget exhaustion on a converging trend, exactly as the amendment argued. In the same round both previously-reliable families failed.
- **What six rounds establish about the TOOLING**: it converged and is not the limiting factor. Nine gates were built from observed defects and every class has held without recurrence: chart auto-titles, rendered contrast, SVG label collisions, brand visibility, chart deformation, opening-screen opacity, print contrast, lost layout declarations, and focus restoration. Print contrast went from 52, 35 and 46 failures across three artifacts to zero in a single round through guidance alone. Each individual family has now demonstrably passed at least twice.
- **Why three at once did not happen**: this is a joint outcome, not a quality threshold. Each family passes roughly half to two thirds of attempts, so three simultaneous passes is near one attempt in five. Six rounds without it is an unremarkable result at those odds, and a seventh would be another draw rather than a fix. The round-six failures were a four-pixel stage overflow at a single viewport after findings fell 36, 7, 3, 3, and a shipped-stylesheet defect now fixed as BG-6.
- **Decision**: carried forward rather than pursued further. Roughly fifteen hours of qualification runtime across six rounds has extracted the available signal. The claim v4.11.0 ships is therefore narrower and is stated plainly: each of the three source families has been independently qualified to pass, the tooling that judges them is verified and negative-controlled, and simultaneous single-invocation delivery across all three within bounded repair is NOT established.
- **Suggested next step**: if a future version wants the three-family gate, raise per-family reliability rather than re-running. The two highest-value candidates are already recorded: MT-9, a control-liveness check built on listener presence rather than observed change, and WN-5, the `text-overlap` false positive that has now cost working navigation three times and directly contradicts MT-7.
