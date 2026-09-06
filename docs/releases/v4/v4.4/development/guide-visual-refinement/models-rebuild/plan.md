# Models section rebuild

## Scope and design

Replace only the Models section in Foundations. Keep the existing section anchor, Home-style headings, theme tokens, surrounding Foundations content, Home, and Training. Replace the eight-stage essay with three visual groups: learned capability, four generation demonstrations, and model capability versus reasoning effort. Construction-debt: one scoped controller, native buttons/tabs, inline SVG, finite animations; no dependency, live model call, or new rendering engine.

## Acceptance

- [x] Explain a model as learned neural-network weights with broad abilities; distinguish training from using a prompt.
- [x] Demonstrate next-token language generation, noise-to-image diffusion, action-conditioned world prediction, and multimodal/omni input and output without conflating them.
- [x] Teach model-category differences with Haiku/Luna, Sonnet/Terra, Opus/Sol (assumed correction of duplicated Luna), and Mythos/Fable/Astra. Treat pairs as rough roles rather than benchmark equivalence.
- [x] Explain Low, Medium, High, and Max effort as relative processing allowances, not guaranteed correctness or fixed loops. Show reasoning as a conceptual illustration, not private thoughts.
- [x] Keep the desktop default view below 1800 pixels and 420 visible words, and reduce both from the baseline. Demos must work without network calls and remain readable without motion.
- [x] Verify all four demos and all model/effort choices, keyboard controls, replay, route/offscreen cancellation, reduced motion, and no-JavaScript fallback.
- [x] Inspect screenshots during implementation and at completion at desktop and phone widths in both themes. Check 320, 420, 768, 1024, and 1440 pixels for overflow, wrapping, stable demo height, and alignment.
- [x] Replace assertions that prescribe the superseded eight-stage implementation with behavior coverage; retain unrelated tests and document their mapping.
- [x] Run affected guide tests, document evidence, update the tracker, and make one scoped local commit. No publication.

## Source notes

Official sources checked on 2026-09-05:

- [Claude family roles](https://academy.claude.com/tutorials/choosing-the-right-claude-model)
- [OpenAI model families](https://developers.openai.com/api/docs/models)
- [Reasoning tokens](https://developers.openai.com/api/docs/guides/reasoning)
- [Effort levels](https://platform.claude.com/docs/en/build-with-claude/effort)
- [Text tokens](https://help.openai.com/en/articles/4936856-understanding-and-counting-tokens)
- [Diffusion denoising](https://openai.com/index/simplifying-stabilizing-and-scaling-continuous-time-consistency-models/)
- [Interactive world models](https://deepmind.google/models/genie/)
- [Omni models](https://openai.com/index/hello-gpt-4o/)

Availability and effort labels vary by provider and release. Keep dated model examples separate from durable conceptual explanations.
