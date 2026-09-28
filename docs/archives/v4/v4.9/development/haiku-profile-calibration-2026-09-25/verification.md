# Haiku 4.5 Profile Calibration - 2026-09-25

**Scope**: Recheck the Haiku part of v4.9 MT-1 against current first-party guidance and the local Claude Code model picker. This is source qualification, not a profile write or paid model evaluation.

**Base**: `develop` at `7c085cdd` after PR #312.

**Result**: A model-specific candidate exists, but a complete live Claude model-ID roster was not available for the deterministic profile writer. MT-1 stays open.

## Source and refutation

- [Anthropic's Haiku 4.5 migration guide](https://platform.claude.com/docs/en/models/haiku-4-5/migration-guide) recommends considering `thinking: {type: "enabled", budget_tokens: N}` for coding and reasoning tasks on Haiku 4.5. The recommendation is conditional, not a mandate for all requests.

- [Anthropic's extended-thinking guide](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) confirms manual enabled thinking for Haiku 4.5; adaptive thinking is not its mode. The migration guide also notes an effect on prompt-caching efficiency.

- Three independent read-only refutation lenses checked source support, current applicability, and profile actionability. Currency and actionability survived. The source lens rejected only the candidate's unquoted `enabled` token; the corrected candidate above matches the vendor syntax. The profile layer already contains model-specific thinking and effort controls, so this is a candidate for that layer, not for a shared skill body.

## Local qualification boundary

- `python scripts/verify_model_prompting_profiles.py` exited 0 and reported 12 profiled of 16 rostered models; Haiku 4.5 and three GPT-5.6 variants remain unprofiled.

- With Git Bash prepended only to this process's PATH, `python scripts/ci/run.py --profile fast --quiet` passed 17/17 in the isolated checkout before any documentation edit. No host PATH setting changed.

- The installed Claude Code `/model` picker displayed Haiku 4.5. The `enumerate-models.ps1 claude-code` helper returned `{"source":"picker","models":[]}`, and the picker did not expose a complete machine-readable ID list. The primary index roster remains a 2026-09-08 `config` snapshot that includes multiple vendors; it was not relabeled as a live Claude roster.

- The Codex CLI's own six-model list was not substituted for Claude provenance. No profile, generated mirror, roster hash, or freshness marker changed.

## Disposition

Capture a complete current Claude model-ID roster from a primary live surface, then run the one-model planner and deterministic writer for the corrected claim. Re-run structural verification and keep the three GPT-5.6 entries independently open until each has a source-backed disposition. The optional advisor-tool configuration in the same known-gaps row remains outside this calibration and carries no transcript-forwarding authorization.
