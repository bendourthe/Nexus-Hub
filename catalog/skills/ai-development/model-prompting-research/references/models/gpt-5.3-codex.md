# Prompting Profile: gpt-5.3-codex

**Platform**: codex
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.3-codex"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Call gpt-5.3-codex through the Responses API (v1/responses). The model page lists Chat Completions, Assistants, Batch, Realtime, Fine-tuning and Embeddings as not supported. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.3-codex) |
| gpt-5.3-codex accepts reasoning effort values low, medium, high and xhigh. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.3-codex) |
| Use medium reasoning effort as the all-around default for interactive coding with gpt-5.3-codex. Reserve high or xhigh for the hardest tasks. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| When using gpt-5.3-codex, store each assistant output item with its phase value (null, commentary or final_answer) and send it back in later requests. phase is supported only on assistant items, so do not add it to user messages. The guide says correct implementation is required, and dropping it causes significant performance degradation. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| For preambles, prompt gpt-5.3-codex to give a 1-sentence acknowledgment and a 1-2 sentence plan before any tool calls. Keep most updates to 1-2 sentences, aim for an update every 1-3 execution steps, and never go more than 6 steps or 10 tool calls without one. Mid-rollout updates are promptable for this model, unlike earlier Codex models. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| gpt-5.3-codex supports function calling, hosted shell, skills and web search as Responses API tools. It also supports streaming, structured outputs, image input and prompt caching, with a 400k context window, 272k max input and 128k max output. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.3-codex) |
| Prompt caching is supported for gpt-5.3-codex, and cached input is billed at $0.175 per 1M tokens against $1.75 for uncached input. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.3-codex) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
