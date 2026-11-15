# Prompting Profile: gpt-oss-120b-medium

**Platform**: antigravity
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gpt-oss-120b-medium"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Call gpt-oss-120b through the Responses API (v1/responses) or Batch (v1/batch); Chat Completions, legacy Completions, Realtime, Assistants and Fine-tuning are listed as not supported for this model on its model page. Researched as gpt-oss-120b; Antigravity runs it at medium reasoning effort. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-oss-120b) |
| Reasoning effort is configurable at three levels: low, medium, and high. The model page lists the levels but no API parameter name or default. Researched as gpt-oss-120b; Antigravity runs it at medium reasoning effort. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-oss-120b) |
| Tools supported for gpt-oss-120b (Responses API only) are function calling, code interpreter, MCP, and web search. Streaming and structured outputs are also supported. Context window and max output are both 131,072 tokens, and the knowledge cutoff is June 1, 2024. Researched as gpt-oss-120b; Antigravity runs it at medium reasoning effort. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-oss-120b) |
| When prompting the raw open-weight model directly, always use the harmony format; gpt-oss should not be used without it. Use the openai-harmony renderer to build prompts. Roles are system, developer, user, assistant and tool, with priority in that order. Researched as gpt-oss-120b; Antigravity runs it at medium reasoning effort. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| Set reasoning effort in the system message with the line 'Reasoning: low', 'Reasoning: medium' or 'Reasoning: high'. The default is medium. Put task instructions and function definitions in the developer message, not the system message, and keep the system identity line ('You are ChatGPT, a large language model trained by OpenAI.'). To change the identity, use the developer message. Researched as gpt-oss-120b; Antigravity runs it at medium reasoning effort. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| Do not show the analysis channel (chain-of-thought) to end users, because it is not held to the same safety standards. Only the final channel carries the user-facing answer. Function tool calls go to the commentary channel. Researched as gpt-oss-120b; Antigravity runs it at medium reasoning effort. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| In multi-turn use, drop prior chain-of-thought once the assistant has finished a turn on the final channel. During tool calling, pass the previous chain-of-thought back with the tool call and tool result until a final response is reached. Researched as gpt-oss-120b; Antigravity runs it at medium reasoning effort. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| Define function tools in the developer message under '# Tools' as a TypeScript-like 'namespace functions' block. Built-in browser and python tools are defined in the system message instead. Add a '# Response Formats' section with a JSON Schema to the developer message for structured output; this only influences the model, so enforce the schema during sampling. Researched as gpt-oss-120b; Antigravity runs it at medium reasoning effort. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| The raw chain-of-thought must be returned by the API and fed back on subsequent sampling during tool use, so the model receives it until it reaches a final response. In the Responses API it travels as a reasoning_text element in the reasoning item's content array, and these items are inserted back into the harmony prompt on later turns. Researched as gpt-oss-120b; Antigravity runs it at medium reasoning effort. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/gpt-oss/verifying-implementations) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
