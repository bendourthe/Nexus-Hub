# Prompting Profile: gemini-3.8-flash-tts

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.8-flash-tts"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Gemini 3.8 TTS treats the text field strictly as a verbatim transcript, so inline directions such as 'Say cheerfully:' or 'Speaker 1:' may be read aloud. Put delivery direction in speech_metadata.style and speaker in speech_metadata.speaker instead of in the text. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-flash-tts) |
| Use angle-bracket tags (laugh, sigh, cough, breath, short pause and long pause, each written inside angle brackets) inline only for momentary vocal events and pauses; put sustained delivery (whispering, pacing, volume, emotion) in speech_metadata.style. Stick to human vocalizations rather than non-vocal sound effects, and use English tags even in non-English text. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| In multi-speaker requests, each turn must be its own content item carrying speech_metadata.speaker matching a configured speaker; do not use 'Speaker:' prefixes inside one text block. A single request supports at most 2 speakers and only with prebuilt voices; to mix custom voices, synthesize each speaker's turn separately and concatenate. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| Unary requests return audio/wav with a RIFF header (24 kHz, mono, 16-bit PCM) by default, unlike earlier TTS models that returned headerless audio/l16 PCM; do not add your own WAV header. Set response_format.mime_type to audio/l16, audio/mulaw or audio/alaw (AUDIO_L16/AUDIO_MULAW/AUDIO_ALAW in generateContent) for headerless formats; streamed chunks (stream: true) are headerless raw 16-bit LE PCM at 24 kHz mono. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-flash-tts) |
| Limits and unsupported features: text input up to 8,192 tokens, audio output up to 16,384 tokens; supports Batch API, Flex and Priority inference; does NOT support thinking, function calling, structured outputs, caching, search grounding, code execution, or Live API, so do not set thinking or tool parameters. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-flash-tts) |
| Start with an empty style and add a short style string only for turns that need adjustment. Avoid meta-instructions telling the model to hold the voice steady (they increase drift), and do not put immutable traits (age, gender, names, permanent accent) in style; choose a suitable voice or use Voice design for persistent personas instead of long Audio Profile/Director's Notes blocks. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| For natural pacing use commas, dashes and ellipses for hesitation, pause tags for exact timing, and style for overall speaking rate; capitalize specific words to add stress; write text as a realistic spoken transcript including disfluencies where appropriate. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| For voice agents, make one TTS call per turn, keep style empty or a single short constant string, and split long responses into shorter turns. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| Choose gemini-3.8-flash-tts over gemini-3.8-flash-lite-tts when maximum fidelity, acting nuance, dialect coverage (130 languages vs 101), complex multi-speaker dialogue, heavy vocal-burst tags, difficult pronunciation or long-form stability matter; Flash-Lite is the recommended replacement for gemini-3.1-flash-tts-preview. Both share the same API schema and prompting structure. Overlapping speech/backchannels (listener reactions wrapped in pipe characters inside a speaker turn) work best on gemini-3.8-flash-tts. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-flash-tts) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
