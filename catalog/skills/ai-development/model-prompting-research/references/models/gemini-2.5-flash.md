# Prompting Profile: gemini-2.5-flash

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-2.5-flash"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| gemini-2.5-flash is deprecated: it is no longer selectable in Google AI Studio and API access is limited to existing users. Effective December 1, 2026 (earliest possible shutdown date), all API requests to gemini-2.5-flash automatically route to gemini-3.5-flash-lite and are billed at Gemini 3.5 Flash-Lite rates. Set the model string to gemini-3.5-flash-lite before that date. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/deprecations) |
| The gemini-2.5-flash model page lists a 1,048,576-token input limit and a 65,536-token output limit, with text, image, video and audio input and text-only output. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash) |
| gemini-2.5-flash supports Batch API, Caching, Code execution, File search, Function calling, Search grounding, Grounding with Google Maps, Structured outputs, Thinking and URL context. It does not support Live API, audio generation or image generation. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash) |
| Thinking is on by default for gemini-2.5-flash. The thinking guide controls thinking with the thinking_level parameter in generation_config, and lists low, medium and high as supported levels for this model. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |
| The gemini-2.5-flash model page lists its knowledge cutoff as January 2025, so supply recent facts in the prompt or use search grounding or URL context for anything later. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash) |
| For thinking models, response pricing is the sum of output tokens and thinking tokens. In stateless mode, resend all thought blocks exactly as received from the model. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
