# Prompting Profile: gemini-3-flash-preview

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3-flash-preview"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Set reasoning effort for gemini-3-flash-preview with thinking_level; the supported values are minimal, low, medium and high. The model thinks by default at high ('On (high)'), so set a lower level explicitly when you want lower cost or latency. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |
| Do not set max_output_tokens too low on a thinking model. The model can stop while it is still reasoning and return truncated or empty output. To cut cost or latency, lower thinking_level instead of squeezing max_output_tokens. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking?generate-content=true) |
| Match thinking effort to the task. Use minimal for simple lookups or classification, the default for moderate comparisons, and maximum effort for advanced coding, math or multi-step planning. For lengthy outputs, prompt the model to think less to save tokens. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking?generate-content=true) |
| Thought summaries are off by default for this model (only the final output is returned). Set thinking_summaries to 'auto' to receive them, then read them to understand failures and refine prompts. Write client code that tolerates a thought step with a signature but an empty or missing summary. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking?generate-content=true) |
| In stateless Interactions API use, resend all thought blocks and built-in tool steps (for example Google Search) unchanged in the history, and do not remove or modify them. In stateful mode (store: true with previous_interaction_id) the server preserves signatures automatically. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |
| For function calling with Gemini 3 series models (the series gemini-3-flash-preview belongs to), the SDKs handle thought signatures automatically. In stateless mode, pass back all model-generated steps from the earlier turn, including thought and function_call steps, exactly as received. Gemini 3 series models can also take multimodal content in function response parts and can combine built-in tools with function calling in Interactions. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/function-calling) |
| gemini-3-flash-preview takes text, image, video, audio and PDF input and returns text only. Its input limit is 1,048,576 tokens and its output limit is 65,536 tokens. It supports function calling, structured outputs, code execution, search grounding, URL context, computer use, caching, batch, flex and priority inference, file search and Maps grounding. It does not support the Live API or audio or image generation. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3-flash-preview) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
