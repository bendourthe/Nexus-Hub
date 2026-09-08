# Prompting Profile: claude-sonnet-5

**Platform**: claude-code
**Last verified**: 2026-09-08
**Roster provenance**: `config`

This file mirrors the `models["claude-sonnet-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Primary source |
|---|---|---|---|
| This model calibrates response length to task complexity rather than defaulting to a fixed verbosity, giving shorter answers on simple lookups and longer ones on open-ended analysis; tune prompts if the product depends on a specific verbosity, and prefer positive examples of the concision you want over instructions about what not to do. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Effort defaults to `high`; raise to `xhigh` for the hardest coding and agentic tasks, and reserve `low` for short scoped or latency-sensitive work that is not intelligence-sensitive. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| As a rough migration mapping, this model at `medium` is comparable to Claude Sonnet 4.6 at `high`, and at `high` comparable to Sonnet 4.6 at `max`; when benchmarking, match by observed thinking length rather than by effort name. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| This model respects effort levels strictly, especially at the low end: at `low` and `medium` it scopes work to what was asked rather than going above and beyond, with some risk of under-thinking on moderately complex tasks at `low`; raise effort rather than prompting around shallow reasoning. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Adaptive thinking is on by default, a change from Claude Sonnet 4.6 where the same requests ran without thinking; disable entirely with `thinking: {type: "disabled"}`, and revisit `max_tokens` because it is a hard limit on thinking plus response text. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is not supported and returns a 400 error; use adaptive thinking with the effort parameter instead. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| This model uses a new tokenizer that produces approximately 30% more tokens for the same text, so `max_tokens` limits tuned for Claude Sonnet 4.6 may truncate equivalent output. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| Setting `temperature`, `top_p`, or `top_k` to a non-default value returns a 400 error, which is new for Sonnet-class models; remove those parameters when migrating and steer tone through system-prompt instructions instead. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| This model is more agentic than Claude Sonnet 4.6 and reaches for tools and self-verification loops more readily; with thinking disabled it is LESS likely to reach for tools, so add an explicit nudge if tool calls matter with thinking off. Higher effort (`high`, `xhigh`) shows substantially more tool usage. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| This model provides regular, higher-quality user-facing updates through long agentic traces, so REMOVE scaffolding that forces interim status messages (such as "after every 3 tool calls, summarize progress"). | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| This model interprets prompts literally and explicitly, particularly at lower effort: it does not silently generalize an instruction from one item to another and does not infer unmade requests, so state scope explicitly (for example "apply this to every section, not just the first"). | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| On open-ended frontend and design briefs this model may settle into a consistent default visual style, and generic negative instructions shift it to a different fixed palette rather than producing variety; specify a concrete alternative direction, or have the model propose several directions before building. Because `temperature` is not accepted on this model, propose-options-first is the documented way to get meaningfully different design directions across runs. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |
| A code-review harness tuned for an earlier model may show lower measured recall on this model because it follows "only report high-severity issues" more faithfully; ask for coverage at the finding stage and move confidence filtering to a separate step. The page is explicit that this is a harness effect rather than a capability regression: same investigation depth, fewer investigations converted into reported findings. | `high` | `model-specific` | [source](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5) |

## Does not apply to shared bodies

Every claim in this file is scoped to the model named in the H1. It must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one, and `scripts/check_base_template_parity.py` fails the build when such a line diverges across the templates.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
