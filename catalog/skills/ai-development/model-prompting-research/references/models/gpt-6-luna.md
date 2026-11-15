# Prompting Profile: gpt-6-luna

**Platform**: openai
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["gpt-6-luna"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Set reasoning effort on gpt-6-luna to one of none, low, medium (default), high, xhigh or max. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-6-luna) |
| Use the Responses API for built-in tools and function calling with gpt-6-luna. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-6-luna) |
| In Chat Completions, gpt-6-luna supports function calling only when reasoning_effort is none. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-6-luna) |
| When reasoning effort is not none, remove temperature, top_p and top_logprobs from the request. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-luna) |
| When migrating a request that uses minimal reasoning effort to GPT-6 models, start with low and compare results on representative tasks. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-luna) |
| To change reasoning effort between responses, use configuration_update input items in single-agent requests. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-luna) |
| When migrating from GPT-5.5 or earlier, replace prompt_cache_retention with prompt_cache_options.ttl set to "30m". | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-luna) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
