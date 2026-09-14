# Development log: Phase 4 final qualification

**Date**: 2026-09-14. **Objective**: Complete local final-phase duties and prepare a concrete publication decision for the [v4.12 plan](../../plans/v4.12.0-sole-contributor-attribution.md). **Status**: local implementation and CI-aligned qualification complete; publication and public contributor proof pending.

## 1. Starting State

Phase 3 commit `e56d0251407ec84f59d9425cf6a64dc15c3a112e` was clean and locally verified. The isolated worktree remains the active candidate; original history and seven stash objects remain preserved in the independent recovery mirror. No v4.12 remote push has occurred.

## 2. Chronological Steps

Inventoried indexed project artifacts and all 40 known-gaps ledgers; preserved independent catalog/template consumers and prior evidence. Checked mapped handbook freshness and the GitHub branch/settings state. Compared all 23 canonical CI fields. Ran both actual installers into temporary native Windows/Linux homes and exercised the same shared postconditions. A Linux wrapper revision lookup failed on the Windows worktree pointer; original logs were retained and the wrapper reran with the explicitly bound source revision.

The independent reviewer reported that GitHub's read-only PR refs exceed normal publication authority, then was stopped by an automated security filter. Its coverage remains incomplete. Final CI inspection found the required Presentify `verify` job had no manual dispatch path; added that path with an actual Bash detector exercise. Scoped documentation verification corrected a copied queue-assessment link. Pre-commit normalized checkout line endings; Git staging confirmed no source content changes from normalization. An incidental README label encoding change was restored before staging.

The decision moved from proposed to implemented with copy/hash verification and explicitly pending remote publication. A local bare-repository rehearsal proved stale-lease atomic rejection, exact ref publication, clean fresh-clone attribution and exact rollback. No remote setting or ref changed.

The first Windows full profile completed 46 commands successfully but the whole repository test command exceeded 4,500 seconds. Its original non-pass receipt remains intact. A Linux full-profile run was started in a temporary Python 3.11 container matching CI's complete test job, with an exact staged-patch snapshot on its native filesystem. Separate Windows CI-native checks retain their own results. No product code or timeout was changed for this environment split.

## 3. Verification Gate

| Check | Observed result |
|---|---|
| Native Windows PowerShell installer and shared postconditions | Exit 0; maintainer checker excluded |
| Native Ubuntu Bash installer and shared postconditions | Exit 0; maintainer checker excluded |
| Independent Linux bare-clone CLI | 1,697 commits; zero findings/errors |
| Current Windows all-ref CLI | 1,699 commits; zero findings/errors |
| Affected workflow and required-context tests | 108 passed; 17 explicit existing skips |
| Final validate-equivalent profile | 38 commands passed |
| Scoped docs links and decision validator | Pass; 41 valid decisions |
| Installer declarative parity | PASS |
| Publication rehearsal | 119 original refs -> 120 candidate refs -> 119 exact original refs |
| Stale expected ref in rehearsal | Nonzero exit; no ref changed |
| Fresh normal clone after simulated publication | 1,686 commits; zero findings/errors |
| Windows full repository-native profile | 46 commands passed; repository tests timed out at 4,500 seconds; NOT PASS |
| Corrected Linux full repository-native profile | 47 commands passed; 6,583 tests passed and 918 skipped; 358.6 seconds |
| Windows native integration files | 251 passed; two skipped |
| Windows installer/validator complete rerun | 2,070 passed; 45 skipped |
| Windows security-evidence command | 458 passed; ten skipped |
| Directory-membership regression/module | Deterministic red case, then 54 passed and two skipped; Ruff clean |

## 4. Known Issues

The [ledger](../../known-gaps.md) records existing lint/reporting/settings drift, the read-only PR-ref limitation, pending publication/UI proof and incomplete independent adversarial coverage. The [final evidence](../last-phase-evidence.md) separates these from ordinary functional tests. Historical signed objects and original provenance remain in the backup; rewriting does not re-sign or re-attest them. No macOS native execution is claimed on this Windows/Linux workstation.

## 5. Plan Discrepancies

### Plan delta

**Incorrect assumption, explicitly bounded**: GitHub advertises 212 read-only PR refs, so a normal force-push cannot make every GitHub-retained ref canonical. The writable scope is three existing branches and 116 tags, plus the new feature branch. The user must see that limit when deciding publication. The original Goal is not silently redefined as complete.

**Incomplete, corrected**: post-rewrite validation needs manual execution of every required context. CI and doc co-location already support dispatch; the Presentify workflow now does too and its dispatch path runs the full check without PR metadata. Existing job names, permissions, required contexts and schedule behavior remain intact. The final mapped-handbook contract supersedes an older literal folder example in the plan. This does not authorize a general CI migration.

Three tree-correction cycles were used: documentation/encoding repair, the missing required-check dispatch, and the directory-membership guard exposed by the full Linux suite. That last correction adds a deterministic timestamp-restoration regression; the unchanged-timestamp case failed before the fix and the complete module then passed 54 tests with two skips. The independent review interruption remains a coverage gap, including for the later stabilization change. Current session routing remains unchanged.

## 6. Assumptions Made

Publication must use only the reviewed public ref set and one atomic tag batch, preserving private historical branches, internal refs and stashes locally. Both protected branches are ancestors of the feature, so final local integration can fast-forward without a content merge. Explicit old-tip leases must be compared again immediately before any approved push. No branch protection may be deleted.

## 7. Testing Summary

The local installer wrapper ran organization connection, the real platform installer and `check_installer_smoke.py` on Windows PowerShell 5.1 and Ubuntu Bash. All three commands returned zero on both hosts. Shared assertions covered installed scripts, organization markers, functional-verification artifacts and the host-correct responsive hook; an additional assertion proved `check_commit_attribution.py` was not distributed.

The affected test command selected `test_attribution_workflow.py`, `test_presentify_extractor_workflow.py`, `test_workflow_policy_repo_wide.py` and `test_ci_required_gate.py`, with `--import-mode=importlib -q`. The result was 108 passed and 17 platform skips. The dispatch test executed the actual YAML Bash body with empty PR SHAs and observed `presentify=true`.

The 38-command native validation profile passed after the Phase 4 workflow and decision changes, with receipts under `phase4-validation/`; final record checks are retained under `phase4-final-validation/`. The original Windows full non-pass is retained under `phase4-full/`, and the initial Linux assertion failure under `phase4-linux/full/`. The corrected complete Linux profile passed under `phase4-linux-corrected/full/`, bound by its staged-patch hash and index tree. This is a separate full run, not a focused result promoted to full coverage.

The Windows installer/validator command initially failed with `WinError 5` during atomic replacement of a test settings file, with 2,069 tests passed and 45 skipped. Five isolated attempts passed, and no file-handle defect or responsible external process was established. Its complete rerun passed 2,070 tests with 45 skips; WN-4 retains the unexplained first failure. Neither that rerun nor the green Linux result retroactively changes the original non-pass receipts. Current Linux full and Windows CI-command coverage is green; Windows whole-repository profile qualification remains QG-4.

## CI impact

Phase 4 changes only the existing Presentify workflow's manual trigger, explicit full-check detection for that event and verify-job event condition. No new context, external dependency, catalog surface, secret or deployment is introduced. Final comparison retains unrelated report/pinning gaps with owners. Post-publication verification will dispatch CI, Doc Co-location and Presentify extractor on the approved tips, then observe the existing post-merge smoke/provenance. No v4.12 remote CI has run yet.

## 8. TODO Tracker

- [x] T014-T020 local audits, bounded deep-pass record and independent Goal assessment.
- [ ] T021 actual post-publication GitHub UI observations.
- [x] T022 full local suite and final local phase commit.
- [ ] T023 explicit publication approval, operator-controlled protection exception, one ref update and remote verification.

## 9. Summary and Next Steps

The final local phase commit contains this record and the external publication manifest binds its full SHA. The reviewable action updates only the named public branches and 116 tags, with exact leases, a rehearsed recovery path and immediate restoration of any approved protection exception. Publication, required remote checks and public contributor observations remain pending the owner's explicit decision. No release tag or version bump is part of this implementation driver.
