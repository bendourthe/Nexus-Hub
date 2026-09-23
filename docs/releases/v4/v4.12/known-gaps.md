# Known gaps - v4.12

**Project**: Nexus-Hub
**Status**: released
**Last updated**: 2026-09-22

Release-scoped gaps for the sole-contributor-attribution plan. Planned future-phase work is tracked in the plan rather than reported as completed here.

## v4.12.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 1 |
| Warnings (WN) | 1 | 3 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 3 | 1 |

### Open Items

#### WN-1: Existing CI-profile lint findings

**Status**: RESOLVED 2026-09-22. `Mapping` and `Sequence` now come from `collections.abc`, and the PowerShell parser command joins a named parts tuple rather than a literal list. `python -m ruff check scripts/ci/profiles.py --output-format concise` and all 65 CI engine tests pass.

**Source phase**: Phase 3. **Plan reference**: T013. **Reason**: the parent profile already contains these unrelated lint findings.

**Owner**: CI profile maintainer. **Status**: resolved 2026-09-22 by the focused changes and verification recorded above.

Phase 3 confirmed both findings against the parent commit before its one-command change. No new checker or test-module lint finding remains. Evidence: external `phase3-baseline-lint.json`; this does not waive the final functional validation gate.

#### WN-2: Existing CI reporting and tooling-lock differences

**Follow-up status, 2026-09-22**: PR #235 merged report upload and direct guide/Windows JUnit generation. Hosted run 35799198474 exposed five seven-day report artifacts, and post-merge run 35801251735 passed smoke and provenance. Tool versions are still not locked across the CI workflows and editable extension extras. This combined warning remains open for the locking half.

**Locking candidate, 2026-09-22**: A universal Python 3.11 constraints file now pins CI-only tools and every optional dependency from the six extension manifests; pip installs in five workflows consume it, and two offline Docker builds receive it through a named context. The Claude Code npm install, ShellCheck apt package, Docker Python base digest, and code-search Git package are pinned to observed versions. Pip resolved the six editable development extras under the constraints, the regenerated 495-line lock matched the committed package set, 95 workflow/security tests passed, and pinned no-network Docker suites passed 54 memory and 380 code-search tests. This is local candidate evidence only; the warning remains open until the lock branch's hosted jobs and merged result pass.

**RESOLVED 2026-09-22 (post-release)**: PR #238 merged the tool locks at `3ee00582` after the Linux, Windows, guide, offline extension, Presentify, and aggregate checks passed. Its post-merge run 35810094225 passed smoke and provenance. The first hosted attempt failed because a relative pip constraints path was not visible to pre-commit's isolated environment; the final head uses an absolute workspace path and passed the rerun. The original failed run remains evidence of that repair, not a claimed pass.

**Source phase**: Phase 4. **Plan reference**: T018. **Reason**: the canonical comparison finds incomplete tool version-locking and incomplete JUnit/coverage/report-bundle retention across existing CI legs. This overlaps v4.4 WN-446-1; it is not introduced by attribution enforcement.

**Owner**: CI maintainer. **Suggested next step**: in the queued CI-maintenance scope, lock tooling and generate/upload detailed reports with explicit seven-day retention, preserving required contexts and fail-closed job selection. No unrelated pipeline migration was applied in this release.

#### WN-3: Repository description count drift

**Status**: RESOLVED 2026-09-22. The live repository description now states 337 skills and matches the current catalog. The original observation below is retained as failure evidence.

**Source phase**: Phase 4. **Plan reference**: T017. **Reason**: live GitHub description reports 336 skills while the current catalog has 337.

**Owner**: Repository maintainer. **Suggested next step**: reconcile the description at the next release settings review. The report-only attribution audit did not mutate GitHub metadata.

#### WN-4: Unexplained Windows file-replacement failure

**Source phase**: Phase 4. **Plan reference**: T022. **Reason**: the Windows installer/validator command passed 2,069 tests but failed `test_sibling_keys_and_user_content_survive` with `WinError 5` while replacing its temporary settings file. No open-file defect was found in the helper's `read_text` / `write_text` calls, and five isolated reproduction attempts passed. The process holding or denying access at the original failure was not observed, so no cause is asserted.

**Owner**: Windows installer maintainer. **Suggested next step**: retain the original command receipt and five-attempt reproduction record; capture file-handle/permission evidence if it recurs. The complete installer/validator rerun is separate evidence, not a rewrite of the first failed run. No permission policy, atomic-write behavior or retry limit was changed to suppress this failure.

#### QG-1: GitHub retains read-only pull-request refs

**Source phase**: Phase 4 independent review. **Plan reference**: Goal, T020 and T023. **Reason**: 212 `refs/pull/*` exist on GitHub outside the 119 writable branches/tags. They cannot be replaced by a normal force-push; the local all-ref proof covers the captured 139 local refs, not every GitHub-retained ref.

**Owner**: Repository owner. **Suggested next step**: approve the explicit writable-ref publication scope only with this limitation understood; observe both default-branch contributor surfaces afterward. If purging every GitHub-held ref is required, obtain GitHub's supported administrative disposition separately. Do not promise old SHA disappearance or a clean GitHub mirror that fetches PR refs.

#### QG-2: GitHub contributor-view confirmation pending

**Recheck, 2026-09-22**: The live contributors API now returns only `bendourthe` (1,753 contributions), and the statistics API also returns only `bendourthe` (1,394 non-merge commits). A fresh, unauthenticated Chromium rendering of the public [Code page](https://github.com/bendourthe/Nexus-Hub) still shows `Contributors 5`; its avatar labels identify `bendourthe`, `cursoragent`, `benjamin-dourthe`, `claude`, and `dependabot[bot]`. The rendered Code result fails the one-contributor criterion despite the API results. No new history rewrite is justified by this discrepancy.

**Source phase**: Phase 4. **Plan reference**: T021-T023. **Reason**: the owner approved publication, all 120 reviewed writable refs were updated, both protections were restored exactly, and all five required checks passed. The fresh public clone scans 1,687 commits with zero findings. At `20260914T232622Z`, the contributor API still returned `bendourthe` (1655), `dependabot[bot]` (8), while the Insights default-main graph data contained only `bendourthe` (1,345 non-merge commits). Subsequent user screenshot 1 confirms Insights with Period: All, main, excluding merge commits, showing only bendourthe with 1,345 commits. Screenshot 2 confirms the published ba468f5 tip and a Code sidebar labeled Contributors 5. The other account names cannot be established from the avatars alone. The live API recheck still lists bendourthe and dependabot[bot], while the statistics endpoint lists only bendourthe. The rendered Code result therefore fails the one-contributor criterion; Insights passes. This discrepancy is consistent with GitHub's documented refresh delay, but the Code result is not yet resolved.

**Owner**: Repository owner and publication operator. **Suggested next step**: contact GitHub Support with the publication receipts, earlier screenshots, and the fresh Code-sidebar result; request a supported contributor-cache correction or explanation. Insights is already confirmed by the user's screenshot. GitHub documents about 24 hours for contributor displays to refresh after history changes and recommends contacting Support if they remain incorrect after that window. See [GitHub's stale-contributor guidance](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-a-projects-contributors#contributor-data-is-stale-after-history-changes). No further history rewrite is warranted by the current evidence. Existing releases and assets are already verified unchanged. No public-view success or release completion is claimed.

#### QG-3: Independent adversarial review incomplete

**Source phase**: Phase 4. **Plan reference**: T019, functional-verification deep-pass Step 6. **Reason**: a separate reviewer returned the PR-ref finding, then its turn was stopped by an automated security filter before remaining exercise results were returned.

**Owner**: Repository owner and authorized independent reviewer. **Suggested next step**: obtain the remaining independent review through the supported review process before assigning a clean adversarial verdict. Existing ordinary tests and the returned finding remain valid evidence for their own scopes. See [review status](../../../archives/v4/v4.12/development/ADVERSARIAL-REPORT.md).

#### QG-4: Windows whole-repository profile timed out

**Status**: RESOLVED 2026-09-22. The original timeout below remains immutable evidence. The current full profile partitions repository tests at stable ownership boundaries without raising a timeout; exact-file guards prove every repository test is covered once. The corrected Windows run passed all 59 commands with zero failures, skips, or advisories in 7,208.2 seconds.

**Source phase**: Phase 4. **Plan reference**: T022. **Reason**: the Windows full profile completed 46 commands successfully, but `repo-tests` exceeded its unchanged 4,500-second limit. Its timeout receipt contains no completed repository-test totals. The passing hook and extension groups do not turn that run into a pass.

**Owner**: CI maintainer. **Suggested next step**: retain `phase4-full/summary.json` and investigate the current Windows whole-repository runtime before claiming that host's full profile qualified. The documented 3,341.7-second baseline dates to August 28 and predates newer benchmark tests; this is a workload hypothesis, not a measured cause. Current CI runs the full repository suite on Ubuntu and separately pins Windows-specific coverage to PowerShell 5.1. Linux full-profile and exact Windows CI-group results are recorded separately in the final evidence; neither retroactively changes the original Windows non-pass. No test limit was increased.

### Resolved

#### WN-1: Existing CI-profile lint findings

The two named findings were repaired without changing the generated PowerShell command or the profile contract. The focused lint check and owning CI engine module pass on the corrected tree.

#### WN-3: Repository description count drift

The repository setting was updated on 2026-09-22 from 336 to 337 skills. The public Code page and the repository API both expose the corrected description; the existing release-precondition check continues to detect future drift.

#### QG-4: Windows whole-repository profile timed out

The original 4,500-second monolithic timeout was retained. Repository tests are now partitioned by stable owner, with separate bounded commands for skills, installers, integration concerns, plans, CI, guides, and governance. Both coverage guards pass, and the complete corrected Windows profile passed 59 commands in 7,208.2 seconds without increasing a timeout.

#### BG-1: Directory membership changes could evade a timestamp-only check

**Source phase**: Phase 4. **Plan reference**: T022. **Owner**: Target-manifest maintainer. **Resolution**: final validation found that a file added during traversal could share the directory's original modification timestamp. The manifest now compares the captured entry-name set as well as directory identity and timestamp. No API or history-rewrite policy changed.

**Evidence**: the original Linux full receipt retains one failed directory-change assertion, 4,970 passing repository tests and 343 skips. A deterministic timestamp-restoration regression failed before the fix; afterward the target-manifest module passed 54 tests with two explicit Windows skips. Both changed Python files pass Ruff. The complete corrected-candidate rerun is recorded separately in the final evidence.


### Release disposition

v4.12.0 was published on 2026-09-15 at tag `v4.12.0` (`0dabca77`) and reconciled into `develop` by the back-merge in PR #220. Post-publication verification of the downloaded artifacts passed for both published forms (1,929 manifest entries each, matching asset digest, successful provenance attestation). The published archive was then installed on Windows in two disposable user homes (global and workspace scope); each installed CLI reported 4.12.0, `attribution check` returned VERIFIED for the configured user, and a commit, an annotated tag and a push from each install carried that user identity rather than an agent identity. The guard reports its own limit: direct API writes are outside it. Publication does not close the two open warnings and three open quality-gate gaps above; resolved historical entries remain visible rather than being rewritten. Portable attribution integration passed PR #217 and post-merge run 34925451808; it does not close those independent items. No unresolved portable-code finding remains. See [release qualification](../../../archives/v4/v4.12/development/release-qualification.md) for the release evidence and queue impacts.

#### DF-1: Antigravity workflow surface retires on 2026-11-01

**Source phase**: v4.12.1 release, platform-contract verification (2026-09-16). **Plan reference**: /update release governance step 4. **Reason**: the vendor documents retirement of the legacy workflow format on 2026-11-01 in favour of the Agent Skills standard. Nexus-Hub already emits every command as BOTH a skill and a workflow (`scripts/lib/integrations/antigravity.py` calls `commands_to_skills` alongside `commands_to_slash`), and the vendor states skills take precedence where both exist, so the skill copy is already what Antigravity executes.

**Impact**: none before the retirement date, and none after it for the skills surface. No re-architecture is required for Antigravity to remain supported.

**Why not now**: dropping workflow emission before the date would remove the slash surface for anyone still on a pre-retirement build. Shipping both is the correct posture until the date passes.

**Owner**: Antigravity integration maintainer. **Status**: open, dated. **Suggested next step**: after 2026-11-01, remove the `commands_to_slash` workflow emission from the Antigravity integration, drop `commands_subdir`/`ide_commands_subdir` from its config, update the read-contract row, and re-run the platform-contract verification. Re-check the date against the vendor page before acting, in case retirement slips.
