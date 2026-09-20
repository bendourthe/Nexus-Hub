# Development log: Phase 1 attribution checker

**Date**: 2026-09-14
**Objective**: Implement T001-T005 of the [v4.12 attribution plan](../../../../../releases/v4/v4.12/plans/v4.12.0-sole-contributor-attribution.md), with local evidence before any rewrite.
**Outcome**: Inventory, policy, proposed decision, checker and fixture tests prepared for one local phase commit. No v4.12 branch push, PR or remote CI run.

## 1. Starting State

Branch `feat/v4.12.0-sole-contributor-attribution` started at verified develop `89758d824a92bc7c801dd9c913640c759ac1d6ce`. The preceding cleanup merged PRs #214, #215 and #216 and removed 31 confirmed merged local branches. PR #203 became merged through #215; #197 was closed as superseded by already integrated code. Both final post-merge jobs passed. Unmerged historical refs, seven stashes and ignored worktree artifacts remain preserved; a verified pre-cleanup bundle is external to the checkout.

Environment: Windows PowerShell, Python 3.12.10, Git, pytest, Ruff 0.16.1 and Coverage.py 7.13.4. The current session model was retained because a supported live model-enumeration/switch tool was unavailable; no lower-tier substitution was made.

## 2. Chronological Steps

T001 enumerated 1,696 unique reachable commits and verified account mappings through GitHub commit REST responses and GraphQL co-author records. T002 froze the closed allowlist and proposed the all-ref maintenance decision. T003 added a stdlib checker and its installer-test exclusion. T004 added isolated repository and message fixtures. T005 exercised the real CLI and the fixture suite; all work is scoped to this phase's local commit.

The checker rejects unknown names/emails, forbidden or malformed attribution fields, shallow clones, missing Git, unreadable messages, legacy grafts and malformed Git output. Raw history ignores mailmaps and replacement refs so display configuration cannot hide an author. Both selected operations report findings; environment errors take precedence with exit 2. Diagnostics quote values and cap the displayed rows while retaining the total.

The full docs reference graph exceeded the proportional Phase 1 window and was stopped; the full inventory was retained and the helper completed a v4.12-scoped refgraph over Git-indexed source files (seven documents scanned, two with inbound references). No file move depended on that scan. The operator tool was absent (`git: filter-repo is not a git command`); `uv tool install git-filter-repo --quiet` installed it outside project dependencies, and `git filter-repo --version` returned `a40bce548d2c`. Phase 2 therefore begins with its required tool available.

Initial Ruff output reported `PLW1510 subprocess.run without explicit check argument` on two CLI tests. Both calls now explicitly use `check=False` because nonzero exit status is part of their assertion. The first 41-test run already passed; the formatted, corrected tree passed the 42-test checker-plus-installer selection.

## 3. Verification Gate

| Check | Observed result |
|---|---|
| Checker and installer exclusion tests | 42 passed, 32 unrelated tests deselected |
| Checker statement coverage | 88/90 statements, 97.78%; uncovered CLI guard/usage line exercised in separate subprocess tests |
| Ruff check | All checks passed |
| Fast repository profile | 14 passed, 0 failed, 0 skipped |
| Build/import | Real CLI help and fixture imports succeed; no build artifact required for a stdlib script |
| Clean CLI repository | Exit 0; `Attribution: 1 commits scanned; 0 findings; 0 errors` |
| Dirty CLI repository | Exit 1; Cursor co-author reported; `Attribution: 2 commits scanned; 1 findings; 0 errors` |
| Live pre-rewrite history | Expected exit 1; `Attribution: 1696 commits scanned; 3234 findings; 0 errors` |

### Functional exercise

The maintainer consumer ran `python scripts/check_commit_attribution.py --all-refs --root <temporary-repository>` through the actual CLI, first with one canonical commit and then with a second commit carrying a Cursor trailer. Both results matched their expected exit status and output. The live checkout exercise confirms the scanner detects the history the next phase must rewrite. Evidence is bound to the checker SHA-256 in `../Nexus-Hub-backups/2026-09-14-pre-v4.12-cleanup/phase1-cli-smoke.json`; coverage is in `phase1-coverage.json` beside it. These are current Phase 1 observations, not whole-plan or GitHub contributor-page proof. Functional-verification and verification-before-completion govern the exercise and its limited claim.

## 4. Known Issues

No unresolved Phase 1 implementation findings. [Known gaps](../../../../../releases/v4/v4.12/known-gaps.md) has zero open entries. History is intentionally dirty until Phase 2; CI/live enforcement is intentionally absent until Phase 3.

## 5. Plan Discrepancies

See the required disposition below. The corrections change verification wording, not the requested canonical identity or all-ref scope.

## Plan delta

**False assumption, corrected without expanding scope.** GitHub currently maps both old maintainer name variants at the Gmail address to bendourthe. GraphQL confirms Cursor and Claude co-author accounts; Dependabot remains a separate author. Broad `--grep=cursoragent` also matches ordinary planning prose and is not a valid zero-trailer assertion. The dated inventory and policy replace those assumptions with observed mappings; T008 now checks structured fields while preserving prose. Phase 2 must preserve the backup and all ref names, Phase 3 must reject future unknown identities, and Phase 4 still requires explicit publication approval and GitHub UI evidence. The [queue assessment](../../../../../releases/v4/v4.12/development/phase-1-queue-assessment.md) records 103 readable plans, unknown statuses and shared-file/ref ordering constraints. No Phase 1 prerequisite is blocked.

## 6. Assumptions Made

The requested all-author rewrite includes the eight Dependabot-authored commits. This deliberately reassigns metadata; the inventory and external original backup retain provenance. The policy uses exact names and case-insensitive emails. GitHub's committer is allowed for web commits as well as merges. Any new unmapped identity discovered before rewriting requires policy review instead of guessing.

## 7. Testing Summary

Command: `python -m pytest tests/validators/test_commit_attribution.py catalog/hooks/tests/test_installer_smoke.py -k 'attribution or copy_every_scripts_dir_py_file' --import-mode=importlib --cov=scripts --cov-report=json:../Nexus-Hub-backups/2026-09-14-pre-v4.12-cleanup/phase1-coverage.json --cov-report= -q --disable-warnings --maxfail=1`.

Observed: 42 passed, 32 deselected. Coverage is reported for the changed checker only, not for the whole scripts directory. Tests create temporary repositories and do not scan Nexus-Hub history. Cases cover authors, committers, case normalization, names, trailers, folded fields, ordinary prose, unmerged branch/tag reachability, annotated tags, bare and shallow clones, missing Git, malformed output, unreadable messages and operation disagreement. Human QA is deferred to the last phase.

## CI impact

GitHub Actions is active. Existing validators test discovery covers `tests/validators/test_commit_attribution.py`; installer smoke covers the DEV_ONLY_SCRIPTS exclusion. No dependency, environment secret, required-check name or pipeline file was added. The checker is intentionally absent from Makefile and hygiene until Phase 3. The final phase owns terminal pipeline reconciliation. The cleanup's earlier remote runs are separate from this plan, which has had no remote validation.

## 8. TODO Tracker

- [x] T001 inventory and empty-open gap ledger.
- [x] T002 policy and proposed decision.
- [x] T003 checker and installer exclusion.
- [x] T004 isolated fixture tests.
- [x] T005 local verification, evidence and phase commit.
- [ ] T006-T023 rewrite, prevention wiring and final qualification/publication.

Post-phase sequence: no new gitignore pattern is needed; coverage/caches are already ignored and verbose evidence is external. Test review reran the focused selection. CI impact and plan delta are recorded. Gap counts are zero. Documentation audit preserves active evidence and the proposed decision; DEVLOG and todos point to this phase. README/runtime product documentation has no new user-facing feature to describe. The commit includes this history and the audit report.

## 9. Summary and Next Steps

Phase 1 supplies a locally verified attribution checker and an evidence-based rewrite policy. Phase 2 must create a fresh mirror after this commit, verify remote tips and available space, rewrite a separate clone, and prove clean attribution with unchanged trees, dates and ref names. No history rewrite or force-push has occurred.
