# Prompting Profile: gemini-3.5-transcribe-live

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.5-transcribe-live"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Call gemini-3.5-transcribe-live through the Live API (Google Gen AI SDK client.aio.live.connect, ai.live.connect in JavaScript, or a raw WebSocket BidiGenerateContent setup message with model 'models/gemini-3.5-transcribe-live') and set response modalities to TEXT. It is a dedicated low-latency speech recognition pipeline, not a conversational agent. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-transcribe) |
| Send audio as raw 16-bit PCM, 16 kHz, mono, little-endian with MIME type audio/pcm;rate=16000, in roughly 100 ms chunks (1,024 to 2,048 frames), and signal the end of input with audio_stream_end. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-transcribe) |
| Leave language_codes omitted or empty ([]) to have the model auto-detect language and handle multilingual speech; pass BCP-47 hints such as es-ES or fr-FR only to bias recognition. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-transcribe) |
| Choose the transcription mode explicitly: VERBATIM (default) gives a literal transcript including filler words and false starts; SMART removes disfluencies and applies formatting, grammar and casing. SMART mode cannot be combined with word annotations. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-transcribe) |
| Render interim_input_transcription (speculative partial hypotheses updated while the speaker talks) for live subtitles, and store input_transcription (the finalized transcript emitted on pause or turn completion) as the committed text. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-transcribe) |
| Voice activity detection has three modes: automatic server-side (default), hybrid (server speech-start detection plus a client audioStreamEnd signal for faster finalization), and manual push-to-talk (set automatic_activity_detection.disabled to true and send activity_start/activity_end). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-transcribe) |
| Live transcription sessions support continuous streaming for up to 10 minutes per session, so long audio must be split across sessions. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-transcribe) |
| Speaker diarization and word-level timestamps are not supported on gemini-3.5-transcribe-live (only utterance-level timestamps are emitted); use the non-streaming gemini-3.5-transcribe model for speaker labels or word timing. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.5-transcribe) |
| For browser or mobile clients, create a short-lived ephemeral token on the server with auth_tokens.create, constrained via live_connect_constraints to this model, rather than shipping an API key. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/live-transcribe) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
