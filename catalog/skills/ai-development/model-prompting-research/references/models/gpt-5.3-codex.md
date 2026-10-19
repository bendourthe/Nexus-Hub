# Prompting Profile: gpt-5.3-codex

**Platform**: codex
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["gpt-5.3-codex"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Use medium reasoning effort as the default for interactive coding with gpt-5.3-codex, and raise it to high or xhigh only for the hardest tasks. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| When reconstructing conversation history for gpt-5.3-codex, persist each assistant output item's phase value (commentary or final_answer) and send it back in later requests. Dropping it degrades performance. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| Never attach the phase field to user messages. It belongs only on assistant items. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| With gpt-5.3-codex, mid-rollout preambles and progress updates can be prompted, which earlier Codex models did not allow. Prompt for a short acknowledgement and plan before any tool calls. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| Prompt for a regular update cadence: about every 1 to 3 execution steps, and never more than 6 steps or 10 tool calls without an update. Keep most updates to 1 or 2 sentences. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| Tell the model to carry the task through to completion within the current turn, including implementation and verification, rather than stopping at analysis or a partial fix. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| Tell the model to maximize parallel tool calls, for example batching file reads, rather than calling tools one at a time. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| Tell the model to use a dedicated tool when one exists for the action, instead of raw shell commands. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| Tell the model to skip the planning tool for simple tasks, never to write single-step plans, and to reconcile every stated plan or TODO before finishing. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |
| Truncate tool output returned to the model to about 10k tokens (estimated as bytes divided by 4), keeping half the budget for the beginning and half for the end. | `high` | `model-specific` | not recorded | [source](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
