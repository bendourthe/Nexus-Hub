# Prompting Profile: gemini-3.1-pro-preview

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.1-pro-preview"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Gemini 3.1 Pro (gemini-3.1-pro-preview) supports thinking_level values low, medium and high; minimal is not offered for this model. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking.md) |
| The default thinking setting for gemini-3.1-pro-preview is On (high); lower thinking_level to reduce cost or latency. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking.md) |
| max_output_tokens counts thought tokens, so a low limit can truncate responses; the page recommends lowering thinking_level instead to cut cost or latency. Billing is based on the full thought tokens generated, not just the returned summary. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking.md) |
| In stateless use of the Interactions API, all thought blocks (with their signatures) must be resent exactly as received; in stateful mode (store true with previous_interaction_id) the server manages signatures. Thought summaries are opt-in via thinking_summaries. | `medium` | `model-agnostic-candidate` | not recorded | [source](https://aistudio.google.com/docs/thinking.md) |
| gemini-3.1-pro-preview takes text, image, video, audio and PDF input and returns text only, with 1,048,576 input and 65,536 output token limits. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-pro-preview) |
| gemini-3.1-pro-preview supports function calling, structured outputs, code execution, search grounding, URL context, file search, caching and the Batch API; it does not support the Live API, image generation or audio generation. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-pro-preview) |
| For agentic work that mixes bash with custom tools (for example view_file and search_code), use the variant gemini-3.1-pro-preview-customtools, which prioritizes custom tools but may show quality fluctuations in use cases that do not benefit from such tools. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-pro-preview) |
| Gemini 3 models respond best to direct, well-structured prompts that define the task and constraints, and are direct and efficient by default, so conversational or detailed output must be requested explicitly. The page is written for Gemini 3 models and does not name 3.1 Pro. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/prompting-strategies.md) |
| For long context with Gemini 3, supply all context first and put the specific question or instructions at the very end, using a clear transition phrase; put behavioral constraints, persona and output format in the system instruction or at the start of the user prompt. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/prompting-strategies.md) |
| For earlier Gemini 3 models, keep temperature, top_p and top_k at their default values to avoid degraded reasoning performance (Gemini 4 and 3.6+ models ignore them). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/prompting-strategies.md) |
| Gemini 3.1 Pro Preview has a minimum of 4,096 input tokens for caching; implicit caching is on by default for Gemini 2.5 and newer models, and placing large common content at the start of the prompt and sending similar-prefix requests close together improves cache hits. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/caching.md) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
