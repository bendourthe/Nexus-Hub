# Development log: Phase 2 isolated history rewrite

**Date**: 2026-09-14
**Objective**: Complete T006-T009 of the [v4.12 plan](../../plans/v4.12.0-sole-contributor-attribution.md) locally, preserving recoverable original history.
**Outcome**: All 139 captured refs were rewritten in a separate repository; 1,697 commits pass attribution checks and preservation comparisons. No remote history changed.

## 1. Starting State

Original Phase 1 commit: `1b8f94df618fa1d2bba84eb51ca82356c1394201`. The working tree was clean before backup. Rewritten Phase 1 commit: `0dd54bad647345d0602f31d20e535faccd1c2374`. The [backup record](../rewrite-backup.md) names the verified original mirror, active rewritten worktree, recovery command and disabled push destination.

## 2. Chronological Steps

T006 cloned an independent mirror with `--no-hardlinks`, compared all 139 ref names and SHAs, compared both 1,697-commit sets, checked the captured GitHub tips, retained the seven-entry stash reflog and ran `git fsck --full` successfully. Available space was 401 GB for an approximately 239 MB object database.

T007 first exercised the callback on a real temporary repository. The full copy then failed on a long internal Codex checkpoint path: `Filename too long`. The failure changed no ref, verified against the manifest. `core.longpaths=true` in the isolated copy allowed the same operation to succeed. Original failed output remains in `rewrite-output.txt`; success is separately recorded in `rewrite-longpaths-output.txt`.

T008 independently compared raw objects through the commit map, then expired reflogs and pruned obsolete objects only in the rewritten copy. A former Cursor-trailer SHA is absent from the rewrite and recoverable in the backup. T009 reran the fixture suite and live checker from the rewritten working checkout. The source checker and tests did not change in this phase.

## 3. Verification Gate

| Check | Observed result |
|---|---|
| Original mirror fsck | Exit 0 |
| Original/mirror ref-set and commit-set equality | 139 refs and 1,697 commits; no difference |
| Rewrite fixture | Clean checker; tree, dates, GitHub committer, prose and tag preserved |
| Rewritten live scan | Exit 0; 1,697 commits, zero findings, zero errors |
| Original/new tree equality | 1,697/1,697 |
| Original/new author and committer timestamps | 1,697/1,697 |
| Ordered parent relationships | 1,697/1,697 after mapping |
| Co-author fields stripped | 182; all other message bytes preserved |
| Ref names retained | 139/139; 118 tags |
| Former Cursor SHA | Absent from rewritten copy; present in backup |
| Checker and installer-exclusion tests | 42 passed, 32 unrelated tests deselected |
| Fast repository profile | 14 passed, 0 failed, 0 skipped |

## 4. Known Issues

No unresolved Phase 2 implementation finding. The original stash reflog remains backup metadata, not a public ref set. Local-only historical branches and internal refs are not automatically approved for publication. Remote contributor-page proof remains a Phase 4 duty.

## 5. Plan Discrepancies

The Windows long-path setting was an environment repair on the isolated copy. Phase 1 already corrected the invalid broad-prose grep assertion. The plan's documented-checkout option is used; the original checkout is deliberately not replaced in place.

## Plan delta

**No delta.** Phase 1's refreshed policy and T008 verification apply unchanged. Phase 2 re-enumerated 103 readable plans; no source or CI files changed between phase entries. The repository-wide ref snapshot constraint remains: Phase 3 may modify the rewritten candidate locally, while Phase 4 must compare current GitHub tips with the captured manifest before any approved publication. The full plan-entry membership and shared-file assessment remains in [Phase 1 queue assessment](../phase-1-queue-assessment.md); current inventory is retained externally as `phase2-queue.json`. The current session model remains in use; no lower-tier substitution occurred.

## 6. Assumptions Made

All captured refs are rewritten locally, including internal refs needed for a truthful `--all-refs` scan. Publication scope is narrower than the backup's internal-ref inventory and must be explicitly reviewed. Only the independent target is eligible for reflog expiration and object pruning. Original objects and the manifest remain recoverable.

## 7. Testing Summary

The actual CLI `python scripts/check_commit_attribution.py --all-refs --root .` ran from the rewritten working checkout and returned `Attribution: 1697 commits scanned; 0 findings; 0 errors`, matching the expected clean result. Fixture, raw-object and live-scan evidence is retained beside the mirror in `rewrite-fixture.json`, `rewrite-proof.json` and `rewrite-live-scan.txt`. These observations prove local history properties; they do not prove GitHub has accepted or refreshed anything.

`python -m pytest tests/validators/test_commit_attribution.py catalog/hooks/tests/test_installer_smoke.py -k 'attribution or copy_every_scripts_dir_py_file' --import-mode=importlib -q --disable-warnings --maxfail=1` returned 42 passed, 32 deselected. Phase 1 coverage applies to identical checker bytes; no new coverage percentage is claimed. Human QA is deferred to the last phase.

## CI impact

No pipeline file, runtime dependency, secret, required context or test path changed. GitHub Actions still discovers the Phase 1 tests. The live history gate remains off until Phase 3. The operator tool is installed outside the project. No branch push, PR or remote CI run occurred for this plan.

## 8. TODO Tracker

- [x] T006 independent verified backup.
- [x] T007 all-ref rewrite in an isolated repository.
- [x] T008 clean live scan and preservation proof.
- [x] T009 fixture rerun, evidence and one local phase commit.
- [ ] T010-T023 maintainer enforcement and final qualification/publication.

Post-phase review requires no new gitignore pattern, source refactor or user-facing README change. Backup artifacts live outside both checkouts; active records remain in the v4.12 release tree. The DEVLOG and dashboard track the local phase result, not a shipped release.

## 9. Summary and Next Steps

The rewritten candidate has clean attribution while retaining original file trees, dates and topology. Phase 3 can now add the live scan to the existing validate path and implement the maintainer-only hook. Continue from the active rewritten worktree named in the backup record; the original checkout is a recovery copy.
