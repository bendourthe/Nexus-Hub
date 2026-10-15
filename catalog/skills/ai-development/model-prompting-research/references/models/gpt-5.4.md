# Prompting Profile: gpt-5.4

**Platform**: codex
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.4"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Early in a session, when there is little context, tell GPT-5.4 the prerequisites and dependencies explicitly. Its tool routing can be less reliable at that stage. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Add a dependency-check rule: resolve prerequisite steps before taking the final action, even when that action looks obvious. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| For long-horizon or batch tasks, add a completeness contract: the task stays incomplete until every requested item is covered or explicitly marked [blocked]. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Add tool-persistence rules: keep calling tools while another call is likely to improve correctness, and retry with a different strategy when results are empty or partial. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Treat reasoning effort as a last-mile tuning knob. Before raising it, add completeness_contract, verification_loop and tool_persistence_rules prompt blocks, and default to none, low or medium. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Migrate to GPT-5.4 one change at a time: switch the model string first, pin reasoning_effort, run evals, then iterate on prompts. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| Prefer prompt-only upgrades with small, targeted prompt blocks, and avoid broad prompt cleanup unrelated to the upgrade. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/upgrading-to-gpt-5p4) |
| Only request parallel tool calls for independent retrieval or lookup steps. Never parallelize steps where one result determines the next. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| In research workflows, tell the model to cite only sources retrieved in the current workflow and never fabricate citations, URLs, IDs or quote spans. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |
| For gpt-5.4-mini, put critical rules first and define explicitly when to ask, abstain or proceed, because the model is more literal and makes fewer assumptions. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
