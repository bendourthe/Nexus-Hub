# Prompting Profile: claude-sonnet-4-6

**Platform**: antigravity
**Last verified**: 2026-10-15
**Roster provenance**: `api`

This file mirrors the `models["claude-sonnet-4-6"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Always set the effort parameter explicitly when calling Sonnet 4.6. Its API default is high, which can add unexpected latency. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| Use medium as the default effort for Sonnet 4.6 in most applications, including agentic coding, tool-heavy workflows, and code generation. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| On Sonnet 4.6, use low effort for chat, non-coding, high-volume, or latency-sensitive workloads. Reserve high for complex reasoning where quality matters more than speed or cost. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/effort) |
| Do not prefill the last assistant turn on Claude 4.6 models such as Sonnet 4.6, because those requests return a 400 error. Get the output format from Structured Outputs or by asking for the structure directly. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Where a prefill was used to skip preambles, put a direct no-preamble instruction in the system prompt instead. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| On Sonnet 4.6, use adaptive thinking with the effort parameter instead of manual extended thinking with budget_tokens. budget_tokens still works on this model but is deprecated. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| To get thinking on Sonnet 4.6, request it explicitly with thinking type adaptive. Thinking is off on this model when the thinking parameter is omitted. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Dial back anti-laziness wording and aggressive "use tools more" instructions carried over from older prompts, because Claude 4.6 models are more proactive and may overtrigger on them. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| Sonnet 4.6 tracks its remaining context window. When it runs in a harness that compacts context or saves state to files, say so in the prompt so the model does not wrap up early as it nears the limit. | `high` | `model-specific` | not recorded | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
