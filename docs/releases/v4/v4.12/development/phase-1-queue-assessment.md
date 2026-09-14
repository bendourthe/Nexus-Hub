# v4.12 plan-entry and Phase 1 queue assessment

Observed 2026-09-14 after integration at `89758d824a92bc7c801dd9c913640c759ac1d6ce`. `python scripts/enumerate_plan_queue.py --root . --json` exited 0 and enumerated 103 readable plans. Full inventory is retained externally at `../Nexus-Hub-backups/2026-09-14-pre-v4.12-cleanup/queue-after-cleanup.json`.

## Recommendation

Proceed with the explicitly requested v4.12 plan. Phase 1 adds a repository-only checker, fixtures and one installer-test exclusion. v4.15 also touches `catalog/hooks/tests/test_installer_smoke.py`; v4.10.1 and v4.13 name CI/profile surfaces used in v4.12 Phase 3. Serialize these changes. The all-ref rewrite and origin-tip lease in T007/T023 impose a repository-wide ordering constraint before Phase 2, even on plans with disjoint source files. No parallel implementation group is recommended during that snapshot and publication window.

After v4.12, qualifying the v4.13 native runner remains a prerequisite to its capability work; v4.15 maintainer push protection and v4.10.1 isolation remain candidates. Diagram and handbook work follows a refresh against the then-current tree. This is a maintainer judgement about prerequisites and scope, not a measured speed claim. Unknown-status plans remain unranked until their owner resolves membership. No plans were renumbered.

## Per-plan disposition

Status is taken from the declared field, not unchecked-task volume. Completed or superseded plans are excluded explicitly. Undeclared or contradictory status remains unknown; the inventory is a lower bound on touched paths. Phase 2 and Phase 3 must recheck current origin tips and the named shared files.

| Plan | Membership | Verdict | Evidence |
|---|---|---|---|
| command-consolidation-skill-security.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-claude-red.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-dynamic-workflows.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.1.0-adoption-roadmap.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-headroom.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-teach.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-loop-engineering.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-nessie-and-agency-agents.md | Undeclared | Unknown | no Status line; membership is undeclared |
| model-routing.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-loopmaxxing-and-autoresearch.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-spec-kit.md | Undeclared | Unknown | no Status line; membership is undeclared |
| install-ux-overhaul.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-ralph-claude-code.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-looper-and-deer-flow.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-no-mistakes.md | Undeclared | Unknown | no Status line; membership is undeclared |
| presentify-interactive-html.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-ruflo.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-davidondrej-skills.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-pxpipe.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-spec-kit.md | Undeclared | Unknown | no Status line; membership is undeclared |
| adoption-t3mp3st.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.11.0-workflow-governance-refinements.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.12.0-presentify-fidelity-and-variety.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.12.1-cross-platform-install-adapters.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.13.0-presentify-imagery-and-interactivity.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.13.0-presentify-universal-ingestion.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.14.0-agentic-setup-adoption.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.14.0-codex-lb-adoption.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.14.1-installer-hotfix.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.14.2-comparison-versioning-fix.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.14.3-presentify-upfront-questions.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.14.4-usage-monitor-split.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.14.5-installer-ux-and-monitor-fixes.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.0-platform-parity-all-gaps.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.1-adoption-codesight.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.2-adoption-awesome-llm-apps.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.3-adoption-no-ai-slop.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.4-presentify-visual-fidelity.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.5-model-prompting-research.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.6-adoption-sandbox-escapes.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.7-adoption-raptor-loop-hunt.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.8-platform-parity-and-github-usage-monitor.md | Declared closed | Excluded | Complete (2026-08-02). Re-verification proved both surfaces, so neither shipped as finding-only. Custom agents transform `catalog/agents/*.md` into Codex TOML at `~/.codex/agents/` and `.codex/agents/`; hooks structurally merge into `hooks.json` at both scopes with `commandWindows` carrying the `.ps1` sibling. Two upstream constraints are surfaced rather than hidden: the hook engine ships disabled behind `[features] hooks`, and hooks stay inert until trusted via `/hooks`. |
| v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.10-end-of-task-agent-behavior.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.12-cursor-live-transport-and-github-billing-monitor.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.13-cursor-live-usage-and-monitor-parity.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.15.14-spec-driven-development.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.16.0-platform-defaults-config.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.16.1-evals-and-selective-installation.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.16.2-loop-longevity-and-doctor-preflight.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.16.3-github-usage-monitor-ux.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.16.5-presentify-visual-overhaul.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.16.6-presentify-verbosity-intake.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.16.7-presentify-first-shot-hardening.md | Declared active or unresolved | Ordering impact | Listed source paths differ; . T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: **RELEASE-READY.** All four phases shipped. Phase 3's intake closed on 2026-08-13 with the VectorCAST-session lessons and all six sub-tasks were built; Phase 4 root-caused the WN-1 manifest defect carried since v3.16.5. The full battery is green (3383 passed / 0 failed) and no release blocker remains. `/update release` owns the version bump, the platform-contract re-stamp for v3.16.7, the manifest regeneration, the merge, the tag, and the GitHub Release; nothing in this plan tags or pushes. |
| v3.16.8-adoption-watermark-hygiene.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.17.0-agent-autonomy-toggle.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.17.4-org-knowledge-layer.md | Declared active or unresolved | Ordering impact | Listed source paths differ; . T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: Included in the uncommitted v3.17.4 release candidate and locally verified on 2026-08-17; pending final release-note approval and release commit. |
| v3.17.5-adoption-deepseek-harness.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.17.6-ci-gate-and-branch-hygiene.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.18.0-docs-lifecycle-retention.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.18.1-github-usage-monitor-accuracy.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.18.3-presentify-slide-navigation.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.19.0-code-intelligence-hardening.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.19.1-agent-memory-substrate.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.19.2-rtk-and-meterless.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.20.0-adoption-agent-security-layers.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.20.1-adoption-cybersecurity-skills.md | Declared active or unresolved | Ordering impact | Listed source paths differ; scripts/check_agentskills_conformance.py, docs/framework-coverage.md. T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: complete |
| v3.20.2-interface-craft-skills.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.20.3-skills-craft-and-prime-agent.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v3.21.0-plan-implement-lifecycle-and-docs-architecture.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.0.0-agent-communication-overhaul.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.0.0-cost-effective-ci-cd.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.0.0-docs-lifespan-tree-and-enforcement.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.1.0-adoption-pi-and-grill-me.md | Declared active or unresolved | Ordering impact | Listed source paths differ; . T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: COMPLETE. **Recommended model tier**: strong. **Recommended effort level**: medium. |
| v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.1.1-adoption-openworker-security-refinement.md | Declared active or unresolved | Ordering impact | Shared task paths: github/workflows/ci.yml. T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: Confirmed |
| v4.1.2-adoption-minimal-construction.md | Declared active or unresolved | Ordering impact | Listed source paths differ; docs/releases/v4/v4.1/development/v4.1.2-construction-discipline-contract.md, templates/ai-instructions/base-claude.md. T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: Confirmed |
| v4.2.0-interactive-guide-redesign.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.2.1-guide-visual-education.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.2.2-guide-cinematic-rebuild.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.2.3-guide-refinement.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.3.0-agentic-verification-discipline.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.4.0-guide-depth-and-training-rebuild.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.4.1-guide-visual-and-arcade-rebuild.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.4.2-guide-production-ready-rebuild.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.4.3-guide-illustration-clarity-rebuild.md | Declared active or unresolved | Ordering impact | Listed source paths differ; . T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: COMPLETE LOCALLY, UNPUBLISHED PENDING OPERATOR REVIEW |
| v4.4.4-guide-teaching-clarity-rebuild.md | Declared active or unresolved | Ordering impact | Listed source paths differ; . T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: IN PROGRESS |
| v4.4.5-guide-mockup-integration.md | Declared active or unresolved | Ordering impact | Listed source paths differ; . T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: COMPLETE LOCALLY, UNPUBLISHED |
| v4.4.6-guide-learning-experience.md | Declared closed | Excluded | SUPERSEDED BY USER. The content/structure redesign was rejected; v4.4.5 is restored. Do not resume this plan. See the [corrected visual scope](../development/guide-learning-experience/restoration/verification.md). |
| v4.5.0-anti-cliche-and-agent-security.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.7.0-adoption-gpt-6-astra-prompting.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.7.0-adoption-model-behavior-and-distribution-integrity.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.8.0-adoption-agentic-loops-and-coding-agent-practice.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.9.0-adoption-visa-vulnerability-agentic-harness.md | Declared active or unresolved | Ordering impact | Listed source paths differ; catalog/skills/code-review/security-review/references/closure-gate-review-record.md, catalog/skills/code-review/security-review/scripts/closure-gate.py. T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: IMPLEMENTED AND INTEGRATED - 7/7 phases and 31/31 tasks; PR 190 merged at `bd2c896892203ce7a5adf0a103242c1bfe68244a` after 28 successful checks and one inapplicable skip. Post-merge smoke and provenance passed. Release publication is tracked separately. |
| v4.9.2-slide-build-contract-and-projection-floors.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.10.0-plan-queue-continuity.md | Declared closed | Excluded | Implementation COMPLETE - 6/6 phases and 26/26 tasks. Published 2026-09-11 as PR [#198](https://github.com/bendourthe/Nexus-Hub/pull/198) into `develop`: 23 checks passed, 0 failed, 1 skipped, aggregate `ci-required` green. Awaiting merge; the Phase 6 gate line covering merge-on-green stays open until then, and `/update release` follows the merge. |
| v4.10.1-adoption-eval-isolation-and-adaptive-compaction.md | Undeclared | Unknown | no Status line; membership is undeclared |
| v4.11.0-interactive-handbooks-and-presentation-default.md | Declared active or unresolved | Ordering impact | Listed source paths differ; catalog/skills/specialized-domains/document-to-interactive-html/references/dual-view-handbooks.md, tests/fixtures/interactive-handbooks/. T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: Phases 1-5 complete; implementation in progress (5/7 phases, 18/31 tasks) |
| v4.11.1-adoption-cache-and-diagram-quality.md | Declared active or unresolved | Ordering impact | Listed source paths differ; docs/releases/v4/v4.11/development/phase-1-cache-accounting.md, catalog/skills/ai-development/prompt-engineering/references/step-8-optimize-cost-and-latency.md. T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: Phases 1-3 implemented locally on 2026-09-10 and reconciled for integration on 2026-09-14; 9/25 tasks and 3/6 phases complete. Phases 4-6 remain open. |
| v4.11.2-adoption-document-and-deck-quality.md | Declared closed | Excluded | COMPLETE (7/7 phases, 28/28 tasks). Integrated via PR #208 on 2026-09-13. |
| v4.12.0-sole-contributor-attribution.md | Active by explicit user request | Subject | Phase 1: checker, fixtures, DEV_ONLY_SCRIPTS; no existing checker or .githooks directory. |
| v4.13.0-adoption-evidence-driven-agent-improvement.md | Declared active or unresolved | Ordering impact | Shared task paths: github/workflows/ci.yml. T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: READY for documentation publication after review; implementation entry NOT QUALIFIED; implementation 0/7 phases and 0/34 tasks |
| v4.15.0-push-size-guard.md | Declared active or unresolved | Ordering impact | Listed source paths differ; docs/releases/v4/v4.15/development/phase-1-baseline.md, catalog/hooks/pre-push.ps1. T007/T023 rewrite and freeze every ref; concurrent commits invalidate the captured origin tips. Status: Authored 2026-09-11; implementation not started, 0/23 tasks and 0/5 phases complete. |

## Drift and phase consequences

The former Gmail identity currently maps to bendourthe, and GitHub confirms the Cursor and Claude co-authors. Update the rewrite policy from observed identities. A free-text grep for cursoragent matches legitimate planning prose; use structured author/committer/trailer checks in Phase 2. Both corrections preserve the requested outcome. Phase 1 has no prerequisite blocker. Model enumeration/switching is unavailable through the current tool surface; retain the current session model without a downshift.
