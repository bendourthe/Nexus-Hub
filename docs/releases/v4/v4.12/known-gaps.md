# Known gaps - v4.12

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-09-14

Release-scoped gaps for the sole-contributor-attribution plan. Planned future-phase work is tracked in the plan rather than reported as completed here.

## v4.12.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 1 |
| Warnings (WN) | 4 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 4 | 0 |

### Open Items

#### WN-1: Existing CI-profile lint findings

**Source phase**: Phase 3. **Plan reference**: T013. **Reason**: the parent profile already contains these unrelated lint findings.

**Owner**: CI profile maintainer. **Status**: open. **Next step**: address UP035 at the existing typing imports and FLY002 in `_PS_AST_PARSE` during the next CI-profile maintenance change.

Phase 3 confirmed both findings against the parent commit before its one-command change. No new checker or test-module lint finding remains. Evidence: external `phase3-baseline-lint.json`; this does not waive the final functional validation gate.

#### WN-2: Existing CI reporting and tooling-lock differences

**Source phase**: Phase 4. **Plan reference**: T018. **Reason**: the canonical comparison finds incomplete tool version-locking and incomplete JUnit/coverage/report-bundle retention across existing CI legs. This overlaps v4.4 WN-446-1; it is not introduced by attribution enforcement.

**Owner**: CI maintainer. **Suggested next step**: in the queued CI-maintenance scope, lock tooling and generate/upload detailed reports with explicit seven-day retention, preserving required contexts and fail-closed job selection. No unrelated pipeline migration was applied in this release.

#### WN-3: Repository description count drift

**Source phase**: Phase 4. **Plan reference**: T017. **Reason**: live GitHub description reports 336 skills while the current catalog has 337.

**Owner**: Repository maintainer. **Suggested next step**: reconcile the description at the next release settings review. The report-only attribution audit did not mutate GitHub metadata.

#### WN-4: Unexplained Windows file-replacement failure

**Source phase**: Phase 4. **Plan reference**: T022. **Reason**: the Windows installer/validator command passed 2,069 tests but failed `test_sibling_keys_and_user_content_survive` with `WinError 5` while replacing its temporary settings file. No open-file defect was found in the helper's `read_text` / `write_text` calls, and five isolated reproduction attempts passed. The process holding or denying access at the original failure was not observed, so no cause is asserted.

**Owner**: Windows installer maintainer. **Suggested next step**: retain the original command receipt and five-attempt reproduction record; capture file-handle/permission evidence if it recurs. The complete installer/validator rerun is separate evidence, not a rewrite of the first failed run. No permission policy, atomic-write behavior or retry limit was changed to suppress this failure.

#### QG-1: GitHub retains read-only pull-request refs

**Source phase**: Phase 4 independent review. **Plan reference**: Goal, T020 and T023. **Reason**: 212 `refs/pull/*` exist on GitHub outside the 119 writable branches/tags. They cannot be replaced by a normal force-push; the local all-ref proof covers the captured 139 local refs, not every GitHub-retained ref.

**Owner**: Repository owner. **Suggested next step**: approve the explicit writable-ref publication scope only with this limitation understood; observe both default-branch contributor surfaces afterward. If purging every GitHub-held ref is required, obtain GitHub's supported administrative disposition separately. Do not promise old SHA disappearance or a clean GitHub mirror that fetches PR refs.

#### QG-2: Publication and GitHub contributor proof pending

**Source phase**: Phase 4. **Plan reference**: T021-T023. **Reason**: no force-push is authorized yet; both protected branches disallow it and enforce PR/status requirements on administrators. Public contributor pages still reflect the original history.

**Owner**: Repository owner and publication operator. **Suggested next step**: after all local work is concrete, review exact old/new refs and recovery mirror, approve the necessary temporary protected-branch exception without deleting protection, publish once, restore captured settings, run required CI and inspect Code/Insights/Release surfaces. If cache delay is observed, record its actual account set and a precise next-check timestamp then; no cache delay is assumed before publication.

#### QG-3: Independent adversarial review incomplete

**Source phase**: Phase 4. **Plan reference**: T019, functional-verification deep-pass Step 6. **Reason**: a separate reviewer returned the PR-ref finding, then its turn was stopped by an automated security filter before remaining exercise results were returned.

**Owner**: Repository owner and authorized independent reviewer. **Suggested next step**: obtain the remaining independent review through the supported review process before assigning a clean adversarial verdict. Existing ordinary tests and the returned finding remain valid evidence for their own scopes. See [review status](development/ADVERSARIAL-REPORT.md).

#### QG-4: Windows whole-repository profile timed out

**Source phase**: Phase 4. **Plan reference**: T022. **Reason**: the Windows full profile completed 46 commands successfully, but `repo-tests` exceeded its unchanged 4,500-second limit. Its timeout receipt contains no completed repository-test totals. The passing hook and extension groups do not turn that run into a pass.

**Owner**: CI maintainer. **Suggested next step**: retain `phase4-full/summary.json` and investigate the current Windows whole-repository runtime before claiming that host's full profile qualified. The documented 3,341.7-second baseline dates to August 28 and predates newer benchmark tests; this is a workload hypothesis, not a measured cause. Current CI runs the full repository suite on Ubuntu and separately pins Windows-specific coverage to PowerShell 5.1. Linux full-profile and exact Windows CI-group results are recorded separately in the final evidence; neither retroactively changes the original Windows non-pass. No test limit was increased.

### Resolved

#### BG-1: Directory membership changes could evade a timestamp-only check

**Source phase**: Phase 4. **Plan reference**: T022. **Owner**: Target-manifest maintainer. **Resolution**: final validation found that a file added during traversal could share the directory's original modification timestamp. The manifest now compares the captured entry-name set as well as directory identity and timestamp. No API or history-rewrite policy changed.

**Evidence**: the original Linux full receipt retains one failed directory-change assertion, 4,970 passing repository tests and 343 skips. A deterministic timestamp-restoration regression failed before the fix; afterward the target-manifest module passed 54 tests with two explicit Windows skips. Both changed Python files pass Ruff. The complete corrected-candidate rerun is recorded separately in the final evidence.
