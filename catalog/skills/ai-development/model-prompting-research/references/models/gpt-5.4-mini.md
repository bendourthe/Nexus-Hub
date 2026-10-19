# Prompting Profile: gpt-5.4-mini

**Platform**: codex
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.4-mini"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Write prompts for gpt-5.4-mini that are longer and more explicit than prompts for larger models. State missing steps, how to resolve ambiguity, and how to package the output directly, because the model is less likely to infer them. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Put the critical rules at the top of the prompt. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| When tool use or side effects matter, specify the full execution order step by step instead of leaving the workflow implied. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Give separate instructions for doing an action and for reporting on it. Show the correct flow, not only the final output format. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Define explicitly what the model should do when input is ambiguous: when to ask, when to abstain, and when to proceed. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Specify output packaging directly: answer length, citation style, section order, and whether to ask a follow-up question. By default, gpt-5.4-mini may end with a follow-up question unless the prompt explicitly suppresses it. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Avoid the blanket instruction "output nothing else". Use a scoped termination instruction tied to a concrete point in the output instead. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Structure gpt-5.4-mini prompts with this default pattern, in order: task, critical rule, exact step order, edge cases or clarification behavior, output format, one correct example. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Avoid implied next steps, unspecified edge cases, schema-only prompts for tool workflows, and generic instructions without structure. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
