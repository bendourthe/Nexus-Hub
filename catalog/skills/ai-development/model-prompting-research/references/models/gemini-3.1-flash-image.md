# Prompting Profile: gemini-3.1-flash-image

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.1-flash-image"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Use the stable model id gemini-3.1-flash-image (Nano Banana 2). Only the stable version is listed; no preview or dated variant is documented on the per-model page. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-image) |
| Plan for a 131,072-token input limit and a 32,768-token output limit. Accepted inputs are text, image, video and PDF; outputs are image and text. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-image) |
| Do not rely on function calling, structured outputs, code execution, URL context, Google Maps grounding, caching, the Live API, or Flex/Priority inference for this model. The per-model page lists all of these as unsupported. Supported are the Batch API, image generation, Search grounding and thinking. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-image) |
| Set output size with image_size. Valid values are 512px (0.5K, unique to Gemini 3.1 Flash Image among the Gemini 3 image models), 1K, 2K and 4K, with 1K the default. Labels must be uppercase because lowercase values such as 1k are rejected. The model also adds aspect ratios 1:4, 4:1, 1:8 and 8:1. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Thinking is on by default and cannot be disabled in the API for Gemini 3 image models. Gemini 3.1 Flash Image accepts thinking_level values minimal and high, with minimal the default. Set it in generation_config. Thinking tokens are billed, and the model may produce up to two interim images, the last of which is the final image. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Reference-image budget for this model: up to 10 object images for fidelity, up to 4 characters for resemblance, and up to 14 reference images in total. No style-reference allowance is listed for it. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Video input is supported for image generation on Gemini 3.1 Flash Image (and Nano Banana 2.1 and Flash Lite Image). Audio input is not supported. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Sequential-art prompts (comic panels, storyboards) work best with Gemini 3 Pro Image and Gemini 3.1 Flash Image, because of their text accuracy and storytelling ability. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Do not expect the model to honor an exact requested number of output images. For text rendered in images, first generate the text, then ask for an image containing it. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| Prompt for images by being specific, stating the image's purpose as context, iterating conversationally with small follow-up edits, breaking complex scenes into ordered steps, describing the wanted scene positively (semantic negative prompts) instead of listing exclusions, and using photographic terms (wide-angle, macro) for camera control. The page states these as general best practices, not for one model. | `medium` | `model-agnostic-candidate` | not recorded | [source](https://aistudio.google.com/docs/image-generation) |
| On Vertex AI, gemini-3.1-flash-image supports GenerateContent and Count Tokens but not the Interactions API, Live API or Chat Completions. It supports implicit context caching, Google Search grounding and multi-turn image editing, but not function calling, structured output, code execution, URL context or tuning. Defaults are temperature 1.0 (range 0.0-2.0) and topP 0.95, with candidateCount fixed at 1. | `high` | `model-specific` | not recorded | [source](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-1-flash-image) |
| On Vertex AI, plan image budgets with 14 images max per prompt, 1,120 tokens per input image, and output tokens of 747 at 512, 1,120 at 1K, 1,680 at 2K and 2,520 at 4K. Input formats are PNG, JPEG, WebP, HEIC and HEIF. | `high` | `model-specific` | not recorded | [source](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-1-flash-image) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
