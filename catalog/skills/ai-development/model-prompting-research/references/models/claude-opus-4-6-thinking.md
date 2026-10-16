# Prompting Profile: claude-opus-4-6-thinking

**Platform**: antigravity
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["claude-opus-4-6-thinking"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Opus 4.6 does not think unless you ask it to. To get thinking, explicitly send thinking: {type: "adaptive"} rather than relying on the default. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Do not cap thinking with budget_tokens on Opus 4.6, because that setting is deprecated there. Use adaptive thinking, control depth with effort, and use max_tokens as the hard ceiling. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Opus 4.6 explores a lot up front, so remove or weaken prompts that push for thoroughness. Replace blanket defaults such as 'Default to using [tool]' with targeted wording such as 'Use [tool] when it would enhance your understanding'. If it still over-explores, lower effort. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| When Opus 4.6 thinks too much, add explicit instructions that limit its reasoning (for example, choose an approach, commit to it, and revisit only on contradicting new information), or lower the effort setting. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Drop aggressive tool and skill triggering language written for older models, such as 'CRITICAL: You MUST use this tool when...'. Use plain wording such as 'Use this tool when...', because Opus 4.6 follows the system prompt closely and will overtrigger. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Do not prefill the final assistant turn for Opus 4.6. Prefill returns a 400 error on this model, so get the format you want from instructions or structured outputs instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| In agentic deployments, add a reversibility and confirmation rule to the prompt. The rule should tell Opus 4.6 to ask before destructive, hard-to-reverse or externally visible actions, such as deleting files, force-pushing or posting to external services. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Limit subagent use in the prompt. Opus 4.6 tends to spawn subagents when a direct call such as grep would be faster and enough, so say when delegating is warranted. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Add explicit minimal-scope guidance for coding work: only make changes that are requested or clearly necessary, with no extra files, abstractions or configurability. Opus 4.6 tends to over-engineer without it. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| To reduce how often an adaptive-thinking model thinks, lower the effort level first. Use system-prompt or per-message steering phrases only if thinking still triggers wrongly, and measure quality before shipping. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
