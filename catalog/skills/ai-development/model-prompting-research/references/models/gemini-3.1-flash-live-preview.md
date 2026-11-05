# Prompting Profile: gemini-3.1-flash-live-preview

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.1-flash-live-preview"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Set reasoning with thinkingConfig.thinkingLevel (minimal, low, medium, high) instead of thinkingBudget; the default is minimal, chosen to optimize for lowest latency, so raise the level only when more reasoning is needed. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-live-preview) |
| Function calling is synchronous only: the model does not respond until the client sends the tool response. Async function calling (NON_BLOCKING behavior, scheduling) is not supported on this model. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/tools) |
| The client must handle tool calls manually and reply with a list of FunctionResponse objects; the Live API does not answer tool calls automatically. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/tools) |
| Google Search grounding is supported through the session configuration; Google Maps grounding, code execution and URL context are not supported on this model. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/tools) |
| Do not configure proactive audio or affective dialogue on this model (not yet supported); remove those settings when migrating from gemini-2.5-flash-native-audio-preview-12-2025. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-live-preview) |
| A single BidiGenerateContentServerContent event can contain multiple parts (for example audio chunks plus transcript), so client code must process every part in each event rather than only the first. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-live-preview) |
| Use send_client_content to add text or structured context mid-session and to seed history (initial_history_in_client_content in history_config); use send_realtime_input to stream text, audio or video. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-live-preview) |
| Caching, Batch API, structured outputs, code execution, file search, image generation and URL context are not supported; token limits are 131,072 input and 65,536 output; inputs are text, images, audio and outputs are text and audio. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-live-preview) |
| The model is a legacy preview; for new and production apps Google recommends migrating to gemini-3.8-live, or gemini-3.8-live-extended-thinking when more background reasoning is needed. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-live-preview) |
| For Live API system instructions, write one per agent ordered as persona, conversational rules, guardrails; list rules in the order the model should follow them, describe each tool step in its own sentence, state conditions for invoking each tool, give if-x-then-y guardrail examples, and give an explicit output-language instruction. Prefer prompt chaining over long prompts, and add a prompt telling the model to greet the user first because the Live API waits for user input. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/live-api/best-practices) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
