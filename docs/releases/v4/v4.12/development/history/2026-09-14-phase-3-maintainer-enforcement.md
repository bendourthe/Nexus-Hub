# Development log: Phase 3 maintainer enforcement

**Date**: 2026-09-14
**Objective**: Complete T010-T013 of the [plan](../../plans/v4.12.0-sole-contributor-attribution.md) through local verification and one commit.
**Outcome**: The repository-native hygiene profile scans complete history; an opt-in, maintainer-only commit hook checks pending identities and message attribution. Publication remains pending.

## 1. Starting State

Phase 2 commit: `19f98baf9006d03352fc6bc1cf6346a3b78c880d`. Work continues in the isolated rewritten checkout documented in [rewrite-backup](../rewrite-backup.md). The original checkout and backup remain recoverable.

## 2. Chronological Steps

Added the checker to Makefile validate and the hygiene profile. Both CI validate and post-merge smoke now fetch full history because both consume hygiene. Added an optional `.githooks/commit-msg`, its setup and recovery instructions, and an LF attribute for Windows checkouts. The hook checks Git's pending author and committer as well as trailers, including inherited amend authors. No hook was enabled in a maintainer checkout; only temporary test repositories enabled it.

The canonical validation profile exposed a Phase 1 decision-record header defect. Corrected its required title and status syntax. The original failed result remains immutable in `phase3-validation`; the subsequent green run is separate in `phase3-validation-rerun` beside the external backup.

## 3. Verification Gate

| Check | Observed result |
|---|---|
| Checker, real Git hook, CI wiring and installer-exclusion tests | 55 passed; 32 unrelated tests deselected |
| Checker statement coverage | 106/109, 97.25% |
| Ruff on checker and changed test modules | All checks passed |
| Canonical validate-equivalent profile | 38 passed, zero failed or skipped |
| Live all-ref CLI | 1,698 commits; zero findings; zero errors; exit 0 |
| Fresh CRLF-configured checkout | Hook retains LF and accepts a canonical commit |
| Actual forbidden commit/amend attempts | Rejected for author, committer or trailer violations |

## 4. Known Issues

Two pre-existing Ruff findings in `scripts/ci/profiles.py` are retained as WN-1 in the [ledger](../../known-gaps.md). Baseline verification used the committed parent bytes. They were not introduced by the one-command addition and are not suppressed. GitHub publication and contributor-page proof remain final-phase duties.

## 5. Plan Discrepancies

### Plan delta

**Incomplete, corrected within the Goal**: message-only hook validation cannot reject forbidden pending author or committer metadata, so the checker gains `--pending-commit`. Post-merge smoke also consumes hygiene and therefore needs full history. LF normalization makes the hook executable through Git Bash after a Windows checkout. The existing profile owns the single CI invocation; a duplicate direct CI step would add no coverage. The decision header fix restores the already-required document contract. No unrelated pipeline or distributed installer capability was added.

The 103-plan inventory and shared CI-file constraints from the [queue assessment](../phase-1-queue-assessment.md) remain applicable. Current session routing is retained without a model downshift; the runtime exposes no model-switch operation.

## 6. Assumptions Made

The local hook is an opt-in maintainer aid, not an authentication boundary. CI independently checks history even if a user bypasses local hooks. Repository configuration is not changed without the requested opt-in. Existing five required contexts remain unchanged.

## 7. Testing Summary

`python -m pytest tests/validators/test_commit_attribution.py tests/workflows/test_attribution_workflow.py catalog/hooks/tests/test_installer_smoke.py -k 'attribution or copy_every_scripts_dir_py_file' --import-mode=importlib -q` returned 55 passed and 32 deselected. Real temporary Git consumers exercised commits, amended authors, inherited authors, trailers and a fresh checkout with spaces and `core.autocrlf=true`. Coverage is retained in `phase3-final-coverage.json`.

With process-scoped Git Bash on PATH, `python scripts/ci/run.py --profile full --only catalog-parse,hygiene,interpreters,catalog,security,workflows,platform-contracts,docs,version --quiet --reports-dir ../../Nexus-Hub-backups/2026-09-14-v4.12-attribution/phase3-validation-rerun` returned 38 passing commands. This is the validate-equivalent local gate; it is not the entire final test profile. Directly running `python scripts/check_commit_attribution.py --all-refs --root .` again returned `Attribution: 1698 commits scanned; 0 findings; 0 errors`.

## CI impact

Changed `.github/workflows/ci.yml` and `.github/workflows/post-merge.yml` only to fetch complete history for their hygiene consumers. Added one repository-native hygiene command and its matching Makefile validate command. No new required status context, secret, dependency or catalog hook. CI validate remains unconditional. No v4.12 push, PR or remote CI run occurred.

## 8. TODO Tracker

- [x] T010 live validation wiring.
- [x] T011 full-history CI consumption.
- [x] T012 maintainer-only local hook and CHANGELOG entry.
- [x] T013 local validation, history and phase commit.
- [ ] T014-T023 final reconciliation, qualification and approved publication.

## 9. Summary and Next Steps

Maintainer enforcement is locally verified. Final qualification must inspect every feature and prepare an exact ref publication set before requesting approval for destructive remote history replacement.
