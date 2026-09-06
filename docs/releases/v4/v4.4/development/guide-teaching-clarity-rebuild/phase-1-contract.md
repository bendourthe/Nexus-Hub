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
| E6 | Models: one model per provider without numbers, next-token, base versus reasoning, three modality tiers | `test_v444_phase6_models.py` (4 tests) | 6 |
| E7 | ONE Agentic Platforms scene, chatbot merged in | `test_v443_phase7_comparison.py` (4, repointed) + `test_v441_phase4_foundations.py::test_the_agentic_scene_carries_the_comparison_and_the_boundary` | 7 |
| E8 | Harnesses: animated journey carrying the brain, degree, and experience analogy | `test_v443_phase8_harness.py::test_the_flow_carries_the_analogy_and_the_platform_limits` | 8 |
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
| `test_nexus_hub_guide.py` | `test_foundations_model_lifecycle_is_chronological_and_responsive` | four output kinds including `audio`, plus `preload="none"` and `transcript equivalent` | E6: audio left the teaching | DONE: three kinds, and the audio element asserted ABSENT. The two effort qualifiers (`when supported`, `does not promise a fixed number of iterations`) were kept in the copy rather than dropped from the test. |
| `test_v441_phase4_foundations.py` | `test_embedded_audio_matches_the_approved_asset` | the embedded WAV matches the ledger | E6 | DONE: inverted into `test_the_audio_asset_left_the_page_with_its_teaching`, which asserts the WAV, the element, the canvas, and the engine are all absent. A 12 KB payload nothing explains is worse than no payload. |
| `test_v441_phase4_foundations.py` | `test_embedded_image_matches_the_approved_asset` | the wrapper class `fx-out-media` exactly | E6: the image sits in the multimodal tier | DONE: the regex allows a second class; the hash check is unchanged |
| `test_v441_phase4_foundations.py` | `test_inside_the_model_is_complete_under_reduced_motion` | three `.fx-pass-step` elements | E6: the block is a token strip plus two lanes | DONE: asserts the chips and nodes are all readable without motion, and the caveat survives |
| `test_v442_phase4_media.py` | `test_output_labels_and_waveform_states`, `test_waveform_is_static_under_reduced_motion` | four output labels and the waveform's static and live states | E6 | DONE: replaced by one `test_modality_tier_labels`. The waveform tests are GONE rather than rewritten, because there is no waveform to be static or live. |
| `test_v443_phase5_models.py` | `test_inside_the_model_states_three_true_things_with_the_caveat`, `test_released_models_are_named_from_three_providers` | the three-step block and the versioned provider list | E6 | DONE: both removed, because `test_v444_phase6_models.py` asserts the replacements. Thin duplicates would have meant two places to update and one going stale. |
| `test_v443_phase5_models.py` | `test_the_video_output_plays_without_being_asked` | the label came from `.fx-out-tag` inside `.fx-out` | E6 | DONE: reads the omni tier's tag |
| `test_nexus_hub_guide.py` | `test_foundations_phase3_has_eight_title_subtitle_scenes` | seven scenes, and the title `Chatbot vs. Agentic Platforms` | E7: the comparison moved inside the platform scene | DONE: six scenes, the entry removed |
| `test_nexus_hub_guide.py` | `test_foundations_chatbot_and_agent_share_a_request_but_not_the_handoff` | `_foundation_scene(..., "fx-chatbot-agent")` and `Same request, different handoff` | E7 | DONE: reads the merged scene. Its three copy requirements (`same request`, `where the work happens`, `what each lane leaves behind`) were put BACK into the copy rather than out of the test. |
| `test_nexus_hub_guide.py` | `test_foundations_phase3_diagrams_animate_with_observer_and_static_fallback` | `data-grammar="one-pass"` count 2 | E7: the platform's flow is retired | DONE: 1 |
| `test_v442_phase3_foundations.py` | two scene counts | seven scenes | E7 | DONE: six |
| `test_v443_phase6_platforms.py` | `test_the_flow_is_choreographed_in_execution_order` | the five-stage flow and its order | E7: the flow is retired | DONE: removed, recorded here rather than quietly dropped; the comparison's choreography is asserted in the comparison module |
| `test_v441_phase4_foundations.py` | `test_models_and_agentic_platform_share_visual_grammar` | two byte-identical entry motifs, three missions, an execution order | E7 | DONE: rewritten as `test_the_agentic_scene_carries_the_comparison_and_the_boundary`. The shared-grammar rule existed so a comparison BETWEEN two scenes would teach; with one scene carrying both lanes the sameness is on screen instead. |
| `test_v442_phase4_media.py` | `test_flow_connectors_never_cross_a_card` | three roots, seven paths | E7: the retired flow owned one root and four connectors | DONE: two roots, three paths |
| `test_v442_phase4_media.py` | `test_models_and_agentic_still_share_the_entry_and_inside_bytes` | two entries, byte-identical, and two one-pass motifs | E7 | DONE: renamed to `test_the_entry_motif_is_singular_after_the_merge`; one each, and the retired scene asserted absent |
| `test_v442_phase1_foundation.py` | 23 section titles across the four pages | E7 | one scene fewer | DONE: 22 |
| `test_v443_phase5_models.py` | `data-grammar="one-pass"` count 2 | E7 | DONE: 1 |
| `test_v443_phase8_harness.py` | seven Foundations scenes | E7 | DONE: 6 |
| `test_v443_phase8_harness.py` | `test_the_three_layers_are_geometrically_nested` | the rings nest with the model innermost | E8: the review asked for a flow, not a picture of where the layers sit | DONE: replaced by `test_the_flow_carries_the_analogy_and_the_platform_limits`, which asserts the three layers in order, their ports, the analogy on each, and the platform layer's stated limits |
| `test_v443_phase8_harness.py` | `test_the_journey_reads_as_movement_and_ends_in_verified_work` | six `.hx-stop` elements | E8 | DONE: five `.hxf-step` elements, renamed to `..._the_flow_is_choreographed_...` |
| `test_v442_phase4_media.py` | the harness figure tests | `.hx-stop`, `.hx-stop--out`, six steps | E8 | DONE: `.hxf-step`, `.hxf-step--out`, five steps |

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

## 3b. Two structural repairs, and the trap behind both

Two of the Phase 6 replacements used a non-greedy regex that stopped at the first matching closer, so
each left stray closing tags behind. One orphaned the old effort note, which then said something the
new copy already said; the other closed the request region early, which dropped a nested flow root
and cut the connector count from seven to two.

The second was found by `test_flow_connectors_never_cross_a_card`, which asserts three roots and
seven paths and therefore noticed a structural change that rendered without visible error. The fix
was not more closer-counting: the Models section is re-emitted from its harvested parts with the
nesting written out, and the script asserts each part is balanced before assembling them. **A
non-greedy match against nested markup finds the first close, not the matching one.**

## 3bb. Three contrast defects the strengthened contract exposed

Never hiding a sequence step under reduced motion had a side effect worth recording: the contrast
sweep samples only VISIBLE text, so every element that had been invisible until its sequence played
was silently outside the sweep's reach. Making them visible put them inside it, and three failed
WCAG AA in light theme:

| Element | Where it came from | Ratio | Fix |
|---|---|---:|---|
| `.gf-out--ok` and `--stop` | v4.4.3 Phase 2 guardrails | 3.92 | the tint gives way to an outline in light theme |
| `.cv-changes li` | v4.4.3 Phase 7 comparison | 4.08 | same |
| `.cx-ex` | v4.4.4 Phase 5 material examples | 1.90 | `--blue` had NO light-theme override, so it stayed a bright sky blue; one was added |

The first two are pre-existing and shipped invisible; only the third is this phase's own. The general
lesson is uncomfortable and worth keeping: **a contrast sweep that skips hidden text will pass a
palette it never measured.** The missing `--blue` override is the same shape of gap: a token used for
strokes and fills for four versions, then used for text once, at which point its absence mattered.

## 3ba. The stale-offset splice, repeated

v4.4.3 Phase 8 recorded this exact mistake: compute a section's offsets, edit something EARLIER in
the file, then splice with the offsets already computed. v4.4.4 Phase 7 made it again. Inserting the
new stylesheet block shifted every later index, so the merged scene was spliced into the middle of a
base64 GIF payload, taking the Models scene's closing tags with it.

It was caught immediately, by rendering the scene and looking at it: the screenshot showed an image
alt text where a scene should have been. The guide was restored from the last commit and the splice
redone with the spans recomputed.

Recording a lesson in a history file did not prevent the repeat. What prevents it is the recompute
sitting on the line above the splice, in the script, where the next person editing that script reads
it. Both scripts now carry it.

## 3c. One accessibility contract strengthened

Zeroing the transition under reduced motion made a sequence step reveal instantly, but it still
waited for the observer to play the sequence, so a reader who had asked for less motion saw an empty
strip until they scrolled it into view. Under reduced motion a step is now never hidden at all.

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
| 3 | Foundations title pair inverted (name first, description under) | -226 | 374,402 |
| 4 | Prompt Engineering rebuilt: vague prompt beside its flaws, engineered prompt full width | +3080 | 377,482 |
| 5 | Context Engineering rebuilt: copy full width, request beside material, both outcomes named | +2374 | 379,856 |
| 6 | Models rebuilt to teach next-token, base against reasoning, three tiers; audio and waveform retired | -11,379 | 368,477 |
| 7 | Chatbot comparison merged into Agentic Platforms; one scene retired | -2753 | 365,724 |
| 8 | Harness rings and six-stop journey replaced by one five-step flow | +805 | 366,529 |
| 9 | Verification and closeout; no artifact change | 0 | 366,529 |

Final: **366,529 bytes**, 73,471 under the 500,000 ceiling and 3724 BELOW where v4.4.3 finished.
A review round that rebuilt six scenes made the file smaller, because Phase 6 retired an audio
asset whose teaching had left the page and Phase 7 deleted a whole scene by merging it.
