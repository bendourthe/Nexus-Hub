# Session History - v3.11.0 Phase 7 (part 1): per-platform read-contract audit

**Date**: 2026-07-07
**Plan**: `docs/v3/v3.11/plans/v3.11.0-workflow-governance-refinements.md`
**Phase**: 7 of 8 - Cross-platform distribution robustness (sub-task 7.1 complete; 7.2-7.6 deferred to a fresh focused pass)
**Status**: In progress (7.1 done + committed; installer mutations paused by user choice)

## Goal (Phase 7)

After any install on Windows/macOS/Linux, every supported platform actually surfaces the catalog's commands/skills/hooks/rules - verified against each platform's real read-path, not assumed. This is the fix for the originally-reported bug: Codex and Antigravity IDE not showing Nexus-Hub commands/skills after a v3.10.3 install.

## What was done this session (7.1)

- Produced `docs/v3/v3.11/platform-read-contracts.md`: a sourced, per-platform map of where each of the 15 supported platforms READS each surface (instruction file, commands, skills, agents, rules, hooks; global vs workspace) versus where the installer WRITES it, each cited to `file:line`. Built by auditing every `scripts/lib/integrations/*.py` config, both installers, the specs, and the Antigravity probe.
- Confirmed the reported bug's two root causes: (1) Antigravity 2.0 reads workflows/skills/rules ONLY from an open project's `.agents/`, so a global-only install seeds nothing usable; (2) Codex surfaces via the `AGENTS.md` SKILL_INDEX + prompts, with skills/agents/rules-dir discovery unverified.
- Surfaced additional defects beyond the plan's scope (recorded in the contract doc and in `known-gaps.md`): C1/C2 Gemini bash/PowerShell parity break + agents/rules never delivered; C3 Antigravity 1.0 integration registered but unreachable; C5 Codex agents/rules declared but never installed; C6/C7 Copilot workspace instruction body hand-built without the SKILL_INDEX.
- Addressed the user's mid-session requirement (generalize the migration): strengthened the `/update refactor` scope in `catalog/commands/update.md` to migrate the ENTIRE docs tree (every version dir + archive, not just the active version) to the canonical scheme, so `/update refactor` and `/update release` canonicalize any repo's whole docs tree via the `docs-layout-refactor` `--canonicalize-layout` path.

## Decisions

- **Fix scope**: user chose "fix all surfacing defects" (C1/C2/C3/C5/C6/C7) alongside the planned Codex fix + auto-seed + doctor + CI smoke.
- **Pace**: user chose a "fresh focused pass" for the installer-mutating sub-tasks (7.2-7.6). Rationale: for a template repo, a half-applied two-language installer edit breaks installs for every downstream platform on every OS - the exact failure class Phase 7 exists to prevent - so the highest-blast-radius change should not be rushed under accumulated context pressure. 7.1 (read-only) was committed as the foundation.

## Verification

- `docs/v3/v3.11/platform-read-contracts.md` written and committed (694423b); no installer behavior changed in 7.1 (findings only, per the plan).
- `known-gaps.md` records the deferred 7.2-7.6 work, Phase 8, and the residual live-verification gaps (D1-D7), so a future `/plan` ingest and the fresh pass pick them up automatically.

## Next steps (the fresh focused pass for 7.2-7.6)

1. 7.2 Codex delivery fix (both installers + `codex.py`); resolve D1/D2 with a live probe first.
2. 7.3 project-surface auto-seed + on-open hook (the reported Antigravity bug) - `runner.py` + both installers.
3. 7.4 post-install `doctor` uplift (per-platform read-path PASS / NEEDS-ACTION) - the guardrail that reports C1-C7.
4. 7.5 cross-platform CI install-smoke (`ci.yml`).
5. Secondary defects C1/C2/C3/C6/C7 (fix-all scope).
6. 7.6 testing + stabilization.
7. Then Phase 8: full repo dogfood migration to the canonical scheme + v3.11.0 bump (the user's end-of-plan requirement).

All the above is tracked in `docs/v3/v3.11/known-gaps.md` (NI-1 through NI-6, DF-1, WN-1).
