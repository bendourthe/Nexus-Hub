# Prompting Profile: gemini-3-pro-image

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3-pro-image"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Use gemini-3-pro-image (Nano Banana Pro) for complex visual tasks that need advanced reasoning, brand consistency and high-fidelity text rendering; it is optimized for professional asset production (graphic design, product mockups, factual data visualizations). Flash-based image models are the speed and volume option. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation?generate-content=true) |
| Thinking is always on for Gemini 3 image models: it is enabled by default and cannot be disabled in the API. The model may generate up to two interim images to test composition, and the last image within Thinking is also the final rendered image. The thinking-levels table lists only Nano Banana 2.1 and Gemini 3.1 Flash (Lite) Image, so no thinking-level control is documented for Pro. Thinking tokens are billed by default. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation?generate-content=true) |
| Reference images: Nano Banana models accept up to 14 reference images in total. For the Pro column the documented limits are up to 6 high-fidelity object images, up to 5 character images for consistency, and up to 3 style-reference images. Style references are not offered by the other Nano Banana models. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation?generate-content=true) |
| Output size: Gemini 3 image models default to 1K output. Pro supports 1K, 2K and 4K. Set image_size with an uppercase K (for example "2K" or "4K"); lowercase values such as "1k" are rejected. The 512px size is for Gemini 3.1 Flash Image only. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation?generate-content=true) |
| gemini-3-pro-image can produce interleaved text and images in a single response; convenience properties such as .output_image will not capture the full sequence, so iterate over the response steps/parts instead. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation?generate-content=true) |
| Model card facts for gemini-3-pro-image: stable id gemini-3-pro-image; inputs are image and text, outputs are image and text; input limit 65,536 tokens, output limit 32,768 tokens. Supported: Batch API, image generation, search grounding, thinking. Not supported: function calling, structured outputs, code execution, URL context, file search, Google Maps grounding, caching, Live API, flex and priority inference. Search grounding is the only supported tool. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3-pro-image) |
| Lifecycle and migration: the preview id gemini-3-pro-image-preview launched 2025-11-20; gemini-3-pro-image (Nano Banana Pro) went GA on 2026-05-28, and gemini-3-pro-image-preview was deprecated with shutdown on 2026-06-25. Calls should use the GA id gemini-3-pro-image (the changelog does not name it explicitly as the replacement). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/changelog) |
| Text-in-image prompting: for accurate text rendering use Gemini 3 Pro Image, and describe the font style descriptively in the prompt. For comic or storyboard sequences that need accurate text and storytelling, the guide says the prompts work best with Gemini 3 Pro and Gemini 3.1 Flash Image. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation?generate-content=true) |
| For iterative image edits the guide recommends multi-turn conversation; in the Interactions API turns are chained with previous_interaction_id, and the thought-signatures page says the Interactions API manages reasoning (thought signatures) at the API level. The fetched pages do not state signature requirements specifically for gemini-3-pro-image. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thought-signatures) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
