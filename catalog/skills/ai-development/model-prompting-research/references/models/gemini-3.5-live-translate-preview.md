# Prompting Profile: gemini-3.5-live-translate-preview

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.5-live-translate-preview"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Call this model only through the Live API as a continuous audio-to-audio interpreter pipeline; it does not wait for conversational turns, and it supports no tools, function calling, Google Search, or system instructions, so do not try to steer it with a prompt. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-translate) |
| Enable translation by adding translationConfig inside the session generation config, with responseModalities set to ["AUDIO"] and translationConfig.targetLanguageCode set to a BCP-47 code (default "en"; variants such as pt-BR, pt-PT, zh-Hans, zh-Hant). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-translate) |
| Set translationConfig.echoTargetLanguage to control speech already in the target language: true echoes it back, false (default) keeps the model silent for it. With echo true, background noise or music may add artifacts to the translated audio. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-translate) |
| Input must be raw 16-bit little-endian mono PCM at 16kHz with MIME type audio/pcm;rate=16000, sent in 100ms chunks for low latency; output is raw 16-bit mono PCM at 24kHz. Text input is not supported. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-translate) |
| To receive transcripts, add inputAudioTranscription and outputAudioTranscription (empty objects) to the session config; read them from serverContent.inputTranscription and serverContent.outputTranscription, and read translated audio from serverContent.modelTurn.parts[].inlineData. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-translate) |
| The model page lists these as not supported for gemini-3.5-live-translate-preview: thinking, function calling, structured outputs, caching, code execution, search grounding, Maps grounding, file search, URL context, Batch API, Flex and Priority inference. Do not send thinking settings or tool declarations. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.5-live-translate-preview) |
| Token limits for this model are 131,072 input and 65,536 output; it is preview-only and handles audio input with audio plus text (transcript) output. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.5-live-translate-preview) |
| In client-side apps use ephemeral tokens on the v1beta endpoint: include translationConfig in liveConnectConstraints to lock the target language, or omit it and set lock_additional_fields to [] so the client can choose the target language. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-translate) |
| Expect limitations: input language detection can struggle with heavy accents, similar languages (e.g. Spanish vs Portuguese) and rapid switching (mainly affecting the input transcript); output voice replication is inconsistent (voice may shift after pauses, be assigned the wrong gender, or stick on one voice in rapid multi-speaker talk); noise and music are filtered but not all background audio is ignored. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-translate) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
