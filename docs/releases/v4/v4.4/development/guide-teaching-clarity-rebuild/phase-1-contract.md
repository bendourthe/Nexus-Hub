# v4.4.4 Phase 1 Contract -- Gates, Register, and Byte Ledger

**Plan**: [v4.4.4-guide-teaching-clarity-rebuild.md](../../plans/v4.4.4-guide-teaching-clarity-rebuild.md)
**Base**: the v4.4.3 closeout at `bcfa3413`
**Guide at start**: 370,253 bytes
**Ceiling**: 500,000. Allocation for this plan: 40,000, and the plan expects to CLOSE at or below its
start, because retiring the audio output and merging two Foundations scenes both return bytes.

## 1. Gates

| # | Gate | Test | Phase |
|---|---|---|---|
| E1 | Guardrails segment renamed, both ring headers and the chips centred, both subtexts rewritten | `test_v444_phase12_home.py::test_the_guardrails_segment_is_renamed_and_centred` | 1 |
| E2a | Command segment and both column headers renamed, stacked labels following | `test_the_command_segment_is_renamed` | 2 |
| E2b | Both benefits present: one install across four platforms with a mid-task switch, and commands built on the generic ones | `test_the_segment_carries_both_benefits` | 2 |
| E3 | Foundations reads scene name as title, descriptive phrase as subtitle | `test_v442_phase3_foundations.py::test_scene_titles_come_before_their_subtitles` | 3 |
| E4 | Prompt Engineering: vague prompt beside its flaws, full-width engineered prompt below | `test_v444_phase4_prompts.py` (4 tests) | 4 |
| E5 | Context Engineering: copy full width, prompt left and material right, bad versus good with cost named | `test_v443_phase4_context.py` (`..._grid_of_examples`, `test_dumping_everything_names_its_cost`) | 5 |
| E6 | Models: one model per provider without numbers, next-token, base versus reasoning, three modality tiers | NEW, Phase 6 | 6 |
| E7 | ONE Agentic Platforms scene, chatbot merged in | NEW, Phase 7 | 7 |
| E8 | Harnesses: animated journey carrying the brain, degree, and experience analogy | NEW, Phase 8 | 8 |
| E9 | Matrix green, byte ledger closed | Phase 9 | 9 |

## 2. Superseded-assertion register

| File | Assertion | Literal it pinned | Superseded by | Status |
|---|---|---|---|---|
| `test_v441_phase2_home.py` | `test_home_sections_render_in_the_agreed_order` | `Guardrails and safety` | E1 | DONE: `Adds an extra layer of security` |
| `test_v441_phase2_home.py` | same test | `Familiar commands, leveled up` | E2a | DONE: `Install once, work anywhere` |
| `test_v442_phase3_foundations.py` | `test_scene_subtitles_are_eyebrows_above_their_titles` | the phrase is an uppercase eyebrow ABOVE the scene name, sharing the Home label's base size and tracking ratio | E3: the review calls that pair inverted | DONE: rewritten as `test_scene_titles_come_before_their_subtitles`, which asserts the h2 first in DOM and on screen, a smaller subtitle, and `text-transform: none`. Home is unchanged and still reads label-above-title. |
| `test_v443_phase1_headings.py` | the measured selector included `.page.active .fx-subtitle` | E3: a subtitle sentence should wrap like prose, not shrink to one line | DONE: the selector measures titles and Home labels only; the docstring records why |
| `test_nexus_hub_guide.py` | `test_foundations_prompt_engineering_uses_one_non_coding_job` | `Precise`, `class="fx-state fx-state--weak"`, `class="fx-state fx-state--strong"` | E4: the three-column lane grid is gone | DONE: reads `Engineered` and the new carriers, and now also requires each flaw to be NAMED rather than summarised in one sentence |
| `test_v443_phase4_context.py` | `test_attachable_material_is_a_two_by_two_illustrated_grid` | every material cell carries a DRAWING | E5: the review asked for made-up examples instead | DONE: rewritten as `..._grid_of_examples`; the grid and the four kinds are unchanged, each cell now carries a monospaced example, and drawings in that grid are asserted ABSENT so the two cannot both creep in |
| `test_nexus_hub_guide.py` | `test_foundations_context_makes_budget_competition_and_full_behavior_visible` | `class="fx-mat"` and `<span class="fx-mat-name">` | E5 | DONE: reads `.cx-mat` and `.cx-kind`; the four kind names and the without-then-with order are unchanged requirements |

## 3. One rule narrowed, with its reasoning

`test_restored_sections_are_at_most_two_thirds_of_their_v412_word_count` capped each restored Home
section at two thirds of its v4.1.2 word count, so a restoration could not reintroduce v4.1.2's
length. v4.4.4 adds content to one of those sections that v4.1.2 never contained: the portability
figure the review asked for. Measuring new content against a baseline that never included it
measures the wrong thing.

The rule is narrowed rather than raised. Blocks marked `data-v444-new` are excluded from the
restored-prose count, AND the new block carries its own explicit cap (20 to 120 words). Both halves
stay honest: restored prose still cannot creep back toward its old length, and the new figure cannot
grow without a number on it. The restored prose in that section measures 262 words against its 266
ceiling after the lead was trimmed to fit, rather than the ceiling being moved.

## 4. One deviation from the plan lifecycle, stated

Phases 1 and 2 are recorded in ONE commit. Both are Home wording and illustration work, and the
Phase 1 edits were already in the working tree when Phase 2 began, so splitting the diff afterwards
would have meant reconstructing a commit boundary rather than observing one. The phase histories
describe each separately.

## 5. Byte ledger

| Phase | Change | Bytes | Running total |
|---|---|---:|---:|
| start | v4.4.3 final | | 370,253 |
| 1 + 2 | guardrails wording and centring, portability figure, column renames | +4375 | 374,628 |
