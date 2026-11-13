# Prompting Profile: gemini-2.5-flash-lite

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-2.5-flash-lite"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Call the model with the code gemini-2.5-flash-lite (stable). The preview code gemini-2.5-flash-lite-preview-09-2025 is shut down and must not be used. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-lite) |
| Size requests to the documented limits: input token limit 1,048,576 and output token limit 65,536. Accepted inputs are text, image, video, audio and PDF; output is text only (no audio or image generation, no Live API). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-lite) |
| The model supports Batch API, caching, code execution, file search, flex inference, function calling, Grounding with Google Maps, priority inference, search grounding, structured outputs, thinking and URL context, so these tool and API features can be used with it. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-lite) |
| Thinking is Off by default for gemini-2.5-flash-lite, unlike gemini-2.5-flash and gemini-2.5-pro which are On. To get reasoning, set a thinking level explicitly; the thinking page lists low, medium and high as the supported levels for this model. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |
| The thinking page controls thinking through the thinking_level parameter; it does not document thinking_budget (0 to disable or -1 for dynamic) for this model, so do not assume budget semantics from this page. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |
| When thinking is turned on, response pricing is the sum of output tokens and thinking tokens; read total thinking tokens from the total_thought_tokens field when budgeting cost. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |
| For a stateless tool-using flow, resend the tool result signatures (including those for built-in tools such as Google Search) in subsequent turns. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |
| Always include few-shot examples in prompts, keep their structure and formatting identical, and do not include too many because the model may overfit to the examples. Instructions can be removed if the examples already show the task clearly. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/prompting-strategies) |
| Give clear, specific instructions, state constraints and the desired response format, supply the needed context rather than assuming the model has it, and for complex JSON schemas use the API's structured output feature. Break complex prompts into one prompt per instruction. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/prompting-strategies) |
| The model's knowledge cutoff is January 2025, so enable search grounding when recent or obscure facts are needed. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-2.5-flash-lite) |
| Access to the 2.5 models is limited to users who have actively used them before. gemini-2.5-flash-lite is not deprecated and is served until further notice, but for new projects the page recommends 3.5 Flash-Lite or 3.8 Flash. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
