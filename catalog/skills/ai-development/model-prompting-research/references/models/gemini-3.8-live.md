# Prompting Profile: gemini-3.8-live

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.8-live"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Do not send thinking settings for gemini-3.8-live: omit thinking_level and thinking_config from session setup (thinking_level is not supported; the model uses built-in interleaved reasoning with a fixed latency profile). For configurable reasoning use gemini-3.8-live-extended-thinking instead. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live) |
| Request AUDIO as the only response modality for gemini-3.8-live; if you need text, enable output_audio_transcription in the setup config instead of asking for text output. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live) |
| Do not set proactive_audio: false (or configure proactivity) on gemini-3.8-live: proactive audio is permanently enabled and disabling it returns an error. Remove enable_affective_dialog settings as well, since affective dialogue was removed. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/capabilities.md) |
| Function calling on gemini-3.8-live supports both synchronous (BLOCKING) and asynchronous (NON_BLOCKING) behavior; set the behavior on the function declaration explicitly, and use SILENT, WHEN_IDLE, or INTERRUPT scheduling in the FunctionResponse for non-blocking tools. The client must handle tool responses manually. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/tools.md) |
| On gemini-3.8-live, send_client_content works throughout the whole session with explicit user or model roles, and sending turn_complete=true unconditionally interrupts active generation. To seed prior history before streaming, set initial_history_in_client_content to true in history_config, and prefer a single summary message for long contexts. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/capabilities.md) |
| gemini-3.8-live defaults turn coverage to TURN_INCLUDES_AUDIO_ACTIVITY_AND_ALL_VIDEO, so all video frames are sent to the model by default; send video frames only when needed to manage context and cost. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live) |
| gemini-3.8-live does not support caching, code execution, file search, structured outputs, URL context, Google Maps grounding, image generation, or the Batch API; supported features are Live API, function calling, Search grounding, audio generation, and interleaved reasoning. Limits are 131,072 input and 65,536 output tokens; inputs are text, image, audio, and video-type frames per the page, outputs text and audio. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live) |
| Use gemini-3.8-live as the default for low-latency conversational voice agents where immediate turn-taking matters and reasoning delays are unwanted (fast tools such as reading sensor values); choose gemini-3.8-live-extended-thinking when higher background reasoning is needed. Migrating from gemini-3.1-flash-live-preview means changing the model string and applying the removals above. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/thinking.md) |
| Live API prompting: give each agent its own system instruction with name, role and persona; specify the output language whenever you specify an accent; tell the model the conditions under which each tool should be called (names, descriptions, parameters, invocation conditions); state tool calls in distinct sentences; and include examples of what the model should and should not do. Live API expects user input before responding, so include a prompt that asks it to greet the user to start the conversation. | `medium` | `model-agnostic-candidate` | not recorded | [source](https://aistudio.google.com/docs/live-api/best-practices.md) |
| Live API audio streaming: send small audio chunks (20ms-40ms recommended, up to 100ms), do not buffer input audio significantly, resample microphone input to 16kHz, discard the client audio buffer immediately on an interrupted server_content message, and use ContextWindowCompressionConfig for long sessions because native audio tokens accumulate quickly (without compression audio-only sessions are limited to 15 minutes, audio-video to 2 minutes). | `medium` | `model-agnostic-candidate` | not recorded | [source](https://aistudio.google.com/docs/live-api/best-practices.md) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
