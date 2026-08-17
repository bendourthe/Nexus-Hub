# Nexus-Hub Progress Dashboard

**Branch:** `feat/v3.17.4-org-knowledge-layer`

---

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| Plan phases complete | 7 | 7 | 0 |
| Phase 1 tasks complete | 3 | 3 | 0 |
| Phase 2 tasks complete | 3 | 3 | 0 |
| Phase 3 tasks complete | 4 | 4 | 0 |
| Phase 4 tasks complete | 3 | 3 | 0 |
| Phase 5 tasks complete | 4 | 4 | 0 |
| Phase 6 tasks complete | 4 | 4 | 0 |
| Phase 7 tasks complete | 4 | 4 | 0 |
| v3.19.0 CI/CD plan phases complete | 0 | 8 | 8 |
| v3.16.1 planning milestones complete | 2 | 2 | 0 |
| v3.16.1 plan phases complete | 8 | 8 | 0 |
| Local release integration | 1 | 1 | 0 |
| Release metadata and docs | 1 | 1 | 0 |
| Platform contract audit | 1 | 1 | 0 |
| Local release gates | 1 | 1 | 0 |
| Remote publication gates | 1 | 1 | 0 |
| Open phase blockers | 0 | 0 | 0 |
| v3.15.8 plan phases complete | 4 | 9 | 5 |
| v3.15.8 Phase 1 tasks complete | 7 | 7 | 0 |
| v3.15.8 Phase 2 tasks complete | 9 | 9 | 0 |
| v3.15.8 Phase 3 tasks complete | 9 | 9 | 0 |
| v3.15.8 Phase 4 tasks complete | 7 | 7 | 0 |
| v3.17.2 autonomy retirement tasks complete | 6 | 6 | 0 |
| v3.17.2 release tasks complete | 5 | 7 | 2 |
| v3.17.3 release-candidate tasks complete | 9 | 9 | 0 |
| v3.17.4 plan phases complete | 5 | 6 | 1 |
| v3.17.5 plan phases complete | 0 | 7 | 7 |
| Cursor hook portability tasks complete | 4 | 4 | 0 |
| Usage monitor color-race tasks complete | 2 | 2 | 0 |
| Codex Extra Credits payload tasks complete | 2 | 2 | 0 |
| Codex credit display tasks complete | 3 | 3 | 0 |

## Corrective Patch - Cursor Hook Portability [DONE]

- [x] Install and register PowerShell hook siblings on Windows without a Bash dependency
- [x] Preserve Bash hook registration and install every referenced hook on macOS and Linux
- [x] Normalize Claude-imported hook output to Cursor JSON while preserving Claude Code behavior and hook deny decisions
- [x] Add Windows, POSIX, fresh-settings, upgrade-repair, full-template, and dangerous-command regression coverage

## Corrective Patch - v3.17.3 Usage Monitor Warning Color Race [DONE]

- [x] Prevent low and critical Codex display ticks from replacing an active High orange warning color with Moderate yellow
- [x] Apply the same shared-token guard and regression coverage to the Claude usage monitor

## Corrective Patch - v3.17.3 Codex Extra Credits Live Payload [DONE]

- [x] Map the live `spend_control.individual_limit` response into detailed Extra Credits usage
- [x] Add a live-shaped 225-of-5,000 regression fixture and pass the full Codex extension gate

## Corrective Patch - Codex Extra Credits Display [DONE]

- [x] Round used and limit credit counts to whole numbers in every display surface
- [x] Render paired live USD amounts without a hard-coded credit conversion and omit incomplete monetary data
- [x] Align the dashboard and hover layouts, then pass the focused and full Codex extension gates

## Release Candidate - v3.17.3 Cursor Hook Portability and Usage Monitor Reliability [DONE]

- [x] Isolate the corrective diff on `fix/v3.17.3-corrective` from the committed Org Knowledge Phase 1 work
- [x] Obtain approval for the diff-derived release notes and the provider-state migration deferral
- [x] Keep the corrective fixes in scope and exclude unfinished Org Knowledge implementation
- [x] Renumber Org Knowledge to v3.17.4 and DeepSeek Harness Adoption to v3.17.5
- [x] Complete canonical version, extension package, release-documentation, and staged manifest updates
- [x] Re-verify platform read contracts and behavioral-default levers for v3.17.3
- [x] Pass the complete bounded local release gates and present the candidate before commit, push, tag, or publication
- [x] Merge the release PR into `main` and pass post-merge and tag CI
- [x] Publish v3.17.3 and verify the downloaded source archive against all 1,239 manifest entries

## Parallel Plan - v3.15.8 Platform Parity and GitHub Usage Monitor [IN PROGRESS]

- [x] Phase 1 - Contracts, probes, and test foundation
- [x] Phase 2 - GitHub usage data and authentication core
- [x] Phase 3 - GitHub usage monitor extension and visual assets
- [x] Phase 4 - Installer distribution, packaging, and focused CI
- [ ] Phase 5 - Codex capability parity
- [ ] Phase 6 - Gemini CLI and Qwen hook parity
- [ ] Phase 7 - Kimi and Copilot capability parity
- [ ] Phase 8 - Cross-platform lifecycle and contract verification
- [ ] Phase 9 - Architecture refactor, known-gaps reconciliation, and CI/CD

## Release Preparation - v3.15.7 [IN PROGRESS]

- [x] Integrate `feat/adoption-raptor-loop-hunt` into the isolated `release/v3.15.7` worktree
- [x] Confirm the release scope and defer newly discovered additive platform drift to v3.15.8
- [x] Reactivate the CI and CodeQL workflows that were manually disabled
- [x] Bump version surfaces and reconcile release documentation
- [x] Regenerate the release manifest and pass all local release gates
- [x] Repair and locally verify the Claude and Codex usage-monitor Node 22 workflows and npm 10 lockfiles
- [x] Obtain explicit approval before push, pull request, protected-branch promotion, tag, or GitHub Release
- [x] Diagnose the release PR failures and correct hook parity, Presentify lint and OCR enrichment, pytest module discovery, executable modes, and EOF hygiene
- [x] Pass the updated release PR checks
- [ ] Repair the Windows PowerShell 5.1 post-merge CI failures and pass the follow-up PR and `develop` push gates
- [ ] Merge the usage-monitor CI repair into `develop`, promote to `main`, pass post-merge CI, tag v3.15.7, and publish the GitHub Release

## Phase 1 - Finding-disposition doctrine [DONE]

- [x] Add two-axis severity and the four-disposition model to `catalog/skills/security/pentest-reporting/SKILL.md`
- [x] Align `catalog/skills/security/exploitability-analyzer/SKILL.md` with the shared disposition vocabulary
- [x] Run validation, lint, tests, the partial-visibility dry check, CI audit, and post-phase documentation

## Phase 2 - Refutation discipline [DONE]

- [x] Add the refutation-validity taxonomy to `catalog/skills/orchestration/adversarial-verifier/SKILL.md`
- [x] Add the rejection proof burden and thin `security-review` rejection gate
- [x] Run validation, lint, tests, dry checks, and post-phase documentation

## Phase 3 - Hunt coverage accounting [DONE]

- [x] Add component denominator and explicit COVERED, OMITTED, and UNCOVERED accounting to `catalog/skills/code-review/security-review/SKILL.md`
- [x] Add multi-altitude traversal and the proven-dirty sink sweep with reciprocal ownership pointers
- [x] Surface the N-of-M coverage promise in `catalog/commands/review.md`
- [x] Run validation, full tests, the coverage dry check, and post-phase documentation

## Phase 4 - Anti-costume-rigor [DONE]

- [x] Add ten fraud-class rows with objective Compare or Diff tells to `catalog/skills/workflow/verification-before-completion/SKILL.md`
- [x] Reference the audit owner from `catalog/skills/security/pentest-reporting/SKILL.md` and add binary report-claim checks
- [x] Run validation, two full test matrices, the mechanical table audit, the CI audit, and post-phase documentation

## Phase 5 - Execution-authorization broker [DONE]

- [x] Build the pure-standard-library typed capability-grant broker under `agent-access-policy`
- [x] Add denial-first, plan-only, sandbox-execution, import, and installer-distribution tests
- [x] Document the broker, v3.15.6 composition seam, and `re-full` policy disposition
- [x] Run validation, coverage, cross-shell smoke checks, full tests, CI audit, and post-phase documentation

## Phase 6 - Closure gate, eval hardening, and monotonicity [DONE]

- [x] Build the pure-standard-library claim-to-evidence closure gate and its review-record schema
- [x] Add mismatch, clean-record, malformed-input, documentation, and installer-distribution tests
- [x] Add adversarial-eval doctrine and the monotonic-scrutiny invariant with durable storage deferred
- [x] Run validation, coverage, full tests, coherence and CI audits, and post-phase documentation

## Phase 7 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD [DONE]

- [x] Audit repository and documentation structure and retain the canonical layout
- [x] Resolve WN-3 and reconcile the durable-store and declined-candidate gaps
- [x] Audit all CI workflows for coverage and action-minute optimization
- [x] Run validation, coverage, full tests, hook tests, and release-readiness checks

## Corrective Patch - v3.17.2 Autonomy Controller Retirement [DONE]

- [x] Remove the shared autonomy engine, CLI, and platform descriptors
- [x] Remove Claude and Codex usage-monitor autonomy indicators and toggles
- [x] Remove expiry and guard hooks plus feature-specific CI
- [x] Remove active controller contracts and user-facing instructions
- [x] Reserve v3.17.2 for the correction and shift planned work to v3.17.3 and v3.17.4
- [x] Pass focused extension, integration, manifest, and repository validation

## Release - v3.17.2 Autonomy Controller Retirement [IN PROGRESS]

- [x] Reconcile the v3.17.1 release ancestry into `release/v3.17.2`
- [x] Add and focus-test the fail-safe legacy-state restoration migration
- [x] Complete the full platform read-contract and defaults-lever re-verification
- [x] Finalize release metadata, documentation, known gaps, and the supply-chain manifest
- [x] Pass the complete local release gates and artifact round-trip
- [ ] Integrate and push `develop`, then pass remote CI
- [ ] Promote `main`, tag v3.17.2, publish the GitHub Release, and verify the downloaded artifact

## Parallel Plan - v3.17.4 Org Knowledge Layer [IN PROGRESS]

- [x] Deep research completed: `docs/v3/v3.17/development/org-knowledge-layer-research.md`
- [x] Plan generated and design decisions confirmed: `docs/v3/v3.17/plans/v3.17.4-org-knowledge-layer.md`
- [x] Complete Phase 1: Org Bundle Contract
- [x] Complete Phase 2: Connect CLI
- [x] Complete Phase 3: Cross-Platform Materialization
- [x] Complete Phase 4: Guided Authoring Surface
- [x] Complete Phase 5: Lifecycle Integration and Docs
- [ ] Complete Phase 6: Architecture Refactor, Known-Gaps Reconciliation, and CI/CD

## Parallel Plan - v3.17.5 DeepSeek Harness Adoption [PLANNED]

- [x] Comparison report written: `docs/v3/v3.17/comparisons/v3.17.5-comparison-deepseek-harness.md`
- [x] Plan generated and phase breakdown confirmed: `docs/v3/v3.17/plans/v3.17.5-adoption-deepseek-harness.md`
- [ ] Complete Phase 1: Doc Word Budgets (B1)
- [ ] Complete Phase 2: deepseek-harness Skill (A1)
- [ ] Complete Phase 3: Skill Extensions (A2 + A3 + A4)
- [ ] Complete Phase 4: Decision-Record Lifecycle (B2)
- [ ] Complete Phase 5: Registry Entry Drift-Check (B4)
- [ ] Complete Phase 6: Invocation-Policy Frontmatter (B3)
- [ ] Complete Phase 7: Architecture Refactor, Known-Gaps Reconciliation, and CI/CD

## Parallel Plan - v3.19.0 Cost-Effective CI/CD

- [ ] Complete Phase 1: Canonical Lifecycle Contract and Baseline Audit
- [ ] Complete Phase 2: Canonical CI/CD Skill Architecture
- [ ] Complete Phase 3: Plan Generation Defaults
- [ ] Complete Phase 4: Implementation and Commit Lifecycle
- [ ] Complete Phase 5: Branch, Release, and Cross-Platform Policy
- [ ] Complete Phase 6: Nexus-Hub Repository-Native CI Engine
- [ ] Complete Phase 7: Nexus-Hub Workflow Migration
- [ ] Complete Phase 8: Architecture Refactor, Known-Gaps Reconciliation, and CI/CD

## Parallel Plan - v3.16.1 Evaluation Methodology and Selective Installation

- [x] Complete `docs/v3/v3.16/comparisons/v3.16.1-comparison-evals-skills-and-claude-codex-settings.md`
- [x] Generate and approve `docs/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md`
- [x] Complete Phase 1: Evaluation Contract and RAG Metrics
- [x] Complete Phase 2: Evaluation Pipeline Audit Skill
- [x] Complete Phase 3: Error Analysis and Evaluator Calibration
- [x] Complete Phase 4: Synthetic Data, Human Review, and Skill Quality
- [x] Complete Phase 5: Selective Installation Contract and Resolution
- [x] Complete Phase 6: Cross-Platform Selective Installation
- [x] Complete Phase 7: Distribution, Parity, and Documentation
- [x] Complete Phase 8: Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
