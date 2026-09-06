# Prompting Profile: claude-opus-5

**Platform**: claude-code
**Last verified**: 2026-07-27
**Roster provenance**: read from the platform model picker (live API enumeration was unavailable because no `ANTHROPIC_API_KEY` was present)

This file mirrors the `models["claude-opus-5"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index.

## Verified prompting guidance

| Claim | Confidence | Scope | Primary source |
|---|---|---|---|
| State the task, the desired output shape, and any hard constraints explicitly rather than relying on implicit convention. | `unverified` | `model-specific` | [Prompt engineering overview](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview) |

**Seed status**: this profile was hand-seeded to establish the contract, not produced by a research run. The single claim above has NOT survived the adversarial-verify pass, which is why it carries `confidence: unverified`. A verified run must re-fetch the primary source, confirm the URL resolves, refute-test the claim, and re-tag the confidence before anything acts on it. It is scoped `model-specific` per the ambiguous-defaults-to-model-specific rule, so it cannot reach a shared catalog body in its current state even if the auto-apply engine runs.

## Does not apply to shared bodies

Every claim in this file is scoped to the model named in the H1. It must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one, and `scripts/check_base_template_parity.py` fails the build when such a line diverges across the templates.

If a claim here turns out to be true of models generally rather than of this one, that is not a reason to paste it into a shared body by hand. Re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
