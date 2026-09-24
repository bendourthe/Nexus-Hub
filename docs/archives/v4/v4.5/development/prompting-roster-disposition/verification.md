# v4.5 Prompting Roster Disposition

This frozen record resolves the exact Claude roster mismatch named by v4.5 WN-3. It does not assert that the profile index covers every current vendor model.

Commit `5f4c76eb` refreshed `model-prompting-research/assets/profiles-index.json` and added `references/models/claude-fable-5-1.md`. The index now records `claude-fable-5-1`, does not record `claude-fable-5`, and dates that profile and the primary roster to 2026-09-08. On 2026-09-24, `python scripts/verify_model_prompting_profiles.py` passed with 12 profiled models of 16 rostered; 62 focused profile and freshness-checker tests passed. These checks verify the shipped index and reference contract, not a fresh account-backed Claude model enumeration.

The four rostered models without per-model profiles remain in [v4.9 MT-1](../../../../../releases/v4/v4.9/known-gaps.md), which records their source-availability boundary. A future live roster can drift again and must be checked at its next qualified prompting-research pass; neither limitation reopens the specific Fable 5 to Fable 5.1 mismatch from v4.5.
