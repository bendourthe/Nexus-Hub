# Prompting Profile: gemini-3.1-flash-tts-preview

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.1-flash-tts-preview"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Treat gemini-3.1-flash-tts-preview as a legacy preview model: for new and production workloads, migrate to gemini-3.8-flash-tts (quality) or gemini-3.8-flash-lite-tts (high volume, low cost). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-tts-preview) |
| Send text-only input and expect audio-only output. Input token limit is 8,192 and output token limit is 16,384 for this model. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-tts-preview) |
| Do not rely on thinking, function calling, structured outputs, caching, code execution, search grounding, URL context, or the Live API with this model; the per-model page lists all of them as not supported. Audio generation and the Batch API are supported. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-tts-preview) |
| The model supports expressive audio tags for controlling narration (steerable prompts); the per-model page refers to the Text-to-Speech guide's controllable-speech section for syntax. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-tts-preview) |
| Both single-speaker and multi-speaker generation are supported by 3.1 Flash TTS Preview, but voice design, voice replication and voice remixing are not supported for it. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| Multi-speaker generation supports at most 2 speakers using prebuilt voices (limitation stated for TTS multi-speaker requests on the speech generation page). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation?generate-content=true) |
| On unary requests this model returns headerless raw PCM (audio/l16) by default, unlike the 3.8 models which return WAV; handle or decode raw PCM accordingly, and set audio/l16 explicitly in a 3.8 migration if the pipeline expects headerless audio. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| Earlier preview models including 3.1 took stage directions embedded in plain text, and multi-speaker scripts as 'Speaker: ...' prefixes in one text block; when migrating to 3.8, move acting and pacing directions into speech_metadata.style and use one content item per speaker turn. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
