# v4.4.1 Phase 1 Contract -- Requirements, Superseded Assertions, and Byte Ledger

**Plan**: [v4.4.1-guide-visual-and-arcade-rebuild.md](../../plans/v4.4.1-guide-visual-and-arcade-rebuild.md)
**Phase**: 1 -- Contracts, Asset Provenance, and Byte Budget
**Branch**: `feat/v4.4.1-guide-visual-and-arcade-rebuild`
**Created**: 2026-09-01
**Baseline**: the released v4.4.0 guide at tag `v4.4.0`, plus its retained render evidence

This document is the executable-contract half of Phase 1. It maps every accepted visual and teaching correction to a named assertion, records which currently-passing assertions a later phase will replace, and carries the byte ledger for the single-file budget. It deliberately does NOT weaken any current assertion: each superseded expectation stays green until its owning phase installs the replacement, which is why Phase 1 exits with zero intentionally-failing tests.

## 1. Requirement-to-test matrix

Legend for **State**: `covered` -- an existing assertion already proves it; `supersede` -- an existing assertion proves the OLD behavior and its owning phase must replace it; `new` -- no assertion exists yet and the owning phase must add one.

### 1.1 Home

| # | Requirement | Owning phase | Target assertion | State |
|---|---|---|---|---|
| H1 | Home renders the exact title `Nexus Hub` (not a hyphenated `Nexus-Hub`) with nav-matched typography and theme colors | 2 | new `test_home_title_is_nexus_hub_with_nav_parity` in `test_nexus_hub_guide.py` | supersede |
| H2 | The complete mark-and-wordmark lockup floats as one unit when motion is allowed | 2 | new `test_home_lockup_floats_as_one_unit`, observer-gated | new |
| H3 | Floating motion stops fully under `prefers-reduced-motion: reduce` | 2 | extend the existing reduced-motion sweep in `test_phase6_verification_sweep.py` | new |
| H4 | The platform rail contains exactly Claude, ChatGPT, Gemini, Cursor, GitHub Copilot in that order | 2 | replaces `test_home_lists_six_platforms_without_invented_marks` | supersede |
| H5 | OpenCode and its explanatory note are removed | 2 | same replacement assertion; negative check on `OpenCode` in Home markup | supersede |
| H6 | Every rail mark is inlined from an approved staged asset, proved by SHA-256 against this phase's ledger before normalization | 2 | new `test_home_platform_marks_match_staged_hashes` | new |
| H7 | Marks are transparent, share one optical box, and carry no opaque shell | 2 | new structural assertion on `platform-mark` | new |
| H8 | Marks are static and nonfocusable; visible labels are the accessible names | 2 | new; `aria-hidden="true"` plus `focusable="false"` on decorative SVG | partly covered |
| H9 | Label contrast is at least 4.5:1 in both themes | 2 | browser contrast check in `test_phase6_verification_sweep.py` | new |
| H10 | No clipped labels, horizontal overflow, or orphan row at 320 and 420 px | 2 | render matrix at 320/420 | new |
| H11 | Workflow command pills are readable two-line pills, not undersized one-liners | 2 | new `test_home_workflow_pills_are_two_line` | new |
| H12 | An accessible attribution/credits disclosure exists wherever asset terms require it | 2 | new; gated on the ledger license column | new |
| H13 | `guides/website/README.md` no longer says "six platform marks" once the rail becomes five | 2 | documentation sync, not a test; the sentence sits in the keyboard/interaction section | supersede |

### 1.2 Foundations -- the eight accepted scenes, in order

The accepted order replaces the shipped v4.4.0 order. Both are eight scenes, so `test_foundations_phase3_has_eight_title_subtitle_scenes` keeps its count assertion and changes only its heading tuple.

| Position | Accepted heading | Shipped v4.4.0 heading at this position | Owning phase |
|---:|---|---|---|
| 1 | Tokens Definition | What Is a Model | 3 |
| 2 | Prompt Engineering | What Are Tokens | 3 |
| 3 | Context Engineering | What Is Prompt Engineering | 3 |
| 4 | Models | What Is an Agent Platform | 4 |
| 5 | Agentic Platform | Chatbot or Agentic Platform? | 4 |
| 6 | Chatbot vs. Agentic Platform | What Is Context | 4 |
| 7 | Harnesses | What Is a Harness | 4 |
| 8 | Nexus-Hub Harness | What Changes in Practice | 4 |

| # | Requirement | Owning phase | Target assertion | State |
|---|---|---|---|---|
| F1 | Exactly eight `fx-scene` blocks, each with one `fx-title` and one `fx-subtitle` | 3 and 4 | `test_foundations_phase3_has_eight_title_subtitle_scenes` (count part unchanged) | covered |
| F2 | The eight headings are the accepted professional headings above, in order | 3 and 4 | heading tuple inside the same test; order becomes positional, not membership | supersede |
| F3 | No `What Is ...` heading survives | 4 | negative check added when the last old heading is replaced | supersede |
| F4 | The page is compact: excessive unused vertical space is removed | 3 | new scene-height budget in `test_phase6_verification_sweep.py` | new |
| F5 | Models and Agentic Platform share one visual grammar | 4 | new `test_models_and_agentic_platform_share_visual_grammar` | new |
| F6 | Any reasoning animation is labelled an abstract work-cycle illustration, never a chain-of-thought transcript | 4 | new copy assertion; extends the existing "generic and may invent missing details" guard | new |
| F7 | Teaching copy stays broadly applicable: the requested `codebase` example is permitted, and broad non-coding context examples remain required | 3 | `test_foundations_is_project_generic` | supersede |
| F8 | Diagram process relationships are visually obvious (direction and ordering legible) | 4 | visual-defect detector on Foundations at every matrix width | new |
| F9 | Terminology is consistent across scenes | 3 and 4 | new cross-scene vocabulary consistency assertion | new |

**F7 is the one guard that becomes more permissive, so it is spelled out.** `test_foundations_is_project_generic` currently forbids `repo`, `repository`, `terminal`, `git`, and `codebase` anywhere in Foundations teaching copy. Phase 3 narrows it: `codebase` becomes permitted because the accepted Context Engineering copy uses it as one concrete example, while the test must still positively require at least one broad non-coding context example so the scene does not silently become code-only. Removing the term from the forbidden tuple without adding that positive requirement would satisfy the letter of the change and lose its purpose.

### 1.3 Arcade shooter (replaces the Asteroids scenario)

| # | Requirement | Owning phase | Target assertion | State |
|---|---|---|---|---|
| G1 | A portrait or square playfield begins behind a real `Click to start` control | 5 | new `test_arcade_requires_explicit_start` | new |
| G2 | The player moves left and right and fires | 5 | new deterministic engine test | new |
| G3 | Enemies and enemy shots descend | 5 | new | new |
| G4 | Asteroids fall at seeded speeds (deterministic given the seed) | 5 | new; the same seed must reproduce the same frame sequence | new |
| G5 | Enemy projectiles consume three lives total | 5 | new | new |
| G6 | Any asteroid collision destroys the player immediately | 5 | new | new |
| G7 | Seeded bug: the FIRST enemy projectile destroys the player outright | 5 | new; the bug must be observable, not merely described | new |
| G8 | `/implement` fixes damage to consume exactly one life | 6 | new | new |
| G9 | The follow-on feature enabled after `/compare` adds up-and-down movement | 6 | new | new |
| G10 | The eight existing command IDs are preserved and no ninth scene is added | 6 | extend the existing Training scene-count assertions | covered |
| G11 | Every prior Asteroids-specific assertion is retired with its scenario | 5 | `test_asteroids_game.py` is replaced, not deleted piecemeal | supersede |

### 1.4 Training workspace and fullscreen

| # | Requirement | Owning phase | Target assertion | State |
|---|---|---|---|---|
| T1 | Panels never overlap in or out of fullscreen | 6 | extends the v4.4.0 `BG-2` rectangle-separation checks | covered |
| T2 | One viewport does not carry too much material | 6 | new per-region height budget | new |
| T3 | Terminal, explorer, game, and Outline stay synchronized | 6 | new | new |
| T4 | Focus stays inside the presentation dialog and returns to its invoker | 6 | v4.4.0 `BG-3` assertions | covered |
| T5 | An in-dialog exit control remains present | 6 | v4.4.0 `BG-5` assertions | covered |
| T6 | Leaving Training by hash routing exits presentation and restores inert state | 6 | v4.4.0 `BG-4` assertions | covered |
| T7 | Numeric scene navigation rejects non-integer and out-of-range values | 6 | v4.4.0 `BG-1` assertions | covered |

### 1.5 Delivery, accessibility, themes, and the viewport matrix

| # | Requirement | Owning phase | Target assertion | State |
|---|---|---|---|---|
| D1 | One self-contained offline HTML file; no server, build step, CDN, remote font, or runtime network call | all | existing offline / no-remote assertions in `test_nexus_hub_guide.py` | covered |
| D2 | The canonical HTML stays strictly below 500,000 bytes | all | `SIZE_BUDGET_BYTES = 500_000` in `test_nexus_hub_guide.py` | covered |
| D3 | The Phase 1 artifact is below 400,000 bytes | 1 | this phase; see the byte ledger in section 3 | met |
| D4 | Inline SVG carries no script, event handler, `foreignObject`, external `href`, or CSS import | 1 and 2 | new sanitization assertion over every inline mark | new |
| D5 | WCAG AA contrast holds in both themes | 2, 3, 4, 6 | `test_phase6_verification_sweep.py` | covered |
| D6 | Reduced motion disables animation everywhere | 2 to 6 | existing reduced-motion sweep, extended per phase | covered |
| D7 | Render checks cover 320, 420, 720, 721, 900, and 1440 px | 2 | `WIDTHS = (320, 420, 900, 1440)` in `test_phase6_verification_sweep.py` | supersede |
| D8 | The Training height matrix is exercised | 6 | existing 1920x1080 / 1440x900 / 1024x768 / 900x900 set | covered |
| D9 | Render evidence never overwrites another label output directory | 1 | `test_render_guide_tool.py` label-isolation assertions | covered |

**D7 is a widening, and the 720/721 pair is deliberate.** `WIDTHS` is currently `(320, 420, 900, 1440)`. Phase 2 must widen it to `(320, 420, 720, 721, 900, 1440)`. The adjacent 720 and 721 values exist to straddle a layout breakpoint so an off-by-one boundary error is caught on the pixel where it happens rather than being averaged away between 420 and 900.

## 2. Superseded-assertion register

Every row below is currently GREEN and must stay green until its owning phase lands the replacement in the same commit that changes the behavior. This is the register the Phase 1 exit checklist refers to when it says no assertion was weakened.

| Assertion | File | Current expectation | Becomes | Owning phase |
|---|---|---|---|---|
| `test_home_lists_six_platforms_without_invented_marks` | `test_nexus_hub_guide.py:578` | exactly 6 rail items in the order Claude, ChatGPT, Gemini, Cursor, GitHub Copilot, OpenCode; `official = {Claude, Cursor, OpenCode}` get `platform-mark` and the rest get `platform-item--text`; asserts the OpenCode instruction-file note is present | exactly 5 items in the order Claude, ChatGPT, Gemini, Cursor, GitHub Copilot; ALL five carry approved inline geometry hash-matched to the ledger; the OpenCode note must be ABSENT | 2 |
| `test_foundations_phase3_has_eight_title_subtitle_scenes` | `test_nexus_hub_guide.py:763` | eight scenes and the eight `What Is ...` headings as a membership check | eight scenes and the eight accepted headings as an ORDERED check | 3 (scenes 1-3), 4 (scenes 4-8) |
| `test_foundations_is_project_generic` | `test_nexus_hub_guide.py:1032` | forbids `repo`, `repository`, `terminal`, `git`, `codebase` | forbids `repo`, `repository`, `terminal`, `git`; permits `codebase`; ADDS a positive requirement for at least one broad non-coding context example | 3 |
| `WIDTHS` | `test_phase6_verification_sweep.py:14` | `(320, 420, 900, 1440)` | `(320, 420, 720, 721, 900, 1440)` | 2 |
| Asteroids scenario suite | `test_asteroids_game.py` | wrap-boundary collision scenario, seeded wrap bug, splitting feature | arcade-shooter scenario: descending enemies, falling asteroids, three lives, seeded first-projectile-kills bug, vertical-movement feature | 5 |
| `test_home_identity_is_centered_nonwrapping_and_observer_gated` | `test_nexus_hub_guide.py` | asserts the literal hero markup `<h1 class="hero-wordmark">Nexus-Hub</h1>` and reads `flex-wrap: nowrap` off `.hero-lockup` | asserts the two-span `Nexus Hub` title inside `.hero-lockup-float`, and reads `flex-wrap: nowrap` off the new inner wrapper | 2 (ADDED during Phase 2; missed by the Phase 1 register) |
| `test_foundations_phase3_diagrams_animate_with_observer_and_static_fallback` | `test_nexus_hub_guide.py` | asserts the literal selector string `document.querySelectorAll(".fx-scene")` | asserts `document.querySelectorAll(".fx-scene, .hero-lockup")`, since the hero float joins the same liveness observer | 2 (ADDED during Phase 2; missed by the Phase 1 register) |

A phase that changes one of these behaviors without updating its register row has left the suite asserting history. A phase that updates the row without changing the assertion has weakened coverage. Both are Phase 7 findings.

**The register was incomplete when Phase 1 closed, and the last two rows record that.** Phase 2 broke two assertions this register had not anticipated: one pinned the exact hero markup string, and one pinned the exact text of a `querySelectorAll` selector. Both were found by running the suite rather than by reading the register, which is the failure mode the register exists to prevent. The rows were added when the breakage surfaced, and the lesson generalizes: an assertion that pins a literal implementation string is invisible to a requirements-level register, so a phase that edits shared markup or shared script should grep the suite for the strings it is about to change before assuming the register is complete.

## 3. Byte ledger

The single-file budget is the live risk for this plan: the shipped v4.4.0 page had roughly 8 KB of headroom against a strict 500,000-byte ceiling, and this plan adds five marks, output media, and a game.

### 3.1 Measured result of sub-task 1.2

| Measurement | Bytes |
|---|---:|
| Canonical HTML before (git blob, LF) | 487,681 |
| `#nexus-mark` symbol before | 220,358 |
| `#nexus-mark` symbol after | 2,118 |
| Symbol saving | **-218,240** |
| Canonical HTML after | **269,441** |
| Phase 1 gate (must be below) | 400,000 |
| Release ceiling (UNCHANGED) | 500,000 |
| Headroom against the ceiling | 230,559 |

The old symbol was a single 220,140-character base64 PNG (165,104 decoded bytes) wrapped in an `<image>` element. The replacement is true vector geometry measured from that raster: four corner nodes at (106,97), (410,97), (106,395), (410,395) with r=34; two 26-unit round-capped diagonal strokes; a white hub at (258,246) with r=30; two large gradient triangles with vertical bases at x=89 and x=425 spanning y=144 to 356, with apexes at (196,250) and (320,250); and two narrow gradient wedges at (164,102)-(285,179)-(270,196) and its 180-degree rotation about (258,250). A single `feGaussianBlur` glow layer reproduces the luminous halo of the original. Every coordinate was derived by pixel measurement of the decoded original rather than estimated, and the result was confirmed by browser render in both themes.

`assets/nexus-hub-primary_no-background.svg` was explicitly NOT reused: it is 1,012,475 bytes containing one base64 `<image>` and zero `<path>` elements, so it is an oversized SVG-wrapped raster, exactly as the plan cautioned.

### 3.2 Per-phase allocation

The recovered space is allocated rather than left as slack, so a later phase cannot quietly consume all of it.

| Phase | Purpose | Allocation | Running total |
|---|---|---:|---:|
| 1 | compact Nexus mark (spent) | 2,118 | 269,441 |
| 2 | five sanitized platform marks plus lockup and pill CSS | 30,000 | 299,441 |
| 3 | Foundations scenes 1 to 3 rebuild | 25,000 | 324,441 |
| 4 | Foundations scenes 4 to 8, shared visual grammar, output-media examples | 60,000 | 384,441 |
| 5 | deterministic arcade-shooter engine plus procedural art | 55,000 | 439,441 |
| 6 | Training workspace, fullscreen, integrated loop | 30,000 | 469,441 |
| 7 | closeout, no net growth expected | 0 | 469,441 |
| | **reserve against the 500,000 ceiling** | | **30,559** |

A phase that needs more than its allocation must take it from the reserve and record that here, not raise the ceiling. The ceiling is not raised in this plan.

### 3.3 Measured actuals

The projections above were budget ceilings, not forecasts; the measured spend runs far
under them because each rebuilt scene DELETED more bespoke SVG than its replacement added.

| Phase | Projected running total | Measured page bytes |
|---|---:|---:|
| 1 | 269,441 | 269,441 |
| 2 | 299,441 | 281,301 |
| 3 | 324,441 | 275,316 |
| 4 (media embedded) | 384,441 | 280,351 |
| 5 (engine replaced) | 439,441 | **284,278** |


## 4. Verification performed in this phase

```text
python -m pytest tests/guides/test_nexus_hub_guide.py -q
92 passed, 1 skipped in 2.83s
```

Browser render of Home in both themes at 1440 px confirmed the compact mark is visible and geometrically equivalent in the header brand and the hero lockup. In light theme the mark sits on the existing dark chip supplied by `html[data-theme="light"] .hero-mark`, so no theme-variant fill is required.

## 5. Open Phase 1 items

- Sub-task 1.3 requires explicit user approval of five platform-mark hashes before Phase 2 may start. Tracked in [asset-provenance.md](asset-provenance.md).
- Output-media candidates for Phase 4 are recorded in the same ledger; an unresolved media item blocks Phase 4 only, not Phase 2.
