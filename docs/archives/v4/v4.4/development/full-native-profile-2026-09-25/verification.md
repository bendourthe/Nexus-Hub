# v4.4 Windows full-profile follow-up - 2026-09-25

This record qualifies the current repository-native Windows profile with a process-local Git Bash PATH correction. It does not turn the original v4.4.6 NO-GO run into a pass or complete the user-superseded v4.4.6 plan.

## Full-run receipt

- Source commit: `bb3b2b97fee1eee2f4212419942a655aa2115271`, the PR #301 merge result. The isolated worktree was clean before and after the run.
- Host: Windows 11, CPython 3.12.10, Git 2.52.0.windows.1. The run began at `2026-09-25T06:18:20Z` and ended at `2026-09-25T08:18:41Z`.
- Process setup: prepend `C:\Program Files\Git\bin` to PATH for this PowerShell process only, then run `python scripts/ci/run.py --profile full --quiet --reports-dir reports` with no `--base` or group filter.
- Terminal result: exit code 0, 61 passed, zero failed, zero skipped, zero advisory in 7,220.4 seconds. All 12 groups passed. The 13 test commands and seven extension checks passed; the previously incomplete repository test coverage now has terminal results in every partition. Twelve JUnit group files, CI coverage XML, and a skill-security SARIF file were emitted.
- Receipt integrity: the ignored `reports/summary.json` had SHA-256 `6991128C029A21BEBA8C0D6004E2EE9050CE55CE9FCA5BEA404DC0788909809F`; `reports/metadata/environment.json` had SHA-256 `6756765BA0495129A6CC0E550264FBBC6BE78C7BDC500585EE5C3AAAE4C058A2`.

| Group | Passed commands |
|---|---:|
| catalog-parse, hygiene, interpreters | 13 |
| catalog, security, workflows, claude-plugin | 12 |
| platform-contracts, docs, version | 16 |
| tests | 13 |
| extension-tests | 7 |
| Total | 61 |

The 13 test partitions include `hook-tests` (1,242.1 seconds), `repo-tests-integrations-adapter-contracts` (1,294.9 seconds), `repo-tests-guides` (508.1 seconds), and `repo-tests-governance` (1,490.7 seconds). Every test partition reported `pass`; none reached its configured timeout.

## Current-tip and host limits

Current `origin/develop` at `0338b11db03312cef45facfb3b4da2a0ec305c80` differs from the full-run commit only in five documentation and evidence paths from PRs #302-303. A separate clean detached checkout at that exact tip passed the native fast profile 17/17 and the full profile's docs group 8/8, both with the same process-local Git Bash prefix. This is changed-path coverage, not a second full run on the newer tip.

The default Windows PATH still resolves `bash` to the unusable System32/WindowsApps shim. A fresh `python scripts/check_interpreter_resolution.py --gate` without the prefix exited 1 and warned that hooks launched as `bash <script>` could be inert. The identical gate with `C:\Program Files\Git\bin` first exited 0 and resolved Git Bash. Changing the user's persistent PATH is a separate host decision; no user or system environment setting was changed here. QG-446-1 therefore has a green process-qualified full run but remains open for the default-host interpreter boundary.

The original [full-profile disposition](../../../../../releases/v4/v4.4/development/guide-learning-experience/phase-7/full-profile-disposition.md) remains the immutable failed-run record. The v4.4.6 plan is marked superseded by the user, so its T027 and T028 boxes are not completed by this post-release verification. MT-446-1 comprehension and final visual approval and MT-446-2 native zoom and OS occlusion remain separate manual gates.
