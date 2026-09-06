# Decision Note - Does the Claude Code settings reference document `max` as an effort level?

**Plan**: `docs/releases/v4/v4.7/plans/v4.7.0-adoption-model-behavior-and-distribution-integrity.md`, sub-task 1.1 (T001)
**Date**: 2026-09-05
**Pages fetched**: `https://code.claude.com/docs/en/model-config` and `https://code.claude.com/docs/en/settings`, both on 2026-09-05

## Outcome

**Option (a) holds, with a twist the plan did not anticipate**: the reference was fetched and the recorded `doc_statement` was stale, but in the opposite direction from the one the plan describes. The plan expected the question to be whether `max` had been added to the settings key. The vendor page says `max` is NOT accepted by the settings keys and IS accepted by the environment variable. The 2026-09-04 statement in `configs/platform-defaults.json` had those two surfaces inverted.

## Quoted evidence

From the model-config page, fetched 2026-09-05:

- "set `effortLevel` to `low`, `medium`, `high`, or `xhigh` as the default for models without one. `max` isn't accepted in either key" (the two keys being `effortLevel` and `modelSettings`).
- "`max` is the deepest reasoning level. Unless you set it through the `CLAUDE_CODE_EFFORT_LEVEL` environment variable, Claude Code applies `max` to the current session only."
- "set `CLAUDE_CODE_EFFORT_LEVEL` to a level name or `auto`"
- "It saves the level per model, under the `modelSettings` key in your user settings, so each model keeps its own saved level."

From the settings page, fetched 2026-09-05: "Claude Code applies some `/effort` levels, such as `max` and `ultracode`, to the current session only; see Adjust effort level."

## What changes

- `configs/platform-defaults.json` Claude entry: `doc_statement` rewritten to the quoted contract and `verified` set to 2026-09-05 (sub-task 1.3). The seeded value `high` is accepted by every surface, so no seeded value changes and the derived artifacts (`catalog/hooks/settings.json` core keys, the `claude.py` fallback) regenerate to identical values.
- `docs/policy/platform-defaults-levers.md`: the Claude section's inverted sentence corrected, with a dated log row.
- No template, command, or shared skill body names `max` as a settings value; `model-routing` speaks of effort as a generic tier property and of `/effort max` only as the Claude Code keystroke, which the page confirms is session-scoped.

## What does not change

The `effortLevel` / `env.CLAUDE_CODE_EFFORT_LEVEL` upgrade-pair rule: if either lever already exists in a user config, the pair's shape is user-owned and the missing partner is not added. Both levers still accept `high`, so the pair is still declared together.
