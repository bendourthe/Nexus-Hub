# Prompting Profile: gemini-omni-1.1-flash

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-omni-1.1-flash"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Call gemini-omni-1.1-flash through the Interactions API (a POST to the v1beta interactions endpoint on generativelanguage.googleapis.com, or client.interactions.create in the SDKs) with model set to gemini-omni-1.1-flash; the stable model code is gemini-omni-1.1-flash and the preview id gemini-omni-flash-preview is shut down, so migrate to the stable id. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-omni-flash) |
| The model accepts text, image and video input (video input up to 10s for editing and extension) and outputs video only (3s-10s at 360p/720p/1080p/4K, 24 FPS), with a 1,048,576-token context window. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-omni-flash) |
| Control output with response_format: aspect_ratio is 9:16 or 16:9 (16:9 is the default) and resolution is 360p, 720p (default), 1080p (upscaled) or 4k (upscaled). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/omni) |
| Do not rely on system instructions, temperature, top_p, stop sequences or negative-prompt parameters, which this model does not support; express negatives in the prompt text (for example 'No dialogue', 'No extra sound effects', 'Do not do X'). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/omni) |
| Prompt for text-to-video with scene description, camera movement, lighting and mood, and describe the audio you want (for example 'Include calm background music'); the model generates a default audio track but music needs explicit description. To avoid multiple shots, ask for 'a single continuous shot' or 'No scene cuts'. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/omni) |
| For image-to-video, use high-resolution reference images and give specific motion, camera and environmental-effect descriptions (vague prompts such as 'make it move' give weaker results); for first/last-frame interpolation pass two images in input (first, then last) and describe the transition in text. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/omni) |
| Try natural-language prompting first and set generation_config.video_config.task (text_to_video, image_to_video, reference_to_video, edit, extend) only as a fallback, because task adds strict constraints; do not put control strings such as FIRST_FRAME or IMAGE_REF_0 written inside angle brackets in prompts, describe each media input's role in words instead. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/omni) |
| For multi-turn editing, chain turns with previous_interaction_id (each turn yields a new video), keep edit prompts simple and minimal, and add 'Keep everything else the same' for targeted edits; store=false makes the generated video non-editable in later turns. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/omni) |
| For faster synchronous generation set background=false, store=false and stream=false; for outputs larger than 4MB set response_format.delivery to 'uri' and download via the Files API (poll until ACTIVE), since the default returns inline base64 video data. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/omni) |
| Stated limitations: no reasoning across multiple videos (degraded performance), video references max 3 clips of up to 3s each with reference audio ignored, no audio reference uploads, no YouTube video sources, no provisioned throughput; English is fully supported while other languages are not evaluated. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/omni) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
