# Prompting Profile: claude-opus-4-8

**Platform**: claude-code
**Last verified**: 2026-10-15
**Roster provenance**: `manual`

This file mirrors the `models["claude-opus-4-8"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| For coding and agentic work, start at effort xhigh. For most intelligence-sensitive work, use at least high. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| If reasoning on complex problems is shallow, raise effort to high or xhigh instead of compensating in the prompt. If latency forces low effort, add targeted guidance asking for careful multistep thinking. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| When running at max or xhigh effort, set a large max output token budget. Start at 64k and tune from there. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| Thinking is off by default on this model, so enable it explicitly with adaptive thinking. If it thinks too often (for example with large system prompts), add prompt guidance limiting thinking to multistep problems. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| The model follows instructions literally and does not generalize them. When an instruction should apply broadly, state its scope explicitly. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| The model prefers reasoning over tool calls. To get more tool use, raise effort, or say explicitly in the prompt when and how to use each tool. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| Response length tracks task complexity. To control verbosity, add explicit concision instructions, and prefer positive examples of the target concision over 'do not' instructions. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| Remove scaffolding that forces interim status messages. If the updates are miscalibrated, describe what they should look like and give examples. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| The model spawns fewer subagents by default. Say explicitly when subagents are wanted and when they are not. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| In code-review harnesses, tell the model to report every finding with confidence and severity, and leave filtering to a later stage. If it must self-filter, define a concrete bar rather than qualitative terms such as 'important'. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| In interactive coding products, put the task, intent, and constraints in the first user turn rather than spreading them across turns, use xhigh or high effort, and reduce the number of human interactions required. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |
| To break the persistent default frontend house style, give a concrete alternative design spec or have the model propose distinct directions before building. Generic negations only shift it to another fixed palette. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
