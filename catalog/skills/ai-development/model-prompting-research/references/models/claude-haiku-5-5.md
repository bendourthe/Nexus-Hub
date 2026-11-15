# Prompting Profile: claude-haiku-5-5

**Platform**: claude-code
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["claude-haiku-5-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Use the effort parameter as the main control for how much Claude Haiku 5.5 thinks (it replaces budget_tokens). Default is medium; use low for chat, short tool tasks and high-volume simple requests; high for knowledge work, longer agent tasks and strict instruction following; xhigh and max only when evals justify the cost. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| Send thinking as {"type":"adaptive"} (or omit it) with output_config.effort; thinking {"type":"enabled","budget_tokens":N} returns a 400 error. thinking {"type":"disabled"} works only at low, medium and high effort; at xhigh and max it returns a 400 error. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) |
| Omit temperature, top_p and top_k for Claude Haiku 5.5 (they can return an error) and guide behavior through prompting instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) |
| Assistant message prefill is rejected with a 400 error even with thinking off; end messages with a user turn and use structured outputs, tools with enum fields, or system-prompt instructions instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) |
| Thinking tokens count toward max_tokens (up to 128,000 synchronous output), so a max_tokens value sized for Haiku 4.5 without thinking can cut off the reply; leave room for thinking or lower effort. Select response content blocks by type, not position, because responses can begin with thinking blocks. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| When giving the model a search tool, supply today's date in the system prompt or tool description; at low effort or with long system prompts, add a nudge that training data ends before today's date and to search for changeable facts. Avoid blanket 'always search' instructions, which caused searches on half of prompts needing none. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| With thinking off and structured outputs (output_config.format), the model may skip a needed tool call; use adaptive thinking for such requests, remove output_config.format where a tool call is required, or force the call with tool_choice (forced tool_choice yields a response starting with the tool call and no thinking block). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| In long coding-agent system prompts at low effort the model can stop early; add instructions to keep working until everything asked is done, and raise effort (low to medium roughly halved early stopping). At low and medium effort it may report code changes done without running a check, so instruct it to run a real check (tests, type-check, build) before reporting done. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| Deliver mid-turn user messages as a user turn text block after the last tool_result, never inside a tool_result block, because the model is trained to resist prompt injection through tool results and may ignore it. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| Keep conversations append-only (system, tools and earlier messages unchanged) when sending Haiku 5.5 thinking blocks back; changing earlier turns can return a 400 error (default on accounts created on or after August 31, 2026). Thinking blocks are valid only in the producing (or linked) account, and thinking text is omitted by default unless thinking.display is set to "summarized". | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) |
| Claude Haiku 5.5 uses the newer tokenizer (about 30 percent more tokens than Haiku 4.5 for the same text), so recount tokens with model set to claude-haiku-5-5; minimum cacheable prompt length is 512 tokens; long prompts over 100,000 tokens are billed at higher prices. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-5-5/whats-new-haiku-5-5) |
| Requests can return stop_reason "refusal" from safety classifiers (stop_details.category: cyber, frontier_llm, bio, general_harms); there is no server-side fallback, so handle refusals in the client and do not simply resend the same request. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
