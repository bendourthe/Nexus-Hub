# v4.4.3 Phase 1 Contract -- Gates, Register, and Byte Ledger

**Plan**: [v4.4.3-guide-illustration-clarity-rebuild.md](../../plans/v4.4.3-guide-illustration-clarity-rebuild.md)
**Base**: `develop` at `a376c1ae`
**Guide at start**: 345,623 bytes
**Ceiling**: 500,000 bytes. Allocation for this plan: 60,000.

## 1. Gates

| # | Gate | Test | Phase |
|---|---|---|---|
| T1 | Label at three times 11px and title at half the v4.4.2 size, one token each | `test_v443_phase1_headings.py::test_label_is_tripled_and_title_is_halved` | 1 |
| T2 | No heading wraps at 720px and wider | `test_no_heading_wraps_from_720_upward` (3 widths) | 1 |
| T3 | No heading's glyph run spills past its container at any declared width, and none renders below the 15px floor | `test_no_heading_spills_past_its_container` (5 widths) | 1 |
| T4 | Migration table headers carry the comparison-label grade, with per-column colour | `test_migration_table_headers_carry_the_comparison_grade` | 1 |
| T5 | The static document never addresses the reader | `test_static_document_never_addresses_the_reader` | 1 |
| G1 | Every guardrails label sits inside its own box; the blocking hook is named per attempt | `test_v443_phase2_guardrails.py` (6 tests) | 2 |
| L1 | The command loop fills the content column with triangular heads | `test_v443_phase3_loop.py` (5 tests) | 3 |
| C1 | Request and context render as swatch-plus-label over description | `test_v443_phase4_context.py::test_every_legend_row_is_swatch_and_label_over_description` | 4 |
| C2 | Attachable material is one 2x2 illustrated grid; the Context scene adopts it in Phase 4 and the Models and Platforms scenes reuse it in their own rebuilds | `test_v443_phase4_context.py::test_attachable_material_is_a_two_by_two_illustrated_grid` | 4 |
| M1 | No work-cycle ring anywhere; no scene has an empty column | `test_v443_phase5_models.py::test_no_work_cycle_ring_survives_anywhere_in_a_scene` | 5 |
| M2 | The video output plays with no gesture; models from three or more providers are named | `test_v443_phase5_models.py` (`test_the_video_output_plays_without_being_asked`, `test_released_models_are_named_from_three_providers`) | 5 |
| P1 | Agentic Platforms is plural and names four platforms with ledger-approved marks | `test_v443_phase6_platforms.py` (5 tests) | 6 |
| X1 | Chatbot versus agentic platforms is one illustration of can-do against does | `test_v443_phase7_comparison.py` (4 tests) | 7 |
| H1 | ONE harness scene, animated as one journey | `test_v443_phase8_harness.py` (4 tests) | 8 |
| V1 | Declared matrix green, byte ledger closed | Phase 9 | 9 |

## 2. Superseded-assertion register

Rule inherited from v4.4.1 (`WN-2`) and v4.4.2: an assertion pinning a LITERAL implementation string
(a pixel value, a label, a copy sentence, a class) is listed here the moment the change supersedes
it, with what replaced it. A test updated without a row here is how a silent loosening enters.

| File | Assertion | Literal it pinned | Superseded by | Status |
|---|---|---|---|---|
| `test_v442_phase1_foundation.py` | `test_section_titles_share_one_scale_and_never_overflow` | `64 <= sizes[0] <= 67` (the 2.4 token) | T1: token 1.2, base 32.6 | DONE: bound now `32..34` on `data-fit-base` |
| `test_v442_phase1_foundation.py` | same test | `len(set(sizes)) == 1` on RENDERED px | T2, T3: rendered size is per-container by design | DONE: equality moved to the stylesheet base, plus floor and base-ceiling checks on rendered px |
| `test_v442_phase3_foundations.py` | `test_scene_subtitles_are_eyebrows_above_their_titles` | `cs.fontSize === eyebrow.fontSize`, `cs.letterSpacing === eyebrow.letterSpacing` | T2, T3 | DONE: base equality plus a tracking-to-size ratio, so the primitive is still asserted |
| `test_nexus_hub_guide.py` | `test_home_hero_restores_the_v412_subtitle_and_lead` | `Upgrade your agentic AI platforms ...` | T5 | DONE: `Upgrade any agentic AI platform ...` |
| `test_v441_phase2_home.py` | `test_home_hero_statement_is_centred_and_exact` | same hero sentence | T5 | DONE |
| `test_v441_phase2_home.py` | `test_home_sections_render_in_the_agreed_order` | four heading strings carrying `you` or `your` | T5 | DONE |
| `test_nexus_hub_guide.py` | `test_foundations_model_lifecycle_is_chronological_and_responsive` | `happens long before your request` | T5 | DONE: `happens long before any request` |
| `test_nexus_hub_guide.py` | `test_foundations_chatbot_and_agent_share_a_request_but_not_the_handoff` | `you apply and check`, `check result` | T5 | DONE: `every step is applied and checked`, `checked result` |
| `test_nexus_hub_guide.py` | `test_foundations_context_makes_budget_competition_and_full_behavior_visible` | `class="fx-ctx-kinds"`, `<span class="fx-ctx-kind">`, `fx-budget--noisy/--focused` | C2 and the budget rebuild | DONE: reads `.fx-mat`, `.fx-mat-name`, and `fx-spend-tag--bad/--good`; the four kind names and the without-then-with order are unchanged requirements |
| `test_nexus_hub_guide.py` | `test_foundations_comparisons_show_both_states_without_a_toggle` | `fx-budget--noisy/--focused` | same | DONE |
| `test_nexus_hub_guide.py` | `test_foundations_orders_unaided_state_first` | `fx-budget--noisy/--focused` | same | DONE |
| `test_nexus_hub_guide.py` | `test_foundations_phase3_diagrams_animate_with_observer_and_static_fallback` | `data-grammar="work-cycle"` count 2, the rule `.js .fx-scene.live .fx-cycle svg`, and `.fx-cycle svg` in the reduced-motion block | M1: the ring is gone from both scenes | DONE: counts `data-grammar="one-pass"`, asserts the ring cannot return, and points the liveness and reduced-motion checks at the hero lockup, which is now the only continuous motion |
| `test_nexus_hub_guide.py` | `test_foundations_animations_have_reduced_motion_fallback` | `.fx-cycle svg` in the primitive list | M1 | DONE: `.hero-lockup-float` |
| `test_v441_phase4_foundations.py` | `test_embedded_gif_and_poster_match_the_approved_assets` | `src` must equal the poster, and a separate `data-motion-src` must hold the GIF | M2: the animation is the element's own src | DONE: `src` is the GIF, `data-poster-src` is the still, both still hash to the ledger, and `data-motion-src` must be absent so the GIF appears once |
| `test_v441_phase4_foundations.py` | `test_moving_image_plays_only_on_request` | the whole press-to-play behaviour | M2 | DONE: rewritten as `test_moving_image_plays_unaided_and_stills_under_reduced_motion`; the accessibility half of the old rule is kept and asserted |
| `test_v441_phase4_foundations.py` | `test_work_cycle_is_static_and_complete_under_reduced_motion` | the ring's spin and its text label | M1 | DONE: rewritten as `test_inside_the_model_is_complete_under_reduced_motion`, which asserts all three steps are readable without motion and the honesty caveat survives |
| `test_v441_phase4_foundations.py` | `test_models_and_agentic_platform_share_visual_grammar` | `data-grammar="work-cycle"` count and its position in the flow order | M1 | DONE: `one-pass` in both places; the byte-identical entry rule is unchanged and the Platform entry moved with the Models entry to keep it true |
| `test_v442_phase4_media.py` | `test_models_and_agentic_still_share_the_entry_and_cycle_bytes` | the `<figure class="fx-cycle">` regex and the count of 2 | M1 | DONE: renamed to `..._entry_and_inside_bytes`, counts `one-pass`, and asserts the ring grammar is retired |
| `test_nexus_hub_guide.py` | `test_foundations_phase3_has_eight_title_subtitle_scenes` | the scene title `Agentic Platform` | P1: the scene is plural | DONE: `Agentic Platforms`. Phases 7 and 8 change two more entries in the same list, each with its own row. |
| `test_nexus_hub_guide.py` | same test | the scene title `Chatbot vs. Agentic Platform` | X1: the comparison follows the plural | DONE: `Chatbot vs. Agentic Platforms`. The substring assertion in the chatbot handoff test still holds unchanged, and every copy assertion in it was kept satisfied by the rebuild rather than edited. |
| `test_nexus_hub_guide.py` | same test | eight scenes, and the title `Nexus Hub Harness` | H1: the two harness scenes are one | DONE: seven scenes, the entry removed |
| `test_nexus_hub_guide.py` | `test_foundations_harness_layers_are_honest_and_repository_anchored` | the split between `fx-harness` (platform) and `fx-practice` (Nexus Hub) | H1 | DONE: one scene holds all three layers; both port sets are now asserted, and every honesty phrase is still required |
| `test_nexus_hub_guide.py` | `test_foundations_comparisons_show_both_states_without_a_toggle`, `test_foundations_orders_unaided_state_first` | `_foundation_scene(..., "fx-practice")` | H1 | DONE: both read the merged scene; the without-then-with order is unchanged |
| `test_v442_phase4_media.py` | `test_harness_diagram_is_layered_and_choreographed` | `#fx-hstack-nexus`, `.h-port`, `.h-portg`, `.h-out`, `.h-ghost`, the static second instance, `total == 7` | H1: one HTML figure | DONE: reads the merged figure, all nine ports, `total == 6`, and an end state with every stop and the output lit. The two-instance rule went with the merge and is recorded here rather than silently dropped. |
| `test_v442_phase4_media.py` | `test_harness_choreography_end_state_under_reduced_motion` | `lit >= 15` over SVG port groups | H1 | DONE: `lit == 6` over the journey stops |
| `test_v442_phase4_media.py` | `test_harness_svg_text_stays_inside_its_viewbox` | `.fx-hstack svg text` | H1 | DONE: renamed to `test_harness_text_stays_inside_its_own_box` and rewritten over the HTML figure. The old form would have passed VACUOUSLY, since the selector no longer matches anything. |
| `test_v442_phase1_foundation.py` | `test_section_titles_share_one_scale_and_never_overflow` | `len(sizes) == 24` | H1: one scene fewer | DONE: 23 |
| `test_v442_phase3_foundations.py` | `test_scene_subtitles_are_eyebrows_above_their_titles` | `len(rows) == 8` | H1 | DONE: 7 |
| `test_v442_phase3_foundations.py` | `test_no_scene_has_an_empty_column_at_1440` | `len(scenes) == 8` | H1 | DONE: 7 |
| `test_v441_phase2_home.py` | `test_guardrails_section_names_only_shipped_registered_hooks` | `.g-port`, `.g-blocked`, and the `blocked by ` prefix | G1: the figure has no SVG | DONE: reads `.gf-hooks li` and the `<b>` hook name in each stop cell; the rule (only shipped, registered hooks named) is unchanged |
| `test_v441_phase2_home.py` | `test_guardrails_choreography_reaches_a_fully_blocked_end_state` | `total == 5`, `.g-block` count | G1: three attempts, not five chips | DONE: `total == 3`, stop count read from `.gf-out--stop`; the rule (ends fully blocked) is unchanged |

Not superseded, and deliberately not touched: `test_restored_sections_are_at_most_two_thirds_of_their_v412_word_count`.
The sweep pushed the How-it-works section to 118 words against a 116 ceiling, so the COPY was
trimmed back to 115. Raising a ceiling to accommodate a rewrite is the failure this register exists
to make visible.

## 3. Stated deviation from the Definition of Done

`D2` asked for no title wrapping at 320, 420, 720, 900, and 1440. That cannot hold together with a
legible type size, and the arithmetic is the argument: at 320px the content column is about 288px,
while the longest Home title (`Three things make this more than a prompt library`) needs roughly
1,100px on one line at the 32.6px base. Fitting it to one line costs about 8px of type. The rule
shipped is therefore:

- **720px and wider**: one line always, no exceptions (`T2`).
- **Below 720px**: the fit pass shrinks to the 15px floor and then hands wrapping back, so the
  heading wraps rather than shrinking into illegibility or spilling out of the column (`T3`).
- **Every width**: nothing spills past its container, which was the actual defect in the review.

## 3b. One rule violation committed and repaired

Phase 2 shipped `max-width: 460px` on the guardrails outer ring, which the v4.2.3 responsive rule
forbids on a text-bearing element, and `test_no_hardcoded_text_width_caps_remain` caught it during
Phase 4. The cause was procedural: Phase 2 ran its own module plus the two it touched, not the broad
`test_nexus_hub_guide.py`. Repaired in Phase 4 by removing the cap; the figure column is the only
width constraint. From Phase 4 onward every phase runs the broad module before committing.

## 3c. One pre-existing accessibility gap, found and closed

Removing the ring left the hero lockup as the guide's only continuous animation, and it turned out to
have no reduced-motion state at all: a seven-second infinite float kept running for a reader who had
asked for less motion. The old reduced-motion assertion covered the ring and not the lockup, so
nothing caught it. One rule added, and the assertion now points at the animation that is actually
still there.

## 3d. One regression this plan shipped and Phase 8 caught

Phase 4 removed the `fx-budget`, `fx-bar`, `fx-legend`, and `fx-key` rules after counting four
usages of `fx-budget` and reading that as "the two boxes I am replacing". Two of the four were in
the harness trail comparison, which then rendered with no border, no background, and no two-column
layout for four commits. No test noticed, because no test tied markup to style.

The cause is precise and worth keeping: **a usage count cannot tell you where a class is used.**
Phase 8 rebuilt that block with its own rules and added
`test_v443_phase8_harness.py::test_every_class_used_in_foundations_has_a_style_rule`, which ties
every class in the Foundations markup to a declaration in the stylesheet. It found one further gap
immediately, a Phase 7 wrapper with no rule, which now has one.

A second, smaller instance of the same oversight: the narrow-width media query still named
`.fx-ctx-budgets` after its rule was deleted. Removed in Phase 8 with the markup that used it.

## 4. Byte ledger

| Phase | Change | Bytes | Running total |
|---|---|---:|---:|
| start | v4.4.2 final |  | 345,623 |
| 1 | two size tokens, NexusFit, table-header grade, second-person sweep | +4,282 | 349,905 |
| 2 | guardrails figure rebuilt in HTML, its SVG retired, table column shares | +2,584 | 352,489 |
| 3 | loop fills the column, larger box type, CSS triangles | +966 | 353,455 |
| 4 | two-line legend rows, illustrated material grid, legend-free budget meters | +1,985 | 355,440 |
| 5 | ring retired from both scenes, one-pass block, model names, autoplaying video, thicker connectors | +3,920 | 359,360 |
| 6 | plural title, four platform chips with reused approved marks, shorter copy, five-stage choreography | +13,989 | 373,349 |
| 7 | chatbot comparison rebuilt as a two-zone reach illustration | +4,365 | 377,714 |
| 8 | two harness scenes merged into one HTML figure, two SVG figures retired | -7,508 | 370,224 |

The file is SMALLER than at Phase 7 close: replacing two SVG figures with nested elements
returned more bytes than the four inlined platform marks cost.

Headroom at Phase 8 close: 129,776 under the ceiling, and 35,399 under the plan's own 405,623 target.
