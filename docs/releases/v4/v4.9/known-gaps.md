# Known Gaps - v4.9

**Project**: Nexus-Hub
**Status**: open; seeded 2026-09-08 from post-v4.8.0 work. The v4.8 ledger is finalized, so findings after that release land here rather than reopening it.
**Last updated**: 2026-09-10 (v4.9.1 Phase 6 native authoring gate at 1 of 3)

## Open Items - found 2026-09-08 during post-v4.8.0 follow-up

### Missing tests / coverage gaps (MT)

#### MT-1 - Four rostered models carry no prompting profile, because no vendor publishes per-model guidance for them

- **Source**: the post-v4.8.0 `/tune-prompting` full roster sweep.
- **What was observed**: 12 of 16 rostered models are now profiled. Four are not, and each for a sourced reason rather than for lack of effort:
    - **`claude-haiku-4-5`**: Anthropic's model-specific guidance table lists dedicated prompting pages for Fable 5.1, Fable 5, Sonnet 5, Opus 5, and Opus 4.8 only. Haiku 4.5 is covered by the general best-practices reference, which is model-agnostic across current Claude models and therefore yields no model-SPECIFIC claim.
    - **`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`**: OpenAI's prompt-engineering guide documents `gpt-6-astra` (already profiled) and reasoning-versus-GPT guidance generally. It names no member of the 5.6 family, so there is nothing model-specific to record.
- **Why this is the correct outcome, not a shortfall**: the runbook is explicit that no primary source found means zero claims rather than a guess, because an unsourced claim in the layer is indistinguishable from a hallucinated one and every later phase treats recorded claims as verified input. All four are reported UNVERIFIED by `verify_model_prompting_profiles.py`, which treats that as tracked rather than as a gate failure.
- **Suggested next step**: re-check at the next `/tune-prompting` run. A vendor publishing a per-model page is the trigger; nothing else changes the answer. Do not fill these from the general guidance, which would silently convert model-agnostic advice into a model-specific claim.

### Warnings (WN)

#### WN-1 - Cursor and Gemini claims are family-scoped, recorded at per-model granularity

- **Source**: the same sweep.
- **What was observed**: Google documents Gemini 3.x as a unified family and publishes no per-version prompting guidance, and Cursor publishes no prompting guidance at all (its documentation covers pricing, cache rates, and plan constraints). The claims recorded for the four Gemini models and the four Cursor entries are therefore family-level or plan-level facts, recorded once per rostered model because that is the granularity the layer indexes. Each such claim carries a `note` stating the true scope.
- **Why it is worth recording**: a future reader comparing two Gemini entries will find identical claims and could reasonably conclude the layer is padded. It is not: the source genuinely makes one statement about the family, and the alternative (leaving all four UNVERIFIED) would discard a real, sourced constraint such as Google's recommendation to keep `temperature`, `top_p`, and `top_k` at their defaults.
- **Suggested next step**: if the layer ever grows a family or vendor tier, move these claims up to it and leave the per-model entries pointing at it. That is a schema change and belongs in a decision record, not in a research pass.

#### WN-2 - One vendor claim tensions with a shared catalog skill, recorded and not acted on

- **Source**: the sweep's `claude-opus-5` research.
- **What was observed**: Anthropic's Opus 5 page says to REMOVE explicit verification instructions and legacy harness verification scaffolding, because they cause over-verification on that model and removing them reduces wasted tokens with no loss in quality. The catalog's own `verification-before-completion` skill requires a fresh proving command before any completion claim.
- **Why they are not actually the same rule**: the vendor claim is about redundant self-re-checks inside a turn ("double-check your answer"), while the skill is about evidence for a claim made to a human. Both can hold at once. But they read as contradictory, and someone reconciling them should read both first.
- **What was done**: the claim is recorded in the profile layer scoped `model-specific`, so it structurally cannot reach a shared body through that path, with the tension stated in its `note`. No shared-body edit was proposed and the classifier ran with zero proposals.
- **Suggested next step**: if a future pass wants to reconcile them, that is a decision record about what verification-before-completion means inside a turn versus at a claim boundary, not a prompting edit.

## v4.9.0 - adoption-visa-vulnerability-agentic-harness

**Plan**: [v4.9.0-adoption-visa-vulnerability-agentic-harness.md](plans/v4.9.0-adoption-visa-vulnerability-agentic-harness.md)
**Base**: `develop` at `843c147d` (the PR #188 merge)
**Retargeted**: from v4.8.0 on 2026-09-08, because v4.8.0 shipped carrying only its sibling plan

### Summary

Phase 1 local verification passed: 230 tests, 8 platform-dependent skips, 87.30 percent affected-script coverage. Earlier draft deferrals DF-1 through DF-4 have been implemented. Counts below apply only to this plan's subsection; unrelated post-v4.8 follow-up items above remain unchanged.

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 4 |
| BG | 0 | 1 |
| WN | 1 | 0 |
| MT | 0 | 1 |
| QG | 0 | 1 |

### Open Items

Phase 2 adds no deferred implementation gap. Its final gate passes 395 tests with 25 explicit platform skips and 87.07% coverage. MT-2 and QG-1 retain their original ownership; the additional workflow-policy skips do not constitute Windows or remote CI evidence.

Phase 4 adds no deferred implementation gap. Its final gate passes 447 tests with eight existing platform skips and 87.93% coverage; both bounded reviewers approved the corrected normalization boundary. MT-2 and QG-1 remain assigned to Phase 7.

Phase 5 adds no deferred implementation gap. Its final gate passes 105 tests without skips and 98.96% coverage across the two new runtime files. Both bounded reviewers approved the serializer boundary; existing platform and CI qualification ownership remains unchanged.

Phase 6 adds no deferred deterministic gap. The fresh benchmark suite passes 78 tests with 98.63% coverage and the integration/contract group passes 119 tests. Both declared host attempts are informationally unavailable because no code-search tools are registered; retained outcomes and limitations appear in [the benchmark report](development/security-audit-benchmark.md). The additional POSIX descriptor-swap test extends MT-2; the full scope now has nine platform-specific skips on this Windows workstation, including seven in the safe-artifact file alone. QG-1 still requires terminal pipeline approval and remote proof.

Phase 7 cycle 1 resolved two non-deferrable graph-evidence findings instead of deferring them: absent query seeds and contradictory zero-match/location receipts now reject at their actual boundaries. Independent retest passes 131 cases and final implementation convergence reports zero feature gaps. The current candidate is `bd37a8b8e91ba5c28001d068445a6b3e65a97fada223e5c7b1441ab6bdb3506c`; both newly retained attempts remain informationally unavailable. [Final-phase evidence](development/last-phase-evidence.md) preserves all 37 reachable ledger dispositions, the current v4.5 prerequisite and actual Windows installation. Cycle 2 repaired the full-profile Unicode long-path failure, selected working Git Bash for local validation, and applied the presented CI changes under the user's instruction to finish Phase 7 and integration. All three initially failing profile groups pass their current-tree rerun; no failure is waived. Required hosted checks still precede integration.

#### WN-1 - Private independent verification-harness cleanup was policy-blocked

- **Source phase**: Phase 7, T027 independent adversarial verification.
- **Plan reference**: Tier 3 ancillary local harness cleanup; this is separate from benchmark projection and retained-attempt cleanup.
- **Severity and bounded impact**: P3. A private synthetic test-workspace residue remains ignored locally after standard-library cleanup hit a Windows long path. It contains repository fixture/runtime copies and synthetic records only; no real target or credentials were ingested. Declared benchmark roots and the real MCP probe's disposable copy completed their own cleanup.
- **Reason**: automatic approval review rejected the explicitly checked cleanup action with `blocked by policy`. No alternate deletion or retry was attempted. The residue is excluded from staging, distributed payloads and promoted evidence.
- **Owner and target**: local workspace maintainer; next authorized maintenance session, independent of the v4.9 artifact. This is not an application runtime or release-gate deferral.
- **Suggested next step**: inspect and remove the retained private harness directory manually under the workstation's policy, then record observable absence. Do not erase candidate evidence or answer archives as part of that cleanup.

#### MT-2 - Platform-specific filesystem cases need their matching host

- **Source phase**: Phase 1, T003.
- **Plan reference**: T002 Windows/POSIX containment and path-identity verification.
- **Reason**: nine tests skip on this Windows workstation: six symlink-creation cases require a capability unavailable here, one case-collision fixture collapses on the host filesystem, and the POSIX mode-bit and descriptor-swap cases are inapplicable. Native Windows junction, directory-lock, hard-link, ownership, and cleanup cases execute locally. No POSIX execution is claimed from Windows results.
- **Suggested next step**: execute the matching platform cases during Phase 7 qualification and verify their first permitted remote CI run; retain explicit skip accounting.

#### QG-1 - The Windows CI job does not yet select the new filesystem tests

The first PR run selected the new tests and passed every Linux/macOS/Windows bootstrap and installer smoke job. Its Linux jobs exposed two test-fixture assumptions; Windows additionally exposed golden-fixture CRLF conversion. All three causes were reproduced locally and corrected in the single cycle-3 stabilization commit. Affected suites pass 97 tests with seven platform skips and 152 tests against real Git checkout bytes. These failures are repaired rather than deferred; the corrected head still requires terminal hosted proof before this item closes. See [publication and integration](development/last-phase-evidence.md#publication-and-integration).

- **Source phase**: Phase 1, T003 CI impact record.
- **Plan reference**: Phase 7 terminal pipeline reconciliation and T002 Windows/POSIX coverage.
- **Current state**: locally wired; hosted proof pending. The full repository test profile includes tests/skills on Linux. Phase 7 now selects ten audit files plus the repaired Unicode validator regression in the Windows job, enables Git long paths before Windows checkouts and includes the existing interpreter gate before merge. The presented proposal and direct failure repair were authorized by the user's instruction to finish Phase 7 and integration; independent review approves the final eleven-file selection.
- **Suggested next step**: retain the first PR's exact Windows/installer success results and close this item in the SHA-bound integration handoff. Local results alone do not establish hosted coverage; no gate bypass is permitted.

### Independent maintenance handoffs

The repository-wide [platform review](development/qualification/v4.9-platform-verification.md) confirms two pre-existing discrepancies outside this audit's native skill-delivery path: Copilot's bypass-permission seed type and Antigravity's compatibility workflow directory. The existing platform-default and platform-read-contract owners retain them for a separately scoped maintenance/release handoff. This plan changes neither those settings nor installer destinations and does not claim those surfaces were live-tested. The complete CI comparison likewise retains the existing v4.3 profile/cache/reporting owners. These findings are not silently closed or counted as audit feature gaps.

The advisory model-prompting check used the native Codex CLI's current enumeration and reports roster drift relative to its stored September 5 roster. That CLI omitted recorded `gpt-6-astra`; this does not assert global model availability. Existing model-prompting maintenance owns a future source-backed refresh. No profile, freshness marker or shared prompting rule was changed.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| BG-1 | Public qualified-symbol explore | Phase 3, approved A1 | Existing qualified resolver reused; punctuation and ambiguity regressions pass, with successful real MCP probe. |
| DF-1 | Sanitized Git metadata | Phase 1 corrective implementation | Index/ref/ignore snapshots use empty config/hooks; invalid target config does not affect classification. |
| DF-2 | Index identity | Phase 1 corrective implementation | Index bytes and parsed entry digests are bound; index changes invalidate a manifest. |
| DF-3 | Submodule classification | Phase 1 corrective implementation | Each in-scope gitlink binds child HEAD, dirty and untracked state; incomplete/external metadata fails. |
| DF-4 | Windows containment primitives | Phase 1 corrective implementation | Native directory handles deny rename during operations, with identity checks before content publication; no process assurance is claimed. |


### Open items after the fresh presentation-readable and repo-semantic invocations - 2026-09-10

Both queued invocations completed and are non-passes, so the native authoring gate stays at 1 of 3 accepted and Phase 6 cannot close. Full context, evidence links and the confirmed mechanisms are in [Phase 6 evidence](development/interactive-handbooks/phase-6-evidence.md#fresh-presentation-readable-and-repo-semantic-invocations). The chart-title defect did not recur and is not relisted. Counts below apply to this plan's subsection only.

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 0 |
| BG | 0 | 4 |
| WN | 1 | 3 |
| MT | 2 | 4 |
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

#### MT-5 - No automated coverage for values fabricated mid-animation

- **Source phase**: Phase 6, T019 and T020, found by screenshot inspection in two independent runs.
- **Plan reference**: R16 source fidelity; T019 non-vacuous checks.
- **What was observed**: a count-up animation paints numbers the source does not contain. One run displayed 11 / 17 / 28 / 29 mid-flight where the true value was 31; another transiently painted a retry limit of 2, precisely the stale figure that refresh existed to correct. Both were caught only by looking at screenshots, and both runs independently repaired it the same way, by making the printed values static and animating a proportion bar instead.
- **Why no detector was added**: every gate in this system measures a settled frame, so the defect is invisible to all of them by construction. Catching it automatically needs temporal sampling of text content against the source model across the whole animation window, which is a new measurement architecture rather than an extension of the existing pass, and a naive version would fire on any legitimately animated non-sourced number.
- **What was done instead**: a binary authoring rule in `references/interactive-features.md` forbids animating the digits of a sourced value, requires the surrounding form to carry the motion, and permits animation of numbers the source does not contain. Guidance is the appropriate instrument here because both runners found and fixed the defect unaided once looking.
- **Suggested next step**: if this recurs after the rule ships, build the temporal sampler as its own scoped work with a fixture that animates a known-wrong intermediate value; do not bolt it onto the settled-frame pass.

#### MT-6 - Contrast is measured from computed style, which print does not honour

- **Source phase**: Phase 6, T020, third qualification round, repository case.
- **Plan reference**: T019 contrast by owner; R06 print behavior.
- **What was observed**: the delivered page declares dark bands with light ink. Chromium drops background painting for print unless `print-color-adjust: exact` is set, so the band prints white while its text keeps the light ink. The runner measured 46 of 86 dark-band text elements below 4.5 to 1 in print, worst 1.11 to 1, and retained a rendered page image that shows the defect plainly.
- **Why the installed check cannot see it**: the rendered contrast pass added earlier in this cycle reads `getComputedStyle().backgroundColor`. Print emulation changes what is PAINTED, not what is computed, so the check still reads the declared dark background and scores the pair clean. Verified directly: measuring the delivered page under `emulate_media('print')` reports zero contrast findings while the rasterised page is visibly unreadable. This is the same lesson as the PowerPoint automatic chart title, one medium over: the value the defect lives in is absent from the object model.
- **Suggested next step**: a deterministic static check is available and cheap. A page that paints a dark surface behind light ink MUST either declare `print-color-adjust: exact` on that surface or remap the palette in an `@media print` block; a page that does neither will print unreadable text. That is checkable without rasterising, and it fails the cause rather than sampling pixels for the symptom. Rasterising the print output and sampling is the fallback if the static rule proves insufficient.

#### WN-5 - The text-overlap rule fires on deliberately overlaying elements

- **Source phase**: Phase 6, T020, third qualification round, report case.
- **Plan reference**: T019 non-vacuous checks.
- **Owner**: `catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py`, which belongs to `functional-verification` rather than to this skill.
- **What was observed**: a sticky global navigation produced 86 `text-overlap` errors across 7 of 8 sections, because its links overlap the prose beneath them once the reader scrolls. That is what a sticky nav is for. The runner removed the sticky behavior rather than silence the rule or edit the tooling, and recorded the disagreement with retained evidence. The delivered page is worse for it: a reader deep in the document must scroll to the top to reach navigation. The two installed tools disagreed on the same page, since `visual_qa_score.py`'s render-only-defects criterion passed the sticky version.
- **Why this matters beyond one page**: the same class was already adjudicated by hand during v4.9.0, whose evidence records that all 56 raw overlap warnings were opaque sticky-navigation occlusion. A false positive that is waived by a human every round is eventually obeyed instead, and this round it deleted a legitimate feature.
- **Suggested next step**: exempt an element whose computed `position` is `sticky` or `fixed` AND which paints an opaque background, because such an element occludes by design. Keep the rule for ordinary flow content, where overlap is always a defect. This is a change to another skill's script and should be scoped to that owner rather than folded into this plan.

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

#### QG-2 - The three-family authoring gate remains unmet after four rounds

- **Source phase**: Phase 6, T020.
- **Plan reference**: T020 three of three final passes with no high-severity unresolved finding.
- **Round history**: round two 1 of 3; round three reported 2 of 3 but was 0 of 3 once print contrast became visible; round four 2 of 3, with the report case a clean pass, the repository case a qualified pass carrying medium residuals, and the presentation case a self-declared non-pass on two defects.
- **What the rounds establish**: the gate is converging on the measurable and has stopped finding high-severity machine-detectable defects. Print contrast went from 52, 35 and 46 failures across the three artifacts to zero on all three in one round, entirely through guidance, without any artifact ever failing the new gate in anger. Every other machine check passes on all three round-four artifacts. Every fix this cycle held.
- **What still blocks it**: the surviving defects are of three kinds that the gate does not cover by construction. A contract term that is named but unmeasured (focus restoration, MT-8). A declared property that never applied (MT-7). And design judgements the plan forbids automating (a connector crossing a label, a slide left a fifth empty). Round four contains no high-severity unresolved finding in any case, which is the plan's literal bar, but two cases self-declared short of a clean pass.
- **Suggested next step**: land MT-7 and MT-8, which are both narrow, cheap, and read values the contracts already promise, then re-run. If a further round still turns on design judgement rather than measurable defect, the honest conclusion is that this gate has reached what automation can settle, and the remaining decision belongs to a human reviewer rather than another round.


## Resolved during this follow-up

- **The intermittent org-CLI failure was a Windows directory-rename race, now fixed** (carried in as v4.8 `WN-I`, org-CLI half, and briefly tracked here as `BG-1`). It arrived as a test that failed twice on a DIFFERENT test each time, never reproduced in isolation (12 consecutive clean runs of the file, 470 passing for the whole directory), and passed on both CI test jobs. Four candidate causes were ruled out first: the `PYTHONUTF8` decoding defect that explained the PowerShell half (that file was already hardened), load (it failed inside a 4-second single-file run), order randomization (no such plugin is installed), and cross-suite pollution (1319 hook tests immediately before left the suspects passing).
- The mechanism is platform behavior, not test flakiness. On Windows `os.replace` on a DIRECTORY fails with `PermissionError` (`WinError 5`) while any process holds a handle to a file inside it, and the identical call succeeds once released. A lingering `git.exe` child from the fixture's clone or push, an on-access scanner, or a desktop indexer is enough to open the window. It is invisible on POSIX, where rename ignores open handles, which is why CI's Linux job could never see it and a clean hosted Windows runner sees it far less often than a developer workstation.
- **Reproduced deterministically before anything was changed**, which is what unblocked the fix. `tests/installer/test_org_repo_replace_retry.py` holds a real handle inside the destination and releases it from a timer; against the unfixed code it failed in 0.77s with the genuine `PermissionError: [WinError 5]` at `nexus_hub_cli.py:782`, the exact line suspected. A once-in-hundreds-of-runs intermittent became a sub-second red test.
- **Fix**: `_replace_path_with_retry` wraps both directory renames in `_replace_org_repo` with a bounded backoff (50ms, 150ms, 300ms, 500ms), then makes a final unguarded attempt so a PERMANENT permission problem still raises the real error rather than being swallowed or spun on. The module already accepted this class of Windows behavior for deletion, in `_remove_owned_path`'s chmod-and-retry handler; the rename path simply had no equivalent tolerance. The restore-on-failure path now also tolerates a blocked restore without masking the original error.
- **Five tests**, covering the baseline with nothing blocking, a transient block that clears, a block that never clears (the retry must stay bounded), the restore-on-failure guarantee, and the unmocked real-held-handle case on Windows. The last is the one that would have caught this without knowing the mechanism in advance.
- **Why the earlier record said "not fixed"**: a fix could not be verified against a failure that would not reproduce on demand, and shipping unverifiable installer code is worse than shipping an accurate finding. Building the deterministic reproduction removed that objection, and the fix followed in minutes.

- **`_owned.py` staged files world-writable under a permissive umask** (carried in as v4.8 `WN-K`). `_atomic_replace_bytes` created its staging file `0o666`, which is `0o666 & ~umask`: world-writable on a host with `umask 000`, in code that ships in `scripts/` and runs during a user's install. It also rewrote the destination's permissions on every refresh, because `os.replace` carries the source's mode. Both are fixed by adopting the convention the sibling implementation in `scripts/lib/installer/instruction_merge.py` already used: create owner-only, then reapply the destination's own mode when one exists. Seven tests in `tests/integrations/test_owned_file_modes.py`, negative-controlled by restoring the original defect and confirming three of them fail. The tests spy on `os.open` and `os.chmod` rather than reading back `stat().st_mode`, because on Windows `S_IMODE` reflects only the read-only bit and a mode-readback test would have passed against the original defect.
- **The prompting profile layer reported DRIFTED** (carried in from the v4.8.0 release as an advisory). 12 of 16 rostered models are now profiled from fetched vendor primary sources, and the advisory check reports IN SYNC. Every claim is scoped `model-specific`; the classifier proposed zero shared-body edits, so no shared surface was touched.
- **The writer generated orphan bundled files.** Every per-model mirror it emitted was unreferenced from `SKILL.md`, so the orphan-warning count grew by one per profiled model (1 after the first OpenAI profile, 11 after this sweep) and the agent would never load a Tier-3 reference nothing points at. The writer now regenerates `references/model-profiles.md` linking every mirror, which returned the audit to its exact pre-sweep baseline of 65 warnings and also closed the pre-existing `gpt-6-astra` orphan. Guarded by `tests/validators/test_model_prompting_layer_bundle.py`, negative-controlled by removing one link and confirming the guard fails.

## Release reconciliation

MT-2 and QG-1 are resolved by [PR 190](https://github.com/bendourthe/Nexus-Hub/pull/190): Windows filesystem and Unicode selections passed, Linux tests and all three operating-system installer legs passed, and the corrected merge tree was integrated at `bd2c8968`. All 28 applicable checks passed; the unrelated Presentify job skipped. Post-merge smoke and provenance passed in run 34289027085. Their descriptions above preserve the pre-publication evidence boundary.

The separately owned platform follow-up is included in this release: Copilot new-install defaults use the documented string value, and Antigravity 2 workflows use the documented directory. Existing user settings and old workflow files are retained. The benchmark remains informational with native host attempts unavailable; the ignored private cleanup residue and prompting-profile limitations remain open. The interactive-handbooks plan remains queued at 0/7 phases and 0/31 tasks.

## v4.9.1 - interactive-handbooks-and-presentation-default

**Status**: Phases 1-5 complete; Phase 6 incomplete. No accepted gate bypass. Native sandbox writes, Chromium and explicit installed-skill loading work. A cross-profile probe exposed discarded deny rules in CLI 0.153.4; temporary CLI 0.154.0 applies the configured denials and passes all five tested forbidden reads. The current affected suite passes 510 tests and all 30 catalog checks. One of three native authoring families is independently accepted: the report. The latest repository fails branding placement and semantic process motion; the previous presentation fails native chart-title contrast. Corrected shared guidance is under fresh serialized qualification with frozen inputs, predeclared time limits and three internal repairs. Original failed artifacts remain unchanged. Full feature/design and native export qualification, the Phase 6 commit and Phase 7 integration remain open. See [Phase 6 evidence](development/interactive-handbooks/phase-6-evidence.md).

### Summary

No new deferred item or waived requirement. Existing v4.9.0 gaps retain their owners.

The completed report retry is also a non-pass: native Word paints the source-appendix table beyond the page edge despite successful HTML/PDF/rebuild checks. The DOCX owner now keeps grid and header/body cell widths consistent and checks usable page width. Four new regressions and twelve affected DOCX/distribution/workflow checks pass. The diagnostic correction is excluded from qualification; a fresh bounded report invocation remains required.

The completed presentation retry opens normally and retains correct native chart values and process edges, but timed PowerPoint playback shows no automatic process or chart-series builds. The shared PPTX owner now includes a portable native fade helper, an explicit required-motion gate and a documented integration recipe. Seventeen affected checks pass with 96.59% helper coverage; both installers deliver matching helper bytes, and a separate diagnostic deck visibly executes eight overlapping process effects and one chart-series fade. Native PowerPoint also opens the corrected connector-only case without repair. The failed author output is unchanged, and a fresh presentation invocation is queued after the corrected report. No diagnostic edit is counted as qualification.

The repository final attempt timed out after 3,600.75 seconds without its final result record. Independent browser inspection reproduces two alternate-panel overflows at 2560x720; this remains a non-pass. The QA owner now requires alternate-panel inventory before first QA. The report run is active, the presentation run is queued, and a fresh repository case is queued with the same frozen input and three-correction ceiling under a predeclared 5,400-second limit. No result from an earlier skill revision or failed artifact is silently restamped.

The subsequent report-final invocation is independently accepted after three internal corrections in 3,247.39 seconds. Its final HTML, PDF and DOCX rebuild byte-identically; native Word renders two complete pages with correct Arial fonts and no outside-page text, and the PDF passes two rendering engines plus QPDF. Two hundred default states and 404 independent control/paint-order checks pass their recorded scopes. See [accepted report evidence](development/interactive-handbooks/phase-6-native-attempts/report-final/summary.json). The native authoring gate is 1/3 accepted; the active presentation and queued repository cases remain required. Earlier failed reports are not relabeled.
