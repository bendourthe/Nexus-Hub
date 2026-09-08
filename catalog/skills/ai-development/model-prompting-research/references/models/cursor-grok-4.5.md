# Prompting Profile: cursor-grok-4.5

**Platform**: claude-code
**Last verified**: 2026-09-08
**Roster provenance**: `config`

This file mirrors the `models["cursor-grok-4.5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Primary source |
|---|---|---|---|
| On Cursor's Start plan this model runs at a FIXED `medium` effort level, so effort is not an available prompt-side or routing lever there. | `high` | `model-specific` | [source](https://cursor.com/docs/models-and-pricing) |
| Cursor publishes no per-model prompting guidance for the models it serves; prompting guidance must come from the underlying model vendor. | `high` | `model-specific` | [source](https://cursor.com/docs/models-and-pricing) |

## Does not apply to shared bodies

Every claim in this file is scoped to the model named in the H1. It must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one, and `scripts/check_base_template_parity.py` fails the build when such a line diverges across the templates.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
