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

## Integration and Adoption

This is source qualification against genuine native authority. Installed scripts and approval records were not replaced or edited. Maintenance integration, hosted checks and reviewed runtime adoption remain pending. The v4.14 goal remains active.
