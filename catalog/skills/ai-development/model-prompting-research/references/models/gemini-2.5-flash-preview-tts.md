# Prompting Profile: gemini-2.5-flash-preview-tts

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-2.5-flash-preview-tts"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Send text only as input and expect audio only as output; the model is a text-to-speech model whose supported capability is audio generation. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-preview-tts) |
| Keep each request within the model's token limits: input is capped at 8,192 tokens and output at 16,384 tokens. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-preview-tts) |
| Do not rely on thinking, function calling, structured outputs, code execution, caching, Batch API, Live API, Search grounding, URL context, file search, Google Maps grounding or image generation with this model; the model page lists all of them as not supported. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-preview-tts) |
| Use this model for low-latency, cost-efficient speech synthesis such as real-time assistants, high-volume narration and conversational use cases, where fine-grained control over voice style and pacing is needed. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-preview-tts) |
| Plan migration: the deprecations page lists gemini-2.5-flash-preview-tts (released May 20, 2025) with a shutdown date of November 17, 2026 (stated as the earliest possible date) and recommends gemini-3.8-flash-tts or gemini-3.8-flash-lite-tts as replacements. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/deprecations) |
| Do not apply the Gemini 3.8 TTS prompting pattern (Interactions API with response_format and generation_config.speech_config, style in speech_metadata.style, text as verbatim transcript) to this model. The current speech guide says earlier preview models, including gemini-2.5-pro-preview-tts, take stage directions embedded in plain text, and it does not document the 2.5 Flash TTS API shape. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
