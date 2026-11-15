# Prompting Profile: gemini-3.8-live-extended-thinking

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.8-live-extended-thinking"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Set thinking_config in the session setup with thinking_level of low, medium, or high; MINIMAL is not supported on gemini-3.8-live-extended-thinking. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live-extended-thinking) |
| Declare every function with behavior NON_BLOCKING; only asynchronous function calling is supported, and synchronous blocking calls return an error. The SILENT, WHEN_IDLE and INTERRUPTED scheduling options are not supported on this model. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live-extended-thinking) |
| turnComplete: true no longer means the model is idle. Keep listening for tool calls and audio frames after it arrives, and read interaction_status on BidiGenerateContentServerContent (IN_PROGRESS means processing, background reasoning or awaiting async tool responses; IDLE means all work is done) before closing the session. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live-extended-thinking) |
| Proactive audio is always on for this model; setting proactive_audio to false returns an error. Remove any enable_affective_dialog settings because affective dialogue was removed from the API. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live-extended-thinking) |
| send_client_content works throughout the session (seeding history and mid-turn updates) with explicit user or model roles; setting turn_complete=true immediately interrupts active generation. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live-extended-thinking) |
| Model limits and capabilities: 131,072 input tokens and 65,536 output tokens; supports Live API, thinking, search grounding, audio generation and async function calling; does not support Batch API, caching, code execution, file search, Google Maps grounding, image generation, structured outputs or URL context. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.8-live-extended-thinking) |
| Choose gemini-3.8-live-extended-thinking when background reasoning is needed (multi-step diagnostics, coordinated data retrieval, STEM and code tutoring, masking long tool latency); for low-latency conversational voice without reasoning delays use gemini-3.8-live, which does not take thinking_level. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/thinking) |
| The model can speak intermediate conversational fillers while it reasons or tools run; turnComplete ends an utterance while interaction_status governs session lifecycle, so return the client to idle only when status is IDLE. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/thinking) |
| Async function calling is required on gemini-3.8-live-extended-thinking; the Live API does not handle tool responses automatically, so the client must send FunctionResponse objects (with call id, name, response) via send_tool_response. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/tools) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
