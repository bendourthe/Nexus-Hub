# GPT-5.6 Family Prompting-Profile Qualification

This record covers a bounded local claim-only profile update for the three GPT-5.6 IDs in the recorded Claude Code roster. It does not establish that the 2026-09-08 roster is still complete or that the update has passed protected publication.

## Source and claim boundary

[OpenAI's GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) names Sol, Terra, and Luna and recommends using the prior GPT-5.5 or GPT-5.4 reasoning effort as a migration baseline, then testing one level lower on representative tasks. The [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), and [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) model pages each list the effort levels needed for that comparison. Three independent source, currency, and actionability reviews per candidate found the claim supported for each model after excluding the `none` boundary; `none` has no lower level, and the guide treats it separately.

The one claim in each generated profile is explicitly labeled as GPT-5.6-family guidance, not a distinct Sol, Terra, or Luna performance result. It instructs a comparison; it does not promise that a lower effort preserves quality. All three claims are `model-specific`, and no shared-body edit was proposed.

## Local verification

- The claim-only writer's dry run accepted Sol, then accepted Terra and Luna; the writer generated `profiles-index.json`, all three model mirrors, and `model-profiles.md` without changing roster metadata.
- `python scripts/verify_model_prompting_profiles.py` exited 0 and reported `16 profiled model(s) of 16 rostered`, with `last verified 2026-09-08` unchanged.
- The focused validator, bundle, freshness, and research tests passed: `123 passed` with exit 0. The first run exposed a shipped-seed test that required at least one unprofiled model; that stale assertion was removed because a separate fixture already tests the unprofiled branch. The corrected run passed.
- The repository-native docs group passed 8/8 after the ledger and live-picker update. `validate_skills.py --bundles-only` exited 0 with zero errors and 66 reported warnings across the 337-skill catalog.
- The Windows fast profile passed 17/17 with `C:\Program Files\Git\bin` prepended to PATH for that PowerShell process only. The host's default-PATH interpreter repair is a separate v4.4 gate.

## Remaining gate

The Claude Code 2.1.282 enumeration helper returned `{"source":"picker","models":[]}` on 2026-09-25. The account-backed `/model` picker showed display names, including Opus 5.5, Fable 5.1, Sonnet 5, and Haiku 4.5, but not a complete canonical model-ID roster; no model was selected. This update used the claim-only writer for IDs already in the recorded roster and did not claim a fresh roster. MT-1 remains open for a complete live Claude roster check and protected publication.
