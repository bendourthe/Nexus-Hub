# Last-Phase Evidence - v4.1.1 Local Security-Audit Refinement

**Date**: 2026-08-28
**Branch**: `feat/v4.1.1-adoption-openworker-security-refinement`
**Phase starting commit**: `a94bef54`
**Comparison base**: `origin/develop` (`7ecfe3eb`)
**Plan**: `docs/releases/v4/v4.1/plans/v4.1.1-adoption-openworker-security-refinement.md`

## 1. Architecture refactor

Commands:

> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py inventory --root docs`
>
> `InventoryExit=0`
>
> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py refgraph --root docs`
>
> `RefgraphExit=0`

`project-refactor` and `docs-layout-refactor` ran in propose-only mode over files this plan touched. Classification:

- Stay: schema-v2 closure gate and recipes under `catalog/skills/code-review/security-review/`; owner recipes on existing skills; `agent-presets` evals; `catalog/agents/security-reviewer.md`; inert fixtures under `tests/fixtures/security-audit/`; e2e and installer tests; `guides/reference/SECURITY_AUDIT.md`; version-bound contract, histories, known-gaps, cleanup report, final audit, and this evidence file under `docs/releases/v4/v4.1/`.
- Move / Archive / Prune: none proposed.
- Empty directories introduced by this plan: none.
- Duplicate content: none. The comparison names OpenWorker; distributed artifacts do not.
- Untracked `docs/releases/v4/v4.1/comparisons/v4.1.2-comparison-ponytail.md` is outside this plan and was not staged.

Ownership is recorded in `docs/releases/v4/v4.1/development/v4.1.1-security-audit-final-audit.md`. No confirmation gate activated because nothing is moved or deleted.

## 2. Known-gaps reconciliation

Evidence:

> `docs/releases/v4/v4.1/known-gaps.md` `## v4.1.1`: Open DF=2, QG=1, NI/BG/WN/MT=0

DF-1: live optional scanners were not executed on this host. DF-2: POSIX installer dry-run was not executed on this Windows host. QG-1: local full CI profile was not completed here.

Other ledgers:

- `docs/releases/v4/v4.1/known-gaps.md` `## v4.1.0` remains in-progress on the same file. Its DF-1, WN-1, and QG-1 were not absorbed.
- `docs/releases/v4/v4.0/known-gaps.md` Status is finalized. Its DF-1 (report-artifact upload) was declined for reopen in the pipeline comparison below and stays on that ledger.
- `docs/releases/v3/v3.20/known-gaps.md` and `docs/releases/v3/v3.21/known-gaps.md` Status is finalized. Their deferred items stay on those ledgers.
- Remaining `docs/releases/v3/**/known-gaps.md` and archive ledgers are historical or finalized; none was rewritten.

## 3. Living docs architecture

Scan:

> `docs/handbooks/` authored files = 1 (`README.md`); `docs/handbooks/html/.gitkeep` and `docs/handbooks/markdown/.gitkeep` only; catalog atlas/companion HTML = 0

The living handbook root remains a scaffold. Release-bound plan, comparison, history, contract, cleanup, known-gap, final audit, and this evidence file remain under `docs/releases/v4/v4.1/`. The user guide lives at `guides/reference/SECURITY_AUDIT.md`, matching other reference guides. No `docs/testing/` or `docs/validation/` tree was invented.

## 4. Git-tree hygiene

Command:

> `python scripts/check_release_preconditions.py --branches --repo-settings`

Quoted result:

> Branch hygiene (merged into origin/develop)
>   3 merged branch(es) are cleanup candidates:
>     - origin/backmerge/v4.0.0-release
>     - origin/backmerge/v4.1.0-release
>     - origin/feat/v4.1.0-release
>   (11 branch(es) with an open PR were excluded)
>   1 branch(es) survive a CLOSED, unmerged PR:
>     - origin/backmerge/v3.20.0
>   delete_branch_on_merge does NOT cover these. Review and delete by hand.
>   Reporting only -- nothing was deleted.
> Repository settings
>   OK: delete_branch_on_merge is enabled
>   OK: repository description agrees with README.md

Working tree keeps untracked `docs/releases/v4/v4.1/comparisons/v4.1.2-comparison-ponytail.md` unstaged. No remote cleanup, settings edit, push, pull request, tag, or release was performed.

## 5. CI/CD coverage

Coverage inventory:

> `python scripts/ci/run.py --profile full --list`
>
> groups: catalog-parse, hygiene, catalog, security, workflows, platform-contracts, docs, version, tests (hook-tests + repo-tests), extension-tests
>
> `python scripts/check_required_check_coverage.py`
>
> `Required-check coverage: OK -- 10 declared context(s) across 2 branch(es), every one produced unconditionally.`
>
> `python scripts/check_installer_parity.py` -> `installer parity: PASS`
>
> `python scripts/check_version_sync.py` -> canonical `4.1.0`

Provider detected: GitHub Actions (`.github/workflows/*.yml`). No pipeline file change is proposed. Silence is not approval; none is requested. Real scanner execution must not be added to CI.

Existing-pipeline comparison (canonical fields from `catalog/skills/infrastructure/cicd-architect/references/repository-native-profiles.md`):

| # | Field | State | Evidence |
|---|---|---|---|
| 1 | Provider detected | PASS | GitHub Actions; `.github/workflows/ci.yml`, `post-merge.yml`, `release.yml` |
| 2 | Profiles exist | PASS | `scripts/ci/run.py` profiles `fast`, `full`, `platform`, `report`, `release` |
| 3 | No duplicated validator | PASS | `ci.yml` jobs call `scripts/ci/run.py`; validator lists live in `scripts/ci/profiles.py` |
| 4 | Feature-push runs nothing | PASS | `ci.yml` `on:` is `pull_request` + `merge_group` + `workflow_dispatch`; no ordinary branch `push` |
| 5 | Integration gate is complete | PASS | `ci.yml` runs on PRs to `main`/`develop` including Windows and bootstrap/install-smoke jobs |
| 6 | No duplicate post-merge suite | PASS | `post-merge.yml` is smoke and provenance, not `ci.yml` again |
| 7 | Post-merge is minimal | PASS | `post-merge.yml` smoke job plus advisory version note |
| 8 | Release is separate | PASS | `release.yml` on `v*` tags and dispatch; `permissions: contents: read`; no cancel-in-progress |
| 9 | Aggregate required check | PASS | `ci-required` job `if: always()`; `docs/policy/required-checks.json` lists `ci-required` plus `validate`, `shellcheck`, `colocation`, `verify` |
| 10 | No per-leg required context | PASS | required list has no `job (leg)` names; `test_ci_required_gate.py` enforces this |
| 11 | Scoping is job-level | PASS | no workflow-level `paths:` on `ci.yml`; `changes` job fail-closed |
| 12 | Runner selection | PASS | `ubuntu-latest` and `windows-latest` GitHub-hosted; no self-hosted |
| 13 | Expensive legs pre-merge | PASS | Windows PowerShell 5.1 and installer-smoke run on the pull request |
| 14 | Immutable references | PASS | third-party actions use 40-character SHAs with version comments (for example `actions/checkout@93cb6efe... # v5`) |
| 15 | Least-privilege permissions | PASS | `ci.yml` `permissions: contents: read` |
| 16 | Caching | PASS | pip cache keyed to manifests on CI Python jobs; cold-install smoke jobs do not reuse that cache as a substitute for install |
| 17 | Concurrency | PASS | `ci.yml` cancels superseded PR runs; `release.yml` and `post-merge.yml` set `cancel-in-progress: false` |
| 18 | Untrusted forks | PASS | `contents: read`; no secrets in `ci.yml`; hosted runners |
| 19 | Reports produced | PASS | `scripts/ci/reporting.py` writes summary, JUnit, and metadata locally; CodeQL SARIF goes to the security tab |
| 20 | Reports published | DECLINED (inherited) | machine-readable artifacts are not uploaded. Recorded as v4.0 DF-1; not reopened here |
| 21 | Deployment boundary | PASS | this repository has no application deploy job; `release.yml` is publication-readiness only |
| 22 | Failure recovery | PASS | `implement-phase` 9F and `cicd-architect` section 6 require local reproduction before re-push |
| 23 | External settings | PASS | `docs/releases/v4/v4.0/development/github-ci-settings-runbook.md`; `check_release_preconditions.py --repo-settings` reports OK; nothing mutated |

Comparison conclusion: PASS for this plan. The only canonical difference is inherited v4.0 DF-1 (artifact upload). This plan adds no workflow, dependency, scanner job, or installer copy line.

## 6. Goal-vs-codebase review

Plan Goal restated: make Nexus-Hub's local security-audit workflow prove which deterministic scanners ran, separate remediation from verification, and require a same-detector post-fix re-scan, without OpenWorker, MCP, hosted scanning, or auto-install.

Goals First definition of done, inspected independently:

| Observable | Artifact | Verdict |
|---|---|---|
| Schema-v1 remains valid; schema-v2 adds fail-closed receipts | `closure-gate.py`, `references/closure-gate-review-record.md`, `tests/skills/test_closure_gate.py` | PASS |
| Every applicable scanner has one of five receipt states; none disappears silently | schema-v2 `scanner_inventory` + `scanner_receipts`; fixture `applicable-scanner-omitted` | PASS |
| Corrected finding links equivalent before/after receipts | `corrected_scanner_findings_without_equivalent_rescan` and `mismatched_detector_config_or_scope` | PASS |
| Patch-producing context cannot be the only verifier | `fixer_is_sole_verifier`; `security-reviewer.md` remains without Write/Edit | PASS |
| Ordered `security-audit` preset aligned with `data/workflows.json` | `agent-presets/SKILL.md`, `data/workflows.json` id `security-audit` | PASS |
| Optional local scanner recipes; no auto-install or hosted fallback | `local-scanner-recipes.md` and owning skills | PASS |
| Cloud posture stays read-only | `cloud-security-posture-detection` recipes; guide | PASS |

Gaps that remain visible: DF-1, DF-2, QG-1, and unpublished integration (this file does not claim a green pull request).

Verdict: PASS for the local catalog contract; integration, merge, and release are not proven here.

## 7. Human/manual testing suggestions

- Run the `security-audit` preset on a repository with no optional scanners and confirm every applicable receipt is `UNAVAILABLE` or `NOT_APPLICABLE` and coverage is `degraded`.
- Run it on a repository that has Semgrep and gitleaks installed and confirm gitleaks artifacts contain `[REDACTED]` rather than secret values.
- After a user-approved patch, confirm the after receipt uses the same scanner id, config fingerprint, and target fingerprint as the before receipt.
- Confirm cloud posture does not apply or deploy.
- Confirm a one-CVE question does not activate the full preset.
- On a POSIX host, dry-run `scripts/installer.sh` and confirm `security-review/scripts/`, `security-review/references/local-scanner-recipes.md`, and `agent-presets/evals/` land under the flattened skills tree.

## 8. Full-suite testing and stabilization

Quoted local evidence:

> `python -m pytest tests/skills/test_closure_gate.py tests/skills/test_security_audit_contract_e2e.py tests/skills/test_security_audit_workflow.py tests/skills/test_security_scanner_contract.py tests/installer/test_install_selection.py -q` -> `147 passed in 8.35s`
>
> `python -m pytest tests/skills -q` -> `952 passed` (Phase 4)
>
> `python scripts/validate_skills.py --path catalog/skills/code-review/security-review --allow-existing` -> `PASS (0 errors, 6 warnings)`
>
> `python scripts/validate_skills.py --bundles-only` -> `PASS (0 errors, 64 warnings)`
>
> `python scripts/ci/run.py --profile fast --only catalog-parse,workflows,version` -> `PASS: 7 passed`
>
> `python scripts/validate_no_personal_paths.py` -> exit 0
>
> `python scripts/run_trigger_evals.py --gate` -> `0 routing failures` (Phase 4)
>
> `python scripts/ci/run.py --profile fast` (all groups) -> failed `validate_unicode_safety` on untracked `docs/releases/v4/v4.1/comparisons/v4.1.2-comparison-ponytail.md`, which is outside this plan and is not staged
>
> Hour-scale `python -m pytest tests -q` / `--profile full` was not completed in this last phase (QG-1)
>
> `python scripts/check_model_prompting_freshness.py --advisory`
>
> `[profile-freshness] UNKNOWN: no live roster supplied, so drift cannot be determined.` Recorded roster (4, last verified 2026-07-27): `claude-fable-5`, `claude-haiku-4-5-20251001`, `claude-opus-5`, `claude-sonnet-5`

No live scanner CLI was invoked. `.gitignore` already ignores `.coverage`; 0 patterns added.

## 9. Publication and integration

Not performed. The branch is local only (`24771ad2` .. `a94bef54` plus this Phase 5 commit once created). Explicit approval is required before the first push and before opening the integration pull request to `develop`. `/update release` is blocked until that pull request is green and merged.
