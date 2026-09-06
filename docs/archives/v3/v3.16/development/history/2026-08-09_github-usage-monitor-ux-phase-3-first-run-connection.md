# Session History - v3.16.3 Phase 3: First-run connection

**Date**: 2026-08-09
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.3-github-usage-monitor-ux.md](../../plans/v3.16.3-github-usage-monitor-ux.md)
**Phase**: 3 of 6 (not the final phase; no release-readiness workflow ran)
**Branch**: `develop`
**Outcome**: Complete. Quality gate GO.

## Goal

A freshly installed extension connects itself, and a user who declines is left in a clear state and never asked again.

## Sub-tasks completed

### 3.1 - First-run flow

Added [`providers/firstRun.ts`](../../../../extensions/github-usage-monitor/src/providers/firstRun.ts), a three-step sequence in which the ordering is the design:

1. **Silent.** `peekBinding` with `createIfNone: false, silent: true`. A user already signed in to GitHub in the editor sees nothing at all.
2. **One modal, ever.** Only when there is no session, no stored token, and no prior decline, `logInToMonitor` opens the real flow with `clearSessionPreference: true` so the billing account can deliberately differ from the Copilot account.
3. **Durable decline.** A dismissal writes `githubUsageMonitor.firstRun.declined` to `globalState`, and the flow never opens automatically again.

Wired into `activate()` **without being awaited**. The contrast with Phase 1 is deliberate and worth stating: migration *is* awaited because a configuration read that races it returns defaults, so the ordering is a correctness requirement. Sign-in is the opposite - it can block on a browser round-trip or hang, and activation must not wait on it, because a hung auth provider would otherwise delay VS Code startup for every user.

The whole sequence is guarded behind the same `autoFetch` respect the rest of the extension honors, reuses `logInToMonitor` rather than duplicating it (so scope escalation and owner resolution behave identically whether the flow was automatic or user-initiated), and never throws - a failing auth provider resolves to a decline, because an activation that fails on an auth error leaves the user with no extension rather than an unconnected one.

The explicit `logIn` command now clears the decline flag on success, so a user who changes their mind is not left in a state that suppresses future automatic connection.

### 3.2 - Unconnected presentation

Added a `not-connected` provider error code, distinct from `missing-token`. The distinction is the point: no credential at all is answered by connecting, while a rejected credential is answered by fixing a permission, and the two need different UI. Collapsing them is what made an unconnected install present as a failure.

- **Status bar**: `Not connected` rather than `--`, which reads as a number that failed to load.
- **Hover**: states that there is nothing to report yet, that the monitor reads billing usage for one configured owner, that it never reads code, and that clicking opens the panel.
- **Panel**: a purposeful empty state - one sentence on what the monitor does, one primary Connect button, and an explicit "what it reads / what it does not read" line. Deliberately **not** styled as an error; a genuine failure keeps the existing error treatment, and a test asserts both directions.

### 3.3 - Tests

15 tests in [`first-run.test.ts`](../../../../extensions/github-usage-monitor/test/first-run.test.ts). The load-bearing ones assert the `createIfNone: true` **call count** directly, because that number is the single thing separating correct behaviour from a modal on every startup: zero when a session exists, exactly one when it does not, zero on every activation after a decline. One test loops three further activations after a decline - a per-session flag would pass a single re-run and fail there.

## Closing v3.16.3 Phase 1 MT-1

Phase 1 recorded that `migration.ts` was well covered while its call site inside `activate()` was exercised only incidentally, with nothing pinning the ordering that makes it correct. Its suggested next step named Phase 3, on the grounds that this phase would need an activation harness anyway. It did.

The vscode stub gained an ordered configuration-access log, and a test asserts that the migration **write** of `githubUsageMonitor.staleAfterMinutes` precedes the first **read** of the same key, then that the read observed the migrated value rather than the default. Asserting the final value alone would have passed even if the read won the race, which is precisely the defect MT-1 was worried about.

## Troubleshooting

One failure, correctly classified as TEST rather than IMPL. `auto-connect.test.ts` asserted `missing-token` for the no-credential case; the new `not-connected` code is the point of the change, so the assertion was updated with a comment recording why the two codes are now distinct.

One scope correction of my own: `firstRun.ts` initially exported `isConnectionRefusalAnError()`, a function returning a constant with no call site. It documented intent rather than doing work, and the same reasoning was already a comment on the renderer. Deleted rather than kept - unused structure that looks like API is a maintenance liability, and coverage flagged it immediately at 28% function coverage for the module.

## Test results

| Suite | Result |
|---|---|
| Extension (Vitest, `npm run test:coverage`) | 288 passed, 0 failed (18 files) |
| Extension coverage | 82.08% statements, 78.47% branches, 82.09% functions, 85.7% lines - all above threshold |
| `firstRun.ts` | 100% line coverage |
| Compile + package | `tsc` clean; `npm run package` + `verify:package` succeed at `0.2.0` (59 files) |
| `test_installer_smoke.py` + `test_github_monitor_naming.py` | 48 passed |
| Repository validators | `validate_skills.py --bundles-only`, `check_version_sync.py`, `validate_workflow_security.py`, `validate_no_personal_paths.py` all pass; no unicode warnings in new files |

## CI/CD

No workflow change needed. `.github/workflows/github-usage-monitor.yml` triggers on `extensions/github-usage-monitor/**`, covering the new module and the new test file. No new test directory was created, so the v3.15.8 QG-2 hazard does not apply; collection verified empirically at 18 files, up from 17.

## Deviations from the plan

1. **A new `not-connected` error code**, not named in the plan. 3.2 asks the status bar and panel to distinguish an unconnected install from a failure, and there was no way to tell them apart - both arrived as `missing-token`.
2. **The decline flag is checked before the interactive call rather than only written after it.** The plan's step three describes the write; the read is what makes the decline durable rather than per-session.
3. **MT-1 closed here**, which belongs to Phase 1 rather than Phase 3. Its own suggested next step nominated this phase, and the harness existed only because of it.

## Known gaps recorded

`MT-1` **resolved**. `NI-5` opened: on a truly fresh install the sequence passes `{ scope: <configured>, name: "pending" }` purely to select scope candidates, because with nothing configured there is no session and therefore no detectable owner. The placeholder never reaches a billing request - the refresh that follows re-resolves the owner - but it reads oddly. The fix is to pass a scope rather than an owner, best done when Phase 4 or 5 is already touching that file. Zero release blockers.

## Next steps

Phase 4, "Panel shell - three buttons, inline settings, teal meters". It has all three prerequisites now: Phase 1's renamed ids, Phase 2's percentages to draw, and this phase's Connect affordance. It ports an existing in-repo pattern (`extensions/claude-usage-monitor/src/settingsPanel.ts` exports `settingsStylesCss()`, `settingsSectionHtml()`, and `settingsScriptJs()` for the dashboard to embed), so it is the least speculative phase remaining.

NI-5 is cheap to fold into Phase 4 while that file is open.
