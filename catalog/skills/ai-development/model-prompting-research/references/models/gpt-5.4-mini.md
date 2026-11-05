# Prompting Profile: gpt-5.4-mini

**Platform**: codex
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.4-mini"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| gpt-5.4-mini supports reasoning.effort values none (default), low, medium, high and xhigh. Because the default is none, set reasoning.effort explicitly whenever you need reasoning. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.4-mini) |
| gpt-5.4-mini is supported on Chat Completions, Responses and Batch endpoints. Tools (function calling, web search, file search, tool search, code interpreter, hosted shell, apply patch, skills, computer use, MCP) are listed under the Responses API. Realtime, Assistants, fine-tuning and embeddings are not supported. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.4-mini) |
| gpt-5.4-mini has a 400,000-token context window, max 272,000 input tokens and max 128,000 output tokens. It takes text and image input and produces text output only. The only listed snapshot is gpt-5.4-mini-2026-03-17. Prompt caching and structured outputs are supported. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.4-mini) |
| For gpt-5.4-mini, prompt for literal behavior. It is more literal, makes fewer assumptions and may ask follow-up questions unless told otherwise. Put critical rules first, specify the exact step order, separate 'do the action' from 'report the action', and define ambiguity behavior (ask, abstain or proceed) and packaging rules. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4#prompting-best-practices) |
| For gpt-5.4-mini, use scoped output-stop wording such as 'after the final JSON, output nothing further' rather than 'output nothing else'. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4#prompting-best-practices) |
| For smaller GPT-5.4 models, structure prompts in this order: task, critical rule, exact step order, edge cases or clarification behavior, output format, one correct example. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4#prompting-best-practices) |
| On the GPT-5.4 family, temperature, top_p and logprobs work only with reasoning effort none and other settings return an error. For similar control use reasoning.effort, text.verbosity or max_output_tokens. The page states this for GPT-5.4 and does not restate it for the mini model. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4#prompting-best-practices) |
| When migrating o4-mini or gpt-4.1-mini workloads, the documented starting point is gpt-5.4-mini. Treat reasoning effort as a last-mile tuning knob. Before raising effort, add completeness_contract, verification_loop and tool_persistence_rules prompt blocks, and avoid xhigh unless evals show a clear benefit. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4#prompting-best-practices) |
| For GPT-5.4, text.verbosity (low, medium, high) is configurable and defaults to medium. For long-running Responses agents that replay assistant history manually, preserve each original phase value (commentary or final_answer), and do not add phase to user messages. The page states this for GPT-5.4 and does not restate it for the mini model. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4#prompting-best-practices) |
| When calling reasoning models with function calling, use the Responses API and pass back the reasoning items returned with the last function call along with the function output, for example via previous_response_id. Reasoning tokens count against max_output_tokens and are billed as output tokens. Reserve at least 25,000 tokens for reasoning and output when starting out. | `medium` | `model-agnostic-candidate` | not recorded | [source](https://developers.openai.com/api/docs/guides/reasoning) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
