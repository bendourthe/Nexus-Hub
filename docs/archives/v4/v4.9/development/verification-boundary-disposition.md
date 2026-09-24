# v4.9 Verification Boundary Disposition

This frozen record covers v4.9 WN-2 only. The [living process decision](../../../../decisions/implemented/process/2026-09-24-retain-claim-evidence-for-opus-5.md) is the governing rule; this file preserves the follow-up's scope and verification.

The [official Opus 5 guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5) advises removing inherited verification instructions and verifier scaffolding. The repository's `verification-before-completion` skill instead requires evidence before a user-facing completion claim. The decision keeps that model-independent claim boundary and omits redundant model-specific self-check prompts and automatic verifier subagents. The `claude-opus-5` profile note and its index mirror now say so. No verification requirement or runtime code was removed.

Verification on 2026-09-24: `python scripts/verify_model_prompting_profiles.py` passed the index/reference contract; the focused profile tests and documentation checks passed. This does not assert a new live model-roster enumeration or resolve the four source-availability items in v4.9 MT-1.
