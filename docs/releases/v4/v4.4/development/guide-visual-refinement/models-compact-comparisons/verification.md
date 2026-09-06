# Compact Models verification

## Completed

Pre-training now has a Pattern learning subheading styled like Reinforcement learning. The model-type tabs sit beside the demo heading, replacing the step and playback buttons. Supporting explanations sit below each request. All four architectures use circular nodes, more connections and multiple independently traveling signals. The game example now transforms a basic space-game screen into a new spacecraft, planetary scene and mission-focused flight interface.

Capability tiers advance left to right every 4.2 seconds, with progressively wider and denser graphs, approved Claude and ChatGPT marks, and concise capability, speed and cost tradeoffs. The effort table shows four simultaneous allowances with the same network, separate progress indicators and visibly different completion times. Hover or keyboard focus pauses the corresponding illustration; reduced motion shows settled results.

## Timing and rendering

| Demonstration | Generation or processing | Inspection time |
|---|---|---|
| Text | One word every 600 ms; the six-word response completes after about 3 seconds | The final response remains visible for about 3.6 seconds |
| Image | Five denoising transitions over about 2.5 seconds | The clear photograph remains visible for about 3.5 seconds |
| World | A 17-second camera sequence with forward movement, turns and return | Left and right views each have a stationary hold |
| Multimodal | Multiple signals travel through shared layers | The redesigned game remains visible |
| Capability | One tier highlighted for 4.2 seconds | Hover or focus pauses the sweep |
| Effort | Illustrative 1, 3, 6 and 9 passes at 700 ms per pass | All completed columns remain visible before restarting |

The room uses a continuous textured depth mesh rendered by native WebGL. The camera rotates about 19 degrees to each side and translates forward and sideways, creating perspective and parallax instead of translating a flat image. Depth is an authored approximation from the existing photograph: this is not a complete reconstruction of unseen furniture or a live world model. The photograph remains available without JavaScript or WebGL. No new dependency, server, generated service call or runtime network request was introduced.

## Verified

- The [focused guide run](focused-tests.txt) passed 154 tests, with one optional portfolio-copy check skipped because its sibling root is unset.
- The [final Models run](final-models-tests.txt) passed all 24 tests and covers the final paragraph sizing and deterministic clock setup, including keyboard tabs, distinct graphs, output holds, hover/focus pause, camera rotation and translation, provider marks, tier progression, simultaneous effort allowances, reduced motion, offline loading and no-JavaScript content.
- [40 layout cases](layout.json) cover four model types at 320, 420, 768, 1024 and 1440 pixels in dark and light themes; no horizontal overflow or clipped text was found.
- [Runtime evidence](runtime.json) records 12 independent traveling signals, the perspective camera poses, zero page errors, zero outbound requests and no active animation after leaving Foundations.
- [Scope and syntax evidence](scope.json) confirms all five executable scripts parse, the UTF-8 guide is 497,896 bytes, and content outside Models matches baseline `416da259` exactly.
- Desktop training, every model type, provider tiers and live reasoning were visually inspected. Mobile light-mode multimodal and effort layouts were also inspected. The narrowest screens use two rows of model tabs and a two-by-two effort comparison.

## Compactness

At a 1440-pixel viewport, the demo heights changed as follows. Values include the heading, model tabs and complete active demo.

| Mode | Before | After | Reduction |
|---|---:|---:|---:|
| Text | 601 px | 367 px | 39% |
| Image | 633 px | 424 px | 33% |
| World | 696 px | 413 px | 41% |
| Multimodal | 695 px | 589 px | 15% |

## Verification corrections

The first pass identified model-tab clipping at 320 pixels; those tabs now wrap into two rows. The perspective capture initially moved the pointer over the output while scrolling, correctly triggering hover pause; captures now move the pointer away between frames. The old network CSS assertion was migrated to the new node-and-particle architecture. The tier timing check exposed a test-clock setup issue caused by replacing the clock after initialization; live-animation tests now install and pause their clock before loading the guide.

## Sources and artifacts

The diagrams represent relative capacity and processing allowance, not disclosed parameter counts or fixed provider iteration counts. The teaching copy was checked against [Claude model selection](https://academy.claude.com/tutorials/choosing-the-right-claude-model) and [OpenAI reasoning effort](https://developers.openai.com/api/docs/guides/reasoning). Existing model names and official source links remain in the guide.

[models.css](models.css) and [models.js](models.js) are the authored source snapshots embedded in the self-contained HTML, not runtime dependencies. [game-before.svg](game-before.svg) and [game-after.svg](game-after.svg) are native UI artwork embedded in the guide. The harbor and room photographs are reused from the [previous asset provenance](../models-photographic-examples/assets.md); no new generated images were needed.

## Open and next

No requested Models item remains deferred. Unrelated Home contrast, Agentic Platforms overflow and legacy assertion issues remain in the project tracker. No portfolio synchronization, push or publication was performed. Review Foundations > Models in the canonical guide.

## Reproduce

```powershell
python -m pytest tests/guides/test_models_learning_lab.py tests/guides/test_nexus_hub_guide.py tests/guides/test_v441_phase1_contract.py tests/guides/test_v441_phase4_foundations.py tests/guides/test_v442_phase4_media.py -q
python docs/releases/v4/v4.4/development/guide-visual-refinement/models-compact-comparisons/capture.py
```
