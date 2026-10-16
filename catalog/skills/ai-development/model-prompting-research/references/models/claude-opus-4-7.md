# Prompting Profile: claude-opus-4-7

**Platform**: claude-code
**Last verified**: 2026-10-15
**Roster provenance**: `manual`

This file mirrors the `models["claude-opus-4-7"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| For Claude Opus 4.7, start coding and agentic workloads at xhigh effort, and use high as the minimum for most intelligence-sensitive workloads. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| Set effort explicitly on Claude Opus 4.7. The API default is high, so xhigh is never used unless the request asks for it. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| Reserve max effort on Claude Opus 4.7 for frontier problems, and move to it only when evals show measurable headroom at xhigh. On structured-output tasks, max can cause overthinking. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| When running Claude Opus 4.7 at low effort, keep tasks short and scoped, and give it an explicit checklist when the task has multiple sections. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| If latency forces low effort on Claude Opus 4.7, add a short, targeted instruction asking it to think carefully on multistep reasoning tasks. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| At xhigh or max effort on Claude Opus 4.7, set a large max_tokens (start around 64k and tune) so the model has room to think and act across subagents and tool calls. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| Remove prompt scaffolding that forces interim status messages. Claude Opus 4.7 already gives regular, good-quality progress updates during long agentic traces. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| On Claude Opus 4.7, thinking is off by default. Enable it with thinking type adaptive, not a budget_tokens setting. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking) |
| Do not send non-default temperature, top_p, or top_k to Claude Opus 4.7. Leave them out of the request and guide behavior through the prompt. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
