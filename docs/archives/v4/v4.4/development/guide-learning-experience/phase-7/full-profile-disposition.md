# Full local profile disposition

Result: NO-GO. The native profile terminated with 40 passing commands, three failed commands, and one timeout. The full repository test group did not produce a terminal pytest result. This profile began before the final evidence-format corrections, so later narrow retests are identified separately.

| Command | Native result | Current disposition |
|---|---|---|
| validate_unicode_safety | Failed on a BOM and UTF-16 evidence log | Both normalized without changing substantive results. Strict Unicode and current fast-profile check pass. |
| validate_no_personal_paths | Failed on two matches in the unrelated v4.9 draft | Current fast profile reproduces only that same unrelated draft. Scoped v4.4 scan passes; other session's work remains untouched. |
| check_interpreter_resolution | Default PATH resolves incompatible WSL bash for a Windows script path | Child-only Git Bash retest passes. Global PATH remains unchanged; this is environment-specific retest evidence, not a default-host pass. |
| repo-tests | Runner reports timeout after 4,825.5 seconds, configured limit 4,500 | The still-live exact pytest process was explicitly stopped after 4,825.4 seconds, allowing profile completion. Both the native timeout result and stop record are retained. No aggregate pytest pass or assertion-failure diagnosis is inferred from missing output. |

Hook tests completed with 1,280 passed and 33 skipped. The six extension pytest suites completed with 43, 368, 29, 89, 237, and 53 passing tests respectively; two optional skips occurred across them. The compression-accuracy gate passed. These separate results do not replace the incomplete repository test group or sum into a whole-repository pass.

The independent guide suite completed with 258 passed and one optional mirror skip. Current documentation profile: seven passed. Current fast profile with test-process Git Bash: twelve passed, one unrelated personal-path failure. Historical QG-1 installer failures are not re-confirmed by this run because the timed-out group retained no terminal pytest report.

T027 remains open. Next diagnostic work should identify the stalled repository test with progress evidence and compare the affected boundary to the base, rather than blindly increasing the timeout or rerunning all tests. The final phase commit and publication remain gated. No process is left running from the native profile.
