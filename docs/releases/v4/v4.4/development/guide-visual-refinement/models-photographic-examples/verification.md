# Models photographic examples verification

## Completed

The training row now labels text, image and code with icons and replaces the request bubble with a try-score-improve reinforcement-learning feedback loop. Language uses a single bread-rise request, with the growing response above its probabilities. Diffusion reveals a detailed harbor photograph in a 3.9-second cycle. World views retain one photographic room source across continuous pan and zoom. Multimodal uses a voice recording transcript and booking-screen image, a shared-weights illustration, and text plus a redesigned-screen image. Each demonstration has a distinct illustrative architecture.

## Verified

- [153 focused tests passed, one optional portfolio-copy check skipped](focused-tests.txt). The sibling portfolio root is unset; the canonical guide is the authorized target.
- [40 layout cases passed](layout.json): four modes at 320, 420, 768, 1024 and 1440 pixels, in dark and light themes, without horizontal overflow or clipped text.
- [Runtime checks](runtime.json): all 24 manual frames were reachable, the signal traveled through the network, playback stopped after leaving Foundations, and no page errors or outbound requests occurred.
- [Scope and syntax](scope.json): all five executable scripts passed `node --check`; guide content outside Models is identical to baseline `83fdfa35`; the canonical UTF-8 HTML is 499,320 bytes, below the existing 500,000-byte ceiling.
- Desktop training and all four demonstrations were visually inspected, along with the light mobile multimodal layout. Photographic furniture and materials remain consistent between the recorded room frames. Mobile output stacks request, model and response without clipping.
- Keyboard tabs, pause/play, manual stepping, continuous language playback, the faster diffusion cycle, live reduced-motion changes and JavaScript-disabled content are covered by the browser tests.

## Corrections during verification

The retired canvas assertion was updated to inspect the new main photographic view while checking that its source remains identical. An intermittent live reduced-motion transition was reproduced during the focused run; synchronization now immediately settles an enabled demo when reduced motion becomes active. The final full focused run passes after that correction. The earlier timing failure is retained in [initial-motion-failure.txt](initial-motion-failure.txt).

## Assets and representation

See [asset provenance and exact generation prompts](assets.md). The four WebP assets are embedded once each, so the HTML works offline. World movement is an illustrative pan and zoom of one photograph, not synthesis of unseen geometry. Network diagrams and probabilities are explicitly illustrative. The voice quote is a recording transcript, not an additional typed prompt.

## Open and next

No Models work remains from this request. The existing unrelated Home contrast, Agentic Platforms overflow and legacy guide-assertion issues remain tracked in `docs/todos.md`. No portfolio copy, push or publication was performed. Review the updated Foundations Models section in the canonical guide.

## Reproduce

```powershell
python -m pytest tests/guides/test_models_learning_lab.py tests/guides/test_nexus_hub_guide.py tests/guides/test_v441_phase1_contract.py tests/guides/test_v441_phase4_foundations.py tests/guides/test_v442_phase4_media.py -q
python docs/releases/v4/v4.4/development/guide-visual-refinement/models-photographic-examples/capture.py
```
