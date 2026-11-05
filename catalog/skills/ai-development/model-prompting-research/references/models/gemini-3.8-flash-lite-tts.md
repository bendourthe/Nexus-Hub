# Prompting Profile: gemini-3.8-flash-lite-tts

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.8-flash-lite-tts"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Call gemini-3.8-flash-lite-tts through the Interactions API (client.interactions.create or POST /v1beta/interactions) with response_format={"type": "audio"}; speech_config takes an array for one speaker (e.g. [{"voice": "Kore"}]) and an object with speakers for multiple speakers. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| Treat the text field as a verbatim transcript: put delivery direction and speaker labels in speech_metadata (speaker and style on each text block or part), not inline in the text, because inline directions such as 'Say cheerfully:' may be read aloud. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-flash-lite-tts) |
| Use angle-bracket tags (for example short pause, sigh and laugh, each written inside angle brackets) only for momentary vocal events and pauses; put sustained styles such as whispering in speech_metadata.style. Keep tags to human vocalizations and write them in English even for non-English transcripts. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| Do not rely on this model for features it does not support: the model page lists thinking, function calling, structured outputs, caching, Live API, search grounding and code execution as not supported; supported are audio generation, Batch API, Flex inference and Priority inference. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-flash-lite-tts) |
| Input is text only with an 8,192-token limit, and output is audio with a 16,384-token limit (Gemini API serving limit); split long responses into shorter turns, with one TTS call per turn for voice agents and without resending a long persona. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-flash-lite-tts) |
| Unary requests return WAV (audio/wav, 24 kHz mono 16-bit PCM with a 44-byte RIFF header) by default, unlike gemini-3.1-flash-tts-preview which returned headerless PCM; remove manual WAV wrapping, or request audio/l16, audio/mulaw or audio/alaw (AUDIO_L16 etc. in generateContent) for headerless output. Streaming returns headerless audio/l16 by default; sample_rate accepts 24000, 16000 or 8000. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| In multi-speaker requests set speaker on every turn, matching a configured speaker; a single request supports at most 2 speakers and only with prebuilt voices (for custom voices, synthesize each turn separately and concatenate the audio). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| Replace long style blocks with a custom designed voice (reference its voice_... ID) and a minimal or empty style string; do not put age, gender or permanent accent in style, and avoid meta-instructions like 'maintain identical timbre', which tend to increase voice drift. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |
| Prompt by writing transcripts as people speak (natural disfluencies), test plain synthesis with empty style first, then add short style strings only where needed; pacing can also come from punctuation, ellipses and dashes, and capitalized words add emphasis. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/speech-generation) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
