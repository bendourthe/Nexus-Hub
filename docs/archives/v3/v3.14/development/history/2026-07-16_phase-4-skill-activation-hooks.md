# Session History - v3.14.0 Phase 4: declarative skill-activation ruleset + guard/tracker hooks

**Date**: 2026-07-16
**Branch**: `feat/codex-lb-adoption` (off `develop`)
**Plan**: [docs/releases/v3/v3.14/plans/v3.14.0-codex-lb-adoption.md](../../plans/v3.14.0-codex-lb-adoption.md), Phase 4 of 6 (not the final phase)
**Scope**: `catalog/hooks/` (schema, three hooks, shared helper, test, settings.json registration), `catalog/style-guides/`, `CHANGELOG.md`, AGENTS.md hook count, the v3.14 ledger/devlog/history docs.

## Goal

Adopt codex-lb's `skill-rules.json` activation system (C1) as a deterministic backstop to Nexus-Hub's model-judgment skill triggering, inverted from fail-closed blocking to fail-open / suggest-by-default, opt-in per the hook philosophy.

## Sub-tasks completed

1. **4.1 - schema + template + convention.** `catalog/hooks/skill-rules.example.json` (seeded with all-`suggest` rules) and `catalog/style-guides/skill-activation-rules.md` (schema: enforcement, promptTriggers, fileTriggers, skipConditions, message; discovery order; fail-open/opt-in contract).
2. **4.2 - hooks.** `_skill_rules.py` (shared, defensively imported), `skill-activation-suggest.py` (UserPromptSubmit), `skill-guard.py` (PreToolUse Edit|MultiEdit|Write), `skill-tracker.py` (PostToolUse Skill). All fail-open, no-op without rules, honor NEXUS_DISABLED_HOOKS / NEXUS_HOOK_PROFILE=minimal, stdlib-only, no outbound calls, never log content/token. Guard blocks only under `NEXUS_SKILL_GUARD_BLOCK=1` + an `enforcement: block` rule.
3. **4.3 - register (ask-first), test, validate.** After the ask-first confirmation, registered all three in `catalog/hooks/settings.json`. New `test_skill_activation.py` (14 tests) passes.

## Cross-platform parity

The `.py` hooks ship no `.ps1` sibling; they run cross-platform via the `python3 .claude/hooks/*.py` interpreter convention in settings.json, matching the two existing `.py` hooks (`format-bash-description.py`, `format-powershell-description.py`). This satisfies the plan's "confirm the `.py` hooks run cross-platform" branch of the parity requirement.

## Validation (make unavailable on this Windows host; ran the test/validate commands directly)

- New hook suite: `test_skill_activation.py` 14/14 pass; with `test_platform_parity.py`, 18/18.
- Full `catalog/hooks/tests/`: 458 passed, 36 skipped, **1 failed**. The one failure (`test_installer_smoke.py::test_installers_copy_every_scripts_dir_py_file`) is PRE-EXISTING and unrelated: `scripts/verify_platform_contracts.py` (v3.12.1) is registered in neither installer, and this branch changed no `scripts/` files. Logged as BG-1.
- settings.json + skill-rules.example.json parse; unicode-safety 0 errors (new files ASCII-only); ShellCheck N/A (no new shell); ruff unavailable locally (CI runs it; hooks written ruff-clean).

## Deviations

- None functional. The ask-first settings.json edit was confirmed before the change. The pre-existing installer-smoke failure (BG-1) is documented, not fixed, as it is out of scope and an ask-first installer change.

## Known gaps added

- BG-1 (pre-existing installer-registration failure for `verify_platform_contracts.py`; fix separately or in Phase 6.3). HO-1 (review-trapdoors skill-name collision) still pending Phase 6.4. See [docs/releases/v3/v3.14/known-gaps.md](../../known-gaps.md).

## Next steps

- Phase 5: cross-model review recipe concretization (C2) - a body-only extension to `cross-model-orchestrator`, possibly with a bundled wrapper script.
- Before `/update release` (Phase 6): resolve the v3.14.0 version-number collision with the held `feat/agentic-setup-adoption` plan; decide whether to fix BG-1 (installer registration) in Phase 6.3.
- Phase 6.4 dry-run install: verify HO-1 (no `review-trapdoors` collision) and that the new hooks land at each platform's hooks path.
