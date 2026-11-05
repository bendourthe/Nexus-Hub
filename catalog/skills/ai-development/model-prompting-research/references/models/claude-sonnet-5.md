# Prompting Profile: claude-sonnet-5

**Platform**: claude-code
**Last verified**: 2026-11-04
**Roster provenance**: `manual`

This file mirrors the `models["claude-sonnet-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Claude Sonnet 5 (API id claude-sonnet-5, legacy, released June 30, 2026) has a 1M token context window, 128K max output on the synchronous Messages API, and up to 300K output tokens on the Message Batches API with the output-300k-2026-03-24 beta header. Text and images in, text out. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/models/sonnet-5/overview) |
| Setting temperature, top_p, or top_k on Claude Sonnet 5 returns a 400 error. Omit these parameters and steer tone and variety through system-prompt instructions instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Manual extended thinking (thinking: {type: "enabled", budget_tokens: N}) is not supported on Claude Sonnet 5 and returns a 400 error. Use adaptive thinking with the effort parameter instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| On Claude Sonnet 5 adaptive thinking is on by default: a request with no thinking field runs with adaptive thinking (on Sonnet 4.6 the same request ran without thinking). To turn thinking off entirely, pass thinking: {type: "disabled"}. Revisit max_tokens for workloads that previously ran without thinking, because max_tokens caps thinking plus response text. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| The effort parameter on Claude Sonnet 5 defaults to high. For the hardest coding and agentic tasks raise it to xhigh; max has no token-spend constraints; medium suits cost-sensitive work; low is for short, scoped, latency-sensitive tasks. Effort levels are respected strictly, especially low, so at low and medium the model scopes work to what was asked and may under-think moderately complex tasks. If reasoning is shallow, raise effort rather than prompting around it. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Claude Sonnet 5 uses a new tokenizer that produces roughly 30 percent more tokens for the same text than Sonnet 4.6, so max_tokens limits tuned for Sonnet 4.6 may truncate equivalent output. At high, xhigh, or max effort leave max_tokens headroom for thinking and tool calls, or the response can be mostly thinking followed by a truncated answer with stop_reason max_tokens; raising max_tokens or dropping to medium effort resolves it. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Claude Sonnet 5 is more agentic than Sonnet 4.6 and uses tools more readily, but with thinking disabled it is less likely to reach for tools. If you rely on tool calls with thinking off, add an explicit nudge in the system prompt. High or xhigh effort increases tool usage in agentic search and coding, and prompts should say when and how to use each tool. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Claude Sonnet 5 follows instructions literally, especially at lower effort: it does not generalize an instruction from one item to another or infer unstated requests. State the scope explicitly when an instruction should apply broadly (for example, apply this formatting to every section, not just the first). | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| For code-review harnesses, Claude Sonnet 5 follows severity or confidence filters in the prompt (such as only report high-severity issues) more faithfully than earlier models, which can lower measured recall. Ask it to report every issue with a confidence level and estimated severity and do filtering in a separate stage, or give a concrete reporting threshold instead of qualitative words like important. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Claude Sonnet 5 calibrates response length to task complexity. To reduce verbosity add an instruction such as concise, focused responses with minimal examples; positive examples of the desired concision work better than negative instructions. Remove scaffolding that forces interim progress messages, since the model already gives regular progress updates in long agentic traces. | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Claude Sonnet 5 is a legacy model (status Active, retirement not sooner than June 30, 2027); the docs advise considering migration to Claude Sonnet 5.5 (claude-sonnet-5-5). | `medium` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/about-claude/model-deprecations) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
