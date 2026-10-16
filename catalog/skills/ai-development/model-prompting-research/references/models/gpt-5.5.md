# Prompting Profile: gpt-5.5

**Platform**: codex
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| When migrating to GPT-5.5, start from a fresh, smaller baseline prompt instead of carrying over the older prompt stack (treat it as a new model family, not a drop-in replacement for gpt-5.2/5.4). | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |
| Write outcome-first prompts: state the expected outcome, success criteria, allowed side effects, evidence rules, and output shape rather than prescribing a step-by-step process. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |
| Omit step-by-step process instructions unless the exact execution path genuinely matters. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |
| Reserve absolute language (ALWAYS/NEVER) for true invariants such as safety rules, required output fields, or forbidden actions. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |
| Do not inject the current date into GPT-5.5 prompts; the model already knows the current UTC date. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |
| Use reasoning effort medium (the new default) as the starting point and raise it only when evals show a measurable quality gain. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |
| Give explicit stopping rules for evidence gathering: use the minimum sufficient evidence, cite it precisely, then stop; treat retrieval budgets as stopping rules. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |
| Instruct the model that missing evidence is not by itself grounds for a factual 'no' answer. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |
| Because GPT-5.5 defaults to an efficient, direct style, explicitly specify personality (tone, warmth) separately from collaboration style when a different voice is needed, and use headers/bold/lists sparingly. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |
| Request a short preamble when a task may be multi-step, require tool calls, or run as a long agent workflow. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
