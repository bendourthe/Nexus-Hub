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

- Final focused selection: 96 passed in 21.14 seconds. It includes hook guarding, real Windows subprocess behavior, batch shims, positional arguments, legacy defaults, installer wiring and three affected runner paths. JUnit: console-window-root-repair-oct22/final-qualified.xml under the evidence root.
- Final Windows process files: 14 passed in 0.82 seconds during a separate desktop observation.
- The existing installed ~/.claude/hooks/console-window-guard.py returned 0 for the repaired project. The repaired source guard returned 0 for test, PowerShell installer, npm.cmd ci and npm run build commands. The full project scan completed in 3.430 seconds under its unchanged 20-second limit.
- Four command entry points import under -I -S -B and expose help successfully. Both installer syntax checks passed, including PowerShell 5.1 AST parsing.
- The actual PowerShell workspace installer ran successfully in fresh isolated homes, most recently Temp/ncw-oct22-quiet-approved, with exit 0. Assertions verify that installed nexus_process.py exactly matches source and the workspace console guard exists. The workspace-only install reports missing global Claude read paths; this is not a claim of global platform qualification. Real home paths were not installed or rewritten.
- Win32 desktop observation on the final code recorded zero new visible console windows in 1,018.86 seconds (84,188 samples) and again in 40.50 seconds (3,306 samples), but user input occurred in those intervals. An earlier source iteration had an uninterrupted idle observation of 359.16 seconds, 29,584 samples, zero new visible console windows and no foreground process change. The final-source approved quiet interval then covered both affected process tests (14 passed in 1.99 seconds) and the actual isolated installer (exit 0): 10.387 seconds, 798 samples, minimum idle 1,031 ms, zero visible console events and only the initial foreground process. No keyboard or mouse input occurred during that interval. Evidence: approved-idle-desktop.json and approved-idle-0/1.log.
- Focused independent correctness and security rechecks found no remaining confirmed defect in positional compatibility, legacy default upgrade or expanded dictionary overrides. These are bounded reviews, not full-suite or complete scanner-coverage claims.

## Preservation and Adoption

Every applied edit used the official edit guard with zero accepts. The native run record remained SHA-256 246a0a40f4e28ffc02c3acc957dce4627d4ff3f1848c19d3cb359922590b884a. Frozen approval and review budgets were not reset. The goal remains active; this maintenance repair does not complete v4.14.

Source policy SHA-256: 14ddaaf6bf0f0d48827a866f6ab9cd314676ea4c7644c8bf9f9758e7ea399567. Source guard SHA-256: 8e8e34dbe78edf51085a1a98fa05a33c7a0780d81ab243d83cb5d3e218a8ac5f. Evidence root: C:/Users/BEDOURTHE/AppData/Local/Temp/nexus-v4140-native-hook-budget-oct17/console-window-root-repair-oct22.

Template parity and the exact 2,061-entry staged manifest match also pass. Integration and reviewed runtime adoption are pending. Installed native scripts and the real-home guard have not been manually replaced.
