# Prompting Profile: gemini-3.1-flash-lite

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-3.1-flash-lite"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Call the model with the stable id gemini-3.1-flash-lite. The preview id gemini-3.1-flash-lite-preview was shut down on May 25, 2026 (GA released May 7, 2026), so migrate any requests using the preview id to the stable id. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/changelog) |
| Use gemini-3.1-flash-lite for straightforward, high-volume, low-latency, cost-sensitive tasks (translation, audio transcription, lightweight agentic tasks with structured JSON output, document parsing and summarization, model routing); the page says it 'is best at handling straightforward tasks at significant scale', so route harder tasks to a larger model. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-lite) |
| Plan around the documented limits: input up to 1,048,576 tokens, output up to 65,536 tokens; inputs may be text, image, video, audio and PDF, but output is text only. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-lite) |
| Do not rely on Live API, computer use, image generation or audio generation with this model; the model page lists them as not supported. Supported: function calling, structured outputs, thinking, code execution, search grounding, Grounding with Google Maps, URL context, file search, caching, Batch API, Flex and Priority inference. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-lite) |
| Control reasoning through the thinking config (e.g. thinking_level='high') so the model spends extra compute on internal reasoning before the final output, for tasks that benefit from step-by-step reasoning. The model page does not document the default level or the supported level list for this model, so set thinking_level explicitly and test rather than assuming a default. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-lite) |
| For output-only tasks such as translation, constrain the output with a system instruction; the model page's example uses 'Only output the translated text'. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-lite) |
| The model suits a cheap classifier/router in front of larger models: the model page says the Gemini CLI uses Flash-Lite to classify task complexity and route to Flash or Pro accordingly. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-3.1-flash-lite) |
| To cut cost or latency on thinking models, lower thinking_level (low or medium) instead of setting a small max_output_tokens, and use minimal thinking for fact retrieval or classification. The page frames this as general guidance but its model table has no row for gemini-3.1-flash-lite, so apply it as a candidate. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/thinking) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
