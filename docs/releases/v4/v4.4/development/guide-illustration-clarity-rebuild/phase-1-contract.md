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
| M1 | No work-cycle ring anywhere; no scene has an empty column | NEW, Phase 5 | 5 |
| M2 | The video output plays with no gesture; models from three or more providers are named | NEW, Phase 5 | 5 |
| P1 | Agentic Platforms is plural and names four platforms with ledger-approved marks | NEW, Phase 6 | 6 |
| X1 | Chatbot versus agentic platforms is one illustration of can-do against does | NEW, Phase 7 | 7 |
| H1 | ONE harness scene, animated as one journey | NEW, Phase 8 | 8 |
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

## 4. Byte ledger

| Phase | Change | Bytes | Running total |
|---|---|---:|---:|
| start | v4.4.2 final | | 345,623 |
| 1 | two size tokens, NexusFit, table-header grade, second-person sweep | +4,282 | 349,905 |
| 2 | guardrails figure rebuilt in HTML, SVG removed, table column shares | +2,584 | 352,489 |
| 3 | loop fills the column, larger box type, CSS triangles | +966 | 353,455 |
| 4 | two-line legend rows, illustrated material grid, legend-free budget meters | +1985 | 355,440 |

Headroom at Phase 4 close: 144,560 under the ceiling.
