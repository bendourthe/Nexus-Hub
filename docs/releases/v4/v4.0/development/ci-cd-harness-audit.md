# CI/CD Harness Lifecycle Audit (baseline, v4.0.0 Phase 1)

**Project**: Nexus-Hub
**Status**: baseline, measured 2026-08-25
**Measured against**: [`ci-cd-lifecycle-contract.md`](ci-cd-lifecycle-contract.md)
**Plan**: [`docs/releases/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md`](../plans/v4.0.0-cost-effective-ci-cd.md)

This is the current-state matrix for every harness surface that makes a lifecycle statement. Each row names the authoritative artifact, quotes what it says today, states the conflict with the contract, names the owning artifact for the change, and names the phase and test that closes it.

The distinction between a thin dispatcher and a heavy skill is preserved throughout. A command file surfaces a guarantee; a skill carries the procedure. A later phase that copies procedure into a command is a regression, not an implementation.

## Legend

- **Owner**: the artifact that MUST carry the rule. Every other surface cross-links it.
- **Kind**: `dispatcher` (thin, surfaces a guarantee), `skill` (heavy, carries procedure), `template` (installed instruction surface), `repo` (this repository's own governance).

## A. Plan generation surfaces

| # | Surface | Kind | Current behavior (evidence) | Conflict with the contract | Owner | Closing phase | Validating test |
|---|---|---|---|---|---|---|---|
| A1 | `catalog/skills/workflow/implementation-plan/SKILL.md` line 285 | skill | Each phase's testing sub-task prompt says to update the "CI/CD pipeline to cover this phase's changes and optimize it to reduce CI action minutes" | Contract 2.1: a phase may change pipeline files only when the pipeline is that phase's deliverable. Per-phase pipeline authorship produces divergent topologies. | `implementation-plan` | 3 | `tests/skills/test_plan_lifecycle_contract.py` |
| A2 | `catalog/skills/workflow/implementation-plan/SKILL.md` line 389 | skill | The "CI/CD per phase" contract row states every phase creates or updates CI/CD | Same as A1, stated as a rule rather than a prompt | `implementation-plan` | 3 | `tests/skills/test_plan_lifecycle_contract.py` |
| A3 | `catalog/skills/workflow/implementation-plan/SKILL.md` line 495 | skill | The Verification checklist requires the per-phase CI/CD update | Same as A1, stated as a gate, so removing A1 and A2 alone would leave a failing checklist | `implementation-plan` | 3 | `tests/skills/test_plan_lifecycle_contract.py` |
| A4 | `implementation-plan` generated phase template | skill | Generated phases carry no explicit "do not push" statement | Contract 2.1: a non-final phase MUST NOT push. Silence is read as permission. | `implementation-plan` | 3 | `tests/skills/test_plan_lifecycle_contract.py` |
| A5 | `implementation-plan` mandatory final phase (N.5) | skill | N.5 is "CI/CD create/update/optimize": create or update the pipeline and optimize action minutes | Contract 7: the terminal duty is a compare-propose-approve-apply reconciliation against a named contract, not an open-ended optimize | `implementation-plan` | 3 | `tests/skills/test_plan_lifecycle_contract.py` |
| A6 | `catalog/commands/plan.md` line 59 | dispatcher | Surfaces the fail-closed last phase and correctly refuses to duplicate the template | No conflict on structure. Missing: the lifecycle guarantee (local commit per phase, no non-final push, terminal reconciliation). | `plan.md` | 3 | `tests/skills/test_plan_lifecycle_contract.py` |

## B. Implementation and commit surfaces

| # | Surface | Kind | Current behavior (evidence) | Conflict with the contract | Owner | Closing phase | Validating test |
|---|---|---|---|---|---|---|---|
| B1 | `implement-phase/references/implement-phase-runbook.md` step 8.10, one-phase mode | skill | Always asks a four-option prompt whose option 2 is "Commit and push" | Contract 2.1: a non-final phase MUST NOT offer push as a completion path | `implement-phase-runbook.md` | 4 | `tests/skills/test_implement_lifecycle_contract.py` |
| B2 | `implement-phase-runbook.md` step 8.10, `phase-by-phase` mode | skill | Five-option menu whose options 2 and 4 push | Same as B1, in the interactive driver | `implement-phase-runbook.md` | 4 | `tests/skills/test_implement_lifecycle_contract.py` |
| B3 | `implement-phase-runbook.md` step 8.10, `in-full` mode | skill | Already commit-only on non-final phases, no push | Conforms. This is the shape the other two modes must adopt. | `implement-phase-runbook.md` | 4 | `tests/skills/test_implement_lifecycle_contract.py` |
| B4 | `implement-phase-runbook.md` step 8.3 | skill | Per-phase "CI/CD readiness + optimization": detect the CI system and run an optimization pass every phase | Contract 2.1: a non-final phase records CI impact; it does not run an optimization pass on the pipeline | `implement-phase-runbook.md` | 4 | `tests/skills/test_implement_lifecycle_contract.py` |
| B5 | `implement-phase-runbook.md` section 9.0 duty 5 | skill | Final-phase duty is "create or update the CI/CD pipeline ... and optimize it to reduce action minutes" | Contract 7: must be the named reconciliation with a recorded PASS or a known gap, not an optimize pass | `implement-phase-runbook.md` | 4 | `tests/skills/test_implement_lifecycle_contract.py` |
| B6 | `implement-phase-runbook.md` section 9B / 9C-9E | skill | Verifies tests and CI/CD readiness, then hands off to `/update release` | Contract 2.2: the handoff must additionally require that the branch was published, the integration pull request is green, and the merge landed | `implement-phase-runbook.md` | 4 | `tests/skills/test_implement_lifecycle_contract.py` |
| B7 | `implement-phase/SKILL.md` invariants (lines 38-40) | skill | States the ten-step 8.x sequence ends in "the REQUIRED commit-and-push prompt" | Same as B1, restated in the always-loaded invariant list | `implement-phase/SKILL.md` | 4 | `tests/skills/test_implement_lifecycle_contract.py` |
| B8 | `catalog/commands/implement.md` lines 22, 34 | dispatcher | Advertises the push options and "the commit-and-push prompt" | Same as B1, in the dispatcher. Must become a guarantee, not a menu. | `implement.md` | 4 | `tests/skills/test_implement_lifecycle_contract.py` |
| B9 | `catalog/skills/workflow/code-commit-workflow/SKILL.md` | skill | Generic atomic-commit workflow. Push guidance is generic (`git push -u origin ...`), with no plan-context mode | Contract 2.1: needs an explicit plan-context mode (accumulate within a phase, commit once at the boundary, non-final commits stay local) without weakening the generic one-off workflow | `code-commit-workflow` | 4 | `tests/skills/test_implement_lifecycle_contract.py` |

## C. Branch, release, and repository governance surfaces

| # | Surface | Kind | Current behavior (evidence) | Conflict with the contract | Owner | Closing phase | Validating test |
|---|---|---|---|---|---|---|---|
| C1 | `catalog/skills/workflow/git-branching-workflow/SKILL.md` | skill | Resolves the declared model and enforces "never commit feature or version work directly to the protected branch". No statement about when a feature branch is published. | Contract 2.2 and 2.3: needs delayed publication (final phase only) and the external protected-branch settings contract that makes a filtered push event mean "merge" | `git-branching-workflow` | 5 | `tests/skills/test_cicd_lifecycle_contract.py` |
| C2 | `catalog/commands/update.md` line 31 | dispatcher | `release` "reconciles the version's known gaps and creates/updates/optimizes CI/CD" as part of the ship flow | Contract 7 and 2.2: reconciliation belongs to the plan's final phase, before publication. At release the pipeline is already reconciled; release must instead verify green integration. | `update.md` | 5 | `tests/skills/test_cicd_lifecycle_contract.py` |
| C3 | `catalog/commands/update.md` release preconditions | dispatcher | Gates on clean tree, version sync, approved notes. No gate on "the plan branch is integrated and integration CI is green". | Contract 2.2: `/update release` MUST NOT begin until integration is green and merged | `update.md` | 5 | `tests/skills/test_cicd_lifecycle_contract.py` |
| C4 | `catalog/skills/workflow/version-upgrade/SKILL.md` | skill | Version bump mechanics, no integration-state precondition | Same as C3, at the skill layer | `version-upgrade` | 5 | `tests/skills/test_cicd_lifecycle_contract.py` |
| C5 | Root `AGENTS.md` "Branching and Release Workflow" | repo | Documents develop-plus-main and the `/update release` flow. No lifecycle statement about phase commits, non-final push, or terminal reconciliation. | Contract 2: this repository must follow the lifecycle it distributes | `AGENTS.md` | 5 | `tests/validators/test_ci_workflow_contract.py` |
| C6 | Root `CLAUDE.md` | repo | Imports `AGENTS.md` and carries a six-rule quick reference | Inherits C5. The quick reference should surface the lifecycle rule. | `CLAUDE.md` | 5 | `tests/validators/test_ci_workflow_contract.py` |

## D. Platform instruction templates

Twelve substantive templates exist; five are machine-locked in lockstep by `scripts/check_base_template_parity.py`, and seven are not. The seven unguarded files are the ones a change silently misses, which is exactly the failure recorded as DF-1 in the v4.0.0 known gaps.

| # | Surface | Kind | Current behavior | Conflict | Owner | Closing phase | Validating test |
|---|---|---|---|---|---|---|---|
| D1 | `base-claude.md`, `base-codex.md`, `base-cursor.md`, `base-gemini.md`, `base-opencode.md` | template | Carry `Branching`, `Consequential Decisions`, `End-of-Task Summary`. No plan-lifecycle or CI/CD rule. | Contract 13.6: the canonical templates MUST carry the shared lifecycle rule | the five lockstep templates | 5 | `scripts/check_base_template_parity.py`, `tests/skills/test_cicd_lifecycle_contract.py` |
| D2 | `base-google-shared.md` | template | Inherited by Antigravity 1.0, Antigravity 2.0, Gemini CLI, and (transitively) Antigravity CLI | Same as D1, and not covered by the five-file parity roster | `base-google-shared.md` | 5 | `tests/skills/test_cicd_lifecycle_contract.py` |
| D3 | `base-aider.md`, `base-kimi.md`, `base-openclaw.md`, `base-qwen.md`, `base-windsurf.md` | template | Guardrails-only templates | Same as D1, at guardrail density | the five guardrails templates | 5 | `tests/skills/test_cicd_lifecycle_contract.py` |
| D4 | `generic-instructions.md` | template | Fallback for platforms with no dedicated template | Same as D1 | `generic-instructions.md` | 5 | `tests/skills/test_cicd_lifecycle_contract.py` |
| D5 | Copilot | template | Inherits `base-codex.md`; no separate body | No conflict. Inheritance MUST be tested rather than duplicated. | (inherited) | 5 | `tests/integrations/` |
| D6 | Nexus AI | template | Inherits `base-claude.md` | Same as D5 | (inherited) | 5 | `tests/integrations/` |

## E. CI/CD skills

| # | Surface | Kind | Current behavior | Conflict | Owner | Closing phase | Validating test |
|---|---|---|---|---|---|---|---|
| E1 | `catalog/skills/infrastructure/cicd-architect/SKILL.md` (790 lines) | skill | Over the 500-line Tier 2 target and under the 800-line hard cap. Provider-specific worked examples inline. No repository-native profile concept, no lifecycle, no existing-pipeline comparison mode. | Contract 3, 4, 7: this is the canonical owner and currently owns none of it | `cicd-architect` | 2 | `tests/skills/test_cicd_lifecycle_contract.py` |
| E2 | `cicd-architect/references/` | skill | Existing references exist but carry no provider event model or profile schema | Contract 12: the per-provider mapping must be a named reference | `cicd-architect` | 2 | `scripts/validate_skills.py --bundles-only` |
| E3 | `catalog/skills/infrastructure/cd-pipeline-generator/SKILL.md` (153 lines) | skill | Independent deployment defaults. Links `[[cicd-architect]]` in the Related Skills footer only, which is a pointer rather than a conformance statement. | Contract 4: deployment runs from protected events over a validated immutable artifact, and the rule must be owned once | `cd-pipeline-generator` | 2 | `tests/skills/test_cicd_lifecycle_contract.py` |
| E4 | `catalog/skills/tests-generation/cicd-integration/SKILL.md` (516 lines) | skill | Generates "push and pull request" test pipelines with its own trigger defaults. Same footer-only link as E3. | Contract 4: ordinary feature-branch pushes run nothing | `cicd-integration` | 2 | `tests/skills/test_cicd_lifecycle_contract.py` |
| E5 | `catalog/skills/code-review/plan-review/SKILL.md` | skill | Reviews plans across four lenses; no lifecycle checks | Contract 2: a plan review should flag per-phase pushes and a missing terminal reconciliation | `plan-review` or `cross-artifact-analyzer` | 3 | `tests/skills/test_plan_lifecycle_contract.py` |

## F. Installer and rendering paths

| # | Surface | Kind | Current behavior | Conflict | Owner | Closing phase | Validating test |
|---|---|---|---|---|---|---|---|
| F1 | `scripts/lib/integrations/` | repo | Each integration renders the instruction template into that platform's read path | No conflict. The lifecycle block rides the template, so no adapter change is needed; the rendering MUST be tested. | (unchanged) | 5 | `tests/integrations/test_parity_with_legacy_installer.py` |
| F2 | `catalog/hooks/tests/test_platform_parity.py` | repo | Asserts per-platform artifact parity | Missing: an assertion that the lifecycle block appears exactly once per rendered destination | `test_platform_parity.py` | 5 | itself |
| F3 | `scripts/installer.sh`, `scripts/installer.ps1` | repo | Copy scripts by explicit name | Phase 6 adds `scripts/ci/`. A new directory is NOT auto-copied; it is also repository-internal maintainer tooling, so it belongs in `DEV_ONLY_SCRIPTS` rather than in the copy blocks. | `test_installer_smoke.py` | 6 | `catalog/hooks/tests/test_installer_smoke.py` |

## G. Ownership decisions recorded here

Three overlaps were resolved during this audit so later phases do not duplicate a rule.

1. **Lifecycle policy** is owned by `cicd-architect` for the pipeline half and by `implementation-plan` plus `implement-phase` for the phase half. `code-commit-workflow` owns commit atomicity only; `git-branching-workflow` owns branch model resolution and publication timing only. No other surface states these rules; they cross-link.
2. **Plan lifecycle review** is owned by `plan-review` when the target is a plan document, because `cross-artifact-analyzer` operates over a feature directory rather than a single plan and would need a new scope to see one. Phase 3 records the choice in its session history.
3. **Required-check topology** is owned by `docs/policy/required-checks.json` plus `scripts/check_required_check_coverage.py`, which already exist and already encode contract section 5. The CI/CD contract cites them rather than restating the rule.

## G2. Correction made during Phase 1

Rows E3 and E4 initially recorded "no cross-link to a canonical CI policy". That was wrong: both skills already carry `[[cicd-architect]]` in their Related Skills footer. The strict-xfail contract test caught it by passing when it was expected to fail.

The rows are corrected above, and the assertion was TIGHTENED rather than deleted: `test_related_cicd_skills_declare_conformance_not_just_a_footer_link` now requires the conformance statement to appear in the skill BODY, which is what Phase 2 actually delivers. A footer link and a conformance rule are different things, and a test that cannot tell them apart proves nothing.

## H. Surfaces deliberately not changed

- `catalog/skills/workflow/shipping-and-launch/SKILL.md`: production launch verification. It runs after release and is downstream of every rule here.
- `catalog/skills/orchestration/quality-gate-definitions/SKILL.md`: defines reusable GO/NO-GO gates, which the lifecycle consumes rather than redefines.
- `scripts/check_required_check_coverage.py` and `docs/policy/required-checks.json`: already conforming (see G3).
- The four usage-monitor workflows: extension-scoped, already path-filtered, and outside this plan's stated scope except for the event-separation pass in Phase 7.
