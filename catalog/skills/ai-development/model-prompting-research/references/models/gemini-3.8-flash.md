# Prompting Profile: gemini-3.8-flash

**Platform**: claude-code
**Last verified**: 2026-09-08
**Roster provenance**: `config`

This file mirrors the `models["gemini-3.8-flash"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Primary source |
|---|---|---|---|
| Keep `temperature`, `top_p`, and `top_k` at their default values; Google strongly recommends this for Gemini 3.x models rather than tuning them. Gemini 3.x family-level recommendation, recorded per rostered model at this index's granularity; not a version-specific measurement. | `high` | `model-specific` | [source](https://ai.google.dev/gemini-api/docs/prompting-strategies) |
| Be precise and direct, and use one consistent prompt structure with clear delimiters such as XML tags or Markdown headings. Gemini 3 family-level guidance, not a result measured on this individual version. | `medium` | `model-specific` | [source](https://ai.google.dev/gemini-api/docs/prompting-strategies) |
| The cited Gemini prompting page gives no variant-specific guidance for this Flash ID; check separate official model guidance before recording a variant-specific claim. Page-level negative result only, not an exhaustive claim about all Google documentation; the positive guidance above is family-scoped. | `high` | `model-specific` | [source](https://ai.google.dev/gemini-api/docs/prompting-strategies) |

## Does not apply to shared bodies

Every claim in this file is scoped to the model named in the H1. It must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one, and `scripts/check_base_template_parity.py` fails the build when such a line diverges across the templates.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
