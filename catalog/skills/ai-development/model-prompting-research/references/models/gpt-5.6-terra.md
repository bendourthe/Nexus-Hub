# Prompting Profile: gpt-5.6-terra

**Platform**: claude-code
**Last verified**: 2026-09-25
**Roster provenance**: `config`

This file mirrors the `models["gpt-5.6-terra"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| When migrating from GPT-5.5 or GPT-5.4 with a reasoning effort above none, compare the existing effort with one level lower on representative tasks. OpenAI frames this as GPT-5.6-family guidance, not a Terra-only difference. Test quality, latency, and cost for Terra separately; the source does not promise equivalent quality at lower effort. For prior effort none, retain none as the latency baseline and test low when reasoning or tool use may help. Three independent refutation reviews confirmed applicability and this boundary. | `high` | `model-specific` | `model-family` | [source](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
