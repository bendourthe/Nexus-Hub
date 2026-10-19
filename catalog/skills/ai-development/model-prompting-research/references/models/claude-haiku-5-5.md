# Prompting Profile: claude-haiku-5-5

**Platform**: claude-code
**Last verified**: 2026-10-15
**Roster provenance**: `manual`

This file mirrors the `models["claude-haiku-5-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Use the effort parameter, not a thinking budget or a prompt instruction, to control how much Haiku 5.5 thinks. budget_tokens no longer exists for this model. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| To reduce thinking, lower the effort level instead of telling the model in the prompt to answer directly, because that prompt instruction did not suppress thinking. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| When the model has a search tool, put today's date in the system prompt or in the search tool's description. Avoid blanket 'always search' instructions, which cause extra searches without improving answers. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| Do not use blanket search instructions such as 'search for any present-day factual question'. In Anthropic's testing they triggered searches on half of the prompts that needed none and did not produce more correct answers. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| When thinking is off and JSON output is required, state in the system prompt that the JSON format applies only to the final answer and that tools are called first. Without this, the model can skip a tool call it needs. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| In long coding-agent system prompts, especially at low effort, add an explicit instruction to keep working until the task is done and to stop only when blocked or before a risky step. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| Tell coding agents to run a real check that exercises a change (tests, type-checker, build, or the changed command) before reporting it done. At low and medium effort the model sometimes skips this check. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| Send mid-task user input as a user turn, never inside a tool_result block. The model is trained to treat text in tool results as untrusted and may ignore it. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| For chatbots and support assistants, add a system prompt sentence saying its rules hold for the whole conversation, even when users push back. Use high effort when instruction following matters most. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| If reasoning-like text appears in user-facing replies, switch to adaptive thinking at medium effort instead of trying to fix it with prompt wording. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |
| Assistant prefill returns a 400 error, so replace each prefill: end messages with a user turn, ask for a direct answer in the system prompt, and put continuations and reminders in the user message. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) |
| A forced tool_choice skips thinking. To let the model think before it calls a tool, use tool_choice auto and say in the prompt when to use the tool. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) |
| Add the guide's suggested system prompt text to new conversations only. To change instructions partway through a conversation, put them in the newest turn, because changing system can return a 400 error when thinking blocks are sent back. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
