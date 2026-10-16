# Docs Cleanup Report

**Project**: Nexus-Hub. **Date**: 2026-10-16. **Active version**: v4.14.0. **Mode**: audit. **Scope**: docs/releases/v4/v4.14/.

## Summary

| Category | Count |
|---|---|
| Cat 1 (delete) | 0 |
| Cat 2 (archive) | 0 |
| Cat 3 (stale-flag) | 0 |
| Cat 4 (active) | 20 |

The native inventory used `--root docs --repo-root .`; every scoped record has the canonical releases layout. Phase 2 refreshed the snapshot after the rationale and phase history were created, including this report. The keep-current-version rule retains the whole in-flight minor, including earlier claim-review evidence. No file moved or was deleted.

## Dispositions

| Path | Category | Evidence | Destination |
|---|---|---|---|
| docs/releases/v4/v4.14/docs-cleanup-report.md | Cat 4 | In-flight minor; 8 external references | Keep |
| docs/releases/v4/v4.14/known-gaps.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/plans/v4.14.0-adoption-agent-tooling-and-subagent-cost.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/plans/v4.14.1-adoption-effort-allocation.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/plans/v4.14.2-adoption-harness-decisions-design-rules-and-cache-stability.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/plans/v4.14.3-adoption-argon-enforcement-and-replayable-gates.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/plans/v4.14.4-adoption-gate-outcomes-and-opt-in-git-guard.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/plans/v4.14.5-adoption-codex-memory-levers.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/plans/v4.14.6-nexus-hub-settings-extension.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/development/agent-pinning-rationale.md | Cat 4 | In-flight minor; 2 external references | Keep |
| docs/releases/v4/v4.14/development/gemini-usage-monitor-handbook-claim-review.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/development/phase-1-lever-evidence.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/development/v4.13.13-release-handbook-claim-review.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/development/history/v4.14.0-phase-1.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/development/history/v4.14.0-phase-2.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/comparisons/v4.14.0-comparison-agent-tooling-and-subagent-cost.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/comparisons/v4.14.1-comparison-effort-allocation.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/comparisons/v4.14.2-comparison-harness-decisions-design-rules-and-cache-stability.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/comparisons/v4.14.3-comparison-argon-enforcement-and-replayable-gates.md | Cat 4 | In-flight minor; 0 external references | Keep |
| docs/releases/v4/v4.14/comparisons/v4.14.5-comparison-codex-memory-models.md | Cat 4 | In-flight minor; 0 external references | Keep |

## Cat 3 refresh queue

None introduced by this phase. Broad release-layout reconciliation remains Phase 7.

## Lifespan contradictions

Phases 1 and 2 created release-scoped evidence, the agent rationale, and their phase histories. Both freeze at release close. No archive or signed record was modified.

## Target tree preview

The current `plans/`, `comparisons/`, `development/`, and `development/history/` layout is retained.

## Self-classification

This audit is Cat 4 while v4.14 is active; it freezes with the minor at release close.
