# Prompting Profile: claude-haiku-4-5-20251001

**Platform**: claude-code
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["claude-haiku-4-5-20251001"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Claude API model ID is claude-haiku-4-5-20251001 (pinned snapshot); claude-haiku-4-5 is a convenience alias that resolves to it. Context window is 200K tokens and max output is 64K tokens (synchronous Messages API). Haiku 4.5 is labeled Legacy; Claude Haiku 5.5 is the current Haiku model. Researched under the alias claude-haiku-4-5; this dated snapshot is the same model. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-4-5/overview) |
| Haiku 4.5 uses manual extended thinking (thinking: {type: "enabled", budget_tokens: N}), not adaptive thinking; the effort parameter is not supported on it (default effort listed as 'Not supported'). Researched under the alias claude-haiku-4-5; this dated snapshot is the same model. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-4-5/overview) |
| For Haiku 4.5 extended thinking, budget_tokens must be at least 1,024 and less than max_tokens (thinking tokens count toward max_tokens). Start near 1,024 for simple tasks and 16,000+ for complex tasks; for budgets above 32k use batch processing. Changing budget_tokens between requests invalidates message-level prompt cache breakpoints, so hold the budget stable across a cached conversation. Researched under the alias claude-haiku-4-5; this dated snapshot is the same model. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) |
| Sending thinking: {type: "adaptive"} to Haiku 4.5 returns a 400 error; keep budget_tokens on this model. Haiku 4.5 does not support interleaved thinking (the interleaved-thinking-2025-05-14 beta header is accepted but ignored on the Claude API), and the API strips previous turns' thinking blocks from history when they are passed back. Researched under the alias claude-haiku-4-5; this dated snapshot is the same model. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) |
| Haiku 4.5 pricing is $1 per MTok input and $5 per MTok output; 5m cache write $1.25/MTok, 1h cache write $2/MTok, cache read $0.10/MTok; Batch API gives a 50% discount. Reliable knowledge cutoff is Feb 2025 and training data cutoff is Jul 2025. Researched under the alias claude-haiku-4-5; this dated snapshot is the same model. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-4-5/overview) |
| Lifecycle: claude-haiku-4-5-20251001 is listed as Active (legacy) with tentative retirement not sooner than October 15, 2026 on Anthropic-operated platforms; Anthropic gives at least 60 days' notice before retirement. Anthropic recommends considering migration to claude-haiku-5-5. Researched under the alias claude-haiku-4-5; this dated snapshot is the same model. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/about-claude/model-deprecations) |
| Existing Haiku 4.5 prompts should perform well on Haiku 5.5 without changes. Where Haiku 4.5 ran without thinking or with a small budget_tokens to save tokens, use a lower effort level on Haiku 5.5 instead. Researched under the alias claude-haiku-4-5; this dated snapshot is the same model. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
