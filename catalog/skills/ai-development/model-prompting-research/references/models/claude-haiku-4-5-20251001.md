# Prompting Profile: claude-haiku-4-5-20251001

**Platform**: claude-code
**Last verified**: 2026-10-15
**Roster provenance**: `manual`

This file mirrors the `models["claude-haiku-4-5-20251001"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Configure thinking on Claude Haiku 4.5 with manual extended thinking (thinking.type "enabled" plus budget_tokens); it does not support adaptive thinking. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-4-5/overview) |
| Do not migrate Haiku 4.5 requests to thinking type "adaptive" (it returns a 400); keep budget_tokens until you move to a model that supports adaptive thinking. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) |
| Steer Haiku 4.5 reasoning depth with budget_tokens, not the effort parameter: effort is not supported on this model, and on extended-thinking-only models budget_tokens sets thinking depth. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting) |
| When tuning the extended-thinking budget, start simple tasks near the 1,024-token minimum and raise it step by step; start complex tasks at 16,000 tokens or more. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) |
| Do not design Haiku 4.5 agent loops to rely on reasoning between tool calls: the model does not support interleaved thinking, and the interleaved-thinking beta header is ignored. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) |
| Haiku 4.5 has context awareness. In a harness that compacts context or saves state to files, say so in the prompt so the model does not wrap up early as it nears the context limit. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Do not write your own token-budget tags into Haiku 4.5 prompts: context awareness is automatic, and the API injects the 200k budget and the remaining-token updates. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/context-windows) |
| Assistant prefill is a valid output-steering technique on Haiku 4.5 only when thinking is off. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) |
| For applications that may be asked about medicine doses, add the medication-dosing block written for Claude Haiku 4.5 to the system prompt, exactly as written. Do not reuse the block written for another model. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Size image inputs for Haiku 4.5's standard image tier: images above 1,568 pixels on the long edge, or 1,568 visual tokens, are downscaled. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
