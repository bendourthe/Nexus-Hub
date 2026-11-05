# Prompting Profile: claude-opus-4-7

**Platform**: claude-code
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["claude-opus-4-7"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| On Claude Opus 4.7, a request with no thinking field runs with thinking off. Set thinking: {"type": "adaptive"} to turn adaptive thinking on. thinking: {"type": "enabled", "budget_tokens": N} and thinking: {"type": "between_tools"} return a 400 error. thinking: {"type": "disabled"} is accepted (thinking stays off). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking) |
| On Claude Opus 4.7, non-default temperature, top_p, or top_k values return a 400 error on every request, whether or not thinking is used. The top_p default is 0.99, so top_p of 1 returns a 400, and so does sending both temperature and top_p. Omit these parameters and steer behavior through prompting. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/thinking) |
| For Claude Opus 4.7, start with effort xhigh for coding and agentic work, use high as the minimum for most intelligence-sensitive workloads, step down to medium for cost-sensitive work, and use max only when evals show headroom at xhigh. The API default is high, so xhigh must be set explicitly via output_config.effort. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| When running Claude Opus 4.7 at xhigh or max effort, set a large max_tokens so the model has room to think and act across subagents and tool calls. Starting at 64k tokens and tuning from there is a reasonable default. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| Claude Opus 4.7 respects effort levels more strictly than Opus 4.6, especially at low and medium, scoping work to what was asked. If reasoning looks shallow on complex problems, raise effort rather than prompting around it. If effort must stay low for latency, add targeted guidance such as 'This task involves multistep reasoning. Think carefully before responding.' Pair low effort with explicit checklists for multi-section tasks. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| On Claude Opus 4.7, thinking blocks still appear in responses but their thinking field is empty by default (display omitted; the signature still carries the encrypted thinking for multi-turn continuity). This is a silent change from Opus 4.6, which returned summarized thinking by default. Opt in explicitly (for example display: "summarized") to receive thinking text. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| Claude Opus 4.7 introduced a new tokenizer that may use roughly 1x to 1.35x as many tokens for text as models before it. Increase max_tokens headroom (including compaction triggers), re-test client-side token estimates, and verify with the /v1/messages/count_tokens endpoint. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| Claude Opus 4.7 gives more regular, higher-quality progress updates during long agentic traces. Scaffolding that forces interim status messages (for example 'After every 3 tool calls, summarize progress') can be tried without. Reasoning between tool calls appears in thinking blocks with adaptive thinking. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| Claude Opus 4.7 rejects role: "system" messages inside the messages array with a 400 error and rejects speed: "fast" (fast mode) with an error; put instructions in the top-level system field. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| Claude Opus 4.7 is the first Claude model with high-resolution image support: max image resolution is 2,576 pixels on the long edge (up from 1,568), which can use up to roughly 3x more image tokens per full-resolution image, so downsample if the fidelity is not needed. Pointing and bounding-box coordinates are 1:1 with actual image pixels, so no scale-factor conversion is needed. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide) |
| Claude Opus 4.7 (claude-opus-4-7) is a legacy model released April 16, 2026, with a 1M-token context window, 128K max output tokens (300K on the Message Batches API with the output-300k-2026-03-24 beta header), adaptive thinking, and default effort high. Retirement is not sooner than April 16, 2027, and Anthropic recommends migrating to Claude Opus 5.5. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/opus-4-7/overview) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
