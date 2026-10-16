# Prompting Profile: claude-sonnet-4-5

**Platform**: claude-code
**Last verified**: 2026-10-15
**Roster provenance**: `manual`

This file mirrors the `models["claude-sonnet-4-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| When running Claude Sonnet 4.5 in a harness that compacts context or saves state to external files, tell the model so in the prompt (Sonnet 4.5 is one of the context-aware models). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Without that harness information, a context-aware model such as Sonnet 4.5 may wrap up early near the context limit. Instruct it explicitly not to stop tasks early because of token budget concerns. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Do not add token-budget tags to Sonnet 4.5 prompts yourself. The API injects a 200k budget and per-tool-call usage warnings automatically, so prompts can refer to the budget but should not emulate it. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/context-windows) |
| On Sonnet 4.5, use manual extended thinking (type enabled with budget_tokens). Adaptive thinking returns a 400 error. Keep budget_tokens until the workload moves to a newer model. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) |
| Sonnet 4.5 runs without thinking when the thinking field is omitted. Enable it explicitly for complex tasks. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) |
| Size the Sonnet 4.5 extended-thinking budget to the task: at least the 1,024-token minimum, and 16,000+ tokens for complex tasks. Use batch processing above about 32k. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) |
| To let Sonnet 4.5 reason between tool calls, add the interleaved-thinking beta header. Its manual mode does not interleave automatically. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) |
| Sonnet 4.5 has no effort parameter. Control reasoning depth with budget_tokens and prompt wording, not output_config.effort. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) |
| Prefilling the last assistant turn is still a valid output-steering technique on Sonnet 4.5. Newer Sonnet models reject it. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
