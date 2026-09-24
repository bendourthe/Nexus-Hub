# v4.7 Model-Map Follow-Up

This frozen record covers the post-release disposition of v4.7 DF-1 and a fresh read-only check of DF-2. It does not refresh prompting profiles or assert that API availability equals Codex CLI picker availability.

## DF-1: superseded guide citation

The historical `docs/releases/v4/v4.4/plans/v4.4.6-guide-learning-experience.md` model map already placed `gpt-6-astra` in the OpenAI frontier cell, agreeing with the v4.7 routing decision. Its missing citation was the only remaining action in DF-1. The [v4.4.5 restoration record](../../../../../releases/v4/v4.4/development/guide-learning-experience/restoration/verification.md) states that the user rejected and superseded the v4.4.6 redesign, and that the seven-phase plan must not resume. Editing its model map now would change a rejected historical plan without improving active routing. DF-1 is closed as superseded; the plan is untouched.

## DF-2: current CLI drift remains

On 2026-09-24, the repository's `model-routing/scripts/enumerate-models.ps1 codex` helper read the installed `codex debug models` picker and returned six IDs: `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex`, `gpt-5.2`, and `codex-auto-review`. `gpt-6-astra` was absent. The [official OpenAI model catalog](https://developers.openai.com/api/docs/models/gpt-6-astra) lists the API model, but that does not prove this CLI picker exposes it. DF-2 remains open; no roster or profile file was changed.
