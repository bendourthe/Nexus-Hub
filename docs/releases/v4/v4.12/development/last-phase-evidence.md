# v4.12.0 final qualification

**Current scope: Phase 5 portable attribution.** The user expanded this release to include installed rules and a configured-user Git guard. The [portable qualification record](portable-attribution-evidence.md) owns current implementation, installer, review, handbook and CI evidence. The Phase 4 records below remain historical receipts, including their original non-passes; their repository-only scope does not describe Phase 5. The approved historical publication is complete. Portable feature integration and the v4.12.0 release remain separate pending gates.

Local qualification and publication preparation for the repository owner. Covers preserved history, maintainer enforcement, final review, inherited gaps and the explicit approval boundary for remote history replacement. No v4.12 remote publication has occurred.

**Date**: 2026-09-14. **Candidate input**: `e56d0251407ec84f59d9425cf6a64dc15c3a112e`, the Phase 3 commit. **Final revision**: the Phase 4 commit containing this record, resolved to its full SHA in the external publication manifest. The [backup record](rewrite-backup.md) identifies both independent mirrors and the active rewritten checkout.

## Architecture refactor

The indexed inventory reports `5,634 tracked files; 13 duplicate groups; 1,083 paths deeper than five components outside docs; zero empty top-level directories`. Raw detector membership is retained as `phase4-layout-inventory.json` beside the backup. The detector does not equate an identical file with an obsolete file.

The duplicate groups are Python package markers/placeholders, independently distributed checklists, extension build/config/license assets, preserved guide examples, platform instruction templates and deliberately duplicated test fixtures. Deep paths predominantly belong to the catalog's category/skill/bundle hierarchy and extension fixtures. These have independent consumers and are retained. No changed v4.12 runtime artifact is a duplicate. Its checker belongs in `scripts/`, tests in the matching validator/workflow suites, and the opt-in maintainer hook in `.githooks/`. This is the first sufficient structure; no new package or framework is needed.

The [docs cleanup report](../docs-cleanup-report.md) classifies release evidence separately from living navigation and the process decision. The only planned move is the decision's required proposed-to-implemented lifecycle transition. No unrelated archive or deletion is proposed. Full filesystem traversal of unrelated generated caches is excluded; indexed artifacts and the new phase records are the review scope.

## Known-gaps reconciliation

The tracked canonical and archived/legacy glob found 40 `known-gaps.md` files, all readable. `phase4-gap-inventory.json` retains every file's status and open sections. Older finalized ledgers remain historical evidence; this release does not restamp their tests or infer closure from a new run. The [reconciliation table](gap-reconciliation.md) gives every ledger a disposition.

Current-version findings are owned in the [v4.12 ledger](../known-gaps.md). Prior platform-discovery, native-rendering, model-profile, security-scan and extension gaps retain their original owners because this change adds no distributed capability and preserves historical file trees. The existing reporting-artifact gap in v4.4 WN-446-1 is relevant to terminal CI comparison and is cross-referenced rather than claimed resolved. v4.11 native authoring qualification remains UNMET where its own ledger says so; the separate repository handbook freshness check does not close that gap.

## Living docs architecture

`python scripts/check_release_preconditions.py --handbooks` returned `status: pass`, with both `overview` and `distribution` marked `verified` at candidate `e56d0251`. It bound current mapped Markdown, model, design, builder dependencies and output hashes. Neither handbook source nor renderer changed in this release.

`docs/handbooks/README.md` and the implemented mapped-source decision govern the current layout: editable inputs in `_sources/`, generated topic HTML at mapped paths, and `handbooks.json` as the authoritative map. The plan's older literal `html/` directory example is not a reason to migrate valid mapped outputs. `docs/README.md`, `docs/DEVLOG.md` and `docs/todos.md` remain living navigation. No `docs/testing/` or `docs/validation/` directory was invented.

## Git-tree hygiene

`python scripts/check_release_preconditions.py --branches --repo-settings` reported:

```text
OK: no merged remote branches to clean up
1 branch survives a CLOSED, unmerged PR: origin/fix/target-manifest-git-trust-skip
Reporting only -- nothing was deleted.
Repository settings SKIPPED: isolated origin is a local mirror.
```

Direct authenticated read-only GitHub API calls filled the settings gap: default branch `main`, `delete_branch_on_merge=true`; both `main` and `develop` enforce administrators, disallow force-pushes and require the same five contexts: `validate`, `shellcheck`, `colocation`, `verify`, `ci-required`. The repository description still says 336 skills; the current catalog says 337. No setting was changed. No open PR exists at this audit.

The prerequisite cleanup already merged PRs 214-216, verified the final post-merge smoke/provenance, removed 31 merged local branches and preserved unmerged work plus seven stashes. Phase 4 adds no branch deletion. The remaining closed-unmerged branch is not silently discarded.

## CI/CD coverage

DETECT identified GitHub Actions. COMPARE inspected the existing pipeline against all 23 canonical fields below. PROPOSE: keep this plan's one profile-owned attribution command and full-history consumers; retain unrelated reporting/pinning differences as owned gaps. APPROVE/APPLY: the requested Phase 3 enforcement is implemented; the final phase additionally enables the existing Presentify verify workflow to run on manual dispatch, with full checks when PR metadata is absent; no unrelated pipeline migration or settings mutation is performed. RECORD: differences below remain visible. The comparison is PARTIAL, not a blanket pipeline-conformance claim.

| Field | Observation and disposition |
|---|---|
| 1 Provider | GitHub Actions under `.github/workflows/`. |
| 2 Profiles | `fast`, `full`, `platform`, `report`, `release` are declared in `scripts/ci/profiles.py` and selectable by `run.py`. |
| 3 Shared command ownership | Attribution runs once through hygiene; existing specialized CI browser/bootstrap steps remain separate. Their migration is outside this attribution change. |
| 4 Feature push | `ci.yml` has no push event. |
| 5 Complete integration gate | PR/merge-group CI includes validators, tests, renderer and native platform/bootstrap/install legs. |
| 6 No duplicate full merge suite | Post-merge runs fast smoke and provenance, not full validation. |
| 7 Minimal post-merge | `post-merge.yml` owns only smoke/provenance. |
| 8 Separate release | `release.yml` owns tag/dispatch release work; historical tag updates must be batched as documented below. |
| 9 Aggregate | `ci-required` uses `if: always()` and an allowlist of success/skipped, with missing-result rejection. |
| 10 Required contexts | Five existing contexts; no per-matrix-leg name and no new context. |
| 11 Job scoping | Unfiltered PR events for the protected branches; the classifier and consumer conditions fail closed. |
| 12 Runners | Hosted Ubuntu, Windows and macOS; no persistent self-hosted runner in the gate. |
| 13 Expensive legs | Windows/macOS legs run before integration. |
| 14 Pinning | Third-party actions use full SHAs; existing pip tooling installs are not fully version-locked. Retained maintenance gap. |
| 15 Permissions | Explicit read-only CI; elevated release/attestation permissions isolated to their owner workflows. |
| 16 Caches | Manifest-keyed pip/browser caches; cold installer smoke remains uncached. |
| 17 Concurrency | CI cancels superseded runs; post-merge/release preserve in-flight work. |
| 18 Forks | No privileged PR-target trigger or self-hosted execution in validation. |
| 19 Structured reports | Profiles emit summary JSON/Markdown and metadata, including a failed run. Complete JUnit/coverage artifacts are not produced by every test leg. Existing gap retained. |
| 20 Report retention | CI publishes summaries on every result but does not upload every detailed test report with explicit retention. Existing v4.4 WN-446-1 remains relevant. |
| 21 Deployment boundary | Release/attestation lives separately; no runtime deployment added. |
| 22 Recovery | Local reproduction precedes retries; original failed profile evidence is retained separately. Publication requires exact leases and recoverable original history. |
| 23 External settings | Both protected branches inspected; no mutation. A one-time operator-controlled publication exception remains necessary. |

Smallest future changes for fields 14, 19 and 20 are a tooling lock and profile-produced JUnit/coverage with seven-day report upload. Cost is extra artifact storage and dependency-maintenance work; risk is changing the existing CI contract during unrelated attribution work. These remain with the CI maintainer under WN-2, not an implicit permission to expand this change.

`check_installer_parity`, `verify_platform_contracts`, contract freshness and defaults synchronization passed in the 38-command validate-equivalent run. This checks code against the existing contract, not new vendor research. The release-time official-source refresh remains owned by `platform-contract-verification`; the product version remains 4.11.2 until a separate release handoff. Native installer evidence is recorded below and uses identical shared postconditions.

## Tier 3 deep pass

**Blast-radius verdict**: run. Maintainer CLI, local hook, validation boundaries and CI checkout behavior changed. Phase 3 is the source baseline; Phase 4 adds the workflow correction and manifest stabilization documented here. The Linux receipts bind each complete staged candidate by index tree and patch hash; the final evidence commit binds the completed record. The user also requested pre-implementation branch cleanup, which is included as a separate observed outcome.

| Feature | Task | Real boundary and representative input | Observed result |
|---|---|---|---|
| Identity policy and inventory | T001-T002 | Raw Git fields plus dated GitHub account mapping | Canonical owner, GitHub committer exception, agent trailers and old aliases are explicitly classified. |
| Full-history CLI | T003-T005 | Actual clean/dirty temporary repos, shallow and malformed inputs | Expected exit 0/1/2; current live scan clean. |
| Message and pending metadata CLI | T003, T012 | Commit message file and Git pending identities | Unknown author/committer/trailer rejected; valid owner accepted. |
| Rewrite and recovery | T006-T009 | Independent mirrors, raw commit-map comparisons, object lookups | 139 local refs retained; 1,697 trees/dates/ordered parents preserved; 182 attribution lines removed; original SHA recoverable only in backup. |
| Local hook | T012 | Real commits/amends and fresh Windows CRLF checkout | Canonical commit accepted; forbidden author, committer, trailer and inherited amend author rejected. Hook LF preserved. |
| Live validation and CI config | T010-T011 | Native hygiene command; parsed actual YAML consumers | One invocation; all hygiene consumers fetch full history; validate unconditional. |
| Installer exclusion | T003, T013, T018 | Actual Windows and Linux workspace installers | Windows and Linux pass all shared postconditions; both exclude the maintainer checker. |
| Maintainer instructions | T012 | README commands exercised in scratch consumers | Installation is opt-in; prior hook-path recovery documented; not installed into user catalog. |
| Prerequisite cleanup | User request | Git refs, PR merge results, post-merge jobs | All requested tracked work integrated before the new branch; merged-only cleanup and preserved unmerged refs. |
| Directory-membership stabilization | T022 | Real filesystem addition during hashing, with original timestamp restored | Original guard missed the change; corrected guard raises `directory_changed`; full module passes 54 tests with two Windows skips. |
| Remote publication and public contributor display | T020-T023 | GitHub branch/tag update and contributor pages | NOT YET EXERCISED: explicit approval required; default-branch UI proof follows publication. |

Rendered delegates are NOT APPLICABLE to changed local artifacts: no HTML, CSS, SVG, document generator or interactive UI changed. Existing handbook hash/freshness proof is separately recorded above. GitHub's two public UI surfaces remain pending external evidence; their unavailability is not a visual pass.

The [adversarial report](ADVERSARIAL-REPORT.md) preserves the independent reviewer's confirmed PR-ref finding. The remaining independent review was stopped by an automated security filter; QG-3 records that incomplete coverage, including the later stabilization change. No clean adversarial verdict is claimed. `fix_rerun_cycles_used: 3`: Cycle 1 corrected the queue-assessment copied relative link and restored an accidental README label encoding change found before staging; Cycle 2 added the missing manual-dispatch path for the existing required verify context, including an actual Bash detector exercise and workflow tests; Cycle 3 corrected the timestamp-only directory-change check exposed by the Linux full suite, with a deterministic regression and directory-entry comparison. Maximum three tree-changing correction cycles. External evidence-wrapper and test-host changes are environment work, not product-code correction cycles.

### Code-vs-plan convergence

Present-state inspection covers T001-T023. T001-T020 and the T022 local gate are complete within their recorded scopes and gaps. T021 and T023 require approval and remote observations. No duplicate convergence task is appended for work already assigned to those task IDs. The public all-ref wording is partial because GitHub retains read-only PR refs, recorded as QG-1; this is not hidden by the clean local scan.

### Goal-vs-plan sufficiency

| Question | Finding | Evidence and current action | Owner |
|---|---|---|---|
| What did implementation teach? | Pending metadata needs its own check; post-merge smoke also consumes hygiene. | `--pending-commit`, real amend tests and both full-history checkout changes close these omissions. | Attribution maintainer |
| Which assumption was false? | Writable branches/tags are not every ref GitHub retains. | 212 read-only PR refs; disclose the public scope and retain QG-1. | Repository owner |
| What would the Goal reader expect but has not been delivered? | Both contributor views must show only bendourthe. | No remote rewrite yet; T023 owns publication, cache timing and UI evidence. | Repository owner |
| What did the user ask beyond task lines? | Merge tracked work, return to develop and remove merged branches before starting. | PRs 214-216, 31 merged local branches removed, fresh feature branch from clean develop. | Completed prerequisite |

## Goal-vs-codebase review

The Goal is one public contributor account plus canonical history and prevention. Local CLI, hook, profile wiring and preservation proof satisfy the locally observable parts. A closed allowlist governs metadata, not the authenticated human pushing a commit; Git permits identity spoofing. GitHub's preserved committer exception is intentional.

The public Goal is NOT YET LANDED. GitHub still serves original history, and its retained PR refs cannot be updated by this push. A normal fresh clone after publication can prove branch/tag history; a GitHub mirror that also fetches PR refs cannot truthfully be claimed clean. No old SHA disappearance from GitHub caches is promised.

## Human/manual testing suggestions

After approved publication, verify the Code tab contributor account is exactly `bendourthe`; inspect Insights > Contributors for the default branch over all time excluding merges; open existing Releases and confirm tag names still resolve. There are no open PRs at this audit, so an open-PR-head sample is not applicable. If the contributor graph is stale, retain the observed account set and an explicit next-check timestamp in QG-2 rather than reporting success.

## Full-suite testing and stabilization

The first full repository-native profile ran on Windows with Python 3.12.10 and process-scoped Git Bash on PATH. It finished in 5,217.1 seconds with **46 commands passed and one timeout**: `repo-tests` exceeded its unchanged 4,500-second limit. The original `phase4-full/summary.json`, `summary.md` and console receipt remain unchanged beside the backup. The timeout handler captured no completed repository-test totals, so no assertion-level result is inferred for that command. This full run is NOT PASS and remains QG-4.

Completed Windows groups include 1,319 hook tests passed / 35 skipped, plus six extension suites totaling 830 passed / two skipped; the compression-accuracy command also passed. The hook resolver used Windows PowerShell 5.1 because this host has `powershell` and no `pwsh`; the installed interpreter set was not changed during the run. The 38-command final validate-equivalent run and the 108-passed / 17-skipped affected workflow check separately cover the final workflow change made after the initial full run began.

CI runs the complete repository test job on Ubuntu with Python 3.11, and assigns Windows only its declared native platform commands and six integration files. The local rerun follows that existing split; it does not increase any timeout or remove any test. A temporary Linux container uses Python 3.11.13, the six CI extension dev extras, `pytest`, `tomlkit`, `PyYAML` and additional Pillow coverage. It checks a native-filesystem clone as UID 1000, with the exact staged patch applied before any check. `phase4-linux/source-binding.json` records HEAD `e56d0251`, index tree `19ad7bcea65c4b44326d1e7ac6b638d96e696937` and patch SHA-256 `0a6309c7ab680ef337a8f5339b498d9a04bfc9e153cacb481c9df45e863877c8`. No live worktree edits enter that snapshot mid-run.

The initial Linux full profile completed 46 commands successfully and failed `repo-tests`: one directory-change assertion failed, with 4,970 tests passed and 343 skipped. Its original receipt stays in `phase4-linux/full/`. The failed check compared directory identity and modification time only; a fast new file can leave both unchanged. A deterministic variant restores the original timestamp after adding the file: before the fix it failed while the ordinary variant passed on Windows. The corrected manifest also checks entry names. Its module now passes 54 tests with two explicit Windows skips, and both changed Python files pass Ruff. This is BG-1 and the third bounded stabilization cycle, not a rewrite of the original failure evidence.

The corrected Linux **full profile passed all 47 commands** in 358.6 seconds, finishing at `2026-09-14T22:29:54Z`. Its eight pytest suites total **6,583 passed and 918 skipped**, with five existing Python 3.11 deprecation warnings; the compression-accuracy gate also passed. Host/dependency skips remain visible in the raw receipt. `phase4-linux-corrected/full/summary.json` and `summary.md` are the complete new result, not a focused rerun. `source-binding.json` binds index tree `a9752165684e56e2e13e9294272b8dab2872f56d` and patch SHA-256 `a4f702f9a9747140a92683bedfcd82047362cd8b5b554adc23d679610706b06b`; `pip-freeze.txt` retains installed versions. The final commit differs from that passing source snapshot only in Markdown evidence/tracking records, checked again by final local validation.

Windows CI coverage is recorded by its actual commands rather than promoted to a whole-Windows-profile pass:

| Windows check | Current observed result | Receipt beside backup |
|---|---|---|
| PowerShell 5.1 hook suite | 1,319 passed; 35 skipped | Original full receipt, passing hook command |
| Six native integration files | 251 passed; two skipped | `phase4-windows-ci-native.txt` |
| Installer and validators, complete rerun | 2,070 passed; 45 skipped | `phase4-windows-ci-installer-rerun.json` |
| Security-audit evidence command | 458 passed; ten skipped | Passing command in `phase4-windows-ci-remaining.json` |

The first installer/validator command remains failed: `WinError 5` while replacing a temporary settings file, with 2,069 passed and 45 skipped. Five isolated attempts did not reproduce it; no cause is asserted and no helper code or retry policy was changed. WN-4 retains that unexplained failure. Its complete rerun passed in 537.9 seconds. The separate security-evidence command passed in 596.1 seconds and exercised the corrected manifest. The original Windows full timeout remains QG-4. These historical non-passes are not overwritten by the green current Linux full and Windows CI-command results.

## Publication and integration

Publication is pending explicit approval. The captured writable GitHub ref set is 3 branches and 116 tags; a fresh comparison found zero changed tips. Local-only historical branches, two local-only tags, stashes and internal checkpoint refs are backup/review material, not newly public branches.

The candidate will integrate locally into rewritten `develop` and `main`; prevention files must be present on both tips. Prepare exact old/new ref SHAs and `--force-with-lease=<ref>:<old>` for every public ref. Use one atomic batch containing all 116 tags, plus the reviewed branch updates; never `--mirror`, which would publish internal refs. Do not change tag file trees or manufacture new releases. GitHub documents no tag push events when more than three tags are pushed at once, avoiding historical release reruns. [Event behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

The captured rewritten `main..develop` range contains 18 existing commits and 36 changed paths before v4.12. These include the already merged slide-build, figure guidance, cache-accounting and monitor-test work from the prerequisite cleanup. Bringing the complete candidate to main also brings those changes; it is not a metadata-only main update. `integration-scope.json` beside the backup preserves both baseline tips and the complete commit/path list. The final publication manifest must state this inherited scope as well as v4.12's four local phase commits.

GitHub's 212 `refs/pull/*` are read-only and remain outside the writable publication set. [GitHub PR-ref contract](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/checking-out-pull-requests-locally). Existing signatures and SHA-based provenance do not become valid for rewritten objects; original signed objects and receipts remain in the recovery mirror. Release assets are retained as original artifacts, not falsely re-attested under new SHAs.

Both branches currently prohibit force-push and enforce PR/status requirements on administrators. The final approval must identify the exact refs and the necessary temporary operator-controlled exception, followed by restoration of the captured settings. No protection may be deleted. After publication, dispatch `ci.yml`, `doc-colocation.yml` and `presentify-extractor.yml` on the rewritten tips, observe all five required contexts and post-merge smoke, then scan a fresh normal clone. A dirty fresh-clone scan triggers recovery from the original mirror, not a second layered rewrite.

Offline protection payloads change exactly two fields per branch: `allow_force_pushes` from false to true and `enforce_admins` from true to false. This temporarily permits force-push by writers and allows administrators to bypass the retained PR/status requirements. All five required checks, conversation resolution and other settings remain in the payload. Approval must cover that temporary exposure. Before any mutation, re-read both protections and stop on drift; restore both exact saved payloads immediately in a `finally` path and verify fresh API responses. `protection-review.json` and the branch-specific temporary/restore JSON files are beside the backup. They are prepared only; zero settings mutations have occurred.

A temporary local bare remote rehearsed the 119 captured refs plus the new feature ref. A wrong expected develop SHA rejected the entire atomic push without changing any ref; the correct batch published all 120, a fresh normal clone scanned 1,686 commits with zero findings/errors, and exact recovery restored the original 119 refs. `publication-rehearsal.json` binds that mechanism proof to Phase 3 candidate `e56d0251`; it is not final-candidate remote evidence.

### Approved publication checkpoint - 2026-09-14

This checkpoint supersedes the pre-publication state described above. The owner's explicit approval covered the reviewed four branch refs and 116 tags, plus the temporary protection exception. One atomic push completed at `2026-09-14T23:07:37.124852+00:00` and matched all 120 manifest entries. `main`, `develop` and the feature branch point to `ba468f5f6b6f1bc96a69791e1fb2e76157a94f6d`; the retained fix branch and existing tags match their separate reviewed rewritten SHAs. Both main/develop protections were immediately restored and fresh API responses matched their original snapshots exactly. No new tag or release was created.

All five required contexts passed on this shared main/develop SHA: `validate`, `shellcheck`, `colocation`, `verify` and `ci-required`. [CI run](https://github.com/bendourthe/Nexus-Hub/actions/runs/34907413470), [Doc Co-location](https://github.com/bendourthe/Nexus-Hub/actions/runs/34907415524) and [Presentify verification](https://github.com/bendourthe/Nexus-Hub/actions/runs/34907417465). Both automatic post-merge runs passed smoke and provenance only: [main](https://github.com/bendourthe/Nexus-Hub/actions/runs/34907384213), [develop](https://github.com/bendourthe/Nexus-Hub/actions/runs/34907383091). Required-check observation: `2026-09-14T23:26:00.303313+00:00`. The shared commit was validated once through the explicit develop dispatches rather than duplicating the full suite on main.

A fresh normal GitHub clone at the published tip contains 1,687 reachable commits, zero attribution findings, zero scan errors and a clean `git fsck --full --no-reflogs`. Its 120 remote branch/tag refs match the complete publication manifest. This public-clone count differs from the local 1,700-commit audit because private historical refs were not published. All 116 release IDs, tag names and asset ID/name/size tuples are unchanged. There are no open PRs, so an open-PR-head sample is not applicable.

Public observation at `20260914T232622Z`: the contributor API returned `bendourthe` (1655), `dependabot[bot]` (8). The Insights page names main and excludes merge commits; its graph-data response contains only `bendourthe` with 1,345 commits. The Code page's server response includes a contributor loading placeholder. Both in-app browser and Chrome were unavailable, so rendered Code/Insights verification and the all-time control were not observed. T021 remains open. QG-2 sets the next manual check to `2026-09-15T23:15:00Z (September 15, 4:15 PM America/Los_Angeles)`; this is a recorded checkpoint, not a scheduled background task.

Raw receipts are beside the independent backup in `Nexus-Hub-backups/2026-09-14-v4.12-attribution/`: `approved-publication-result.json`, both restored protection responses, `fresh-public-clone-verification.json`, `postpublication-final-check-runs.json`, `postpublication-required-checks.json` and timestamped public-page/API observations. The original mirror and all original failed receipts remain unchanged. These post-publication Markdown notes are local follow-up evidence and were not part of the approved `ba468f5f` publication; no second push was performed.

### User screenshot verification

After publication, the user supplied two screenshots in this conversation. Screenshot 1 visibly shows Insights > Contributors with Period: All, main, excluding merge commits, and exactly one contributor: bendourthe with 1,345 commits. This passes the Insights portion of T021. Screenshot 2 visibly shows main at ba468f5, 1,685 commits, four branches and 116 tags; its Code sidebar says Contributors 5 and displays five avatars. This fails the Code portion. Account names for the additional avatars are not visible, so they are not inferred.

A live API recheck still returned bendourthe (1,655 contributions) and dependabot[bot] (eight), while contributor statistics returned only bendourthe (1,345). GitHub's official documentation says contributor displays and statistics can take about 24 hours to refresh after history changes; it recommends contacting GitHub Support if they remain incorrect afterward. [Official guidance](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-a-projects-contributors#contributor-data-is-stale-after-history-changes). QG-2 remains open for the Code sidebar, with the existing September 15, 4:15 PM Pacific checkpoint. The screenshot evidence supersedes the earlier inability to observe either rendered view. No remote change or additional rewrite was made.

## Phase 5 terminal reconciliation

The new helper, CLI delegation, installer activation and existing platform templates are the smallest sufficient implementation. Living guidance is in `docs/guides/user-attribution.md` and the installed style guide; the design record is in `docs/decisions/implemented/process/`. No unrelated repository or documentation restructuring is needed. The decision validator reports 42 valid records. Existing history, PR-ref and contributor-cache gaps remain open under their original owners. Platform discovery, native document authoring and CI reporting gaps are not closed by this feature.

Both live handbooks pass the mapped freshness gate. The distribution handbook's changed ownership explanation was rebuilt, measured across 200 states and visually inspected; overview retains its unchanged verified inputs. These are current-content checks, not a new native-authoring qualification. The [portable record](portable-attribution-evidence.md) names the raw receipts and preserved failed attempts.

The authenticated remote integration branch was fetched directly into `public/develop`, avoiding the recovery checkout's local pre-rewrite origin. It still requires `validate`, `shellcheck`, `colocation`, `verify` and `ci-required`. No branch-protection change or force-push belongs to this phase. The final feature diff and its commit count are measured against that remote integration ref before publication.

CI retains its current event/profile contract. Linux already collects the complete repository tests. Windows now includes `tests/test_git_attribution.py` in its existing installer/validator group, and the macOS installer matrix exercises native Bash/Git attribution. Workflow conformance and installer parity are checked locally. Required remote checks validate the integrated result once the normal feature PR exists.

### Tier 3 deep pass - portable extension

The functional matrix in [portable-attribution-evidence.md](portable-attribution-evidence.md) maps every new behavior to real Git or installer operations: configured users, metadata overrides, outgoing history, tags, existing hooks, streaming forwarding, worktrees, human replay, interpreter removal, rollback and platform delivery. Correctness, testing, standards and maintainability reviewers inspected the new feature. The goal review identified a legitimate-human-name false positive, which was corrected and exercised with Claude Martin. Independent follow-up re-ran and closed both interpreter-lifecycle defects. There is no unresolved reported portable-code finding; the older adversarial-review gap remains distinct.

Human testing after installation should run `nexus-hub attribution check` in an actual user repository, create a normal commit and checked tag, and verify the intended hosting account before publication. This is a practical adoption check, not a substitute for the automated qualification. Direct API/cloud writes and deliberate hook disabling are explicitly outside local enforcement, so no unconditional all-path guarantee is claimed.

The normal feature integration must finish green before `/update release` derives and presents notes from the actual last-tag-to-develop range. Version mutation, new tags and release publication have not occurred.
