# Last-Phase Evidence - v4.1.2 Minimal Construction Discipline

**Date**: 2026-08-28
**Branch**: `feat/v4.1.2-ponytail-planning`
**Phase starting commit**: `4bb4e4ae`
**Comparison base**: `origin/develop` (planning commit `9081e65d` is already on the open integration pull request)
**Plan**: `docs/releases/v4/v4.1/plans/v4.1.2-adoption-minimal-construction.md`

## 1. Architecture refactor

Commands:

> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py inventory --root docs`
>
> `InventoryExit=0`
>
> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py refgraph --root docs`
>
> `RefgraphExit=0`

`project-refactor` has no bundled detector scripts. Propose-only classification of files this plan added, by glob of the two new skill trees and `git diff --stat origin/develop...HEAD`:

- Stay: the 12 substantive instruction templates plus lockstep parity and `tests/validators/test_construction_discipline_rule.py`; `catalog/skills/code-cleanup/minimal-construction/` (`SKILL.md`, `evals/trigger-cases.json`, `evals/evals.json`, `references/construction-debt.md`); `catalog/skills/code-review/over-engineering-review/` (`SKILL.md`, `evals/trigger-cases.json`); handoffs on `code-simplification`, `code-quality`, and `multi-agent-code-review`; registries; the version-bound contract, comparison, plan, histories, known-gaps, cleanup report, and this evidence file under `docs/releases/v4/v4.1/`.
- Move / Archive / Prune: none proposed.
- Empty directories introduced by this plan: none. The two skill trees contain only the files listed above.
- Duplicate content: none. The comparison and plan name the source repository; distributed skills and templates do not.
- No top-level installer-copied `scripts/*.py` was added. `scripts/check_base_template_parity.py` already existed; this plan only added `Construction Discipline` to its heading lists.

Cluster ownership matches `docs/releases/v4/v4.1/development/v4.1.2-construction-discipline-contract.md`: one owner per concern (pre-write size, post-write collapse, dead code, delete-list, plan scope, security/a11y, proving commands, talk, version ledgers, SQALE, in-code ceilings). No confirmation gate activated because nothing is moved or deleted.

## 2. Known-gaps reconciliation

Glob of `docs/**/known-gaps.md` found 30 unique files (canonical `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md` plus archive copies). File-level Status `in-progress` is only `docs/releases/v4/v4.1/known-gaps.md`. `docs/releases/v4/v4.0/known-gaps.md` is finalized. `docs/releases/v3/v3.20/known-gaps.md` and `docs/releases/v3/v3.21/known-gaps.md` are finalized. Remaining v3 and archive ledgers are historical or complete; none was rewritten.

Evidence:

> `docs/releases/v4/v4.1/known-gaps.md` `## v4.1.2`: Open WN=1, QG=1, NI/DF/BG/MT=0.

This plan produced:

- WN-1: GitHub repository description still says 326 skills while README and the catalog say 328.
- QG-1: hour-scale local `--profile full` was started and had not finished before this evidence file was written.

Not absorbed:

- v4.1.0 DF-1, WN-1, QG-1.
- v4.1.1 DF-1 (optional scanners not executed on this host).
- v4.0 DF-1 (report-artifact upload), declined again in the pipeline comparison below.

## 3. Living docs architecture

Scan:

> `docs/handbooks/` authored files = 1 (`README.md`); `docs/handbooks/html/.gitkeep` and `docs/handbooks/markdown/.gitkeep` only; catalog atlas/companion HTML = 0

The living handbook root remains a scaffold. Release-bound plan, comparison, contract, history, known-gaps, cleanup report, and this evidence file remain under `docs/releases/v4/v4.1/`. `docs/decisions/` was not used for this adoption; the comparison and plan are the attribution record. `docs/DEVLOG.md` already has a v4.1.2 index row. `docs/todos.md` was not invented into a testing or validation tree. No `docs/testing/` or `docs/validation/` path exists.

## 4. Git-tree hygiene

Command:

> `python scripts/check_release_preconditions.py --branches --repo-settings`

Quoted result:

> Branch hygiene (merged into origin/develop)
>   6 merged branch(es) are cleanup candidates:
>     - origin/backmerge/v4.0.0-release
>     - origin/backmerge/v4.1.0-release
>     - origin/backmerge/v4.1.1-release
>     - origin/feat/v4.1.0-release
>     - origin/feat/v4.1.1-adoption-openworker-security-refinement
>     - origin/feat/v4.1.1-release
>   (12 branch(es) with an open PR were excluded)
>   1 branch(es) survive a CLOSED, unmerged PR:
>     - origin/backmerge/v3.20.0
>   delete_branch_on_merge does NOT cover these. Review and delete by hand.
>   Reporting only -- nothing was deleted.
> Repository settings
>   OK: delete_branch_on_merge is enabled
>   NOTE: the repository description disagrees with README.md:
>     - skills: description says 326, README.md declares 328
>         The description is not a version-carrying surface, so
>         check_version_sync.py cannot see it and it drifts silently
>         across releases. Update it by hand.

No remote cleanup, settings edit, push, tag, or release was performed. The description drift is WN-1. Existing pull request [#141](https://github.com/bendourthe/Nexus-Hub/pull/141) already targets `develop` from this branch; it is not a second publication path.

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
> `python scripts/check_version_sync.py` -> canonical `4.1.1`

Provider detected: GitHub Actions (`.github/workflows/*.yml`). `git diff --name-only origin/develop...HEAD -- .github catalog/mcp-configs scripts/installer.sh scripts/installer.ps1 catalog/hooks/settings.json` is empty. No pipeline file change is proposed. Silence is not approval; none is requested.

The two new skills live under `catalog/skills/` and are copied recursively by both installers. No new top-level `scripts/*.py` needs an installer copy block. `check_base_template_parity.py` was already installer-independent (repo-internal guard).

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
| 23 | External settings | PASS with note | `delete_branch_on_merge` is enabled. Description skill-count drift is v4.1.2 WN-1, not a pipeline edit. Nothing mutated. |

Comparison conclusion: PASS for this plan. The only canonical pipeline difference is inherited v4.0 DF-1 (artifact upload). This plan adds no workflow, MCP row, installer copy line, or hook registration.

## 6. Goal-vs-codebase review

Plan Goal restated: give every Nexus-Hub-backed agent a pre-write construction ladder (skip, reuse, stdlib, native, installed dependency, one line, then minimum) without vendoring Ponytail, adding an MCP, injecting a full ruleset through hooks, or weakening security, verification, or communication owners.

Goals First definition of done, inspected independently of phase checkboxes:

| Observable | Artifact | Verdict |
|---|---|---|
| All 12 substantive templates carry identical `Construction Discipline` | `tests/validators/test_construction_discipline_rule.py` `_SUBSTANTIVE` (5 lockstep + 7 unguarded); 32 tests passed; heading present on each listed file | PASS |
| Include-only shims do not duplicate the heading | `_INCLUDE_ONLY` four files; grep of `*antigravity*` and `base-gemini-cli.md` found no heading | PASS |
| Lockstep parity fails if the section drifts | `Construction Discipline` in `REQUIRED_HEADINGS` and `INVARIANT_SECTIONS`; `python scripts/check_base_template_parity.py` exit 0 | PASS |
| `minimal-construction` registered with intensity as a skill argument | `catalog/skills/code-cleanup/minimal-construction/SKILL.md`; `data/skills.json`, `data/SKILL_INDEX.md`, `data/marketplace.json`, `data/bundles.json`; no env/config key in distributed trees | PASS |
| Ownership table names existing owners | skill body plus contract table; `code-simplification` When NOT points here and does not copy the ladder | PASS |
| `over-engineering-review` emits tagged delete-list and does not apply fixes | `catalog/skills/code-review/over-engineering-review/SKILL.md`; optional lens only on `code-quality` and `multi-agent-code-review` | PASS |
| `construction-debt:` harvest is generic and grep-only | `references/construction-debt.md`; no top-level `scripts/*.py` | PASS |
| Evals reward native/stdlib and refuse safety cuts | `evals/evals.json` ids `eval-native-date-control`, `eval-cache-stdlib`, `eval-refused-safety-cut` | PASS |
| No MCP, no `settings.json` mutation, no new installer-copied script | `git diff` empty for `catalog/mcp-configs`, installers, hooks settings, `.github` | PASS |
| No upstream product name in distributed skills or templates | grep of `catalog/skills` and `templates` for `ponytail` / `PONYTAIL`: no matches. Name remains in the comparison and this plan | PASS |
| `verification-before-completion` not weakened | `git diff origin/develop...HEAD -- catalog/skills/testing/verification-before-completion catalog/skills/security catalog/hooks` empty | PASS |

Gaps that remain visible: WN-1, QG-1, and unpublished integration (this file does not claim a green pull request on the implementation commits).

Verdict: PASS for the local catalog contract; integration, merge, and release are not proven here.

## 7. Human/manual testing suggestions

- After install, start a coding task that could add a date-picker or cache package and confirm the agent names a native control or stdlib option before adding a dependency.
- Invoke `over-engineering-review` on a known-bloated diff and confirm it emits tagged lines or `Lean already. Ship.` without applying edits.
- Run a security-review (or a focused trust-boundary check) on a change that omits input validation and confirm the missing check is still reported, not treated as construction debt.
- Confirm lite/full/ultra is accepted only as a skill argument, not as an env var or config file.
- On a POSIX host, dry-run `scripts/installer.sh` and confirm the two new skill trees land under the flattened `skills/<name>/` layout with no extra copy line.

## 8. Full-suite testing and stabilization

Quoted local evidence:

> `python scripts/ci/run.py --profile fast` -> `PASS: 12 passed, 0 failed, 0 skipped, 0 advisory in 114.3s`
>
> `python scripts/check_base_template_parity.py` -> 5 of 5 lockstep templates present, exit 0
>
> `python -m pytest tests/validators/test_construction_discipline_rule.py tests/validators/test_check_base_template_parity.py -q` -> `32 passed in 4.08s`
>
> `python scripts/validate_skills.py --bundles-only` -> `PASS (0 errors, 64 warnings)`
>
> `python scripts/run_trigger_evals.py --gate` -> `RESULT: PASS (0 un-allowlisted collisions, 37 allowlisted; 0 routing failures across 88 skill(s) with cases)` (328 skills scanned)
>
> `python scripts/check_installer_parity.py` -> `installer parity: PASS`
>
> `python scripts/check_required_check_coverage.py` -> `Required-check coverage: OK -- 10 declared context(s)`
>
> `python scripts/check_version_sync.py` -> canonical `4.1.1` (bump belongs to `/update release`)
>
> `python scripts/check_model_prompting_freshness.py --advisory`
>
> `[profile-freshness] UNKNOWN: no live roster supplied, so drift cannot be determined.` Recorded roster (4, last verified 2026-07-27): `claude-fable-5`, `claude-haiku-4-5-20251001`, `claude-opus-5`, `claude-sonnet-5`. This is v4.1.0 DF-1, not absorbed.
>
> Hour-scale `python scripts/ci/run.py --profile full` was started on this host and had not produced a final profile report when this evidence was written (QG-1)

`.gitignore` already ignores `.coverage`; 0 patterns added.

## 9. Publication and integration

Performed. Feature branch `feat/v4.1.2-ponytail-planning` was pushed once (`9081e65d..2a575519`) and updated pull request [#141](https://github.com/bendourthe/Nexus-Hub/pull/141). Required checks on the merge result were green: `validate`, `shellcheck`, `ci-required`, `colocation`, and `verify`. The pull request merged into `develop` at `34d8272b` (2026-08-29T04:59:00Z). Post-merge workflow run `33235080095` succeeded (`smoke` + `provenance` only; it did not rerun the complete suite). `/update release` for v4.1.2 proceeds from that green merged result.
