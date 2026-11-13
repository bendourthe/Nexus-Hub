# Prompting Profile: claude-sonnet-4-6

**Platform**: claude-code
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["claude-sonnet-4-6"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Use the exact model ID claude-sonnet-4-6 on the Claude API (Bedrock InvokeModel uses anthropic.claude-sonnet-4-6). Context window is 1M tokens, max synchronous output is 128K tokens (up to 300K on the Message Batches API with the output-300k-2026-03-24 beta header). The model is Legacy (released Feb 17, 2026); retirement is not sooner than Feb 17, 2027, and Anthropic recommends considering migration to claude-sonnet-5-5. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-4-6/overview) |
| Sonnet 4.6 defaults to high effort on the API. Set output_config.effort explicitly to avoid unexpected latency; medium is the documented recommended default for most applications (agentic coding, tool-heavy workflows, code generation), low for high-volume or latency-sensitive work, high for complex reasoning, and max is available on this model for the deepest reasoning. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| Thinking is off on Sonnet 4.6 when the thinking field is omitted. Enable adaptive thinking explicitly with thinking: {"type": "adaptive"}, steered by the effort parameter. thinking.type values accepted are adaptive, disabled, and enabled (deprecated). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking) |
| Manual extended thinking (thinking: {"type": "enabled", "budget_tokens": N}) is still functional on Sonnet 4.6 but deprecated. Prefer adaptive thinking with a lower effort level, or max_tokens as a hard limit, for cost control; budget_tokens returns a 400 error on Claude 4.7 and later models, so do not build new code around it. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Do not prefill the last assistant turn on Sonnet 4.6: it is rejected with a 400 error ("This model does not support assistant message prefill. The conversation must end with a user message."). Use other means to control output format. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) |
| Default thinking display on Sonnet 4.6 is "summarized", so thinking blocks return readable summary text without setting display; its first lines of thinking output are more verbose than on newer models. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking) |
| Sonnet 4.6 supports context awareness: the model tracks its remaining context window (token budget) through a conversation, which helps it run long tasks and manage context. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Pricing for Sonnet 4.6 is $3 per MTok input and $15 per MTok output, with cache reads at $0.30 per MTok and a 50 percent Batch API discount. Reliable knowledge cutoff is Aug 2025. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-4-6/overview) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
