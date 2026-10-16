# Prompting Profile: claude-opus-4-5

**Platform**: claude-code
**Last verified**: 2026-10-15
**Roster provenance**: `manual`

This file mirrors the `models["claude-opus-4-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| On Claude Opus 4.5, tone down aggressive tool or skill triggering language carried over from older prompts, because the model is more responsive to the system prompt and may overtrigger. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| For Claude Opus 4.5, replace emphatic tool directives such as 'CRITICAL: You MUST use this tool when...' with plain phrasing such as 'Use this tool when...'. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| When extended thinking is disabled on Claude Opus 4.5, avoid the word 'think' and its variants in prompts. Use 'consider', 'evaluate' or 'reason through' instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Claude Opus 4.5 tends to overengineer by adding extra files, abstractions, or unrequested flexibility. When this happens, add explicit guidance that keeps solutions minimal. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| To keep Claude Opus 4.5 coding work in scope, add an anti-over-engineering instruction that limits changes to what was requested or is clearly necessary. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| For frontend or web-app generation with Claude Opus 4.5, include explicit design-direction guidance in the prompt. Without it, the model falls back on generic 'AI slop' patterns. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| For image-heavy tasks with Claude Opus 4.5, give the model a crop tool or agent skill so it can zoom into relevant image regions. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| On Claude Opus 4.5 (extended thinking, not adaptive), set the effort level and the thinking budget_tokens together: choose effort for the task, then size budget_tokens to the reasoning depth needed. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| Claude Opus 4.5 defaults to high effort. For token-sensitive coding work, consider setting medium effort explicitly: Anthropic reports it matches Sonnet 4.5's best SWE-bench Verified score with far fewer output tokens. | `high` | `model-specific` | not recorded | [source](https://www.anthropic.com/news/claude-opus-4-5) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
