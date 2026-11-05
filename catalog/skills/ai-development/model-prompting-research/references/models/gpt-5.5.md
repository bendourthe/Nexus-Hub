# Prompting Profile: gpt-5.5

**Platform**: codex
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| GPT-5.5 reasoning.effort supports none, low, medium (default), high and xhigh. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.5) |
| Use xhigh reasoning effort only for the hardest asynchronous agentic tasks; reserve none for latency-critical work without multi-step tool use, and for latency-sensitive workflows that still need tool use or planning test low before none. Raise effort only when evals show a measurable quality gain. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5) |
| Treat GPT-5.5 as a new model family to tune for, not a drop-in replacement: start from a fresh, minimal prompt, write outcome-first prompts with success criteria and stopping conditions, and cut step-by-step process guidance unless the path matters. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5) |
| text.verbosity defaults to medium for GPT-5.5; setting it to low gives more concise output than low did on GPT-5.4. Control answer length separately from reasoning quality using word budgets, section counts, or JSON-only output. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5) |
| Use the Responses API for reasoning, tool-calling and multi-turn use with GPT-5.5; use previous_response_id for multi-turn state, or for stateless/Zero Data Retention flows pass back the returned output items each turn. When replaying assistant items manually keep each phase value unchanged (commentary for intermediate updates, final_answer for the completed answer) and never add phase to user messages. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5) |
| Avoid absolute language such as ALWAYS and NEVER for judgment calls in GPT-5.5 prompts (reserve it for true invariants); remove output schema definitions from the prompt and use Structured Outputs instead; do not add the current date since the model knows the current UTC date. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5) |
| For GPT-5.5 tool use, put most tool-specific guidance in the tool descriptions rather than the system prompt, prefer OpenAI-hosted tools where they fit, and use tool search to load only relevant definitions for large tool catalogs. | `medium` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5) |
| For multi-step or tool-heavy GPT-5.5 tasks, ask for a brief user-visible preamble of one or two sentences before tool calls that states the first step, which improves time to first visible token. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5) |
| For GPT-5.5 prompt caching, put stable content first and dynamic user-specific content last, set a stable prompt_cache_key for requests sharing a prefix (spreading busy groups across multiple keys), and track usage.prompt_tokens_details.cached_tokens to measure reuse. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5) |
| gpt-5.5 has a 1,050,000-token context window and 128,000 max output tokens, is served on Chat Completions, Responses and Batch endpoints (not Realtime or Assistants), and prompts over 272K input tokens are billed at 2x input and 1.5x output for the full session. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/models/gpt-5.5) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
