# Prompting Profile: gpt-6.1-terra

**Platform**: openai
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["gpt-6.1-terra"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Set reasoning.effort to one of none, low, medium, high, xhigh, or max. gpt-6.1-terra supports all six values and defaults to medium. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-6.1-terra) |
| Start with reasoning effort medium and raise it only if the quality gain is worth the added time and tokens. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.1-terra) |
| Reasoning effort none is available on gpt-6.1-terra, unlike GPT-6 Astra and GPT-6.1 Sol. When migrating, keep the current effective effort where it is supported. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.1-terra) |
| When reasoning effort is not none, remove temperature, top_p, and top_logprobs from the request to gpt-6.1-terra. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.1-terra) |
| Use the Responses API (v1/responses) for tool calling with gpt-6.1-terra. Chat Completions is supported, but tools are only available through Responses, and the Assistants, Realtime, Embeddings, and fine-tuning endpoints are not supported. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-6.1-terra) |
| When migrating from GPT-5.6 Terra to GPT-6.1 Terra, compare both models at the same reasoning effort on representative images and workflows. The model is positioned for visual reasoning, precise computer use, and clear writing. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.1-terra) |
| gpt-6.1-terra accepts text and image input and produces text output only (no audio or video). It supports streaming, structured outputs, function calling, and prompt caching. Predicted outputs and fine-tuning are not supported. Context window is 1,050,000 tokens, max output is 128,000 tokens, and cached input costs 5% of the uncached input rate. Prompts over 272K input tokens are priced higher across the whole request. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-6.1-terra) |
| The GPT-6 family prompt-guidance prompts are a starting point across the GPT-6 family, but the page says they address behavior observed with GPT-6 Astra and must be evaluated with the chosen model and workload. Do not assume Astra-specific behaviors, such as heavy use of lists and Markdown or the skills and AGENTS.md instruction-following note, apply to Terra. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance) |
| Treat reasoning.effort as a tuning knob, not the primary way to recover quality. Supported values and defaults are model-dependent, so check the model page first. | `high` | `model-agnostic-candidate` | not recorded | [source](https://developers.openai.com/api/docs/guides/reasoning) |
| max_output_tokens includes reasoning tokens as well as visible output. If the limit is hit, the response status is incomplete, possibly before any visible output. OpenAI recommends reserving at least 25,000 tokens for reasoning and output. | `high` | `model-agnostic-candidate` | not recorded | [source](https://developers.openai.com/api/docs/guides/reasoning) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
