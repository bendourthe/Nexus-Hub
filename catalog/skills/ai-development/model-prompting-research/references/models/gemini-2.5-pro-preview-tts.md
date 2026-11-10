# Prompting Profile: gemini-2.5-pro-preview-tts

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-2.5-pro-preview-tts"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Model gemini-2.5-pro-preview-tts takes text input only and produces audio output only; input token limit is 8,192 and output token limit is 16,384. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-pro-preview-tts) |
| Do not rely on Thinking, Function calling, Structured outputs, Caching, Search grounding, Code execution, URL context or the Live API with gemini-2.5-pro-preview-tts: the model page lists all of these as not supported. Supported: audio generation and the Batch API. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-pro-preview-tts) |
| gemini-2.5-pro-preview-tts is positioned for long-form content, professional narration and complex creative workflows (studio-quality speech synthesis). | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-pro-preview-tts) |
| gemini-2.5-pro-preview-tts has a listed earliest shutdown date of November 17, 2026, with recommended replacements gemini-3.8-flash-tts or gemini-3.8-flash-lite-tts; plan migration, since the page says these are the earliest possible retirement dates and exact dates will be communicated in advance. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/deprecations) |
| gemini-2.5-pro-preview-tts supports single-speaker and multi-speaker generation but not voice design, voice replication or voice remixing (those require the Gemini 3.8 TTS models). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| When migrating from gemini-2.5-pro-preview-tts to Gemini 3.8 TTS, separate delivery style from the transcript: put acting and pacing directions in the speech metadata style field, keep the text as a verbatim transcript with inline tags, send each speaker line as its own content item with a speaker label, use angle-bracket inline vocal tags such as laugh or short pause, each written inside angle brackets, and expect default audio/wav output on unary requests. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
