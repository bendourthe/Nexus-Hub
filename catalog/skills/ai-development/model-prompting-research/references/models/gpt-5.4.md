# Prompting Profile: gpt-5.4

**Platform**: codex
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.4"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| gpt-5.4 reasoning effort accepts none, low, medium, high, xhigh, and the default is none, so set reasoning effort explicitly when reasoning is needed. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.4) |
| Treat reasoning effort as a last-mile tuning knob: use none for execution-heavy work, medium or higher for research-heavy work, raise slowly from none to medium, and avoid xhigh as a default unless evals show clear benefit. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Before raising reasoning effort on gpt-5.4, first add completeness_contract, verification_loop and tool_persistence_rules blocks (sections wrapped in tags of those names) to the prompt; at effort none, ask the model to outline its steps before answering. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| temperature, top_p, and logprobs are supported on gpt-5.4 only when reasoning effort is none; requests including them at any other effort fail. Use reasoning effort, verbosity, and max_output_tokens instead. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| gpt-5.4 works best with the Responses API, which preserves prior reasoning between turns (fewer reasoning tokens, higher cache hit rates, lower latency); passing chain of thought exists only in Responses, and previous_response_id is the simplest multi-turn path. Responses uses nested reasoning.effort and text.verbosity; Chat Completions uses top-level reasoning_effort and verbosity. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| gpt-5.4 verbosity is configurable as low, medium, or high and defaults to medium; lower verbosity cuts output tokens and latency, and for code, low yields shorter code with minimal commentary while medium/high yield longer, more structured code. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| With gpt-5.4 in the Responses API, round-trip the phase parameter (commentary vs final_answer) on assistant messages when replaying history, never add phase to user messages; dropping it can cause preambles to be treated as final answers. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| For gpt-5.4 tool use: restrict callable tools via allowed tools in tool_choice (mode auto or required) while listing the full toolkit in tools to improve prompt caching; use tool search to defer tool loading; enable preambles with an instruction like 'Before you call a tool, explain why you are calling it.' | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| gpt-5.4 migration: it is meant as a drop-in replacement for gpt-5.2 with default settings; switch the model first, pin reasoning_effort, run evals, then change one thing at a time. Start with the smallest prompt that passes evals and add prompt blocks only for measured failures. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| gpt-5.4 has a 1,050,000-token context window and 128,000 max output tokens, supports Chat Completions, Responses, and Batch, and prompts over 272K input tokens are billed at 2x input and 1.5x output; pin the snapshot gpt-5.4-2026-03-05 for consistent behavior. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.4) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
