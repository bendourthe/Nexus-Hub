# Known Gaps - v4.1

**Project**: Nexus-Hub
**Status**: finalized; the two open deferred items remain owned by this ledger
**Last updated**: 2026-08-31 (v4.4.0 Phase 7 reconciliation)

## v4.1.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 2 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |

### Open Items

Only DF-1 remains open for v4.1.0. All other categories have no open items.

#### Deferred

##### DF-1 - Prompting profile layer does not match the live Codex roster

- **Source phase**: v4.1.0 release preparation
- **Evidence**: On 2026-08-31, `python scripts/check_model_prompting_freshness.py --advisory gpt-5.6-sol gpt-5.6-terra gpt-5.6-luna` reported `DRIFTED`: the three supplied live Codex model IDs are unprofiled and the four recorded Claude entries are absent from that host roster. The current v4.4 model map independently lists those three Codex IDs.
- **Reason deferred**: The advisory is intentionally not a release or CI gate, and a conformant refresh requires the separate calibrated `/tune-prompting` research and adversarial-verification workflow rather than a release-time hand edit.
- **Next action**: Run `/tune-prompting` in a separately scoped plan, calibrate on one live model before widening, and retain any unverified models as explicit gaps.

### Resolved

#### Warnings

##### WN-1 - GitHub repository description advertises 324 skills

- **Source phase**: Phase 6 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Evidence at deferral**: The release flow confirmed the remote description said 324 skills while the repository catalog and README said 326.
- **Resolution**: `python scripts/check_release_preconditions.py --repo-settings` returned `OK: repository description agrees with README.md`; `README.md` and the generated catalog now declare 329 skills.
- **Resolved in**: v4.4.0 Phase 7 reconciliation on 2026-08-31

##### WN-2 - Claude plugin description advertised 325 skills

- **Source phase**: v4.1.0 release preparation
- **Evidence**: The release docs reconciliation found `.claude-plugin/plugin.json` still said 325 curated skills while `data/skills.json`, README, AGENTS.md, and `data/marketplace.json` said 326.
- **Resolution**: Updated the plugin description to 326 in the v4.1.0 release commit; catalog validation and the final release profile verify the synchronized result.

#### Quality-Gate Gaps

##### QG-1 - Additional local full profile did not complete within the release-prep window

- **Source phase**: v4.1.0 release preparation
- **Evidence at deferral**: The canonical `release` profile passed 3 of 3 checks, and all targeted release validators passed. An additional `python scripts/ci/run.py --profile full --quiet --json` run completed the Windows hook-parity group and continued actively in `pytest tests -q`, but was interrupted after an extended bounded wait without a final profile report.
- **Resolution**: Pull request [#133](https://github.com/bendourthe/Nexus-Hub/pull/133) merged at `163bfeb8d08772ba87af4a2e3cccbc8e7213e24f`. Workflow run [`33199994696`](https://github.com/bendourthe/Nexus-Hub/actions/runs/33199994696) completed the test, Windows, installer, bootstrap, and aggregate `ci-required` checks successfully, satisfying the original remote-suite next action.
- **Resolved in**: v4.4.0 Phase 7 reconciliation on 2026-08-31, using historical v4.1.0 integration evidence

> Finalized on 2026-08-28 at the 4.1.0 bump. DF-1 remains open and owned by this ledger; WN-1 and QG-1 were resolved during the v4.4.0 Phase 7 reconciliation.

### Inherited Ledger Review

- v3.20 DF-1 and DF-2 remain on `docs/releases/v3/v3.20/known-gaps.md`; this adoption plan did not absorb or relabel them.
- v3.21 DF-1 remains on `docs/releases/v3/v3.21/known-gaps.md` because Nexus-Hub still has no authored catalog atlas.
- v3.21 DF-2 is resolved on its original ledger by the v4.1.0 Phase 1 refresh of `docs/todos.md`.
- v4.0 DF-1 (report-artifact upload) remains on `docs/releases/v4/v4.0/known-gaps.md`. The v4.1.1 pipeline comparison declined to reopen it.

## v4.1.1

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |

### Open Items

#### Deferred

##### DF-1 - Live optional scanners were not executed on the implementation host

- **Source phase**: Phase 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Plan reference**: `docs/releases/v4/v4.1/plans/v4.1.1-adoption-openworker-security-refinement.md` T025 / T032
- **Evidence**: Fixture-driven closure-gate tests pass without invoking Semgrep, gitleaks, OSV-Scanner, npm audit, pip-audit, Trivy, or Checkov. Phase 4 history records that those binaries were not present or not executed.
- **Reason deferred**: The plan forbids adding real scanner execution to Nexus-Hub CI. Host-local binaries are optional; missing tools must remain visible as `UNAVAILABLE`.
- **Next action**: On a machine that already has the optional tools, run the `security-audit` preset once with some, none, and all applicable scanners and keep the receipts.

### Resolved

#### Deferred

##### DF-2 - POSIX installer dry-run was not executed on this Windows host

- **Source phase**: Phase 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Plan reference**: T021 / T026
- **Evidence at deferral**: `python scripts/check_installer_parity.py` passed. No `scripts/installer.sh` dry-run was performed on the Windows implementation host.
- **Resolution**: Pull request [#137](https://github.com/bendourthe/Nexus-Hub/pull/137) ran `installer-smoke (ubuntu-latest)` and `installer-smoke (macos-latest)` to SUCCESS, plus Ubuntu and macOS `install-smoke` and `bootstrap`. That is the POSIX delivery proof. A local `installer.sh` dry-run on this Windows host remains unclaimed and is not required.
- **Resolved in**: v4.1.1 release preparation on 2026-08-28

#### Quality-Gate Gaps

##### QG-1 - Local full CI profile was not completed in this session

- **Source phase**: Phase 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Evidence at deferral**: `python -m pytest tests/skills -q` passed 952 tests. `python scripts/ci/run.py --profile fast` failed `validate_unicode_safety` on untracked `docs/releases/v4/v4.1/comparisons/v4.1.2-comparison-ponytail.md`, which is outside this plan and is not staged. The hour-scale local `--profile full` run was not completed in that session.
- **Resolution**: Pull request [#137](https://github.com/bendourthe/Nexus-Hub/pull/137) merged to `develop` at `0787ebf9` with every required check green. Post-merge workflow run `33224364101` succeeded (`smoke` + `provenance`). Remote CI is the complete-suite proof named in the original next action.
- **Resolved in**: v4.1.1 release preparation on 2026-08-28

> Finalized on 2026-08-28 at the 4.1.1 bump. The v4.1.0 and v4.1.1 DF-1 items remain open on this ledger; v4.1.0 WN-1 and QG-1 were resolved during the v4.4.0 Phase 7 reconciliation.

## v4.1.2

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |

### Open Items

None.

The v4.1.0 and v4.1.1 DF-1 items remain open on this ledger; v4.1.0 WN-1 and QG-1 were resolved during the v4.4.0 Phase 7 reconciliation.

### Resolved

#### Warnings

##### WN-1 - GitHub repository description advertises 326 skills

- **Source phase**: Phase 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Plan reference**: `docs/releases/v4/v4.1/plans/v4.1.2-adoption-minimal-construction.md` T023 / T028
- **Evidence at deferral**: `python scripts/check_release_preconditions.py --branches --repo-settings` reported `skills: description says 326, README.md declares 328`.
- **Resolution**: `gh repo edit` updated the description to 328 during the v4.1.2 GitHub Release step. A re-run of `python scripts/check_release_preconditions.py --branches --repo-settings` reported `OK: repository description agrees with README.md`.
- **Resolved in**: v4.1.2 publication on 2026-08-29

#### Quality-Gate Gaps

##### QG-1 - Local full CI profile was not completed in this session

- **Source phase**: Phase 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Evidence at deferral**: `python scripts/ci/run.py --profile fast` passed 12 of 12. Hour-scale local `--profile full` had not produced a final report when last-phase evidence was written.
- **Resolution**: Pull request [#141](https://github.com/bendourthe/Nexus-Hub/pull/141) merged to `develop` at `34d8272b` with every required check green (`validate`, `shellcheck`, `ci-required`, `colocation`, `verify`). Post-merge workflow run `33235080095` succeeded (`smoke` + `provenance`). Remote CI is the complete-suite proof named in the original next action.
- **Resolved in**: v4.1.2 release preparation on 2026-08-28

> Finalized on 2026-08-29 at the v4.1.2 publication. The v4.1.0 and v4.1.1 DF-1 items remain open on this ledger; v4.1.0 WN-1 and QG-1 were resolved during the v4.4.0 Phase 7 reconciliation.
