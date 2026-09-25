# Prompting Profile: claude-haiku-4-5

**Platform**: claude-code
**Last verified**: 2026-09-25
**Roster provenance**: `config`

This file mirrors the `models["claude-haiku-4-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Primary source |
|---|---|---|---|
| For coding or reasoning tasks on Haiku 4.5, consider enabling manual extended thinking with thinking: {type: "enabled", budget_tokens: N}; this is conditional, not a universal default. Three independent refutation lenses on 2026-09-25: currency and actionability survived; source support survived after quoting enabled. A complete live Claude roster remains unavailable, so this claim-only write preserves the 2026-09-08 roster metadata. | `medium` | `model-specific` | [source](https://platform.claude.com/docs/en/models/haiku-4-5/migration-guide) |

## Does not apply to shared bodies

Every claim in this file is scoped to the model named in the H1. It must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one, and `scripts/check_base_template_parity.py` fails the build when such a line diverges across the templates.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
