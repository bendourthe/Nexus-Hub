# Prompting Profile: gemini-2.5-pro

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-2.5-pro"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Call the model with the model string `gemini-2.5-pro`. It accepts audio, images, video, text and PDF as input and produces text only, with a 1,048,576-token input limit and a 65,536-token output limit. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-pro) |
| gemini-2.5-pro supports Batch API, caching, code execution, file search, Flex and Priority inference, function calling, Search grounding, Grounding with Google Maps, structured outputs, thinking and URL context. It does not support audio generation, image generation or the Live API, so do not request those from it. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-pro) |
| gemini-2.5-pro is deprecated and no longer selectable in Google AI Studio, and API access is limited to existing users. Effective December 1, 2026, requests to gemini-2.5-pro are automatically routed to gemini-3.8-flash and billed at Gemini 3.8 Flash rates, so update the model string before that date and review the Gemini 3.8 Flash migration guide. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-pro) |
| When migrating off gemini-2.5-pro, the page lists these breaking changes. Function calling and thought_signature validation change. thinking_level replaces thinking_budget. Sampling parameters are removed. Prefilled model turns are no longer supported. Do not carry prefilled model turns or sampling-parameter tuning over to the replacement. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-pro) |
| On thinking models, max_output_tokens counts thought tokens as well as the visible response. If the limit is reached during reasoning, the response can be truncated or empty, and the thinking tokens are still billed. Set the output cap with the thinking overhead in mind. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |
| Thinking tokens are billed together with output tokens, on the full thoughts generated rather than only the returned summaries. For gemini-2.5-pro the pricing page labels the output price row as including thinking tokens, so budget cost on output plus thinking. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/pricing) |
| Match thinking effort to task difficulty. Use minimal thinking for simple tasks such as fact retrieval or classification, default thinking for moderate tasks, and maximum thinking for complex tasks such as advanced coding or math. For lengthy outputs, prompt the model to think less to save tokens. Thought summaries are off by default and can be enabled to review failures and refine prompts. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |
| For gemini-2.5-pro, context caching (standard paid tier) is priced at $0.125 per 1M tokens for prompts up to 200k tokens and $0.25 above 200k, plus $4.50 per 1M tokens per hour of storage. It is not available on the free tier. Reuse large repeated prefixes through caching. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/pricing) |
| Prompts over 200k tokens are priced at a higher tier for gemini-2.5-pro. Standard is $2.50 input and $15.00 output per 1M tokens, against $1.25 and $10.00 at or below 200k. Keep prompts at or under 200k tokens where possible to avoid the higher rate. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/pricing) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
