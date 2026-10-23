# Windows Console Window Repair

This record covers the October 22 Windows focus-stealing console regression, the isolated maintenance repair and its verification limits. Read it when reviewing launch policy, installer distribution, console guarding or runtime adoption.

## Scope

The user authorized an isolated worktree based on develop commit 393edec8af2f5a37e507a6ac678ee117ec0c2ee9. The repair branch is fix/console-window-root-repair. The primary checkout and other agents' work remain untouched.

## Cause and Process Ownership

Yes, this session launched unsafe console descendants. Private freeze_candidate.py used two Git launches without a hidden-window flag, and guarded_apply.py imported an installed edit guard whose Git calls omitted it. Tests and checker probes also launched console descendants. This establishes our contribution to the risk; it does not identify the owner of every observed popup. Historical child process identifiers were not comprehensively recorded, so no complete historical process census is claimed.

The owned long-running runs were the governance pytest invocation (unified handle 30623, actual process 49928 and launcher 24620) and the native trace (handle 30939). Both were interrupted through their exact owned handles and their known processes were confirmed gone. The guides run (65275), worker regression (32628), measure_native_final.py, run_fixture_qualified.py, freeze_candidate.py, guarded_apply.py, stage_rebudget/count_gap_repeats helpers and reviewer probes were also accounted for in the session inventory. An owned diagnostic guard profiler was stopped through its retained child handle during this repair. No process was terminated by matching a name or command line. Other agents' processes were not stopped.

All subsequent verification and Git launches in this repair used Node child_process with windowsHide: true. Python helpers that import installed scripts were run with -B and prefixed with the shared no-window policy.

## Repair

- scripts/nexus_process.py supplies one Windows subprocess default for product commands and all eight pytest roots. It preserves positional arguments and output forwarding, adds CREATE_NO_WINDOW, rejects detachment and new-console flags, upgrades an older generic wrapper, and handles batch shims through a hidden cmd invocation with literal arguments.
- Standalone distributed helpers retain explicit creationflags so copied hooks and skill scripts do not depend on an unavailable repository helper. Node provider launches set windowsHide: true.
- Both installers copy the shared process module beside the native commands. AGENTS.md, instruction templates and distributed Python and TypeScript rules carry the policy. Start-Process uses the supported hidden form; PowerShell cannot combine WindowStyle Hidden with NoNewWindow.
- The guard inspects test, installer, build and helper commands, including quoted Windows executable paths. Launch aliases, forbidden flags, expanded dictionaries, scoped shared defaults and reasoned same-line exceptions have regression coverage. Ambiguous flag resolution fails closed; bounded resolution keeps the original 20-second scan limit.

## Verification

- Initial focused selection: 96 passed in 21.14 seconds. It includes hook guarding, real Windows subprocess behavior, batch shims, positional arguments, legacy defaults, installer wiring and three affected runner paths. JUnit: console-window-root-repair-oct22/final-qualified.xml under the evidence root.
- Final Windows process files: 14 passed in 0.82 seconds during a separate desktop observation.
- The existing installed ~/.claude/hooks/console-window-guard.py returned 0 for the repaired project. The repaired source guard returned 0 for test, PowerShell installer, npm.cmd ci and npm run build commands. The final full project scan completed in 4.915 seconds under its unchanged 20-second limit.
- Four command entry points import under -I -S -B and expose help successfully. Both installer syntax checks passed, including PowerShell 5.1 AST parsing.
- The actual PowerShell workspace installer ran successfully in fresh isolated homes, most recently Temp/ncw-oct22-quiet-approved, with exit 0. Assertions verify that installed nexus_process.py exactly matches source and the workspace console guard exists. The workspace-only install reports missing global Claude read paths; this is not a claim of global platform qualification. Real home paths were not installed or rewritten.
- Win32 desktop observation on the final code recorded zero new visible console windows in 1,018.86 seconds (84,188 samples) and again in 40.50 seconds (3,306 samples), but user input occurred in those intervals. An earlier source iteration had an uninterrupted idle observation of 359.16 seconds, 29,584 samples, zero new visible console windows and no foreground process change. The final-source approved quiet interval then covered both affected process tests (14 passed in 1.99 seconds) and the actual isolated installer (exit 0): 10.387 seconds, 798 samples, minimum idle 1,031 ms, zero visible console events and only the initial foreground process. No keyboard or mouse input occurred during that interval. Evidence: approved-idle-desktop.json and approved-idle-0/1.log.
- Focused independent correctness and security rechecks found no remaining confirmed defect in positional compatibility, legacy default upgrade or expanded dictionary overrides. These are bounded reviews, not full-suite or complete scanner-coverage claims.

## Publication Verification

The final affected regression selection passes all 109 tests in 43.41 seconds. Independent source reads overlap in ordered batches of 16 with eight threads; the regression proves that every unsafe launch is still reported. There is no cache between requests. A focused performance review found no remaining confirmed defect; the existing deadline remains a soft scan budget around uninterruptible file reads and analysis.

The screenshot helper mock now requires and verifies creationflags; its 12 affected tests pass in 0.38 seconds. The isolated native-launcher fixture includes the CLI process policy dependency; all three ordinary, bracketed and Unicode profile cases pass under PowerShell 5.1 (8.76 seconds) and PowerShell 7 (7.63 seconds). The local evidence path is portable. Standing instructions contain a four-word policy link; the six applicable word ceilings increase only by the exact 1-5 words needed for this explicitly requested durable rule, with no extra headroom or unrelated instruction deletion. The full policy remains in distributed language rules. The legacy fingerprint file is regenerated from actual history and current template bytes.

The distribution handbook explains hidden process policy delivery and includes the shared module in its dependency map. Its deterministic build check and 200-state Chromium measurement pass; fresh content and representative visual reviews are recorded in windows-console-handbook-review.md.

## CI Correction Verification

The correction integrates develop commit 7b0a09a0df0899f6daf43d17789986bc87cdb57e and preserves its Copilot monitor changes. Isolated installed-layout fixtures now explicitly copy nexus_process.py beside the CLI or completion gate, and the installer smoke postcondition requires that distributed dependency. The capability broker mock verifies the hidden-window flag. Seventeen guide references, including comma-separated line lists, are mapped through unchanged installer source spans after the added copy steps.

The two affected selections pass: 153 tests in 145.84 seconds, and 173 tests with 24 browser skips in 371.17 seconds. The skips came from the default Chromium cache path. With the existing pinned Chromium cache, 24 guide cases pass in 131.65 seconds; that run exposes three remaining comma-separated citation errors. After correcting those references, the three affected cases pass in 6.10 seconds. All 27 guide cases therefore have passing pinned-browser evidence across those runs. A broader selection was interrupted through its owned process tree because it included unrelated release-lifecycle fixtures; it supplies no passing qualification. The narrower selection covers the changed completion-gate fixtures and the affected hook, plugin, installer, broker and guide files. Retained JUnit: ci-remaining-fixtures/targeted.xml and ci-fixture-dependencies/narrowed-targeted.xml under the evidence root.

The merged installer then exits 0 in a fresh isolated home, with source-identical policy and workspace hook assertions. The desktop remains idle for its full observation: 26.676 seconds, 2,097 samples, zero new visible console windows and no foreground-process change. Raw observation: windows-console-merged-desktop.json. The repaired and installed console guards both return 0 on the merged project. Handbook, instruction budgets, fingerprints, guide stamps, personal paths, attribution and staged whitespace checks pass. A fresh generation exactly matches all 2,061 staged manifest entries. Hosted checks and reviewed runtime adoption remain pending.

## Installed Policy Reachability

Standing instructions now link to the global style-guides/windows-processes.md policy. Direct workspace installs do not retain the source checkout previously named by the link. Both installers already distribute the global style-guide directory. The new regression first fails on the absent-checkout reference, then all nine console tests pass in 0.54 seconds after correcting AGENTS.md and all 16 instruction templates. The prior eight real-console tests also pass unchanged.

The actual isolated workspace installer exits 0 and asserts that the installed global policy matches source byte for byte and that the seeded CLAUDE.md points to that file. The observation records 152.704 seconds, 12,888 samples, zero new visible console windows and no foreground-process change. The minimum idle time is 1804031 ms. Raw observation: windows-console-policy-desktop.json. The original global Claude read-path advisory remains a qualification limit. The helper and source guard bytes are unchanged. Fingerprints, instruction budgets and handbook checks pass; hosted checks must run at the new commit.

## Final Windows Fixture Correction

CI run 39882000951 at head 4f2360de3297e30597083ff0dd8256e5c41c7a4b passed 41 checks and failed the Windows installer group. The short job summary exposed twelve cases, reproduced exactly on unchanged source: 12 failed in 18.86 seconds. The later full artifact review found 28 failed cases across two commands and a separate validator command that timed out; the twelve-case summary was incomplete. The isolated organization launcher omitted nexus_process.py, two no-terminal fixtures explicitly requested DETACHED_PROCESS, and executable-lookup mocks did not accept the path argument used by the shared process helper.

Five fixture files now copy the shared dependency, use CREATE_NO_WINDOW with redirected input, and preserve the existing which mock behavior with its proper optional path argument. The exact twelve cases plus three adjacent cases pass: 15 passed in 27.55 seconds. Five AST parses, staged whitespace and the official five-file guard apply pass with zero accepts. Distributed process policy, installer and guard bytes are unchanged, so the earlier actual installer and idle-desktop observations remain the behavioral evidence for those bytes. The complete hosted check must pass at the correction commit before merge. Retained receipts: ci-final-installer-failure/ and ci-final-installer-fixture-repair-1792720631714/ under the evidence root.

## Complete Windows CI Diagnosis

The complete failed-run artifact records one installer failure with 789 passes and 45 skips, 27 a-c validator failures with 1,003 passes and one skip, and a co-z validator timeout after 1,800.203 seconds with four failure markers. All 28 named installer/a-c cases pass after the fixture corrections: 28 passed in 63.62 seconds. Three co-z failures were executable-lookup mock signatures in test_interpreter_resolution.py; the complete file passes all 11 cases in 1.34 seconds after accepting the optional path argument. The timeout itself supplies no completed co-z qualification.

A bounded diagnostic with named cases reproduced the fourth failure, test_git_ssh_matches_what_git_itself_reports. Its unchanged Git oracle exercises a git.cmd wrapper, and the shared launcher rejected the literal exclamation mark required by Git shell aliases. The exact case failed in 1.22 seconds. The diagnostic was stopped through its owned process tree after reproducing that case; all 92 source pins remained unchanged and no unrelated process was stopped.

The shared launcher now passes /v:off to its hidden cmd parser so exclamation marks remain literal, while percent signs, quotes, NUL, CR and LF remain rejected. Policy version 2 upgrades an existing version-1 default before converting batch arguments. Private checks cover six direct/ancestor expansion and environment modes, literal alias and adversarial metacharacter arguments, absent injection markers, five rejection inputs, positional flags and streams, upgrade and repeat-install idempotence. The complete process-policy file, unchanged SSH oracle and two nearby route cases pass: 21 passed in 10.08 seconds. Arbitrary batch script internals can still enable delayed expansion themselves; the guarantee covers the helper command parser.

The final affected selection includes the real no-console tests and passes all 30 cases in 9.06 seconds. The actual PowerShell installer exits 0 in a fresh isolated home and verifies source-identical installed policy, global policy guide reachability and workspace hook presence. Win32 observation spans 112.978 seconds and 9,166 samples: zero visible console events, no foreground-process change and no keyboard or mouse input (minimum idle 132,828 ms, equal to the starting idle value). Raw observation: windows-console-literal-bang-desktop.json. Retained logs and inputs: literal-bang-policy-1792723880632/ and literal-bang-desktop-1792724315719/ under the evidence root.

Develop commit 15bd767d6f149ac6ac917bb47517a8cb8376102d is integrated locally, preserving the Cursor local-plugin source and its independent handbook review. The merged handbook gate passes, and all six changed Cursor cases pass in 21.96 seconds. The complete hosted Windows command and the aggregate timeout remain pending fresh CI at the correction commit; no timeout cap or test expectation was relaxed.

## Latest Upstream Integration

CI run 39893143001 at commit 6960246cd passed 44 validation commands, failed only the handbook gate and skipped one unavailable plugin executable. Its complete validation artifact identifies the changed launcher input as stale handbook evidence. The controller stopped only that owned CI run after retaining its full report; it supplies no completed Windows aggregate qualification. The handbook review and snapshot are refreshed against the final launcher source before republication.

The repair also integrates develop commit e89647de8fe05d6a9da9a7d624d12b039b3196c7, preserving PR 517's edit-guard performance changes. Its background-prune launch was already hidden on Windows, but a conditional options dictionary could not be verified by the strengthened console guard. Explicit creationflags and platform-appropriate start_new_session now make that launch verifiable on both platforms. Two new cases fail on the unchanged launch expression in 0.64 seconds; the complete three affected files then pass 59 cases with one host-privilege symlink skip in 38.45 seconds.

A real background-prune child exits 0 against a private fixture store and uses CREATE_NO_WINDOW. The actual isolated PowerShell installer also exits 0. Their second Win32 observation spans 64.318 seconds and 5,583 samples, with zero visible console events, no foreground-process change and no user input (minimum idle 1,080,250 ms, equal to the starting value). Raw observation: windows-console-prune-desktop.json. Both source and installed console guards return 0 on this merged project. The final focused hygiene and documentation profile passes all 18 commands in 114.1 seconds, including the full handbook gate; its deterministic builder confirms the unchanged handbook HTML. Retained inputs, red/green results and actual-child logs: guard-prune-integration-1792725289274/ under the evidence root.

The distributed edit-guard source is SHA-256 6b8bf8eeee25ae863ecdb07fc43dbc2edf9f27dad62d406d516d2414098bc92a. The operational guard remains the exact previously deployed bytes: canonical LF SHA-256 7307222c344feeb1c2194b2698458920a7ff8addf8260f91054c93946d8b48b7 (raw CRLF e950fdbc10cdcf0853c0eb878d8c9345d0ebdbcb61a62f787fbd5cd5aecf22af). No operational guard or installed native script was manually replaced. Full hosted checks and reviewed runtime adoption remain open.

## Preservation and Adoption

Every applied edit used the official edit guard with zero accepts. The native run record remained SHA-256 246a0a40f4e28ffc02c3acc957dce4627d4ff3f1848c19d3cb359922590b884a. Frozen approval and review budgets were not reset. The goal remains active; this maintenance repair does not complete v4.14.

Source policy SHA-256: 682df4e0a79bbd5304cd6985eda7d23a93ddc711b61d28c146a106bd25992c7c. Source guard SHA-256: a3bfec9c76052b069882905c2a0e362f8856ffa410203c62dcbae46e7b24a213. Evidence root: %TEMP%/nexus-v4140-native-hook-budget-oct17/console-window-root-repair-oct22.

Template parity and the exact 2,062-entry staged manifest match also pass. Integration and reviewed runtime adoption are pending. Installed native scripts and the real-home guard have not been manually replaced.

## Pre-commit Interpreter Boundary

A later checker validation exposed an additional Python-interpreter boundary: the external pre-commit CLI started Git without installing the shared policy. The checker maintenance correction loads the unchanged shared default inside pre_commit, repairs the timeout fixture's generated parent and extends command recognition and durable instructions. A safe RED and real Git flag regression pass; the two affected selections pass 82 and 91 cases with overlap. Actual named pre-commit checks and an isolated PowerShell installer pass within a 34.877-second idle observation: 3058 samples, zero visible console events, unchanged foreground process and no user input. The existing installed guard also passes against the project. See [checker maintenance evidence](check-minor-budget-observation-evidence.md#pre-commit-console-children) for scope and retained artifacts. Source integration and reviewed runtime adoption of this followup remain open.

## Merged Interpreter Followup

The pre-commit interpreter repair integrated through PR #521 at `7c3260743fc660919516f65f4b852c82e0d6021a`, with all 46 exact-head checks and the post-merge run passing. Its merged tree matches the tested tree. The retained 34.877-second idle observation covers the real named pre-commit checks and isolated installer, with zero visible console windows or focus changes. Source integration is verified; runtime adoption and global platform-hook delivery remain pending.


## Current Installed Guard Observation

The merged source guard executed successfully for project pytest, installer and pre-commit command payloads. An intentionally unsafe private launch site produced exit 2 and the expected remediation; the unsafe command itself was never executed. The current Claude installed guard instead contains zero physical newline bytes and 455 literal escaped CRLF sequences, leaving its entire content on a shebang comment line. It returned exit 0 even for that unsafe positive control. Its quiet exit is not active guard coverage. Current raw SHA-256 is ee741a0e018cf0eefa695d0d31e746f3c76cebf371a5e323f58c405896c6bcd2, with observed modification time 2026-10-23T17:40:48.812Z. The current bytes were preserved separately; this run did not deploy that change.

All 95 accepted native script hashes, the operational edit-guard bytes, both manifests and native authority still matched their accepted baselines during this observation. Source integration and the earlier idle desktop proof remain separate from installed guard delivery. Verified delivery must restore an executable installed guard and repeat both safe-project and unsafe-positive controls before installed coverage is claimed.

## Operational Preservation Guard Qualification

The separate installed edit-preservation helper changed externally at 2026-10-23T19:12:05.712Z, from the operational canonical `7307222c` baseline to canonical SHA-256 `ff1fbe60fb9e18f0b9830aae97c63f2f8980fa413e73739b528753ebe316bdef` (raw `6dbb14c3126305b70bca886e97cd60e81825f6e8dcdc2d146e302fce3d23e352`). The existing pinned apply wrapper stopped before any guard command or file write. The source of the installed edit remains unknown; this run did not replace or restore it.

Independent comparison found exactly three hunks: a hidden-launch helper and its use in two Git probes. All 69 other functions, including record/check/accept, store format and CLI behavior, match the previous operational guard. Seven stub-only cases passed for hidden flags, compatible flags, forbidden console/detached flags, argument preservation and POSIX behavior, without a real child launch or store call. The qualification receipt is `unexpected-official-guard-review-v4144-1792782957390/static-and-helper-qualification.json`, SHA-256 `dc0ba8fb4ae1f79de05ba640e1ce738581aac72b17283818c62d3493b2461847`.

A new private apply wrapper was derived from the pinned original by changing only the expected official-guard hash; its SHA-256 is `fd9f5e771c19ffc0887d6d03ff0face0050857c1e2eae44de6d3c26fcb0dfd3b`. It applied the one-entry bootstrap manifest update through official record/check/write/record/check with zero accepts. The separate installed Claude console-window hook still has raw SHA-256 `ee741a0e018cf0eefa695d0d31e746f3c76cebf371a5e323f58c405896c6bcd2`; the executable-coverage gap described above remains open. This qualification neither deploys that hook nor adopts the different merged catalog preservation helper.

A separate private GUI preflight exposed a source-guard recognition gap for external Python helpers launched with `pythonw.exe`. The equivalent normal-interpreter guard selection passed 80 tests; the final member qualification uses normal Python through the shared hidden launcher. No unsafe helper was executed. GUI interpreter command recognition remains open and is not covered by the earlier idle desktop observation.
