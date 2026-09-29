# Docs Cleanup Report - Nexus-Hub - 2026-08-17

**Active version:** v3.17.4
**Mode:** audit
**Scope:** `docs/v3/v3.17/`

## Summary

| Category | Count |
|---|---|
| Cat 1 (delete) | 0 |
| Cat 2 (archive) | 0 |
| Cat 3 (stale-flag) | 0 |
| Cat 4 (active) | 22 |
| **Total** | **22** |

The scoped inventory and reference graph completed successfully. All v3.17 planning, comparison, research, evidence, and history artifacts remain current. The v3.17.4 Org Knowledge Phase 1 through Phase 6 histories, v3.17.5 DeepSeek plan and comparison, plus the v3.17.2 and v3.17.3 release-preparation histories bring the scoped total to twenty-two active artifacts. No archive or deletion action is proposed; the active plan and comparison files retain the numbering established around the v3.17.3 corrective release slot.

## Dispositions

| Path | Category | Heuristics | Destination | Notes |
|---|---|---|---|---|
| `docs/v3/v3.17/known-gaps.md` | Cat 4 | Active version, externally referenced | Keep | Living v3.17 gap ledger |
| `docs/v3/v3.17/plans/v3.17.0-agent-autonomy-toggle.md` | Cat 4 | Active version | Keep | Current implementation plan |
| `docs/v3/v3.17/plans/v3.17.4-org-knowledge-layer.md` | Cat 4 | Active version | Keep | Planned parallel version |
| `docs/v3/v3.17/plans/v3.17.5-adoption-deepseek-harness.md` | Cat 4 | Active version | Keep | Approved future adoption plan |
| `docs/v3/v3.17/comparisons/v3.17.5-comparison-deepseek-harness.md` | Cat 4 | Active version | Keep | Source comparison for v3.17.5 |
| `docs/v3/v3.17/development/org-knowledge-layer-research.md` | Cat 4 | Active version | Keep | Research source for v3.17.4 |
| `docs/v3/v3.17/development/permission-matcher-findings.md` | Cat 4 | Active version, externally referenced | Keep | Phase 1 evidence |
| `docs/archive/v3/v3.17/development/history/2026-08-13_agent-autonomy-toggle-phase-1-permission-baseline-and-merge-parity.md` | Cat 4 | Active version | Keep | Phase 1 history |
| `docs/archive/v3/v3.17/development/history/2026-08-14_agent-autonomy-toggle-phase-2-capability-model-and-lever-verification.md` | Cat 4 | Active version | Keep | Phase 2 history |
| `docs/archive/v3/v3.17/development/history/2026-08-14_agent-autonomy-toggle-phase-3-core-consent-ttl-and-audit.md` | Cat 4 | Active version | Keep | Phase 3 history |
| `docs/archive/v3/v3.17/development/history/2026-08-14_agent-autonomy-toggle-phase-4-deny-layer-and-hook-independence.md` | Cat 4 | Active version | Keep | Phase 4 history |
| `docs/archive/v3/v3.17/development/history/2026-08-15_agent-autonomy-toggle-phase-5-cli-monitors-and-decision-walkthrough.md` | Cat 4 | Active version | Keep | Phase 5 history |
| `docs/archive/v3/v3.17/development/history/2026-08_agent-autonomy-toggle-phase-6-architecture-gaps-and-installer-parity.md` | Cat 4 | Active version | Keep | Phase 6 history |
| `docs/archive/v3/v3.17/development/history/2026-08_v3.17.2-autonomy-retirement-release-preparation.md` | Cat 4 | Active version | Keep | Corrective release preparation history |
| `docs/archive/v3/v3.17/development/history/2026-08-16_v3.17.3-cursor-hook-portability-release-preparation.md` | Cat 4 | Active version | Keep | Corrective release candidate history |
| `docs/archive/v3/v3.17/development/history/2026-08-16_org-knowledge-layer-phase-1-org-bundle-contract.md` | Cat 4 | Active version | Keep | v3.17.4 Phase 1 history |
| `docs/archive/v3/v3.17/development/history/2026-08-16_org-knowledge-layer-phase-2-connect-cli.md` | Cat 4 | Active version | Keep | v3.17.4 Phase 2 history |
| `docs/archive/v3/v3.17/development/history/2026-08-16_org-knowledge-layer-phase-3-cross-platform-materialization.md` | Cat 4 | Active version | Keep | v3.17.4 Phase 3 history |
| `docs/archive/v3/v3.17/development/history/2026-08-16_org-knowledge-layer-phase-4-guided-authoring-surface.md` | Cat 4 | Active version | Keep | v3.17.4 Phase 4 history |
| `docs/archive/v3/v3.17/development/history/2026-08-16_org-knowledge-layer-phase-5-lifecycle-integration-and-docs.md` | Cat 4 | Active version | Keep | v3.17.4 Phase 5 history |
| `docs/archive/v3/v3.17/development/history/2026-08-17_org-knowledge-layer-phase-6-architecture-gaps-and-ci.md` | Cat 4 | Active version | Keep | v3.17.4 Phase 6 history |
| `docs/v3/v3.17/docs-cleanup-report.md` | Cat 4 | Active audit artifact | Keep | This report |

## Cat 3 Refresh Queue

None identified.

## Target Tree Preview

```text
docs/v3/v3.17/
|-- docs-cleanup-report.md
|-- known-gaps.md
|-- development/
|   |-- org-knowledge-layer-research.md
|   |-- permission-matcher-findings.md
|   `-- history/
|       |-- 2026-08-13_agent-autonomy-toggle-phase-1-permission-baseline-and-merge-parity.md
|       |-- 2026-08-14_agent-autonomy-toggle-phase-2-capability-model-and-lever-verification.md
|       |-- 2026-08-14_agent-autonomy-toggle-phase-3-core-consent-ttl-and-audit.md
|       |-- 2026-08-14_agent-autonomy-toggle-phase-4-deny-layer-and-hook-independence.md
|       |-- 2026-08-15_agent-autonomy-toggle-phase-5-cli-monitors-and-decision-walkthrough.md
|       |-- 2026-08-16_v3.17.3-cursor-hook-portability-release-preparation.md
|       |-- 2026-08-16_org-knowledge-layer-phase-1-org-bundle-contract.md
|       |-- 2026-08-16_org-knowledge-layer-phase-2-connect-cli.md
|       |-- 2026-08-16_org-knowledge-layer-phase-3-cross-platform-materialization.md
|       |-- 2026-08-16_org-knowledge-layer-phase-4-guided-authoring-surface.md
|       |-- 2026-08-16_org-knowledge-layer-phase-5-lifecycle-integration-and-docs.md
|       |-- 2026-08-17_org-knowledge-layer-phase-6-architecture-gaps-and-ci.md
|       |-- 2026-08_agent-autonomy-toggle-phase-6-architecture-gaps-and-installer-parity.md
|       `-- 2026-08_v3.17.2-autonomy-retirement-release-preparation.md
|-- comparisons/
|   `-- v3.17.5-comparison-deepseek-harness.md
`-- plans/
    |-- v3.17.0-agent-autonomy-toggle.md
    |-- v3.17.4-org-knowledge-layer.md
    `-- v3.17.5-adoption-deepseek-harness.md
```

## Layout Inconsistencies

None identified. The canonical `docs/v3/v3.17/` minor-version layout is retained.

## Repository Architecture Audit

The Phase 6 project-wide audit found eight exact-content duplicate groups. Each is intentional: shared extension assets and code-quality references are copied into independently packaged products, `.gitignore` files serve separate platform destinations, and the five identical base instruction templates are kept in lockstep by a dedicated parity validator. No deduplication or move is proposed.

Three empty local directories were found: `.antigravitycli`, `.claude/worktrees`, and `docs/v3/v3.20/comparisons`. None is tracked, referenced, or distributed, so they remain local placeholders outside this phase's change set. No deprecated or obsolete tracked file, overcomplicated structure, or broken reference was identified.

## Self-Classification

This report classifies itself as Cat 4 (transient/active). A future audit may promote it to Cat 2 after the v3.17 line is no longer active.
