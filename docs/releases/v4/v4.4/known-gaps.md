# Known Gaps - v4.4

**Project**: Nexus-Hub
**Status**: v4.4.0 finalized 2026-09-01 at `/update release`; v4.4.1 through v4.4.5 published together as the v4.4.5 tag on 2026-09-04 (PRs #154 and #157), after the operator's Home and Foundations review lifted the publication hold
**Last updated**: 2026-09-02 (v4.4.2 Phase 8)

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
| MT-1 | Main CI does not enforce browser-backed guide verification | Phase 7 | Added the scoped `guide-render` job with Playwright Chromium and `NEXUS_REQUIRE_RENDER=1`, wired it into `ci-required`, passed 67 workflow contract tests, and ran the exact fail-closed guide and detector targets locally with 154 passed and one explicit optional portfolio-copy skip. Remote clean-runner execution completed on pull request #150, where `guide-render` passed in 1m51s and `ci-required` aggregated green, closing the publication gate this entry named. |
| BG-1 | Training API accepted non-integer numeric scene indexes and corrupted exported state | Phase 7 | Restricted numeric navigation to in-range integers and added browser proof that `NaN` and fractional indexes preserve the current scene; the current focused Training explorer suite passed 3 tests. |
| BG-2 | Training presentation mode painted the game and terminal over later regions | Phase 7 | Restored natural grid height inside the scrollable presentation slide and added rectangle-separation checks at 1920x1080, 1440x900, 1024x768, and 900x900. |
| BG-3 | Training presentation mode allowed focus to escape and did not restore its invoker | Phase 7 | Added dialog semantics, background isolation, a Tab loop, early Escape handling, and post-fullscreen focus restoration; the current fail-closed Training explorer suite passed 3 tests in 21.22 seconds. |
| BG-4 | Denied-fullscreen presentation fallback survived route changes and left the destination inert | Phase 7 | Exit presentation when hash routing leaves Training, restore the recorded inert states, and prove that a rejected Fullscreen API followed by `#home` navigation leaves Home and the site header operable. |
| BG-5 | Presentation mode had no visible close control inside its isolated dialog | Phase 7 | Added an in-dialog `Exit presentation` control, preserved Escape behavior and invoker focus restoration, and exercised pointer exit through the focused browser suite. |
| QG-2 | Harness claim chips were omitted from the rendered label-containment inventory | Phase 7 | Promoted all five desktop and mobile claims to measurable nodes, retained readable font sizes, corrected chip geometry, and passed all 6 responsive widths in both motion modes. |

> Finalized on 2026-09-01 at the v4.4.0 publication. DF-1 remains open and owned by this ledger; it is a vendor-asset availability limit, not a defect, and will be ingested by the next `/plan`.

## v4.4.1 - guide-visual-and-arcade-rebuild

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 0 | 10 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Warnings

##### WN-1 - Phase 1 ran one model tier below the plan's recommendation

- **Source phase**: Phase 1 routing pre-flight.
- **Plan reference**: Phase 1 `**Recommended model tier**: frontier` / `**Recommended effort level**: max`.
- **Reason**: The refreshed model map places the session's `claude-opus-5` at the `strong` tier, while the phase recommends `frontier` (`claude-fable-5`). Claude Code cannot switch models programmatically, so the delta was surfaced at the pre-flight and the maintainer chose to continue on Opus 5 at max effort rather than switch. This is a recorded decision, not a silent downshift, and no mid-phase downshift occurred.
- **Impact**: None observed. Every Phase 1 gate passed, including the fail-closed browser suite, and the two load-bearing outputs (the measured vector mark and the asset ledger) were independently verified by render and by hash.
- **Suggested next step**: Re-surface the tier recommendation at each subsequent phase pre-flight. Phases 3, 4, 5, and 7 are also rated frontier/max and carry more implementation risk than Phase 1, so the same choice should be made deliberately rather than inherited.

##### WN-2 - The Phase 1 superseded-assertion register was incomplete

- **Source phase**: Phase 2 - Home identity, platform rail, and workflow loop.
- **Plan reference**: `docs/releases/v4/v4.4/development/guide-visual-and-arcade-rebuild/phase-1-contract.md` section 2.
- **Reason**: Phase 2 broke four assertions the register had not listed. Three pinned literal implementation strings (the exact hero markup, the exact text of a `querySelectorAll` selector, and a `data-logo-source` attribute selector inside a browser evaluation block) and are structurally invisible to a register built by reading requirements. The fourth was a measurement that became wrong rather than stale: `Range.getClientRects()` counts inline fragments, so a two-span title reported five "lines" on one visual line.
- **Impact**: None shipped. Every case was caught by running the suite, corrected in the same commit, and the two structural rows plus the generalized lesson were added to the register. The risk is to LATER phases, which edit the same shared markup and script.
- **Suggested next step**: Before Phases 3 through 6 change shared markup or shared script, grep the test suite for the literal strings being changed rather than trusting the register alone. Re-check at Phase 7 whether any register row was updated without a matching assertion change, or the reverse.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| BG-1 | The plan document leaked personal filesystem paths | Phase 1 | Sub-task 1.3 named the local Cursor candidates as absolute `C:/Users/<user>/Downloads/...` paths. `validate_no_personal_paths.py` reported 4 findings against the plan file, and that validator runs in `make validate` and CI, so the plan as authored would have failed the pipeline on commit. Redacted to a username-free `~/Downloads/...` form; the scanner is clean. |
| BG-12 | The end-of-file-fixer pre-commit hook rewrote approved-bytes evidence assets | Phase 7 | PR #154's `validate` check failed because `end-of-file-fixer` appended a newline to the seven staged platform and media SVGs, whose SHA-256 values are pinned in the provenance ledger and matched against the guide's embedded bytes. Reproduced locally, assets restored from HEAD, and `docs/releases/**/assets/` excluded from that one hook with a comment recording why; the sole Phase 7 commit was amended with the operator's explicit approval. |
| BG-11 | Opening Outline permanently collapsed the presentation game stage | Phase 6 | In present mode the game column was content-sized (`flex: 0 0 auto` with `max-height: 58%`) while `.nag-stage` inside it was fill-sized (`flex: 1 1 auto`), with `.nht-game` between them also content-sized. A fill-sized child has no definite height to resolve against inside a content-sized parent, so Chromium answered from layout history: opening Outline drove the stage to min-content (180 px to 42 px) and closing Outline never restored it, leaving `Click to start` outside the clipped stage and unclickable. The column was given a definite `height: 58%` and `.nht-game` was made `flex: 1 1 auto`. The fix then lost to the narrow-viewport reset, because a media query adds no specificity and the reset matched one fewer class-level component (the second occurrence of BG-4's lesson in this file), so the reset repeats the `:first-child` shape. Found only because fixed test sleeps were replaced with explicit condition waits, which turned an apparent flake into a consistent failure. |
| BG-10 | reset() created an unstartable idle game | Phase 5 | The engine's reset returned the world to `idle` without re-arming the Click-to-start overlay, so any reset after the first start (including every Training route change through `configureGame`) left an idle game with no visible way to begin. Every reset now re-arms the overlay and `restart()` hides it again immediately. Caught by the Phase 6 keyboard sweep timing out on a game that could never reach `paused`. |
| BG-9 | The fixed-damage fixture could not demonstrate its own rule | Phase 5 | The seeded enemy never re-fired, so after the single pre-placed shot the `enemy-hit` fixture could never walk lives 3 -> 2 -> 1 -> 0 in fixed mode. The enemy now re-fires on a deterministic cadence timed to land after each 90-tick invulnerability window; the buggy-mode tick-75 first hit is unchanged, and the scenario contract records the cadence. |
| BG-8 | The shooter engine crashed on page load | Phase 5 | The reduced-motion probe and the intersection observer both call `pause()`, which snapshots, and both were wired before the first `reset()` created state, so boot died on `Cannot read properties of null`. State creation moved above all DOM wiring with a load-bearing-position comment. |
| DF-1 | The four Phase 4 output-media assets were not yet staged | Phase 4 | All four generated as ORIGINAL local media (procedural balloon SVG, ten-frame Pillow sunrise GIF, a poster drawn from the same geometry constants, and a stdlib-synthesized two-note chime WAV), hashed into ledger section 3 as SETTLED, then embedded. `test_v441_phase4_foundations.py` decodes every embedded payload and hash-matches it against the staged file, so the approved-bytes-only rule is enforced, not assumed. |
| BG-7 | A dead animation primitive kept a reduced-motion check alive | Phase 3 | `fx-grow` lost its only consumer when the SVG context-budget diagram became an HTML node tree, leaving three orphan CSS rules and a reduced-motion assertion that failed on an empty element set. The CSS was deleted and the check made vacuously safe while staying strict for any element that exists, plus a guard asserting `fx-grow` is absent so a reintroduced consumer must restore its static state. |
| BG-6 | Tokens diagram caption text was clipped at the SVG viewBox edge | Phase 3 | Two caption lines ran past the 360-unit viewBox width and were cut mid-word. SVG text does not wrap, so the captions moved to an HTML paragraph below the diagram and the viewBox height was trimmed to match. |
| BG-5 | Unbalanced HTML re-parented the Training page out of `main` | Phase 3 | A two-step `<section>`-to-`<div>` conversion had its first step refused by a guard assertion, but the second step ran anyway, pairing `<section>` openings with `</div>` closings. The browser re-parented everything after the error, so `#page-training` became a direct child of `<body>` and presentation mode's inert walk never reached `.site-header`. A Training test caught a Foundations markup bug. Both opening tags were converted and the ancestor chains re-verified in the browser. |
| BG-4 | Narrow-screen layout overrides lost to source order | Phase 3 | The stacking rules for the new Foundations components were placed in a `@media` block ABOVE the base rules they override. A media query adds no specificity, so the later base rule won and `.fx-states` still computed three columns at 320 px, overflowing the viewport. The overrides were moved below their definitions with a comment recording why the position is load-bearing. |
| BG-3 | The hero heading's line box could not contain its own text | Phase 2 | `.hero-wordmark` used `line-height: 1`, making the h1 line box (68 px at 1440) shorter than its inline children's content boxes (90 px). The visual-defect detector reported 12 HIGH `parent-padding-escape` findings once Phase 2's two-span title gave it child elements to measure; the condition pre-dated Phase 2 and was simply unobservable with a bare text node. Raised to `line-height: 1.34`, which contains the font ascent and descent at every clamp size. Detector then passed both themes with 0 findings. |
| BG-2 | The plan's model map listed a Flash model as the Google frontier tier | Phase 1 | `## Current model map` carried `gemini-3.7-flash` in the frontier slot where the vendor documents `gemini-3.1-pro-preview`. The identical defect was corrected in `catalog/skills/ai-development/model-routing/references/last-known-model-map.json` during the v4.4.0 release, so the plan had inherited it. The plan's map is corrected and annotated, with the strong/standard split recorded as a maintainer judgment. |

### Open from v4.4.1 Phase 7

- **`HT-1` Last-phase human comprehension testing has no cohort.** Owner: maintainer. The plan's Definition of Done requires representative newcomers, without maintainer coaching, to distinguish prompt from context, provider training from a live request, qualified effort from a guaranteed hidden iteration count, chatbot output from permitted agentic action, and a platform's built-in harness from the Nexus-Hub portable layer, and to identify the lives and asteroid rules while using `Click to start`, Escape, and `Full screen`. No cohort was available. Recorded as an owned gap rather than a fabricated pass, exactly as the plan directs. Next step: run the six prompts in `last-phase-evidence.md` with two or more newcomers and append their answers and any comprehension gap.
- **`HT-2` Task 7.5's real current-host installer postcondition is unmet, and a sandbox attempt mutated live platform config.** Owner: maintainer decision required. Redirecting `HOME` did NOT isolate the run: the Nexus-Hub home honored the override, but per-platform integration paths resolve through Python `expanduser`, which reads `USERPROFILE` on Windows, so writes reached the real user profile and were then interrupted mid-run, leaving uneven skill counts across `~/.claude`, `~/.codex`, `~/.gemini`, `~/.cursor`, and `~/.qwen`. `~/.nexus-hub` was never written and still verifies PASS at 1835/1835 files, and the repository tree is unmodified. Two orphaned installer processes were terminated. Next step: repair with `cd ~/.nexus-hub/src && bash scripts/installer.sh --yes` (an idempotent reinstall from the pristine hash-verified v4.4.0 source), then either perform an approved real current-host install or explicitly accept this duty as an owned gap. DISPOSITION 2026-09-02: the operator chose to run the repair themselves and explicitly accepted the unmet real-install duty as an owned gap for v4.4.1 publication; GO recorded. The repair command above remains the owner's next step.
- **`CQ-1` CodeQL `js/xss-through-dom` (high) on the guide's media toggle.** Owner: maintainer. Alert #236 flags `img.src = img.getAttribute("data-motion-src")` in `initMediaToggles` (v4.4.1 code, commit `81b968dc`), reported as new on PR #156 only because the `develop` CodeQL baseline (`39f73a7e`, 2026-09-01) predates the v4.4.1 merge. The attributes are author-controlled static markup in an offline single file with no user input path, so the finding is not exploitable; it is nonetheless a real-looking high alert on the product's flagship safety artifact. Next step: either dismiss #236 as a false positive with this reasoning or, in the next guide release, resolve the two candidate sources through a small allowlist (`data:`/relative paths only) so the assignment is provably scheme-safe. Not fixed in v4.4.2 because the byte ledger and 150-case matrix were closed against the committed guide bytes. The three companion `py/uninitialized-local-variable` alerts (#237-#239) on the new v4.4.2 test fixtures were real static-analysis findings and were fixed in the same phase by loading the playwright entry point through a helper that returns `None` instead of relying on `pytest.fail`/`pytest.skip` being recognised as non-returning.
- **`QG-1` Six PowerShell core-settings seeding tests fail only under the CI profile runner.** Owner: maintainer. `tests/installer/test_core_settings_seeding.py` `[powershell]` variants pass standalone and fail with `proc.stdout is None` when `PYTHONUTF8=1` is set, which `scripts/ci/run.py` sets for deterministic reports; reproduced on `develop` at `68f3d082` with that variable alone, so it predates v4.4.2. The v4.4.1 evidence attributed the same failures to concurrent installer processes; that attribution was incomplete. CI is unaffected (the Ubuntu legs skip the PowerShell variant). Next step: run `PYTHONUTF8=1 python -m pytest tests/installer/test_core_settings_seeding.py -k powershell` and trace why `_run_powershell` (capture_output, text) yields a `None` stdout under that flag.
- **`HT-3` Seventeen merged remote branches remain as cleanup candidates (16 at v4.4.1's Phase 7, plus its own branch after merge).** Owner: maintainer. `check_release_preconditions.py --branches` reports them, `delete_branch_on_merge` does not cover them, and the external-settings contract forbids automatic mutation. Recorded rather than applied because this plan's mutation authority is limited to v4.4.1-traceable work. Next step: review and delete by hand, or accept as standing state.

### Deferred from v4.4.1 Phase 6

- **Outline reflows the presentation slide while open.** The Outline panel is an in-flow block, so in present mode it squeezes the game panel for as long as it is open. State restores exactly on close (proved by BG-11's fix), and no acceptance criterion covers the open state, so overlaying the panel was left out of a late, unvalidated layout diff. Revisit alongside any future presentation-layout work.

> v4.4.1 section closed at its Phase 7 GO (2026-09-02); its open items `HT-1`, `HT-2`, `HT-3`, and the Outline-reflow P3 stay owned as recorded above.

## v4.4.2 - guide-production-ready-rebuild

**Plan**: [v4.4.2-guide-production-ready-rebuild.md](plans/v4.4.2-guide-production-ready-rebuild.md)
**Contract**: [phase-1-contract.md](development/guide-production-ready-rebuild/phase-1-contract.md) (requirement matrix, superseded-assertion register, byte ledger)

### Carried in from v4.4.1

- Outline reflows the presentation slide while open (P3) - CLOSED in Phase 6: the panel is `position: absolute` in present mode and `test_opening_outline_moves_no_region` asserts every region rectangle is identical before and after opening at the four desktop sizes.
- `HT-1` no human comprehension cohort - re-issued in Phase 8 with the annotated-prompt and harness-animation prompts added.
- `HT-2` real current-host installer duty - stays with v4.4.1's release; this plan never runs a sandboxed installer.

### Closed during v4.4.2

| ID | Finding | Phase | Disposition |
|---|---|---|---|
| BG-16 | The v4.4 known-gaps ledger ended with two newlines and turned the required `validate` check red on the first integration run of PR #156 | Phase 8 | Reproduced locally with `python -m pre_commit run end-of-file-fixer --files docs/releases/v4/v4.4/known-gaps.md`; one blank line removed. Same class as `BG-12`: the lifecycle's first remote run is where whitespace hooks bite. |
| BG-15 | The count stamper's `--check` was not reachable from CI | Phase 8 | Phase 1 wired `stamp_guide_counts.py --check` into `make validate` and recorded it as covered by the `validate` job, but that job runs `scripts/ci/profiles.py` groups, not `make validate`. Caught by `test_every_validator_make_validate_runs_is_reachable_from_ci` in the Phase 8 profile run; registered in the DOCS group. |
| BG-14 | The harness ghost chip dimmed text below WCAG AA | Phase 4 | The `raw answer` ghost group used `opacity: .55`; the contrast sweep measured its text at 2.4:1 (light) and 3.3:1 (dark). Same rule as BG-13: text carriers never lose contrast. The ghost is now a dashed chip with `--ink-dim` text at full opacity. |
| BG-13 | The sequencer demo dimmed text below WCAG AA | Phase 1 | The first `NexusSeq` demo faded inactive loop pills to opacity .45 and the contrast sweep measured 1.9:1 (light) and 3.4:1 (dark) mid-sequence. Rule adopted: text carriers never change foreground contrast during a sequence. Added `seq-glow` (accent ring on the active step), switched the loop to it, and reserved `seq-fade` (floor .7) for shapes and connectors with a comment recording why. Sweep green. |

### Phase 2 notes

- No new defect. The new two-thirds word-budget test failed twice on the first integrated run (`Why it matters` 62 vs 56, merged comparison 196 vs 170); both were trimmed in copy, never by loosening the test.
- Platform-mark attribution moved from the Home disclosure to a site footer per `docs/decisions/implemented/policy/2026-09-02-platform-mark-attribution-in-footer.md`; the plan's `product/` decision class does not exist, so `policy/` was used.

### Phase 3 notes

- No new defect. Two first-run failures were specificity and source-order losses (`.fx-stack` to `.fx-scene`, `.fx-subtitle` to `.fx-copy p`), the `BG-4` lesson recurring; fixed with compound selectors and a CSS comment.
- Models and Harnesses are stacked as an interim balance; Phase 4 rebuilds both diagrams and re-measures against the 1.35 bound.

### Phase 4 notes

- Two SVG captions overran the viewBox; repositioned, with a six-width containment test added. A helper CSS rule whose selector contained `.fx-region-tag` shadowed the original in a first-match regex test and was dropped rather than the test loosened.
- Headless Chromium advances a media element slowly with no output device, so the waveform test proves continuous analyser-driven drawing and a live-versus-static difference rather than frame-to-frame change.
- The uppercase `NEXUS-HUB` trail label survived the case-sensitive Phase 1 rename; fixed, and the rename test is now case-insensitive.

### Phase 5 notes

- No new defect. Both seeded teaching beats passed unedited after spawning was added, because the spawn decisions draw from a second stream (`seed ^ 0x9E3779B9`) and never touch the beat stream.
- Tier variety is proven through the pure `logic.spawnSample` seam because a stationary test player does not survive full-width `play` spawning for long, which is correct behaviour and not the property under test.
- The wall-parking bounds test was shortened from 45 simulated seconds to 150 ticks per side: under the amended contract a wall-parked player is a legitimate target, and the clamp is proven in about 62 ticks.

### Phase 6 notes

- Stage-height floor recorded as 0.45 of the viewport instead of the plan's 0.70, with the arithmetic in `presentation-geometry.md`; achieved 0.47 to 0.61 against a baseline of 0.10 to 0.26. Coverage rose from 0.68 to 0.81 up to 0.93 to 0.95, and no region falls below the fold any more.
- No new defect. The first build reached 0.42 at 1280x720 and was lifted by a `(max-height: 768px)` compact-chrome rule rather than by lowering the floor.

### Phase 7 notes

- Title-scale token tuned from 3 to 2.4 by the plan's rule (a title wrapping to three lines at 1440 reduces the token, floor 2.4); every title is now two lines or fewer at 1440. Prompt Engineering was stacked as a consequence (its copy column shrank past the 1.35 bound).
- No new defect. The README sync briefly dropped the exact phrases a v4.4.0 test requires for the CI browser contract; restored with the reason they matter.
- Declared browser matrix: 150/150 cases, 124/124 screenshots, 0 failures, 165 s, 12.7 MiB; fullscreen minimum coverage 0.93 and stage fraction 0.468.

### Phase 8 notes

- Nine local duties recorded in the v4.4.2 evidence block; GO with two accepted owned residuals (`HT-1` no cohort; the 0.45 stage floor deviation). No sandboxed installer run was attempted; the real-install duty stays v4.4.1's owned `HT-2`.
- Fourteen defects were found and fixed across the plan (`BG-13`, `BG-14`, and twelve first-run test failures), each fixed in code or copy, never by loosening a test to fit.

### Deviations recorded

- `.section-title` minimum bound is 0.6x the scaled floor (34.5 px at scale 3) instead of the plan formula's 57.6 px, so a long word cannot overflow a 320 px viewport; the 1440 px anchor (81.6 px, exactly 3x v4.4.1) is unchanged. Recorded in the Phase 1 contract.

> Not finalized. v4.4.2 is in progress; this section is appended per phase and reconciled at the plan's final phase.
## v4.4.3 - guide-illustration-clarity-rebuild

**Plan**: [v4.4.3-guide-illustration-clarity-rebuild.md](plans/v4.4.3-guide-illustration-clarity-rebuild.md)
**Base**: `develop` at `a376c1ae`
**Status**: nine phases complete; published in the v4.4.5 tag on 2026-09-04 after the operator's Home and Foundations review lifted the hold.

### Closed during v4.4.3

| ID | What it was | Closed in |
|---|---|---|
| CV-1 | The guardrails figure escaped its own chips and collided its hook names with the rings | Phase 2 |
| CV-2 | The command loop occupied about two thirds of its column with unreadable arrow glyphs | Phase 3 |
| CV-3 | The budget comparison could not be read: three legend numbers mapped onto three unlabelled stripes | Phase 4 |
| CV-4 | Four dashed boxes each containing the noun they were already labelled with | Phase 4 |
| CV-5 | A spinning ring whose own caption denied what it appeared to show | Phase 5 |
| CV-6 | The motion output required a press before anything moved | Phase 5 |
| CV-7 | The scene taught a singular abstraction and named no platform | Phase 6 |
| CV-8 | The chatbot comparison was two columns of prose the reader had to compare unaided | Phase 7 |
| CV-9 | Two harness scenes whose SVG labels overlapped each other and the rings | Phase 8 |
| CV-10 | The product addressed the reader in 55 places | Phase 1 |

### Defects this plan introduced and fixed inside it

| ID | Defect | Found by | Fixed in |
|---|---|---|---|
| BG-17 | The fit pass measured a `max-width`-capped box, so no label ever shrank and whole scenes overflowed | `test_every_scene_child_stays_inside_its_scene_box` | Phase 1 |
| BG-18 | A `nowrap` heading inflated a `1fr` scene track to 753px inside a 672px scene, and the fit pass then read the inflated track as available room | same | Phase 1 |
| BG-19 | A fixed pixel `max-width` on the guardrails ring, which the v4.2.3 responsive rule forbids on a text-bearing element | `test_no_hardcoded_text_width_caps_remain` | Phase 4, shipped in Phase 2 |
| BG-20 | Removing the budget CSS also unstyled the harness trail, which had borrowed those rules; it rendered with no border, no background, and no columns for four commits | Phase 8 rebuild, then a new class-coverage guard | Phase 8, shipped in Phase 4 |
| BG-21 | `width: max-content` on the harness model box pushed both rings 88px outside the scene at 320px | `test_every_scene_child_stays_inside_its_scene_box[320]` | Phase 8 |
| BG-22 | The `.fx-mat--row` modifier lost to `.fx-mat` on source order, so the wide material row stayed two columns | direct measurement | Phase 5 |
| BG-23 | The merged harness label was 66 characters, which cannot hold one line at 720px above the 15px floor | `test_no_heading_wraps_from_720_upward` | Phase 8 |

### Pre-existing defects found and closed

| ID | Defect | Note |
|---|---|---|
| BG-24 | The hero lockup's seven-second infinite float had NO reduced-motion state | Exposed by Phase 5: removing the ring left the lockup as the only continuous animation, and the old assertion covered the ring instead of it. One rule added. |
| BG-25 | `test_harness_svg_text_stays_inside_its_viewbox` would have passed vacuously once its selector matched nothing | Rewritten over the HTML figure, where it measures every leaf's glyph run against its own box at six widths. |

### Open

- **`CQ-1` (carried from v4.4.2)** CodeQL `js/xss-through-dom` on the guide's media toggle. The toggle itself was REMOVED in Phase 5, so the flagged assignment no longer exists in the shipped file. The alert should be re-evaluated on the next scan rather than assumed closed; if it clears, close `CQ-1` then.
- **`HT-4` No human comprehension cohort for the rebuilt illustrations.** Owner: operator. The whole point of this version is that the pictures read on first look, and that claim is measured only by geometry and contrast, never by a reader. The operator's own review is the intended next step and is why this version is unpublished.
- **`HT-2` (carried from v4.4.1)** Real current-host installer run and the operator's config repair. Untouched by this plan.
- **`QG-1` (carried from v4.4.2)** Six PowerShell core-settings seeding tests fail only under the CI profile runner's `PYTHONUTF8=1`.

### Deviations recorded

- **`D2` relaxed with arithmetic.** No heading wraps at 720px and wider. Below 720px the fit pass holds a 15px floor and hands wrapping back, because one line at 320px costs about 8px of type; nothing spills past its container at any width. Recorded in the phase contract.
- **The label is now larger than the title.** The review named both numbers (triple the label, halve the title), which converges them at about 33px and inverts the usual hierarchy. Shipped exactly as asked, and flagged for the review.
- **Product names against vendor marks.** The four platform chips label the product while the mark belongs to the vendor: Claude Code carries the Claude mark, Codex the ChatGPT mark, Antigravity the Gemini mark. Cursor is exact. Recorded in the asset provenance ledger with the reason the linked aggregator was not used.
- **One second sanitization of an approved asset.** The Gemini mark's 13 internal ids are re-namespaced in its second instance, because a duplicate id would make the second copy resolve its mask and filters against the first. The test derives the variant from the approved bytes so the prefix is provably the only change.
- **Two commits in Phase 2 and Phase 8 carry work belonging to an adjacent task.** Phase 2 carries the table column widths (a Phase 1 refinement found after that commit), and Phase 8 carries three count updates caused by its own scene merge. Both are stated in their histories.

## v4.4.4 - guide-teaching-clarity-rebuild

**Plan**: [v4.4.4-guide-teaching-clarity-rebuild.md](plans/v4.4.4-guide-teaching-clarity-rebuild.md)
**Base**: the v4.4.3 closeout at `bcfa3413`, on the same branch (v4.4.3 was never published)
**Status**: nine phases complete; published in the v4.4.5 tag on 2026-09-04 after the operator's Home and Foundations review lifted the hold.

### Closed during v4.4.4

| ID | What it was | Closed in |
|---|---|---|
| TC-1 | The guardrails segment was named for a property rather than for what it does, and its ring headers were left-aligned | Phase 1 |
| TC-2 | The command segment taught one benefit of two: it never showed that one install reaches every platform | Phase 2 |
| TC-3 | Foundations put the scene DESCRIPTION above the scene NAME | Phase 3 |
| TC-4 | Prompt Engineering pointed a sideways arrow into empty space and compared two paragraphs | Phase 4 |
| TC-5 | Context Engineering stacked the request above the material and left the cost of dumping everything implied | Phase 5 |
| TC-6 | Models catalogued four outputs instead of teaching next-token prediction, base against reasoning, and modality | Phase 6 |
| TC-7 | Two scenes taught one idea, and the platform scene's six-stage flow was unreadable | Phase 7 |
| TC-8 | The harness showed WHERE the layers sit rather than following a request through them | Phase 8 |

### Defects this plan introduced and fixed inside it

| ID | Defect | Found by | Fixed in |
|---|---|---|---|
| BG-26 | Two non-greedy replacements left stray closing tags in the Models scene; one closed the request region early, dropping a flow root and cutting the connectors from seven to two while rendering without visible error | `test_flow_connectors_never_cross_a_card` | Phase 6 |
| BG-27 | The stale-offset splice from v4.4.3 Phase 8, repeated: the CSS insertion shifted every index and the merged scene landed inside a base64 payload | rendering the scene and looking at it | Phase 7 |
| BG-28 | `.cx-ex` used `--blue`, which had no light-theme override at all, measuring 1.90:1 | the contrast sweep, once the reduced-motion fix made the text visible | Phase 6 |
| BG-29 | Three modifier classes lost to their base class on source order (`.fx-mat--row`, `.cx-row`, `.mx-tiers`) | direct measurement | Phases 5 and 6 |

### Pre-existing defects found and closed

| ID | Defect | Note |
|---|---|---|
| BG-30 | A sequence step stayed HIDDEN under reduced motion until the observer played it | Zeroing the transition was not enough. A reader who asked for less motion saw an empty strip until they scrolled. |
| BG-31 | `.gf-out--ok` / `--stop` (v4.4.3 Phase 2) and `.cv-changes li` (v4.4.3 Phase 7) failed WCAG AA in light theme, at 3.92 and 4.08 | Both shipped INVISIBLE, because the contrast sweep samples only visible text. Closing `BG-30` is what exposed them. **A contrast sweep that skips hidden text will pass a palette it never measured.** |

### Open

- **`HT-4` (carried)** No human comprehension cohort. Two rounds of operator review have now driven the illustrations, which is better than none, but no reader outside this loop has been asked whether the pictures land.
- **`RV-1` One correction to the brief, for the operator to accept or reject.** The Models scene names `xAI Grok`, not `Cursor Grok` as the brief listed. Grok is xAI's model; Cursor is a platform that offers models. Applied with the correction flagged rather than silently.
- **`RV-2` The label still renders slightly larger than the title on Home.** That is what tripling one and halving the other produces, and it was asked for explicitly in the first review round. Flagged again because it is the kind of thing a reader notices before a maintainer does.
- **`CQ-1` (carried)** CodeQL `js/xss-through-dom` on the media toggle. The toggle was removed in v4.4.3 and the audio output in v4.4.4, so the flagged construct is gone; re-evaluate on the next scan rather than assuming closed.
- **`HT-2`, `QG-1` (carried from v4.4.1 and v4.4.2)** Unchanged by this plan.

### Deviations recorded

- **Phases 1 and 2 share one commit.** Both are Home wording and illustration work, and the Phase 1 edits were already in the working tree when Phase 2 began; splitting afterwards would have meant reconstructing a boundary rather than observing one.
- **One word-count rule narrowed rather than raised.** The v4.4.1 ceiling on restored Home prose now excludes blocks marked `data-v444-new`, which carry their own explicit cap. Restored prose still cannot creep back toward its v4.1.2 length, and the new figure cannot grow unmeasured.
- **The audio asset is retired but not deleted.** The staged WAV stays in `assets/` and its ledger row stays in the provenance document, so a future reinstatement needs the approval gate rather than a new acquisition pass.

## v4.4.5 - guide-mockup-integration

**Plan**: [v4.4.5-guide-mockup-integration.md](plans/v4.4.5-guide-mockup-integration.md)
**Base**: the v4.4.4 closeout at `3ac90bb2`, on the same branch (neither v4.4.3 nor v4.4.4 was published)
**Status**: eight phases complete; published in the v4.4.5 tag on 2026-09-04 after the operator's Home and Foundations review lifted the hold.

### Closed during v4.4.5

| ID | What it was | Closed in |
|---|---|---|
| MI-1 | The portability figure revealed itself in three steps, which the review said made the boxes hard to read; it had no platform logos, and its triangles drifted off centre at every width but the authored one | Phase 1 |
| MI-2 | Eleven Foundations tag rules each declared their own hand-written size, and every one of them was half the size the review asked for | Phase 2 |
| MI-3 | The prompt's four parts used a vocabulary the review replaced, and one word changed MEANING rather than spelling | Phase 3 |
| MI-4 | The vague prompt sat in a narrow column beside one tall stack of flaws | Phase 3 |
| MI-5 | Two token captions rendered as plain body text because their rule had matched nothing since the figure moved | Phase 4 |
| MI-6 | Models catalogued its content instead of following the eight-stage spine the review supplied, and had no Select or Predict stage | Phase 5 |
| MI-7 | Agentic Platforms never said what "agentic" means, and its boundary showed one setting of three | Phase 6 |
| MI-8 | Only one of the three harness layers stated a limit; the outer loop's work sequence was absent and its artifact chain was claimed rather than shown | Phase 7 |

### Defects this plan introduced and fixed inside it

| ID | Defect | Found by | Fixed in |
|---|---|---|---|
| BG-32 | Hoisting the four vendor marks into shared symbols rendered the Gemini mark BLANK: a `<use>` clone resolves a mask reference against its own shadow tree and found the cloned mask | a screenshot | Phase 1 |
| BG-33 | Hoisting that mask to document level, the documented workaround, rendered an unmasked SQUARE | a screenshot | Phase 1 |
| BG-34 | The centring measurement reported a triangle 530px off centre inside a 720px figure, by comparing a hidden lane's zero rect against a real box | reading an impossible number | Phase 1 |
| BG-35 | The Models rebuild rendered the base-versus-reasoning lanes TWICE, because `.mx-lanes` was a child of `.fx-pass` rather than its sibling. Every test passed | a screenshot | Phase 5 |
| BG-36 | `data-stage="output"` landed on both the phase wrapper and the harvested tiers block | the v4.4.1 chronology guard | Phase 5 |
| BG-37 | The artifact chain shipped as four full-width chips stacked one per line. The test passed, because four identical left offsets sort perfectly well | a screenshot | Phase 7 |

### Pre-existing defects found and closed

| ID | Defect | Note |
|---|---|---|
| BG-38 | `.fx-copy .fx-tokfig-cap`, `--mid`, and `.fx-tokfig-note` have matched NOTHING since the token figure moved into `.fx-diagram`. Both captions and the note under the chips have been rendering as plain 16px sentence-case body text | This is what the review is asking about when it wants a caption "styled like 'Vague'": the styling the rule already described and never applied. The v4.4.3 class-coverage guard cannot catch this class of defect - it proves a class USED in the markup has a rule, not that a rule's selector matches anything. Those are different questions. |

### Open

- **`RV-3` The Models scene names `xAI Grok`, not `Cursor Grok` as the brief listed.** Grok is xAI's model; Cursor is a platform that serves models. Applied with the correction flagged rather than silently, and carried forward from `RV-1` because the brief repeated the pairing.
- **`RV-4` `Context Engineering Best Practices` now reads QUIETER than the two budget tags below it.** Both instructions were followed exactly and they pull against each other: the heading was asked to match the scene subtitle (17px, weight 500, dimmed), and Phase 2 doubled the tags under it to 23px. Which one wins is the operator's call.
- **`RV-5` The Home label still renders slightly larger than its title**, carried from `RV-2`. Unchanged by this plan.
- **`GA-1` A rule's selector is never proven to match anything.** `BG-38` shipped for versions because no guard asks that question, and there is no reason to believe it is the only dead selector in a 396 KB stylesheet. A dead-selector sweep would be cheap and is not in this plan.
- **`HT-4` (carried)** No human comprehension cohort. Three rounds of operator review have now driven these illustrations, which is far better than none, but no reader outside this loop has been asked whether the pictures land.
- **`CQ-1`, `HT-2`, `QG-1` (carried)** Unchanged by this plan.
- **`WN-3` Two warning-severity CodeQL alerts in this release's files were dismissed as false positives at the v4.4.5 release merge.** The repository's code-scanning merge protection blocked the develop-to-main release PR (#159) on alerts new relative to main's baseline. Six sat in files this release changed: four error-severity `py/uninitialized-local-variable` hits on `sync_playwright` in guide test fixtures, fixed by binding the name to `None` on import failure (behaviour unchanged), and two warnings dismissed with reasons recorded on the alerts: #240 `js/xss-through-dom` at `guides/website/nexus-hub-guide.html` (an `img.src` assigned from the page's own `data-poster-src` attribute in a self-contained offline file with no external input) and #241 `py/incomplete-url-substring-sanitization` at `tests/guides/test_nexus_hub_guide.py` (a test assertion, not a sanitizer). The other 94 alerts on the PR were in files untouched since v3.x and appeared only because `codeql.yml` runs on `main` by weekly schedule, so main's baseline predated the v4.4.0 merge; a manual dispatch refreshed it. Suggested next step: give `codeql.yml` a `push: branches: [main]` trigger so the baseline follows every release, and re-check #240 if the guide ever accepts user-controlled input.

### Deviations recorded

- **Phases 6 and 7 are separate commits, but Phase 6's evidence is targeted rather than the full suite.** The full guides suite ran at Phase 7, the next change to the same file. Running it twice for two consecutive edits to one artifact buys nothing, and Phase 6's own modules plus the broad module were green at its commit.
- **The mockups' four closing truths are not all imported.** Two of the agentic mockup's four are now said by the equation and by step 02 of the existing loop; a reader told the same thing twice trusts the second telling less. The two said nowhere else are folded into the boundary block and the closing note.
- **The Gemini mark is duplicated rather than shared, at a cost of about 12 KB.** Three attempts at sharing are recorded in `BG-32`, `BG-33`, and the ledger hash guard. The approved bytes stay where the ledger pinned them.

## v4.4.6 - guide-learning-experience

Current disposition: SUPERSEDED BY USER. The v4.4.6 redesign and temporary follow-up are rejected; the exact v4.4.5 guide is restored. The rows below describe the rejected artifact and remain historical. Existing v4.4.5 visual/animation issues must be assessed under the [corrected scope](development/guide-learning-experience/restoration/verification.md), preserving all sections and content.

Status: local implementation complete through Phase 6; final verification and external gates remain in Phase 7. Historical sections above are preserved. The current disposition below supersedes carried guide items only where fresh evidence exists.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 3 | 7 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 3 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |

### Open Items

| ID | Gap and gate impact | Owner | Next step |
|---|---|---|---|
| BG-46 | Mobile Training introduction leaves an isolated it on the second heading line; D06/D12 are partial | Guide implementer | Apply the previewed shorter heading only after the additional bounded correction pass is authorized, then verify 320/420px in both themes. |
| BG-47 | Fullscreen idle terminal reserves excessive blank space before its reply placeholder; D06/D12 are partial | Guide implementer | Apply the previewed idle-only sizing correction after the bounded-pass decision; verify before/after Run at all four fullscreen sizes and narrow fallback. |
| MT-446-3 | Linux browser verification is unavailable: Ubuntu has no installed browser or Playwright runtime; installer success is separate evidence | Guide owner on Linux | Run the guide browser checks in an available Linux environment and retain engine/version/results. Do not infer Linux browser coverage from the two installer smokes. |
| BG-48 | A hostile-input test fixture appears in the shipped describe reply and distracts from the teaching example | Guide implementer | Remove the fixture from production scene data and retain escaping coverage with test-local input; source/inline parity and the describe exercise must pass. Include in the bounded follow-up disposition. |
| MT-446-1 | Technical and non-technical comprehension plus final user visual review are unverified; D13 and T026 remain open | Guide owner and two readers | Complete the [unassisted exercise](development/guide-learning-experience/phase-7/manual-review.md), retain actual responses, and address unclear concepts before publication. Carries HT-4. |
| MT-446-2 | Native 200% browser zoom and OS occlusion delivery are not proven by effective-width reflow or an instrumented hidden-state test | Guide owner on the target browser/OS | Perform the environment exercise; retain browser, OS, observations, and any affected correction. Native/fallback fullscreen and reduced-motion handlers have automated proof. |
| WN-446-1 | Existing primary guide-render CI lacks retained structured browser/JUnit artifacts; comparison is partial | CI maintainer | Review the minimal report/upload change with seven-day retention in [ci-comparison.md](development/guide-learning-experience/phase-7/ci-comparison.md), approve the pipeline change, then implement and verify it. No pipeline change was made in this guide plan. |
| WN-446-2 | Historical CodeQL CQ-1 has no fresh remote rescan; removal of the flagged construct alone does not close the alert | Security/CI maintainer | Re-evaluate the current head on the next authorized remote scan and record the result. |
| QG-446-1 | Full native profile: 40 command passes, three failures and one repository-test timeout. Encoding is now fixed; default Bash resolution and the unrelated v4.9 path scan remain separately classified. Complete local green gate is not established | Implementer / repository maintainer | Use [terminal disposition](development/guide-learning-experience/phase-7/full-profile-disposition.md) to isolate the repository-test stall and close remaining environment/scope findings. Do not infer the historical QG-1 assertion failures from absent current output. T027 remains open. |

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| BG-39 | Essential teaching nodes depended on animation visibility | Phase 2 | Nodes and connectors remain visible at rest, on ordinary scrolling, and under reduced motion. No-script reading fallback added. |
| BG-40 | Hidden Training canvas repainted on every animation frame | Phase 2 | Scheduling now belongs to the running lifecycle. Idle-page, route-resume, and deterministic game checks pass. |
| BG-41 | Training claimed success before matching completed work | Phase 6 | Pending/blocked/running/complete/failed states, prerequisite checks, and dependent reset invalidation align game, files, and evidence. |
| BG-42 | Keyboard command selection lost focus | Phase 6 | Progress and Outline restore focus after rebuilding the scene; independent failing proof now passes. |
| BG-43 | Disabled graph join control had insufficient contrast | Phase 7, cycle 1 | Readable text and dashed boundary replace opacity reduction; final contrast checks pass. |
| BG-44 | Rotated mobile model arrow inherited a stretched container | Phase 7, cycle 2 | Centered intrinsic geometry removes the parent escape; final detector and inspected mobile capture agree. |
| BG-45 | Graph extraction claimed launch approval unsupported by its input | Phase 7, cycle 3 | Output now says the launch moved, matching the meeting note; human approval remains pending. |

### Carried-item and repository disposition

The [repository audit](development/guide-learning-experience/phase-7/repository-audit.json) discovered 33 canonical and legacy known-gap files and retained their hashes/status observations. Other release owners and frozen history remain unchanged; this guide request does not authorize their implementation. The 735 lifespan scan candidates are archive-review candidates, not 735 confirmed defects. No files or branches were deleted or moved.

HT-2 now has fresh isolated Windows PowerShell and Ubuntu Bash installer proof with identical postconditions; this does not certify or repair the user's existing installation. RV-1 through RV-5 describe retired model-family, heading, and tag compositions and are superseded by the new lessons and measured typography. GA-1's broad dead-selector sweep remains outside this guide plan; no global cleanup was performed. QG-1 and CQ-1 require their own terminal evidence as recorded above. Publication, merge, and release approvals are lifecycle gates in T028, not silently completed implementation.
