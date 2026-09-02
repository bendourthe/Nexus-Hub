# Known Gaps - v4.4

**Project**: Nexus-Hub
**Status**: v4.4.0 finalized 2026-09-01 at `/update release`; v4.4.1 merged to `develop` 2026-09-02 (PR #154), release pending; v4.4.2 in progress on the same minor
**Last updated**: 2026-09-02 (v4.4.2 Phase 2)

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
- **`HT-3` Sixteen merged remote branches remain as cleanup candidates.** Owner: maintainer. `check_release_preconditions.py --branches` reports them, `delete_branch_on_merge` does not cover them, and the external-settings contract forbids automatic mutation. Recorded rather than applied because this plan's mutation authority is limited to v4.4.1-traceable work. Next step: review and delete by hand, or accept as standing state.

### Deferred from v4.4.1 Phase 6

- **Outline reflows the presentation slide while open.** The Outline panel is an in-flow block, so in present mode it squeezes the game panel for as long as it is open. State restores exactly on close (proved by BG-11's fix), and no acceptance criterion covers the open state, so overlaying the panel was left out of a late, unvalidated layout diff. Revisit alongside any future presentation-layout work.

> v4.4.1 section closed at its Phase 7 GO (2026-09-02); its open items `HT-1`, `HT-2`, `HT-3`, and the Outline-reflow P3 stay owned as recorded above.

## v4.4.2 - guide-production-ready-rebuild

**Plan**: [v4.4.2-guide-production-ready-rebuild.md](plans/v4.4.2-guide-production-ready-rebuild.md)
**Contract**: [phase-1-contract.md](development/guide-production-ready-rebuild/phase-1-contract.md) (requirement matrix, superseded-assertion register, byte ledger)

### Carried in from v4.4.1

- Outline reflows the presentation slide while open (P3) - owned by Phase 6, which makes the panel an overlay.
- `HT-1` no human comprehension cohort - re-issued in Phase 8 with the annotated-prompt and harness-animation prompts added.
- `HT-2` real current-host installer duty - stays with v4.4.1's release; this plan never runs a sandboxed installer.

### Closed during v4.4.2

| ID | Finding | Phase | Disposition |
|---|---|---|---|
| BG-13 | The sequencer demo dimmed text below WCAG AA | Phase 1 | The first `NexusSeq` demo faded inactive loop pills to opacity .45 and the contrast sweep measured 1.9:1 (light) and 3.4:1 (dark) mid-sequence. Rule adopted: text carriers never change foreground contrast during a sequence. Added `seq-glow` (accent ring on the active step), switched the loop to it, and reserved `seq-fade` (floor .7) for shapes and connectors with a comment recording why. Sweep green. |

### Phase 2 notes

- No new defect. The new two-thirds word-budget test failed twice on the first integrated run (`Why it matters` 62 vs 56, merged comparison 196 vs 170); both were trimmed in copy, never by loosening the test.
- Platform-mark attribution moved from the Home disclosure to a site footer per `docs/decisions/implemented/policy/2026-09-02-platform-mark-attribution-in-footer.md`; the plan's `product/` decision class does not exist, so `policy/` was used.

### Deviations recorded

- `.section-title` minimum bound is 0.6x the scaled floor (34.5 px at scale 3) instead of the plan formula's 57.6 px, so a long word cannot overflow a 320 px viewport; the 1440 px anchor (81.6 px, exactly 3x v4.4.1) is unchanged. Recorded in the Phase 1 contract.

> Not finalized. v4.4.2 is in progress; this section is appended per phase and reconciled at the plan's final phase.

