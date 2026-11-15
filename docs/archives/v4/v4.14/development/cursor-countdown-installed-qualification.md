# Cursor Countdown Installed Qualification

Installed-host qualification for the v4.14.7 readable reset countdown change, observed on Windows on 2026-11-02 through Computer Use. Release publication remains open.

## Artifact

- Source revision: `7365d5cf297c94e033dbefb030f9902ba1189443`, integrated through PR #595 into develop at `92face60b20083481216e2ee8055753f3a78c623`.
- Candidate: `cursor-usage-monitor-0.1.0-v4.14.7-7365d5cf2.vsix` in the local temporary qualification directory `codex-01a19d33-cursor-qualification-7365d5cf2`.
- VSIX SHA256: `5d6fabadd0f1a34d39239cc7dca4b56cf216a314e921dabaa33139e1f96fc4a2`.
- Installed with the existing Cursor installation's official `resources/app/bin/cursor.cmd --install-extension <candidate> --force`; exit 0 and successful installation reported.
- All 26 packaged JavaScript runtime files under `out/` match the installed files byte for byte. Installed `out/dashboardPanel.js` SHA256: `5820148b17bf836fe7fbf019921572eefc4ddaa3a394e8d18d98e96d087e75b7`.
- The previous extension directory was preserved at `<qualification directory>/installed-before-qualification`; no user settings, credentials or account data were changed by the installation helper.

## Functional Exercise

- Boundary: actual installed Cursor desktop application, dashboard command `Cursor Usage: Dashboard`, with existing live usage tracking.
- Before installation: the accessibility tree and screenshot both showed `1242 min remaining` in Cursor Models, Other Models and Extra Credits.
- Action: install the verified candidate, execute `Developer: Reload Window`, then open `Cursor Usage: Dashboard` after extension activation.
- Expected contract: readable nonzero time units in each applicable countdown, with the reset date unchanged.
- Observed output: all three labels showed `Resets 11/3/2026, 10:43:07 AM (20 hours 38 minutes remaining)`; the dashboard reported auto-fetch at 2:04:52 PM local time on 2026-11-02.
- Extra Credits was naturally in the shared-limit-unavailable state, so its real countdown was observable without modifying account state or injecting fixture data.
- Comparison: matches the readable hours/minutes contract in all three actual labels. The reset date is unchanged; the remaining time decreased during the qualification interval.
- Evidence: native Computer Use screenshot and accessibility observations in this session for Cursor window 2427504. No separate screenshot file was exported.

## Coverage

This record adds actual installed-host observation to the existing source qualification: 371 passing tests, two existing skips, successful compilation and simulated-editor Chromium coverage of minutes, hours, days and weeks. Those prior results are retained evidence, not new test runs in this installed-host exercise. The real live countdown exercised hours and minutes; other live reset durations were not forced. The earlier Chromium geometry checks are separate from this native-host observation; no native-host DOM geometry detector or developer-console audit was performed. This installation is release qualification and does not establish a published v4.14.7 release.
