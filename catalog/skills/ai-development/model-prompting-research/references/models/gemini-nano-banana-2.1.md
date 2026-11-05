# Prompting Profile: gemini-nano-banana-2.1

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-nano-banana-2.1"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Set thinking effort with the thinking_level field (generation_config: {thinking_level: "..."}); gemini-nano-banana-2.1 supports minimal, medium and high, with medium as the default (the 3.1 Flash Image models only offer minimal and high, default minimal). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Thinking is enabled by default for Gemini 3 image models and cannot be disabled in the API, so choose a thinking_level rather than trying to turn thinking off. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Request image output via response_format with type image, plus optional mime_type, aspect_ratio and image_size; image_size must use an uppercase K (1K, 2K, 4K), because lowercase such as 1k is rejected. gemini-nano-banana-2.1 supports 1K, 2K and 4K but not 512px, and the default is 1K. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| By default gemini-nano-banana-2.1 returns both text and an image unless response_format is set to image only; default output size matches the input image, or is 1:1 if there is no input image. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| gemini-nano-banana-2.1 adds extreme aspect ratios 1:4, 4:1, 1:8 and 8:1 (14 ratios total from 1:1 to 21:9, each at 1K, 2K and 4K), at 1,120 / 1,680 / 2,520 output image tokens for 1K / 2K / 4K. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| For multi-image input, gemini-nano-banana-2.1 supports up to 14 reference images total, with character resemblance for up to 4 characters and fidelity for up to 10 objects in one workflow; refer to each input image by position (for example 'the first image') in the prompt. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| For iterative editing with gemini-nano-banana-2.1, chain turns by passing previous_interaction_id set to the prior interaction.id; the page calls multi-turn the recommended way to iterate on images. Use explicit preservation wording such as 'Keep everything else in the image exactly the same' for inpainting-style edits. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Enable Search grounding on gemini-nano-banana-2.1 with tools=[{type: google_search}]; add search_types [web_search, image_search] for Image Search (only on 2.1 and 3.1 Flash Image). When Image Search is used, the search_suggestions from the google_search_result step must be displayed, and real-world images of people from web search are not supported. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| gemini-nano-banana-2.1 accepts video input (public YouTube URL in uri, or a Files API upload) in addition to text, image and PDF; audio input is not accepted for image generation. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| gemini-nano-banana-2.1 does not support caching, function calling, structured outputs, code execution, URL context, file search, Live API, Flex or Priority inference, or Maps grounding; it supports Batch API, image generation, Search grounding and thinking. Input limit 131,072 tokens, output limit 32,768. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-nano-banana-2.1) |
| Parse interleaved responses by iterating interaction.steps where step.type is model_output and checking each content block type for text or image; the convenience properties output_image and output_text only return the last image or the text and miss parts. Thought summaries are read from steps of type thought. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Image prompting best practices: be specific about materials and shapes, state the image purpose, iterate one change at a time, build complex scenes in steps, describe what you want rather than what you do not want, and use camera language (wide-angle, macro). For text in images, specify exact text, font style and design; results are better if you generate the text first and then ask for an image containing it. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
