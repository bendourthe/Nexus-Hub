# Prompting Profile: gpt-6-astra

**Platform**: codex
**Last verified**: 2026-09-05
**Roster provenance**: `api`

This file mirrors the `models["gpt-6-astra"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Primary source |
|---|---|---|---|
| Callers that used the none or minimal reasoning effort should start with low and compare results; GPT-6 Astra does not support the none reasoning effort. Confirmed verbatim on the guide and in the 2026-09-03 changelog entry on the second, refutation-oriented fetch. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| When an application changes reasoning effort between responses in a standard single-agent request, use configuration_update items rather than a new conversation. Guide: 'If your application changes effort between responses, use configuration_update items in standard, single-agent requests.' The changelog adds that effort can change mid-conversation while preserving cached prompt prefixes. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| Chat Completions is supported, but tool calling requires the Responses API. Guide: 'GPT-6 Astra supports Chat Completions, but tool calling requires Responses.' Changelog: 'Tool calling requires the Responses API.' | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| Async tools are enabled by setting async: true on a function or custom tool and returning the result when ready using the original call_id. Confirmed on the guide; the changelog lists async tool calling among the long-running-work controls. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| Remove temperature, top_p, and top_logprobs from requests; the model does not accept custom sampling parameters or log probabilities. Guide: 'Remove temperature, top_p, and top_logprobs.' Changelog: no custom temperature or top_p values or log probabilities. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| Fast mode carries no latency SLA, and service_tier fast is not supported with EU data residency. Guide: 'Fast mode for GPT-6 Astra does not include a latency SLA' and does not support service_tier fast with EU data residency. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| Replace prompt_cache_retention with prompt_cache_options.ttl set to 30m. Confirmed verbatim on the guide. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| Treat a user prompt that requests action, such as one phrased 'can you...', as an instruction to do the work rather than a question about capability. The platform-agnostic form of this rule landed in the v4.7.0 Autonomous Operation block with this page cited as a second source; this claim records the vendor's own statement for this model. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| The user's instructions take precedence over guidelines provided in a skill. Adopted platform-agnostically in the v4.7.0 Autonomous Operation block; recorded here as the vendor statement for this model. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| Do not write tests for reversible, low-impact changes that mirror the implementation. Adopted platform-agnostically as the test-scope restraint rule owned by minimal-construction; recorded here as the vendor statement for this model. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| The vendor instructs the model to parallelize work by delegating tasks to another agent whenever it can. Recorded and deliberately NOT adopted into any shared body: the catalog's agent-orchestration-primitives overrides it with the named-problem escalation gate. | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) |
| Released September 3, 2026 as the vendor's most capable model for the hardest end-to-end work; the models catalog lists it among the flagship models with no access gate on 2026-09-05. Changelog 2026-09-03: 'Released GPT-6 Astra, our most capable model, built for the hardest end-to-end work.' The Codex CLI's live enumeration (codex debug models) did not list this id on 2026-09-05; see the v4.7 known-gaps ledger. Changelog: https://developers.openai.com/api/docs/changelog | `high` | `model-specific` | [source](https://developers.openai.com/api/docs/models) |

## Does not apply to shared bodies

Every claim in this file is scoped to the model named in the H1. It must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one, and `scripts/check_base_template_parity.py` fails the build when such a line diverges across the templates.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
