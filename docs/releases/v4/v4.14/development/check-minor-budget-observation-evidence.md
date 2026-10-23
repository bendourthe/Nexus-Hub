# Minor Completion Observation Repair

This record covers the v4.14 whole-minor checker timeout, honest unavailable-observation verdicts, runner progress handling and source qualification. Read it when reviewing the maintenance repair or adopting its runtime.

## Defect

The installed checker exhausted its shared budget across seven members and reported controller-ownership-unavailable. A timed-out Git observation returned no ownership or provenance data; treating that absence as verified ownership failure or tampering produced a false terminal verdict. The previous whole-minor cap was 120 seconds.

## Repair

Unavailable repository, controller and record-provenance observations now produce INCOMPLETE with cannot-verify. Verified signature failures, tracked records and genuine controller mismatches retain their refusal behavior. Missing tag observations are cannot-verify when Git fails.

The checker supplies no numeric progress score when any required observation is unavailable. The completion gate and runner preserve progress counters in that case, including outer process timeouts and runner lease acquisition. A genuinely observed zero score still participates in no-progress detection. Cleanup and close command boundaries also handle unavailable observations.

One whole-minor evaluation has a 360-second default cap; each member retains its 20-second maximum share, and the environment can only lower the total cap. The runner allows the effective cap plus five seconds of process overhead. Successful ledger text is reused only at full immutable commit SHAs within the same evaluation. Branch scans reuse only identical branch-name and tip-SHA pairs. Moving refs, failed reads and authority decisions are not cached.

## Budget Evidence

The earlier complete source observation took 216.641 seconds, including 154.672 seconds of shared work. Seven fully consumed member shares require 140 seconds, so the measured shared work plus those shares requires 294.672 seconds. The 360-second cap leaves 65.328 seconds of margin for that workload. This is a bounded current-workload allowance, not a guarantee for arbitrary repository growth.

A read-only gap-stage trace returned the genuine unmet result in 136.703 seconds with zero errors or write attempts. The gap stage consumed 122.938 seconds. Repeated authority provenance checks consumed 50.386 seconds; migration verification consumed 57.360 seconds without Git or blob-cache calls. Additional authority caching and parser-index changes were left outside this correction.

## Verification

- The reviewed runner-lease candidate passed 34 affected tests with 57 deselected. The final cap change first failed three existing assertions, then passed 15 affected budget and runner-boundary tests with 76 deselected. AST, whitespace and nine official edit-guard checks pass; zero accepts.
- The final real seven-member source qualification completed in 204.438 seconds: 63.281 seconds for members and 141.157 seconds of shared work. Both default and effective caps were 360 seconds; no artificial member padding was applied. All seven members and all five minor predicates were evaluated.
- The source CLI exited 1 with INCOMPLETE. The qualification harness exited 0 after verifying complete stage counts, cap, timing and record preservation. Five unreleased members retain release.main cannot-verify observations, so the progress score is null; the five shared minor predicates have observed met or unmet values. The remaining predicates describe unfinished release, cleanup, migration and archive work. No observation was converted into a completion claim.
- Record writes are disabled in the qualification harness. The native record SHA-256 remained 246a0a40f4e28ffc02c3acc957dce4627d4ff3f1848c19d3cb359922590b884a before and after. Source files are checked against the frozen nine-file manifest immediately before invocation.
- Base Python runs with -I -S -B. Parent and child commands load the pinned hidden-window process default. The original measurement helper SHA-256 is 2b48164887406e3ae49836b3961c0b39d6aafb5f579fa64e1c4f04a7c42b52c8; its derived hidden-launch helper SHA-256 is 0d0c07b23e8720856f5fd08705a99b339f460a0f21b2d29daa18620e3650109f.

Retained artifacts: %TEMP%/nexus-v4140-native-hook-budget-oct17/checker-budget-prep-codex-oct22/post-review-native360. The proof file SHA-256 is 14c21f170a6f56bf2debab3ad39b1779ce2a5d50991adc5308c5ac673a92e921. The frozen source-manifest SHA-256 is 4f03dff1a0463211daa729eb90a2bd27c85238720f7ab9be2b070eb477743b3b. The corrected gap trace is retained beside it under gap-only-trace180-corrected-20261023T0031.

## Combined Source Recovery

The user approved a fresh isolated worktree after Git restored a text-equivalent file with different line endings and the old official guard refused its changed baseline. The old worktree, all thirteen restored files and its private Git recovery reference were preserved. Twelve source and documentation files were carried through the official guard; the supply-chain manifest was generated from staged bytes and applied separately. Both apply receipts report zero accepts.

The replacement branch starts at console-window repair commit 4f2360de3297e30597083ff0dd8256e5c41c7a4b. Its clean baseline passed 15 process-policy tests. The combined checker source passed 39 affected observation, budget and runner tests with 52 deselected in 2.94 seconds. Both the source and installed console-window guards passed for this project. Whitespace checks passed, the manifest contains 2,062 distributed entries, and the native authority hash above remained unchanged. These focused checks qualify the combined source; the earlier complete seven-member timing remains the recorded budget evidence. Recovery receipts are retained under %TEMP%/nexus-v4140-native-hook-budget-oct17/checker-budget-prep-codex-oct22/fresh-qualified-recovery.

## Current Console Integration

The checker branch now combines committed console repair bd5295cd6bcae94bf14be4cb6a562df7aa907d5d, including policy version 2, the Cursor local-plugin integration and the upstream edit-guard performance repair. The sole changelog conflict retains both maintenance notes. Nine checker-owned source, test and evidence files retain their exact pre-merge raw hashes. The old recovery worktree and private recovery reference remain untouched.

The exact 39 previously qualified checker regressions plus the current real process-policy and no-console files pass 66 tests in 7.32 seconds. Both source and installed console guards pass on this combined worktree. Canonical generation exactly matches all 2,062 staged manifest entries. These are fresh focused integration checks; they do not replace the earlier full seven-member timing, qualify hosted integration or establish installed runtime adoption. Zero edit-guard accepts. Retained merge input, preservation pins, JUnit and guard results: fresh-qualified-recovery/console-integration-1792726663339 under the evidence root.

## Hosted Console Integration

PR #519 merged into develop as fcc19cbb575d56e3e7da8d80e0451a3ffd24f2f0 after all 44 checks passed on exact repair head bd5295cd6bcae94bf14be4cb6a562df7aa907d5d. The checker branch then merged that actual integration commit through the official guard. No incoming source path differed from the previously qualified console tree; all thirteen checker-owned paths remained byte-identical and zero accepts occurred.

The retained current-head Windows reports show installer 790 passed with 45 skipped, validator groups 1030 passed with 1 skipped and 2095 passed with 12 skipped, plus hooks 2689 passed with 15 skipped. The previously timed-out validator group completed in 1711.85 seconds. This is hosted console-repair evidence; the checker repair still requires its own hosted integration and reviewed runtime adoption. Current-head reports and merged PR facts are retained under console-window-root-repair-oct22/current-head-hosted-1792729076.

## Hosted Checker Correction

PR #521 first published exact head 45236172f536cff3350b8375f6f8c8717d1e4383. The Windows installer job passed installer coverage (790 passed, 45 skipped in 313.40 seconds) and a-c validators (1055 passed, 1 skipped in 576.63 seconds), then timed out the co-z validator command at 1800 seconds near 74 percent with no assertion failure shown. The hosted aggregate correctly failed. The quiet log cannot identify an exact slow test. The prior console-only co-z result of 1711.85 seconds left 88.15 seconds of command margin.

Read-only review found no major new wait: the added mocked budget cases do not sleep, and retained Windows evidence measures the three new real CLI cases at 10.582 seconds total. This supports aggregate command fragility; it does not establish exact per-test hosted timing. The correction partitions the same validator corpus into a-c, co-h and i-z. All 117 current validator files run exactly once (37, 22 and 58 files), with future alphabet, co/completion, digit and underscore filenames covered by the regression. Every command retains its 1800-second bound, Windows-only selection and PowerShell 5.1 setting; the job retains its 60-minute bound and two-worker scheduling. Workflow YAML, assertions in product tests, runtime checker budgets and frozen plans are unchanged.

The regression first failed twice against the two-part profile. An initial affected CI run then passed 217 cases and exposed a stale three-command assertion plus a uv environment mismatch: base Python is externally managed. After the count correction, the same 219 affected CI/workflow cases passed in 53.65 seconds using the pinned virtual environment's windowless Python 3.11.15 executable. JUnit records zero failures, errors or skips; hidden PID 38004 exited 0. The actual repository-native --list command shows all four installer/validator commands. Source and installed console guards pass for the profile, and the expanded source guard passes for the installer command. Official guarded edits report zero accepts.

The final canonical fast profile passed all 18 commands in 120.1 seconds; hidden PID 13064 exited 0. The generated manifest still contains 2062 entries and changes only the CI profile hash.

Raw failed hosted logs and summary are retained under fresh-qualified-recovery/hosted-failure-1792732390. Regression, terminal process, JUnit, profile listing and guard receipts are under checker-ci-partition-1792732597697 in the evidence root. Earlier unchanged checker source and seven-member timing evidence retain their original inputs and limits; the new profile requires fresh hosted qualification. No retry is recorded as green before its actual terminal result.

## Develop Planning Refresh

Develop advanced to 90bbbfbc8d490287f198be075b1804b0a0d785d8 through planning PR #518 while the checker hosted run was active. Its five incoming documentation and tracker paths were merged through the official guard. All fifteen named non-overlapping checker-owned paths retained their raw bytes at the merge boundary, including every checker, profile and test file; no conflict or accept occurred. The generated manifest still exactly matches all 2062 staged entries.

The affected repository-native hygiene group then passed all eight commands in 120.0 seconds, with hidden PID 28520 exiting 0. The 219 affected CI/workflow tests and earlier checker timing retain their original unchanged source inputs and stated limits; this is a retained-plus-fresh qualification, not a new unfiltered full run. The partial hosted successes on head 572565aae do not qualify the refreshed head, which requires its own complete current-head checks. Merge input, preservation proof, canonical manifest and fresh hygiene receipts are under checker-ci-partition-1792732597697/develop-refresh-1792735457476 in the private evidence root.

## Integration and Adoption

This is source qualification against genuine native authority. Installed scripts and approval records were not replaced or edited. Maintenance integration, hosted checks and reviewed runtime adoption remain pending. The v4.14 goal remains active.
