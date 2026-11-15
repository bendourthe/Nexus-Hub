# Prompting Profile: gemini-2.5-flash-image

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-2.5-flash-image"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Use the stable model ID gemini-2.5-flash-image (Nano Banana, original). The earlier gemini-2.5-flash-image-preview ID is deprecated (shutdown January 15, 2026), so migrate any code still pointing at the preview ID to the stable ID. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-image) |
| Plan a migration: gemini-2.5-flash-image is listed on the deprecations page with an earliest shutdown date of March 15, 2027 and gemini-3.1-flash-lite-image as the recommended replacement. The image-generation guide calls it the legacy model of the Nano Banana series and recommends Nano Banana 2 Lite for higher quality, faster speeds and lower pricing. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/deprecations) |
| Do not request thinking, function calling, structured outputs, search grounding, URL context, code execution, context caching, or the Live API from this model. Its model page lists all of them as not supported. Supported: image generation and the Batch API, with image and text inputs and image and text outputs. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-image) |
| Budget for token limits of 65,536 input tokens and 32,768 output tokens, with a June 2025 knowledge cutoff. Position the model for high-volume generation and conversational image editing where speed and efficiency matter. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-image) |
| Limit input to about 3 reference images: the Limitations section says gemini-2.5-flash-image works best with up to 3 images as input. The 14-image and multi-character or multi-object fidelity guidance applies to other models (Gemini 3 Pro Image, Nano Banana 2.1, Gemini 3.1 Flash Image), not to this one. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Choose output shape by aspect ratio. This model offers fixed sizes at a flat 1290 tokens per image: 1:1 1024x1024, 2:3 832x1248, 3:2 1248x832, 3:4 864x1184, 4:3 1184x864, 4:5 896x1152, 5:4 1152x896, 9:16 768x1344, 16:9 1344x768, 21:9 1536x672. The 1:4, 4:1 and 1:8 style ratios and the 1K/2K/4K image-size options are documented for newer models, not for this one. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Do not rely on an exact output image count: the model will not always follow the exact number of image outputs requested. Audio input is not supported, and video input is documented only for newer Nano Banana models. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| For images that contain text, generate the text first and then ask for an image that includes that text. For best performance use the listed languages: EN, Arabic (Egypt), German, Spanish (Mexico), French, Hindi, Indonesian, Italian, Japanese, Korean, Portuguese (Brazil), Russian, Ukrainian, Vietnamese, Chinese (Simplified). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| For editing, supply the source image with a text description of the change. The page says the model will match the original image's style, lighting and perspective, and that a mask can be defined conversationally to edit only part of an image. Make sure you have the necessary rights to any images you upload. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Expect all generated images to carry a SynthID watermark. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
