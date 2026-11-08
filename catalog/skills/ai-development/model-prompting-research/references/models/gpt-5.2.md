# Prompting Profile: gpt-5.2

**Platform**: codex
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.2"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| reasoning.effort accepts none, low, medium, high, xhigh for gpt-5.2; none is the default. If more thinking is needed, increase slowly to medium and test. With none, prompt the model to outline its steps before answering. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2) |
| temperature, top_p and logprobs are only supported with gpt-5.2 when reasoning effort is none; sending them with any other effort setting errors. Use reasoning effort, verbosity and max_output_tokens to steer instead. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2) |
| Use the Responses API with gpt-5.2 so the previous turn's chain of thought is passed between turns (fewer reasoning tokens, higher cache hit rates, lower latency); passing CoT exists only in Responses, not Chat Completions. gpt-5.2 is served on Chat Completions, Responses and Batch. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2) |
| The verbosity parameter (low, medium, high) is retained for gpt-5.2 and defaults to medium; low reduces output tokens and latency, and verbosity can still be steered in the prompt after setting it to low. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2) |
| Migrate to gpt-5.2 by switching the model without changing the prompt, pinning reasoning_effort to match the prior model (GPT-4o/4.1 start at none; GPT-5 keeps its value except minimal becomes none; GPT-5.1 keeps its value), running evals, and tuning prompts only if results regress, one change at a time. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| gpt-5.2 is more concise and plan-forward than GPT-5.1 and needs the preferred output length stated in the prompt, for example 3-6 sentences or at most 5 bullets for typical answers, and two sentences or fewer for yes/no questions. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| gpt-5.2 may produce more code or UI than the minimal spec requires; constrain scope explicitly (for example 'implement EXACTLY and ONLY what the user requests', no extra features or invented styling). | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| For gpt-5.2 inputs over about 10k tokens, have the model build a short outline of relevant sections and restate key constraints before answering, anchoring claims to specific sections. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| gpt-5.2 takes more tool actions in interactive flows than GPT-5.1; prompting can reduce this. Parallelize independent reads, and a system/developer instruction can require a short explanation before each tool call (preambles). tool_choice with allowed_tools restricts the model to a subset of tools. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2) |
| For long, tool-heavy gpt-5.2 workflows, use POST /v1/responses/compact after major milestones rather than every turn, treat returned items as opaque, and keep prompts functionally identical when resuming. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| gpt-5.2 specs: 400,000-token context window, 128,000 max output tokens, text and image input with text-only output, snapshot gpt-5.2-2025-12-11, knowledge cutoff Aug 31, 2025; supports function calling, structured outputs, web search, file search, prompt caching, apply_patch and MCP tools in Responses. The page lists it as a previous flagship, and the deprecations page lists gpt-5.2-chat-latest (not gpt-5.2) for shutdown on Aug 10, 2026. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.2) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
