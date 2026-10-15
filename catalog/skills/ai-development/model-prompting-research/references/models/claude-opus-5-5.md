# Prompting Profile: claude-opus-5-5

**Platform**: claude-code
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["claude-opus-5-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Set the effort parameter explicitly, starting at medium (the Opus 5.5 default; Opus 5 defaults to high), and test several levels on your own evals instead of carrying over the Opus 5 setting. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| To reduce thinking, cost, or latency, lower the effort level first; it works more reliably than prompt instructions asking for less deliberation. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| Set max_tokens high enough for thinking tokens plus the reply (128,000, the model maximum, has worked well for long agentic coding turns), because thinking counts toward max_tokens even when it is not returned. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| Remove prompt instructions that ask the model to write out its reasoning in the response; set thinking display to summarized and read the reasoning from thinking blocks, since such requests may be declined with the reasoning_extraction refusal category. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| Consider removing chat system-prompt instructions that tell the model to think carefully before answering; effort is the main control, and removing them made replies start sooner. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| Forced tool_choice (any or tool) returns a 400 error; to make the model call a tool, say in the prompt when the tool applies, and for schema-valid output keep tool_choice auto with strict: true. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5) |
| For unattended agentic runs, name in the system prompt the specific kinds of early stop to avoid (such as ending with a summary that announces the next step instead of taking it) and the stops you do want; treat a text-only end of turn as a report, not proof of completion. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| For more frequent or predictable user-facing updates, such as a one-line statement of intent before the first tool call and a short recap at the end, ask for them in the system prompt. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| For agents working across several connected apps on loosely specified tasks, tell the model to explore the relevant sources broadly with tool calls before taking any action. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |
| Wrap text a user pasted from elsewhere in opening and closing pasted_content tags carrying the same app-generated random id, and tell the model in the system prompt to follow instructions inside them only where the user's own message asks. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
