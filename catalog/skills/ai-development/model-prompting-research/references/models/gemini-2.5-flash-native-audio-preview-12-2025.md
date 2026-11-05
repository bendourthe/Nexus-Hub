# Prompting Profile: gemini-2.5-flash-native-audio-preview-12-2025

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-2.5-flash-native-audio-preview-12-2025"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Control reasoning on this model with thinkingBudget (a thinking token budget); thinkingLevel is the setting for the 3.x Live models, not for 2.5 Flash Live. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/capabilities) |
| Affective dialog is supported on Gemini 2.5 Flash Live only: set enable_affective_dialog to true in the session config and use the v1beta API version. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/capabilities) |
| Proactive audio is configurable on Gemini 2.5 Flash Live: set proactive_audio to true inside the proactivity config under v1beta so the model can decide not to respond to irrelevant input. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/capabilities) |
| The model supports function calling, search grounding, thinking and audio generation, and does not support caching, code execution, structured outputs, URL context, file search, Google Maps grounding, image generation or the Batch API; do not plan on those features. Limits: 131,072 input tokens and 8,192 output tokens. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-native-audio-preview-12-2025) |
| Native audio output models only support the AUDIO response modality; to get text, enable output_audio_transcription in the setup config (the transcription language is inferred from the model's response). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/capabilities) |
| Native audio models choose the output language automatically and do not accept an explicit language code; restrict the languages the model speaks through the system instructions instead. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/capabilities) |
| Function calling on 2.5 Flash Live supports both synchronous and asynchronous calls; send_client_content is supported throughout the conversation for incremental content updates, and each server event carries only one content part. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/capabilities) |
| Input audio is raw little-endian 16-bit PCM (16 kHz default, other rates allowed if declared in the MIME type) and output is always 24 kHz PCM; the native audio context window is 128k tokens, and audio-only sessions are limited to 15 minutes (audio plus video 2 minutes) unless session management or context compression is used. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/capabilities) |
| The model waits for user input at session start, so include a greeting prompt or trigger content to make it speak first; add an explicit output-language directive in the system instruction, order the system instruction persona then conversation rules then guardrails, and describe each tool step in its own sentence. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/best-practices) |
| Native audio accumulates about 25 tokens per second, so enable context compression for long sessions; keep the latest session resumption token (valid 2 hours) and handle GoAway timeLeft to reconnect. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/best-practices) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
