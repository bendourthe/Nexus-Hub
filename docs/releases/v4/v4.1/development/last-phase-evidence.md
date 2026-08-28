# Last-Phase Evidence - v4.1.0 Skill Trial Records and Typed-Boundary Hygiene

**Date**: 2026-08-28
**Branch**: `feat/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts`
**Phase starting commit**: `fb48aed8`
**Comparison base**: `17d1af25`
**Plan**: `docs/releases/v4/v4.1/plans/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md`

## 1. Architecture Refactor and Documentation Layout

Commands and scans:

> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py inventory --root docs`
>
> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py refgraph --root docs`
>
> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py lifespan-contradictions --root docs`
>
> `InventoryExit=0; ActiveFiles=387; V41Inventory=9; RefgraphExit=0; RefTargets=102; Unreferenced=0; V41Unreferenced=0; LifespanExit=1; LifespanFindings=1703; V41Lifespan=0`

The lifespan findings are the historical post-tag baseline from older release buckets; no finding touches v4.1. Root-file, obsolete-name, empty-directory, duplicate-content, single-child-directory, and unusually-deep-path scans were triaged in `docs-cleanup-report.md`. No tracked artifact warranted a move or deletion, so no confirmation gate activated and behavior remained unchanged.

## 2. Known-Gaps Reconciliation

Evidence:

> `docs/releases/v4/v4.1/known-gaps.md: Status=finalized; Open WN=1; Open NI/DF/BG/MT/QG=0`
>
> `docs/releases/v3/v3.21/known-gaps.md: DF open 1; resolved 1`

v4.1 WN-1 records the remote GitHub description's stale 324-skill count for the approved publication flow. v3.21 DF-2 is resolved by this branch's current `docs/todos.md`; v3.21 DF-1 remains owned by v3.21. The plan-explicit v3.20 DF-1 and DF-2 remain on the v3.20 ledger and were not absorbed into this adoption.

## 3. Living Documentation Architecture

Scan:

> `docs/handbooks authored files=1 (README.md); catalog atlas/companion HTML=0`

The living handbook root remains a truthful scaffold rather than a fabricated product atlas. The absence is already v3.21 DF-1 and is not duplicated into v4.1. Release-bound plan, comparison, history, cleanup, known-gap, and evidence records all remain under `docs/releases/v4/v4.1/`.

## 4. Git-Tree Hygiene and Release Preconditions

Command:

> `python scripts/check_release_preconditions.py --branches --repo-settings`
>
> `exit 0 (report only); 3 merged remote cleanup candidates; 1 closed unmerged branch; delete_branch_on_merge enabled; remote description says 324 skills while the repository says 326`

No remote cleanup, settings edit, push, pull request, tag, or release was performed. The description mismatch is v4.1 WN-1 and must be handled only in the approved publication flow.

## 5. CI/CD Coverage and Installer Parity

Coverage inventory:

> `python scripts/ci/run.py --profile full --base 17d1af25 --list`
>
> `catalog-parse, hygiene, catalog, security, workflows, platform-contracts, docs, version, hook-tests, repo-tests, six extension suites, compression gate`

CI uses job-level classification without workflow-level required-check path filters, cancels superseded runs, and retains dependency caching. Hook tests cover `catalog/hooks/tests/`; repository tests cover `tests/`; the six extension commands cover every extension touched by the full profile. This plan adds no workflow, dependency, Oxlint job, or installer copy line.

The first final-profile attempt exposed one repository-native runner defect: Python extension commands inherited ambient import state, so a stale editable checkout could replace the package under test. The profile now gives every `src`-layout extension an isolated checkout-local `PYTHONPATH`; context-compressor also receives the code-search sibling it deliberately reuses for AST extraction. The CI engine contract suite requires these paths. The corrected extension group passed all seven commands before the full-profile rerun.

Parity commands:

> `python scripts/check_installer_parity.py` -> `PASS`
>
> `python scripts/verify_platform_contracts.py` -> `OK (10 platforms)`
>
> required-check context audit -> `OK (10 contexts across 2 protected branches; unconditional)`

Recursive skill copying remains identical across the two installers, and Phase 5 added no Node installation script.

## 6. Independent Goal-vs-Codebase Review

An independent read-only evaluator reviewed the plan goal and current tree rather than trusting phase checkboxes. It initially found four misses: parser-entrypoint ownership contradictions, no executable raw-memory dispatch path, invalid third-arm aggregation, and a rewritten v4.0 historical count. After correction it found two deeper misses in bundled assertion examples and undecodable raw-memory fallback, then exercised the generalized TypeScript assertion guard against namespace aliases.

Final verdict:

> `PASS - no unresolved Goal-vs-codebase misses remain; implementation satisfies the plan goal, acceptance criteria, and explicit non-adoptions.`
>
> `import * as React -> []; export * as api -> []; as string/as unknown/as { id: string } -> detected; focused guard suite 14 passed`

## 7. Browser and Human Testing

Automated browser proof used the generated three-arm fixture with Microsoft Edge headless at 1440x1000 and 390x1200. Desktop rendered three equal condition columns; mobile rendered one column in order with all response, grading, verdict, notes, and submit controls visible. The source path receives explicit wrap opportunities and width-safe fallback styling. No overlap or blank content remained in the accepted captures.

Suggested human checks for the publication candidate:

1. Run one real `--run-raw-memory` eval through the intended CLI and confirm the response metadata names that CLI, records `skill_loaded: false` and `memory_injected: true`, and passes the same assertion grader as the paired arms.
2. Open the viewer on desktop and a narrow browser, switch to Benchmark, exercise an invalid raw-memory fixture, enter a verdict and notes, and confirm `feedback.json` downloads with the selected values.
3. During approved publication, update the GitHub description from 324 to 326 skills and rerun the release-precondition report.

## 8. Full-Suite Testing

Final-tree command:

> `python scripts/ci/run.py --profile full --base 17d1af25 --reports-dir reports`

The machine-readable result is written under ignored `reports/`. The final status and counts are appended to this section immediately after the command exits; Phase 6 remains open until that evidence is green.

The first attempt completed 39 commands and reported three extension failures. Code-search and web-fetch could not import the current checkout's `src` packages, while context-compressor fell back from its code-search AST dependency to regex. Targeted reruns under the new isolated paths passed: code-search 368 passed and 1 skipped, web-fetch 29 passed, context-compressor 237 passed, and the actual extension profile passed all 7 commands in 62.0 seconds. These results diagnose and verify the runner correction; they do not replace the required final full-profile result.

The second attempt passed 41 commands, including the corrected extension group, and timed out only `repo-tests` at its 3,600-second runner ceiling. The same suite had passed the first attempt in 3,341.7 seconds, so the ceiling provided only 7.7% timing variance on this Windows host. The command-specific timeout is now 4,500 seconds and has a CI engine contract assertion; the suite must still complete successfully before this phase closes.

Final result:

> `PASS: 42 passed, 0 failed, 0 skipped, 0 advisory in 4723.9s`
>
> `hook-tests: 1162 passed, 33 skipped in 460.64s`
>
> `repo-tests: 3398 passed, 37 skipped in 3724.29s`
>
> `extension-tests: all 7 commands passed; code-search 368 passed/1 skipped; web-fetch 29 passed; context-compressor 237 passed; memory 53 passed/1 skipped`
>
> `compression accuracy: CCR 100.0%; signatures 100.0%; reduction 45.8%`

The report covers catalog parsing, hygiene, catalog validation, security, workflows, platform contracts, documentation, version synchronization, hook and repository tests, all extension suites, and compression accuracy. Phase 6 is green on the final implementation tree.

## 9. Publication and Integration

Local implementation is commit-only through Phase 6. Publication is not authorized in this run. The next gate is explicit maintainer approval for the plan's single branch push and integration pull request; `/update release` remains blocked until the integration result is green and merged.
