# v4.4.2 Phase 1 Contract - Requirement Matrix, Superseded Assertions, Byte Ledger

**Plan**: [v4.4.2-guide-production-ready-rebuild.md](../../plans/v4.4.2-guide-production-ready-rebuild.md)
**Branch**: `feat/v4.4.2-guide-production-ready-rebuild` (cut from `develop` at `46f18986`, the v4.4.1 merge)
**Frozen**: 2026-09-02

This file is the contract every later phase edits tests against. Section 1 maps each Definition-of-Done clause to the test that proves it. Section 2 lists every existing assertion this plan will legitimately supersede, so a test is never edited merely to make a number match. Section 3 is the byte ledger.

## 1. Requirement-to-test matrix

| ID | Definition-of-Done clause (abridged) | Proving test | Phase |
|---|---|---|---|
| H1 | Hero shows exact title `Nexus Hub`, then the v4.1.2 subtitle and lead, centred, gradient span | `test_v441_phase2_home.py` (extend) | 2 |
| H2 | Credits disclosure absent from the Home flow; licence attribution present in footer on all pages | NEW in `test_v441_phase2_home.py` | 2 |
| H3 | Every section h2 uses `.section-title` at ~3x v4.4.1 size, one token, with eyebrow | `test_v442_phase1_foundation.py::test_section_titles_share_one_scale_and_never_overflow` | 1 |
| H4 | Home section order: hero, Why it matters, Installation, How it works, Guardrails and safety, Raw prompting vs Nexus Hub, Your favorite commands, loop, Learn it | NEW in `test_v441_phase2_home.py` | 2 |
| H5 | Restored sections at most two-thirds of v4.1.2 word count | NEW, fixture `tests/guides/fixtures/v412-home-copy.json` | 2 |
| H6 | Guardrails section names only shipped, registered hooks; claims worded as enforcement | NEW in `test_v441_phase2_home.py` | 2 |
| H7 | Merged comparison labels at 2x v4.4.1 size | NEW in `test_v441_phase2_home.py` | 2 |
| M1 | Every count stamped from the catalog; `--check` gate in `make validate` | `test_guide_counts.py` (6 tests) | 1 |
| M2 | Zero visible `Nexus-Hub`; allowlist enumerated | `test_v442_phase1_foundation.py::test_visible_text_says_nexus_hub_without_the_hyphen` | 1 |
| M3 | One shared motion sequencer with offscreen, hidden-tab, and reduced-motion contracts | `test_v442_phase1_foundation.py` (5 sequencer tests) | 1 |
| F1 | Foundations opens with centred page title in hero-subtitle style; no page kicker | NEW `test_v442_phase3_foundations.py` | 3 |
| F2 | No scene has an empty column (height ratio <= 1.35) or is single-column | NEW `test_v442_phase3_foundations.py` | 3 |
| F3 | Annotated-prompt primitive: one text, labelled spans, sequenced reveal, all-at-once under reduced motion | NEW `test_v442_phase3_foundations.py` | 3 |
| F4 | Outputs labelled Text, Image, Video, Audio; live waveform while playing, static otherwise | NEW `test_v442_phase4_media.py` | 4 |
| F5 | No connector overlaps a card at six viewports | NEW `test_v442_phase4_media.py` | 4 |
| F6 | Layered model / platform harness / Nexus Hub harness diagram with choreography and static end state | NEW `test_v442_phase4_media.py` | 4 |
| A1 | Space or left click fires; pointer-leave or Escape pauses; Resume resumes | `test_arcade_shooter_game.py` (extend) | 5 |
| A2 | Key guide under fine pointer; touch controls only under coarse pointer | `test_arcade_shooter_game.py` (extend) | 5 |
| A3 | Continuous spawning in every fixture: >= 3 enemy velocity bands, >= 3 asteroid size and speed tiers | `test_arcade_shooter_game.py` (extend) | 5 |
| A4 | Buggy first hit and fixed 3 -> 2 -> 1 -> 0 walk unchanged from seed 20260901 | `test_arcade_shooter_game.py` (existing determinism tests, tick values pinned) | 5 |
| P1 | Fullscreen regions cover >= 88 percent of viewport at four desktop sizes; stage >= 70 percent of height | `test_v441_phase6_workspace.py` (extend) | 6 |
| P2 | No pairwise intersection, no horizontal overflow; Outline overlays without moving regions | `test_v441_phase6_workspace.py` (extend) | 6 |
| P3 | Narrow reflow to one scroll surface preserved; sub-640 fallback | `test_v441_phase6_workspace.py` (extend) | 6 |
| M4 | File <= 500,000 bytes; ledger closed | `test_nexus_hub_guide.py` size test + Section 3 | 7 |
| M5 | Declared browser matrix passes with 0 failures inside ceilings | `tests/guides/tools/browser_matrix.py` + summary JSON | 7 |
| M6 | Human cohort prompts recorded honestly | evidence block, Phase 8 | 8 |

## 2. Superseded-assertion register

Rule (the v4.4.1 `WN-2` lesson): the register lists assertions pinning LITERAL IMPLEMENTATION STRINGS (class names, pixel values, label text, markup shape), not only requirement-level statements, because those are the ones a requirements-level register misses. A test may be edited only if it appears here, and only in the phase named.

| File | Test / line | Literal it pins | Superseded by | Phase | Status |
|---|---|---|---|---|---|
| `test_nexus_hub_guide.py` | `ONBOARDING_STALE` regex, `Nexus-Hub\s+v` alternative | hyphenated product name in a version string | M2 | 1 | DONE: now `Nexus[- ]Hub` |
| `test_nexus_hub_guide.py` | line ~345 `aria-label="Nexus-Hub on GitHub"` | hyphenated aria-label | M2 | 1 | DONE |
| `test_nexus_hub_guide.py` | `test_foundations_phase3_has_eight_title_subtitle_scenes`, expected list `"Nexus-Hub Harness"` | hyphenated scene title | M2 | 1 | DONE |
| `test_nexus_hub_guide.py` | same test, `re.findall(r'<h2 id="[^"]+">...')` | h2 with no attributes beyond id | H3 (`class="section-title"`) | 1 | DONE: `[^>]*` tolerated |
| `test_nexus_hub_guide.py` | `test_onboarding_has_no_hardcoded_catalog_counts` (`ONBOARDING_STALE` on Home text) | any `\d{2,4} skills/hooks/commands/agents` in Home prose | M1: stamped `data-count` markers are the sanctioned form; the test must exempt marker-carried numbers (or assert them equal to the catalog) | 2 | OPEN |
| `test_nexus_hub_guide.py` | `<p class="hero-tagline">` regex (~line 577) | tagline element and text | H1 | 2 | OPEN |
| `test_nexus_hub_guide.py` | `"Nexus-Hub" not in home.split("</h1>")` and heading checks (~561, ~673) | absence assertions | none (still true after rename) | - | KEEP |
| `test_v441_phase2_home.py` | hero tagline / rail / loop assertions | `.hero-tagline` text | H1 | 2 | OPEN |
| `test_v441_phase4_foundations.py` | two-column `fx-scene` grid; matched-emission of Models and Agentic | `.fx-scene` grid-template-columns; `Moving Image` label | F2, F4 | 3, 4 | OPEN |
| `test_nexus_hub_guide.py` | `test_foundations_phase3_has_eight_title_subtitle_scenes`: `fx.count("<svg") >= 7`; `Harnesses` / `Nexus Hub Harness` structure | per-scene SVG presence, separate harness diagrams | F6 (one shared layered diagram) | 4 | OPEN |
| `test_arcade_shooter_game.py` | `nag-controls` / `nag-actions` buttons; `enemy-hit` never spawns; two asteroid speeds | touch buttons, spawn gating, `ASTEROID_SPEEDS` length | A1, A2, A3 | 5 | OPEN |
| `test_v441_phase6_workspace.py` | `.nht-col:first-child` `height: 58%`; REGIONS / PAIRS lists | column sizing, region set | P1, P2 | 6 | OPEN |
| `test_phase6_verification_sweep.py` | contrast matrix (unchanged expectation) | WCAG AA on every visible element | none; it caught `BG-13` in Phase 1 | - | KEEP |

## 3. Byte ledger

Ceiling: strict 500,000 bytes. Every phase records its measured actual against its allocation.

| Phase | Allocation | Measured actual | Running size | Note |
|---|---:|---:|---:|---|
| Start (v4.4.1 merge) | - | - | 292,339 | |
| 1 | +8,000 | +7,708 | 300,047 | sequencer JS + primitives, title-scale token, rename |
| 2 | +36,000 | | | |
| 3 | +22,000 | | | |
| 4 | +38,000 | | | |
| 5 | +14,000 | | | |
| 6 | +12,000 | | | |
| 7 | +4,000 | | | |
| Reserve | 73,661 | | | ceiling minus start minus allocations |

## 4. Phase 1 deviations recorded

- `.section-title` minimum bound is `0.6 x` the scaled floor (2.16 rem at scale 3) rather than the plan's `1.2rem x scale`. At the plan's literal formula the 320 px minimum would be 57.6 px and a single long word overflows the viewport; the 1440 px anchor (81.6 px, exactly 3x v4.4.1's 27.2 px) is unchanged, which is the value the Definition of Done names.
- `BG-13`: the first sequencer demo dimmed the loop pills to opacity .45 and the contrast sweep measured 1.9:1 mid-sequence. Text carriers now use `seq-glow` (accent ring on the active step, no foreground change); `seq-fade` is reserved for shapes and connectors with a .7 floor and a comment saying so.
