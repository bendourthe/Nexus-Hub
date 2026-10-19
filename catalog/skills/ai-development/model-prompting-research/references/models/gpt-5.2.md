# Prompting Profile: gpt-5.2

**Platform**: codex
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.2"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Give GPT-5.2 explicit, concrete output-length limits (for example 3-6 sentences or at most 5 bullets by default), because it is steerable on verbosity and builds its own structure by default. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| Constrain scope explicitly: tell GPT-5.2 to implement exactly and only what was requested, with no extra features, and to pick the simplest valid reading of ambiguous instructions. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| For long inputs (above roughly 10k tokens), instruct GPT-5.2 to first outline the relevant sections and restate the user's constraints before answering (force summarization and re-grounding). | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| For ambiguous requests, instruct GPT-5.2 to either ask 1-3 precise clarifying questions or present 2-3 interpretations with labeled assumptions, and never fabricate exact figures, line numbers, or references when uncertain. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| GPT-5.2 takes more tool actions than GPT-5.1 in interactive flows; use prompting (tool usage rules) to reduce unnecessary calls, and tell it to parallelize independent reads. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| In tool-using prompts, require GPT-5.2 to briefly restate what changed, where, and what validation ran after any write or update tool call, and require verification for high-impact operations. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| For structured extraction, always supply a schema or JSON shape and instruct GPT-5.2 to set absent fields to null rather than guessing. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| When migrating to GPT-5.2, switch the model first without changing prompts, explicitly pin reasoning_effort to match the prior model's latency/depth profile (GPT-5.2 defaults to none), run evals, then tune prompts one change at a time. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) |
| With GPT-5.2 reasoning effort set to none, prompt quality matters more; if more thinking is needed, raise effort gradually toward medium and experiment. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2) |
| When using compaction with GPT-5.2 in long agent workflows, compact after major milestones rather than every turn, and keep prompts functionally identical when resuming to avoid behavior drift. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
