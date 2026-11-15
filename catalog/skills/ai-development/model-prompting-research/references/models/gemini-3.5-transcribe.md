# Prompting Profile: gemini-3.5-transcribe

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.5-transcribe"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Use model ID gemini-3.5-transcribe for unary (file) transcription of prerecorded audio; use the separate ID gemini-3.5-transcribe-live for real-time streaming over the Live API (WebSockets). In REST it appears as models/gemini-3.5-transcribe. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.5-transcribe) |
| Call the model through the Interactions API (a POST to the v1beta interactions endpoint on generativelanguage.googleapis.com, or client.interactions.create in the SDKs), uploading audio first with the Files API and passing the file as input. The transcription guide documents only the Interactions API for this model and does not mention generateContent. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/transcribe) |
| Control transcription through generation_config.transcription_config (camelCase transcriptionConfig in JavaScript), not through a prompt: the guide documents no prompt or system-instruction field for transcription. Fields are language_codes, custom_vocabulary and mode. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/transcribe) |
| Set transcription_config.language_codes (BCP-47, for example es-ES) when the language is known; omit it or pass [] for automatic detection, which also handles intra- and inter-sentence code-switching across 85+ languages. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/transcribe) |
| mode defaults to verbatim (word-for-word, keeps filler words, repetitions and false starts). Set mode to "smart" for a reading-optimized transcript that removes disfluencies, resolves spoken self-corrections and applies formatting (lists, dates, currencies, numbers). Timestamps and diarization require verbatim mode; smart mode cannot be combined with timestamps or diarization. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/transcribe) |
| For word timing use mode = {"type":"verbatim","timestamp_granularities":["word"]}; for speaker labels use mode.diarization_mode = "speaker" (up to 8 speakers; attribution for 3 or more speakers is experimental). Word data is returned in steps[].content[].annotations[] with type word_info (text, speaker, start_offset, end_offset). Word-level timestamps may degrade overall transcription accuracy, so enable them only when needed. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/transcribe) |
| custom_vocabulary accepts up to 1,000 terms to bias recognition, with best results at about 100 or fewer distinctive terms (not common words). It cannot be combined with diarization or word timestamps, and the API rejects requests that try. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/transcribe) |
| Unary requests accept audio up to 1 hour, reduced to 30 minutes when speaker diarization or word-level timestamps are enabled; the live model is limited to 10 minutes per session. Supported input MIME types include wav, mp3, aiff, aac, ogg, flac, mpeg, m4a, l16, opus, alaw, mulaw and webm; use the Files API for recordings longer than a few seconds and prefer clean recordings without severe clipping. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/transcribe) |
| The model page lists thinking, function calling, caching, code execution, file search and image generation as not supported, and Batch API, Flex inference and Priority inference as not available consumption options, so do not set thinking or tool configuration or rely on context caching or batch mode for this model. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.5-transcribe) |
| The live model gemini-3.5-transcribe-live does not support word-level timestamps or speaker diarization; those are file-endpoint features only, while language auto-detection, custom vocabulary (up to 1,000 terms) and smart dictation/formatting work on both endpoints. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.5-transcribe) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
