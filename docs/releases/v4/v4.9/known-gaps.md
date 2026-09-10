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
| BG | 3 | 1 |
| WN | 3 | 0 |
| MT | 0 | 2 |
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

#### BG-2 - WITHDRAWN: reading scroll restore is correct; the report was a harness artifact

- **Source phase**: Phase 6, T019, reported against Phase 2 output.
- **Plan reference**: R25 global reset and return-to-page behavior.
- **Status**: not a defect. Recorded here because the claim reached this ledger before it was reproduced, and withdrawing it in place is more useful than deleting it.
- **What was claimed**: closing the presentation left the reading page at scroll 0 instead of its prior 2000, said to reproduce on a stock build and therefore to be a defect in committed `assets/dual-view-runtime.js`.
- **What direct reproduction showed**: the runtime saves and restores correctly. On a 4807-pixel page, opening and closing through the public API restores 2000 and 3000 exactly, and an in-page `click()` on the entry button restores 2000 exactly. The failure appears only when the entry button is clicked through Playwright's `locator.click()`, which scrolls its target into view before dispatching. Both entry buttons sit at the top of the page, so that auto-scroll moves the viewport to 0 BEFORE the deck opens; the runtime then correctly captures and restores 0. Instrumenting the scroll position at the moment of opening shows 0 for the Playwright path and the intended value for the in-page path.
- **Correcting the recorded mechanism**: an earlier note in this cycle attributed the behavior to `window.scrollTo` running before layout after `page.hidden` was cleared, with no `requestAnimationFrame` in the file. That explanation is wrong; `scrollTo` forces layout itself, and the existing `test_entry_reset_chapter_and_exit_restore_reading` already asserts a restored scroll and passes.
- **Suggested next step**: no runtime change. When a future harness exercises scroll restore, drive the entry through an in-page dispatch or place the control below the fold, and assert the scroll captured at open rather than only the value after close. Treat a runner-reported defect in committed code as unconfirmed until reproduced outside the reporting harness.

#### BG-3 - The extractor has no HTML reader while the plan requires legacy HTML migration

- **Source phase**: Phase 6, T020.
- **Plan reference**: T020 legacy HTML migration; R11 layout preservation.
- **Reason**: `scripts/extract_content.py` maps roughly seventy-five extensions and `.html` is not among them, appearing once in the module and never as an input format. The frozen repository fixture supplies `docs/handbooks/html/operations.html`, so the case ingested eight of nine files. The run disclosed the omission on the delivered page rather than concealing it.
- **Suggested next step**: decide explicitly whether an HTML reader is in scope for v4.9.1 or whether T020's legacy-migration clause is amended; do not leave the requirement and the implementation in silent disagreement.

#### BG-4 - Brand light and dark variants are selected inverted

- **Source phase**: Phase 6, T020, repository case.
- **Plan reference**: R26 brand fidelity and source-to-SVG comparison at actual sizes.
- **Reason**: every slide selects the opposite brand variant, leaving the wordmark invisible on both light and dark slides with only the diamond legible. The runner records it as a one-character fix in authored output; no automated gate covers wordmark legibility.
- **Suggested next step**: fix the selection and add a check that a supplied wordmark is legible against the theme it is placed on, so this cannot pass silently again.

#### BG-5 - Chart data points are stretched by a non-uniform aspect ratio

- **Source phase**: Phase 6, T020, repository case.
- **Plan reference**: R17 figure fidelity.
- **Reason**: `preserveAspectRatio="none"` deforms data points into ellipses in the delivered figure.
- **Suggested next step**: correct the aspect handling and cover it in the figure checks.

#### WN-2 - A section renders at partial opacity at load

- **Source phase**: Phase 6, T019, presentation case.
- **Plan reference**: R23 motion lifetime and reduced-motion behavior.
- **Reason**: a section partially visible at load renders at opacity 0.45 from the scroll-driven reveal, so first paint shows content the reader cannot properly read.
- **Suggested next step**: ensure any element within the initial viewport reaches full opacity at first paint regardless of scroll position.

#### WN-3 - The chart pane leaves roughly half the slide empty

- **Source phase**: Phase 6, T020, repository case.
- **Plan reference**: R20 and R23 composition quality.
- **Reason**: a positive-design judgment recorded by independent review; no automated gate covers it and none should be invented as a beauty detector.
- **Suggested next step**: treat as authoring guidance in the design reference; it remains a human or agent visual judgment.

#### WN-4 - The retained chart renderer offers no axis-limit control

- **Source phase**: Phase 6, T019.
- **Plan reference**: `SKILL.md` interactive-chart requirements.
- **Reason**: `SKILL.md` requires readers to adjust axis limits and the retained renderer provides no such control, so the contract and the implementation disagree.
- **Suggested next step**: implement the control or amend the contract; record which was chosen.

#### QG-2 - The three-family authoring gate is unmet and cannot be waived

- **Source phase**: Phase 6, T020.
- **Plan reference**: T020 three of three final passes.
- **Reason**: accepted input families remain 1 of 3 after both queued invocations. A corrected specimen cannot retroactively qualify the invocation that produced it, so fresh cases are required once the findings above are addressed.
- **Suggested next step**: close MT-3, MT-4, BG-2, BG-4 and BG-5, resolve BG-3 as scope or amendment, then run fresh presentation and repository cases under their declared budgets.

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
