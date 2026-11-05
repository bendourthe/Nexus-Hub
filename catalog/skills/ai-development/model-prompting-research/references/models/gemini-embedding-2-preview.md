# Prompting Profile: gemini-embedding-2-preview

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-embedding-2-preview"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Keep each embedding request within the model's 8,192-token input limit. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-embedding-2-preview) |
| Set output dimensionality anywhere from 128 to 3072; the page recommends 768, 1536 or 3072. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-embedding-2-preview) |
| Supply input only as text, image, video, audio or PDF; the page lists these as the supported input modalities and lists the output as text embeddings (vectors), not generated content. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-embedding-2-preview) |
| The model page does not cover task types, prompt formatting, normalization or migration. It points to the Embeddings page, which documents gemini-embedding-2 (not the -preview id), so guidance from that page should not be assumed to apply to the preview model. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-embedding-2-preview) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
