# Prompting Profile: gemini-3.8-flash-high

**Platform**: antigravity
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.8-flash-high"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Do not tune temperature, top_p, or top_k for Gemini 3.8 Flash; remove them from requests. | `high` | `model-specific` | not recorded | [source](https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8) |
| To control determinism, use thinking_level together with a response_schema or json_schema, not sampling parameters (the backend ignores those). | `high` | `model-specific` | not recorded | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash) |
| Choosing a level: use the low thinking level for latency-critical tasks. | `high` | `model-specific` | not recorded | [source](https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8) |
| Choosing a level: keep the default medium level for complex code and agentic work. | `high` | `model-specific` | not recorded | [source](https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8) |
| Choosing a level: use the high thinking level for deep reasoning, mathematics, and difficult multi-step tasks. | `high` | `model-specific` | not recorded | [source](https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8) |
| Choosing a level: Gemini 3.8 Flash uses more tokens on long, complex tasks by design, so lower the reasoning effort for everyday tasks. | `high` | `model-specific` | not recorded | [source](https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8) |
| Choosing a level: do not request the minimal thinking level. Gemini 3.8 Flash supports only low, medium (the default), and high, and minimal returns an error. | `high` | `model-specific` | not recorded | [source](https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8) |
| Do not prefill model turns or end the conversation history with a model-role turn. Remove prefilled turns when upgrading. | `high` | `model-specific` | not recorded | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash) |
| In function calling, if Malformed_Function_Call errors are tied to text before a tool call, clean up the leading commentary that comes before tool calls. | `high` | `model-specific` | not recorded | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash) |
| In function responses, separate inline instructions with blank lines (\n\n) and place multimodal assets inside the response payload. | `high` | `model-specific` | not recorded | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
