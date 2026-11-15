# Prompting Profile: claude-opus-4-6

**Platform**: claude-code
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["claude-opus-4-6"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| On claude-opus-4-6, with no thinking field the request runs with thinking off. Thinking turns on only when you set thinking: {"type": "adaptive"}, which lets Claude decide when and how deeply to think. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking) |
| On claude-opus-4-6, manual extended thinking (thinking: {"type": "enabled", "budget_tokens": N}) still works but is deprecated. Prefer adaptive thinking plus the effort parameter, or max_tokens as a hard limit. Setting budget_tokens returns a 400 error on Claude 4.7 and later models. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| claude-opus-4-6 defaults to effort `high`, and `max` is an available effort level on it. Set effort through output_config.effort, which needs no beta header. Remove the effort-2025-11-24 beta header. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| For claude-opus-4-6, if the model over-explores or thinks extensively at higher effort, replace blanket instructions such as 'Default to using [tool]' or 'If in doubt, use [tool]' with targeted ones. Add an explicit instruction to commit to an approach, or lower the effort setting to reduce thinking tokens and latency. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| claude-opus-4-6 and Claude Opus 4.5 are more responsive to the system prompt than earlier models. Prompts written to reduce tool or skill undertriggering may now overtrigger, so soften aggressive wording (for example 'CRITICAL: You MUST use this tool when...' becomes 'Use this tool when...'). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Prefilling assistant messages returns a 400 error on claude-opus-4-6 and later Opus models. Use structured outputs or system prompt instructions instead of a prefill. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| claude-opus-4-6 and later models may escape JSON strings in tool call arguments slightly differently (for example Unicode or forward-slash escaping). Parse tool call input with a standard JSON parser, not as a raw string. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| On claude-opus-4-6 the thinking display default is summarized, meaning thinking blocks return summarized thinking text. This differs from Claude Opus 4.7 and later, where thinking text is omitted unless the request opts in. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking) |
| Without guidance, claude-opus-4-6 may take hard-to-reverse actions or actions affecting shared systems, such as deleting files, force-pushing, or posting to external services. Add prompt guidance that asks it to confirm before destructive or shared-system actions. It also tends to overengineer with extra files and abstractions, so add specific guidance to keep solutions minimal. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
