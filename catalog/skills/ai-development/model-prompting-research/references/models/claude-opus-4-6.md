# Prompting Profile: claude-opus-4-6

**Platform**: claude-code
**Last verified**: 2026-10-15
**Roster provenance**: `manual`

This file mirrors the `models["claude-opus-4-6"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| For Claude Opus 4.6, tone down forceful tool or skill triggering language such as 'CRITICAL: You MUST use this tool'. The model follows the system prompt more closely and may overtrigger, so plain wording like 'Use this tool when...' works better. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| For Claude Opus 4.6, replace blanket tool defaults with conditional, targeted instructions that say when the tool helps. The model does more upfront exploration than earlier models. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| For Claude Opus 4.6, remove over-prompting written for older models, such as 'If in doubt, use [tool]'. Tools that used to undertrigger now trigger appropriately, and such phrasing causes overtriggering. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| When Claude Opus 4.6 thinks for too long and inflates token use, either add explicit instructions that limit its reasoning (for example, choose an approach and commit to it) or lower the effort setting. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| On Claude Opus 4.6, use adaptive thinking with effort to control thinking depth and cost, and use max_tokens as the hard limit. Manual budget_tokens still works on this model but is deprecated. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| On Claude Opus 4.6, thinking is off when the thinking parameter is omitted. To get thinking, set it explicitly (thinking: {type: "adaptive"}); unlike Claude 5 models, it is not on by default. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Do not prefill the final assistant turn when prompting Claude Opus 4.6, because the request returns a 400 error. Use structured outputs or system prompt instructions instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| In agentic prompts for Claude Opus 4.6, tell the model to confirm with the user before irreversible, destructive, or shared-system actions such as deleting files, force-pushing, or posting externally. Without that guidance it may take them. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| In orchestration prompts for Claude Opus 4.6, watch for and limit subagent overuse. The model may spawn subagents where a direct call such as grep would be faster and enough. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| For Claude Opus 4.6 coding work, add explicit guidance to keep solutions minimal. The model tends to create extra files, add unneeded abstractions, and build flexibility nobody asked for. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
