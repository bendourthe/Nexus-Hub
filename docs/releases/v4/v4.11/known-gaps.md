# Known Gaps - v4.11

**Project**: Nexus-Hub
**Status**: open. Seeded 2026-09-12 by moving the interactive-handbooks ledger out of `v4.9`, where it had been recorded while the plan still carried the v4.11.0 number. The plan was renumbered to v4.11.0 because v4.10.0 was completed and released in parallel; this ledger follows the plan rather than the number it was written under. The v4.9 ledger retains the v4.9.0 security-audit work and the post-v4.8.0 prompting follow-up, which are unrelated and keep their owners.
**Last updated**: 2026-09-12

## v4.11.0 - interactive-handbooks-and-presentation-default

**Status**: Phases 1-6 complete (21 of 31 tasks); Phase 7 open and in progress. The line below was written mid-Phase-6 and its detail is retained as the record of that round; the phase closed with QG-2 recorded as UNMET and carried forward, not waived. No accepted gate bypass. Native sandbox writes, Chromium and explicit installed-skill loading work. A cross-profile probe exposed discarded deny rules in CLI 0.153.4; temporary CLI 0.154.0 applies the configured denials and passes all five tested forbidden reads. The current affected suite passes 510 tests and all 30 catalog checks. One of three native authoring families is independently accepted: the report. The latest repository fails branding placement and semantic process motion; the previous presentation fails native chart-title contrast. Corrected shared guidance is under fresh serialized qualification with frozen inputs, predeclared time limits and three internal repairs. Original failed artifacts remain unchanged. Full feature/design and native export qualification, the Phase 6 commit and Phase 7 integration remain open. See [Phase 6 evidence](development/interactive-handbooks/phase-6-evidence.md).

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


