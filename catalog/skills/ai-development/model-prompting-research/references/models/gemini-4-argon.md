# Prompting Profile: gemini-4-argon

**Platform**: gemini
**Last verified**: 2026-10-28
**Roster provenance**: `api`

This file mirrors the `models["gemini-4-argon"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| The Gemini API supports low, medium and high thinking_level values; medium is the default, and workload evaluations compare all three levels. Vendor behavior only; project effort floors, raise-only rules and spend caps still apply. | `high` | `model-specific` | `model` | [source](https://ai.google.dev/gemini-api/docs/latest-model) |
| Custom temperature, top_p and top_k values do not affect Argon generation. | `high` | `model-specific` | `model` | [source](https://ai.google.dev/gemini-api/docs/latest-model) |
| Cloud requests with frequency_penalty, presence_penalty or candidate_count return HTTP 400. | `high` | `model-specific` | `model` | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-argon) |
| Thinking tokens consume max_output_tokens; reducing thinking_level limits reasoning cost without truncating the response through a small output cap. No output-cap increase or effort downshift is authorized by this profile. | `high` | `model-specific` | `model` | [source](https://ai.google.dev/gemini-api/docs/generate-content/thinking) |
| Legacy Gemini Generate Content migration guidance recommends max_output_tokens of at least 32,768. Recommendation scoped to Legacy Generate Content, subject to existing application output and spending limits. | `high` | `model-specific` | `model` | [source](https://ai.google.dev/gemini-api/docs/generate-content/latest-model) |
| Cloud requires FunctionResponse values to match the preceding FunctionCall id, name and order; Cloud guidance discourages unstructured prose before tool calls. | `high` | `model-specific` | `model` | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-argon) |
| Cloud chat history cannot finish with a model role turn, and prefilled model turns are unsupported. | `high` | `model-specific` | `model` | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-argon) |
| Gemini API explicit caching is unsupported; implicit caching is enabled by default with a minimum input of 4,096 tokens. | `high` | `model-specific` | `model` | [source](https://ai.google.dev/gemini-api/docs/caching) |
| Cloud explicit caching is unsupported; static prefix content of at least 6,144 tokens qualifies for implicit caching. | `high` | `model-specific` | `model` | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-argon) |
| Interactions output exceeding 65,536 tokens requires background execution; other long-running calls use background execution or an HTTP client timeout of at least 15 minutes. Interactions surface only; not a Cloud timeout recommendation. | `high` | `model-specific` | `model` | [source](https://ai.google.dev/gemini-api/docs/latest-model) |
| Legacy Gemini Generate Content guidance specifies an HTTP client timeout of at least 20 minutes per call. Legacy Generate Content surface only; not an Interactions or Cloud timeout recommendation. | `high` | `model-specific` | `model` | [source](https://ai.google.dev/gemini-api/docs/generate-content/latest-model) |
| Legacy Gemini Generate Content accepts thinking_budget alone with a warning and maps it to a thinking_level; combining both controls returns HTTP 400. | `high` | `model-specific` | `model` | [source](https://ai.google.dev/gemini-api/docs/generate-content/thinking) |
| Cloud thinking_budget requests return HTTP 400; thinking_level is the supported reasoning control. | `high` | `model-specific` | `model` | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-argon) |
| The cyber-permissive variant is reserved for Fairwind-approved cybersecurity workloads. Allowlist-only variant; excluded from public routing and this catalog-derived roster. | `high` | `model-specific` | `model` | [source](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-argon) |
| Before a long autonomous run, confirm access to the required tools and documentation and agreement on the intended result. User-supplied PDF, page 8, tip 1, third bullet. This is a candidate for broader use, not evidence of a model-specific advantage or cross-model effectiveness. The actual tip 2 on page 9 concerns verification. | `medium` | `model-agnostic-candidate` | `cited-page` | [source](https://aistudio.google.com/learn/gemini-4-argon-developer-guide) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
