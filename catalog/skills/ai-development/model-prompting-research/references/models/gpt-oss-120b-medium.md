# Prompting Profile: gpt-oss-120b-medium

**Platform**: antigravity
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["gpt-oss-120b-medium"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Always prompt gpt-oss-120b in the harmony response format. Raw or other chat templates are unsupported and degrade behavior. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| Set reasoning effort with a line such as 'Reasoning: medium' in the system message, not in the developer or user message. Medium is the default when the line is omitted. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| Put task instructions (what other APIs call the 'system prompt') in the harmony developer message under an '# Instructions' heading. Keep the system message for identity, reasoning level, channels and built-in tools. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| In multi-turn conversations, remove earlier assistant turns' chain-of-thought (analysis channel) from the prompt. The exception is tool or function calling, where the prior CoT must be passed back in. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| Define every custom function in the developer message using harmony's TypeScript-like syntax inside a 'functions' namespace, following the format exactly to keep function calls accurate. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| Declare built-in tools such as browser and python in a '# Tools' section of the system message. They do not go in the developer message. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| For structured output, put the response format at the end of the developer message. Because the prompt only influences the model, enforce the schema with a grammar during sampling. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| Show end users only final-channel messages. Do not show analysis-channel chain-of-thought unfiltered, because it is not held to the same safety standards. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/articles/openai-harmony) |
| Put constraints that must not be overridden in the higher-priority role. The model resolves conflicts as System > Developer > User > Assistant > Tool. | `high` | `model-specific` | not recorded | [source](https://deploymentsafety.openai.com/gpt-oss) |
| Choose the reasoning level (for example medium) for each use case to balance quality against latency and cost. Higher levels make the chain-of-thought longer on average. | `high` | `model-specific` | not recorded | [source](https://deploymentsafety.openai.com/gpt-oss) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
