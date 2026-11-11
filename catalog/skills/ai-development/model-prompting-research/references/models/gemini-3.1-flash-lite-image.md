# Prompting Profile: gemini-3.1-flash-lite-image

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.1-flash-lite-image"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Thinking is supported at levels minimal and high only, with minimal as the default; set it with thinking_level to trade quality against latency. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Thinking cannot be disabled in the API for Gemini 3 image models, and thinking tokens are billed by default; the model may generate up to two interim images to test composition, and the last thought image is the final rendered image. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Input limit is 65,536 tokens and output limit is 4,096 tokens. Inputs can be text, image, video and PDF; outputs are image and text. Audio inputs are not supported for image generation. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-lite-image) |
| Not supported on this model: search grounding (including Grounding with Google Search), function calling, structured outputs, code execution, URL context, caching, file search, Live API, flex and priority inference. Do not rely on these in requests. Batch API is supported. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-lite-image) |
| Video-to-image generation is supported: pass a public YouTube URL or an uploaded video file as multimodal context. Video inputs are only supported for Nano Banana 2.1, Gemini 3.1 Flash Image and Gemini 3.1 Flash Lite Image. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Migration: gemini-2.5-flash-image is legacy and the recommended migration path is Nano Banana 2 Lite (gemini-3.1-flash-lite-image), for higher quality, speed and lower price. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Prompt with detail and purpose: describe the subject concretely, state what the image is for, use photographic and cinematic terms for composition, and describe the scene positively instead of negating (for example 'an empty, deserted street' instead of 'no cars'). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| For complex scenes, break the prompt into steps (background, then foreground, then details) and iterate conversationally with small changes rather than expecting a perfect first image. The model will not always return the exact number of images requested. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| To render text in an image, first generate the text, then ask for an image containing that text. For best results use the languages listed on the page (EN, ar-EG, de-DE, es-MX, fr-FR, hi-IN, id-ID, it-IT, ja-JP, ko-KR, pt-BR, ru-RU, ua-UA, vi-VN, zh-CN). All generated images carry a SynthID watermark. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
