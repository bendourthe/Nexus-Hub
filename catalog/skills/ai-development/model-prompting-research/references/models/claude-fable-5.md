# Prompting Profile: claude-fable-5

**Platform**: claude-code
**Last verified**: 2026-10-15
**Roster provenance**: `manual`

This file mirrors the `models["claude-fable-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Default effort to high for most Fable 5 tasks; reserve xhigh for the most capability-sensitive workloads and use medium or low for routine work. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |
| Steer behaviors (verbosity, checkpointing) with one brief general instruction instead of enumerating each unwanted pattern by name. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |
| Add an outcome-first brevity instruction so the first sentence after finishing states what happened or what was found, with detail after. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |
| On long autonomous runs, instruct the model to audit every progress claim against a tool result from the session and to say explicitly what is unverified. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |
| Remove instructions that ask the model to echo, transcribe, or explain its internal reasoning in the response; they can trigger the reasoning_extraction refusal. Read thinking blocks instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |
| Review skills and prompts written for earlier models and strip overly prescriptive instructions when default behavior performs better. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |
| State explicit action boundaries (what to do and not do) to prevent unrequested actions such as unasked drafts or defensive git-branch backups. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |
| Give the reason and audience behind a request, not only the request itself, especially for long-running multi-workstream agents. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |
| Do not surface remaining-token or context-budget countdowns to the model; if unavoidable, add a reassurance that ample context remains. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |
| For long-run prompts, make self-verification explicit and delegate it to separate fresh-context verifier subagents rather than relying on self-critique. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
