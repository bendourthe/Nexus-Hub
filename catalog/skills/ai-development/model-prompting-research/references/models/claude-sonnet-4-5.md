# Prompting Profile: claude-sonnet-4-5

**Platform**: claude-code
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["claude-sonnet-4-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Claude Sonnet 4.5 is deprecated (deprecated September 30, 2026) and retires on the Claude API on November 30, 2026; the recommended replacement is claude-sonnet-5-5. Use the dated ID claude-sonnet-4-5-20250929 (alias claude-sonnet-4-5) and plan migration before the retirement date. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/about-claude/model-deprecations) |
| Claude Sonnet 4.5 has a 200K-token context window and a 64K-token max output on the synchronous Messages API; the 300K Message Batches output extension is not available for it, and it has no effort parameter (default effort: not supported). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-4-5/overview) |
| On Claude Sonnet 4.5, a request with no thinking field runs with thinking off. Valid thinking.type values are "disabled" and "enabled" (extended thinking with budget_tokens); "adaptive" and "between_tools" return a 400 error. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking) |
| Claude Sonnet 4.5 uses thinking: {"type":"enabled","budget_tokens":N} for all thinking, and the default thinking display is "summarized" (thinking text is returned unless display is changed). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) |
| Claude Sonnet 4.5 accepts a prefilled last assistant turn (Claude Sonnet 4.6 and later reject it with a 400 error), so prefill still works on this model but should be replaced with structured outputs, system-prompt instructions, or user-turn continuations when migrating. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) |
| Claude Sonnet 4.5 features context awareness, which lets the model track its remaining context window (token budget) during a conversation. In a harness that compacts context or saves state to files, tell the model so, otherwise it may try to wrap up work as it nears the context limit. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| On Claude Sonnet 4.5, interleaved thinking between tool calls uses the beta header interleaved-thinking-2025-05-14, and fine-grained tool streaming uses the beta header fine-grained-tool-streaming-2025-05-14; both are removed or replaced (eager_input_streaming: true) when moving to Claude Sonnet 5.5. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) |
| Claude Sonnet 4.5 and later (4.5+) models keep trailing newlines in tool call string parameters and stop with the model_context_window_exceeded stop reason at the context window limit; handle the refusal stop reason as well. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) |
| Claude Sonnet 4.5 pricing is $3 / MTok input and $15 / MTok output, with cache reads at $0.30 / MTok, 5-minute cache writes at $3.75 / MTok and 1-hour cache writes at $6 / MTok; Batch API gives a 50% discount on input and output. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-4-5/overview) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
