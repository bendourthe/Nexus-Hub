# Haiku 4.5 claim-only profile qualification

This dated v4.9 evidence records a local, per-model prompting-profile qualification for maintainers closing MT-1. It does not claim a fresh Claude model roster or qualify the three GPT-5.6 models.

## Scope and result

- The installed Claude Code picker exposed Haiku 4.5 but not its complete model-ID list; the enumeration helper returned the picker sentinel with no models. The existing 2026-09-08 config roster already contains `claude-haiku-4-5`.
- Anthropic's [Haiku 4.5 migration guide](https://platform.claude.com/docs/en/models/haiku-4-5/migration-guide) supports one conditional coding/reasoning recommendation for manual extended thinking. The [extended-thinking reference](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) confirms the manual-mode boundary. The [calibration receipt](../haiku-profile-calibration-2026-09-25/verification.md) records the independent source, currency, and actionability challenges.
- The deterministic writer's claim-only path wrote the qualified Haiku claim and generated its Markdown mirror without changing the roster metadata. The structural validator reports 13 profiled models of 16 rostered and retains `last_verified: 2026-09-08` for the roster.
- The three remaining unprofiled IDs are `gpt-5.6-luna`, `gpt-5.6-sol`, and `gpt-5.6-terra`. MT-1 and complete-roster freshness remain open.

## Local verification

- The writer's real CLI accepted the one-model payload and generated `references/models/claude-haiku-4-5.md` plus the aggregate reference.
- The one-model planner selected `claude-haiku-4-5`; the classifier routed its finding to `profile-only`, with no shared-body edit.
- `python -m pytest -q tests/skills/test_model_prompting_research.py tests/validators/test_verify_model_prompting_profiles.py`, with third-party pytest autoload disabled, passed 102 tests.
- `python scripts/verify_model_prompting_profiles.py` passed the structural gate and reported 13 of 16 profiled; it did not report a live-roster match.
- The 337-skill bundle audit passed with zero errors and 66 warnings. The Windows fast profile passed 17 checks, and docs-conventions checks passed for the affected v4.9 release and archive trees.

This is local qualification evidence. Protected PR checks and post-merge verification are not represented here.
