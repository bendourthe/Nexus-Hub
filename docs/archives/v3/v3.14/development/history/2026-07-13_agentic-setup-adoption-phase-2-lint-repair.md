# Session History -- agentic-setup-adoption, Phase 2 (lint-repair loop + autofix hook)

**Date**: 2026-07-13
**Version**: v3.14.0
**Plan**: `docs/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md`
**Phase**: 2 of 8 -- Skill-native lint-repair loop + deterministic autofix hook
**Branch**: `feat/agentic-setup-adoption` (off `develop`)

## Goal

Adopt point 5 of the comparison ("custom linters that repair, not just flag") in a policy-compliant form: a repair-loop skill that runs on the session's own model, plus an opt-in precommit hook that runs available formatters' native --fix.

## What was done

### 2.1 lint-repair-loop skill

Authored `catalog/skills/code-cleanup/lint-repair-loop/SKILL.md` (71 lines): the bounded repair loop (native --fix first, then agent judgment on the session model, re-run until clean or a 3-iteration cap, leave a reviewable diff, never bypass hooks). A dedicated Policy section, citing the AGENTS.md MCP Registry Policy, states the skill does NOT shell out to any external repair model - the source post's "Composer 2.5" recommendation reframed as skill-native. Registered across `skills.json` (269 skills), `SKILL_INDEX.md` (+1 row, total 269), and `marketplace.json` (code-cleanup 10 -> 11).

### 2.2 lint-autofix hook (.sh + .ps1)

Authored `catalog/hooks/lint-autofix.sh` and a behavior-equivalent `catalog/hooks/lint-autofix.ps1`. On a `git commit` Bash tool call, the hook runs available formatters' native --fix (ruff / prettier / gofmt / shfmt, each guarded by presence) on the STAGED files that have NO unstaged changes, then re-stages them. Design decisions:

- **Opt-in** (inert unless `NEXUS_ENABLE_LINT_AUTOFIX=1`), mirroring `git-guardrails.sh`'s `NEXUS_PROTECTED_BRANCHES` opt-in, because the hook mutates files. Also honors `NEXUS_DISABLED_HOOKS=lint-autofix` and `NEXUS_HOOK_PROFILE=minimal`.
- **Never touches a file with unstaged changes** (staged-clean files only), avoiding the classic pre-commit hazard of `git add` restaging work in progress.
- **Fail-open** (always exit 0; never blocks a commit). A jq-or-grep/sed fallback extracts the command so an opt-in user is not silently no-op'd without jq. No LLM call, no network.

### 2.3 Registration + test + CI

- `catalog/hooks/tests/test_lint_autofix.py` (7 tests): opt-in gate, disabled-env, minimal-profile, fail-open, non-commit no-op, and (ruff-gated) format+re-stage and skip-unstaged.
- Registered the hook in `catalog/hooks/settings.json` (user-confirmed ask-first gate) as a new PreToolUse Bash matcher, placed after `git-guardrails`.
- Added `ruff` to the CI `tests` job so the ruff-gated formatting cases run in CI.

## Deviations

- **Opt-in, not opt-out** (plan 2.2/2.3 said opt-out): a file-mutating hook must not be on-by-default for the whole install base. Registered dormant; users enable with one env var.
- **Placed after `git-guardrails`** (plan said before), so a guardrail-blocked commit is not autofixed.
- **jq fallback added** to the hook (grep/sed), beyond the plan text, so an opt-in user without jq is not silently no-op'd (mirrors `git-guardrails.sh`).

## Validation

- Hook behaviors: all six verified end-to-end through Git Bash (opt-in gate, fail-open, non-commit no-op, disabled-env, skip-unstaged with stderr note, and format + re-stage with ruff on PATH - `import os` removed, `x=1` -> `x = 1`, re-staged).
- ShellCheck clean on `lint-autofix.sh`; `lint-autofix.ps1` AST parses; `settings.json` valid JSON; `skills.json` valid (269 skills, no dupes); bundle audit PASS; new files ASCII-clean.
- WN-3: `pytest` bash hook tests cannot run on the Windows dev host (WSL `bash.EXE` mangles the Windows-path `.sh`, exit 127); CI ubuntu is the authoritative gate. The test collects cleanly (7 tests).

## Next steps

- Phase 3: performance-regression gate (`performance-regression-gate` skill + bundled baseline-diff script).
