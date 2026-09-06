# Models flow refinement verification

## Completed

Only the Foundations Models section changed. Training examples have explicit text/image/code labels and floating triangle connectors. All four demonstrations share a user prompt, neural-network traversal and output layout. Language prediction repeats continuously with candidate probabilities and a selected token. Pause and Next step controls support inspection without autoplay.

The world example renders a furnished room with floorboards, a sofa, coffee table, armchair, window, plant, artwork and bookshelves. Its camera moves forward and turns left and right; a frame strip makes the changed viewpoints comparable. This is an illustrative local perspective renderer, not photorealistic footage or a live world model. Multimodal combines text, a room image and voice in one model, then shows text and an image with warmer lighting. All user-facing Omni labels are removed.

The four increasing network graphics identify Anthropic and OpenAI explicitly. A selected category explains its practical role. The reasoning illustration repeatedly revisits the same model, allowing more internal work before the reply at higher effort. The confusing meal strip and final picnic demonstration are removed.

## Visual evidence

- [Whole section, dark](dark-section.png) and [light](light-section.png).
- [Training examples](dark-1440-training.png), [model classes](dark-1440-classes.png) and [reasoning](light-320-effort.png).
- [Network signal in flight](network-in-flight.png), [mobile language](light-320-language.png) and [multimodal](dark-1440-multimodal.png).
- Room: [doorway](frame-world-0.png), [moving forward](frame-world-2.png), [looking left](frame-world-4.png), [looking right](frame-world-5.png).
- [Layout matrix](layout.json): 40 cases across 320, 420, 768, 1024 and 1440 pixels, dark and light, and all four model types. No horizontal page overflow or clipped demo text. Output containers grow naturally to accommodate the images instead of clipping content to a forced height.

Screenshots were inspected during implementation and after corrections. Corrections kept furniture visible during turns, added motion-free frame stepping, repaired the signal/node paint order, and removed the remaining Omni source label.

## Functional verification

- [Affected suite](final-tests.txt): 151 passed, one optional portfolio skip, and one remaining source-label assertion failed. The label was corrected and its [final retest](final-copy-retest.txt) passed, completing all 152 selected checks.
- New Models coverage includes repeated token prediction, frozen pause state, manual stepping for all modes, changed room pixels, independent capability/effort selection, increasing model graphic size, longer internal processing at higher effort, tab keyboard navigation, live reduced-motion changes and offscreen/route suspension.
- [Runtime capture](runtime.json): 24 manually inspected states, zero page errors, zero external requests, a signal midway through its network path and zero active Models animations after leaving Foundations.
- [Scope and syntax](scope.json): all five executable inline scripts pass `node --check`; HTML, CSS and JavaScript outside Models are unchanged from `80197e3a`.
- Guide size is 406,247 bytes, below the unchanged 500,000-byte release ceiling. The historical 400,000-byte Phase 1 checkpoint reserved headroom for subsequent phases; its current-page assertion now checks the durable release ceiling. The dated checkpoint and original measurement remain in the original phase contract.
- The previous blanket ban on CSS motion paths now checks the requested Models signal's node layering, visibility gate and reduced-motion fallback. Other retired animation primitives remain prohibited.

The broader [visual sweep](affected-tests.txt) reproduced the known Home light-theme guardrail-pill contrast issue (4.462:1). It reported no Models contrast failure. Other previously recorded unrelated guide gaps remain outside this request. With JavaScript disabled, explanations remain visible; the room renderer and animation controls require JavaScript, as the in-page notice states.

## Source checks

Model categories were checked against [Anthropic's family guide](https://academy.claude.com/tutorials/choosing-the-right-claude-model), [Mythos](https://www.anthropic.com/claude/mythos), and [OpenAI's model catalog](https://developers.openai.com/api/docs/models). The graphics indicate conceptual capability, not parameter counts or cross-provider benchmark equivalence. Reasoning follows the [OpenAI explanation](https://developers.openai.com/api/docs/guides/reasoning) and [Anthropic effort controls](https://platform.claude.com/docs/en/build-with-claude/effort): more processing allowance, not a fixed number of loops or literal self-chat. Native multimodal processing follows the [single-network explanation](https://openai.com/index/hello-gpt-4o/); room prediction illustrates the scene/action concept described for [world models](https://deepmind.google/models/genie/).

## Reproduce

From the repository root:

```powershell
python -m pytest tests/guides/test_models_learning_lab.py tests/guides/test_nexus_hub_guide.py tests/guides/test_v441_phase1_contract.py tests/guides/test_v441_phase4_foundations.py tests/guides/test_v442_phase4_media.py -q
python docs/releases/v4/v4.4/development/guide-visual-refinement/models-flow-refinement/capture.py
```

No dependency, build-step, pipeline or runtime network requirement was added. Publication is not part of this local visual refinement.
