# Prompting Profile: claude-opus-5-5

**Platform**: claude-code
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["claude-opus-5-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Adaptive thinking is always on for claude-opus-5-5. Send no thinking field or thinking {type: adaptive}. thinking {type: disabled} and thinking {type: enabled, budget_tokens: N} are rejected with a 400 invalid_request_error. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| Control thinking depth only through output_config.effort. All five levels (low, medium, high, xhigh, max) are supported. The default is medium (Claude Opus 5 defaulted to high), so set effort explicitly and re-run an effort sweep on your own evals rather than carrying over an Opus 5 setting. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| max_tokens is a hard limit on thinking plus response text. At a given effort level Opus 5.5 tends to think more per turn than Opus 5, especially at xhigh and max. Set max_tokens high; start at 64k when running xhigh or max, and 128,000 (the model maximum) has worked well for long agentic coding turns. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| Forced tool use is rejected with a 400 error: tool_choice {type: any} and {type: tool, name: ...} are not supported. Use tool_choice auto (default) or none; for schema-valid JSON use strict: true strict tool use or structured outputs, and state in the prompt when a tool applies. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5) |
| Omit temperature, top_p and top_k, and do not end messages with a prefilled assistant turn (it is rejected). Use prompting, structured outputs, or system prompt instructions to shape behavior instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| Responses can begin with thinking blocks, so read content by block type rather than position (not content[0].text). In tool-use loops, return thinking blocks complete and unmodified (including empty ones); edited, reordered or dropped thinking blocks cause a 400 error. thinking.display defaults to omitted (empty thinking field); set display summarized to get readable summaries. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| Text the model writes between tool calls comes back as progress-update thinking blocks, empty at the default display, so a client rendering only text blocks goes quiet. Set thinking.display to updates (beta, header thinking-display-updates-2026-08-18) or summarized to receive them. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| Changing the top-level effort value between requests invalidates the prompt cache. To change effort mid-conversation while keeping the cache, use the per-message effort change (beta). Keep the conversation append-only: editing the system prompt, tools or earlier turns invalidates earlier thinking blocks, so use mid-conversation system messages instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| If an Opus 5 integration ran with thinking disabled, start at low effort and measure (move to medium if quality drops), remove instructions asking the model to write its reasoning into the response, and read reasoning from summarized thinking blocks. Prompts pushing reasoning into response text may be declined with the reasoning_extraction refusal category. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| For unattended agent loops, a text-only end_turn can be a progress report rather than completion. Keep a task checklist, send a follow-up user message naming open items, cap automatic continuations at two or three, and optionally add a system prompt paragraph naming the early-stop patterns to avoid (set from the first request of the session to keep the cache and thinking blocks valid). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| Computer use must be declared with the computer_toolset_20260801 toolset with no beta header; computer_20251124 returns a 400 on the Claude API (it still works on Amazon Bedrock with the computer-use-2025-11-24 beta header). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5) |
| claude-opus-5-5 has a 1M-token context window with no context-window beta header needed, 128K max output (300K on the Message Batches API with the output-300k-2026-03-24 beta header), a 512-token minimum cacheable prompt, and fast mode via speed: fast on the Claude API with no beta header. Pricing is $4 input / $20 output per MTok. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/overview) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
