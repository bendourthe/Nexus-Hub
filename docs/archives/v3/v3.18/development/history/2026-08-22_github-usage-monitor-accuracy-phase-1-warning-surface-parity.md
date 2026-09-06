# Session History - GitHub Usage Monitor Accuracy Phase 1: Warning-Surface Parity

**Date**: 2026-08-22
**Branch**: `feat/v3.18.1-github-usage-monitor-accuracy`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.1-github-usage-monitor-accuracy.md`](../../plans/v3.18.1-github-usage-monitor-accuracy.md)
**Phase**: 1 - Warning-surface parity
**Environment**: Windows 11, Git Bash, Node with `vitest` 4.1.10; GNU Make unavailable, so `make` targets run as their constituent commands
**Outcome**: The threshold warning is one surface again. The webview is revealed on every crossing, the competing toast and its coupled auto-dismiss timer are gone, and a cross-extension parity test verified to fail in both directions now guards the four monitors against silent divergence.

## 1. Starting State

- **Starting commit**: `3a26cc11` (develop, merged from `main` after the v3.18.0 release)
- **Extension version**: 0.3.3
- **Worktree**: clean
- **Routing decision**: the plan recorded `strong / medium`. Implementation ran on Opus 5, which is the `strong` tier on the Anthropic column of the plan's model map, so the recommendation was confirmed rather than changed.

## 2. The Defect Had Two Independent Halves

The report was "the warning arrives as a native toast". Both halves had to be fixed, because either one alone reproduces the symptom.

**The reveal never happened.** `WarningViewProvider.show()` rewrote the HTML of an already-resolved view and stopped there. The view is registered with `retainContextWhenHidden: true`, so a view the user dismissed stays resolved from the host's side. Every alert after the first in a session therefore rewrote an invisible panel. `extensions/claude-usage-monitor/src/warningView.ts:86-91` does call `this.view.show(true)`; this was drift, not a design difference.

**The toast and the auto-dismiss timer were coupled.** `maybeShowAlert` fired `showWarningMessage` and scheduled `scheduleWarningDismissal(notificationTimeoutSeconds * 1000)`, and the toast's `.then` handler was what cleared that timer. Removing the toast alone would have left the panel auto-hiding after 12 seconds with nothing to cancel it - a worse bug than the one being fixed. They came out together.

## 3. What Changed

| File | Change |
|---|---|
| `src/warningView.ts` | `show()` calls a new private `reveal()` on the view-exists branch; `reveal()` guards on `typeof view.show === "function"` and falls back to the `.focus` command. `dismiss()` clears `this.view`, matching the Claude monitor's `hide()`. |
| `src/extension.ts` | `maybeShowAlert` reveals the webview only. The toast, the timer, the `dismissed` flag, and the exported `scheduleWarningDismissal` are gone. The threshold dedupe is untouched. |
| `package.json` | `notificationTimeoutSeconds` retained as a key, marked with a `deprecationMessage` and a description stating it no longer applies. |
| `src/settingsPanel.ts` | The editable row for the dead setting removed, along with its `SettingsValues` field, its `config.get`, and its validator entry. |
| `test/warning-parity.test.ts` | New. Cross-extension source-text parity over all four monitors. |
| `test/warning-reveal.test.ts` | New. Four tests including the reported symptom: a second crossing must reveal. |
| `test/ui.test.ts` | Dropped the auto-dismiss test and the fixture field for the removed setting. |

## 4. The Setting Was Deprecated, Not Deleted

`notificationTimeoutSeconds` had three readers: the alert path (functional), `settingsPanel.ts` (an editable control), and `migration.ts` (the 0.3.x rename map). Removing the alert path left the panel offering an editable control that changed nothing, which is a worse state than either keeping or removing it. The resolution splits the difference along the line of who owns the value:

- **The key stays** in `package.json`, because a user may have set it and a removed key surfaces as "Unknown Configuration Setting".
- **The migration entry stays**, so an existing 0.3.x value still migrates rather than being orphaned.
- **The control goes**, because an inert editable input is a lie about what the extension does.

## 5. The Parity Test Was Verified in Both Directions

A source-text parity test is trivially fail-open: if the regex locating the alert path stops matching after a rename, the test passes while asserting nothing. Two guards were added against that, and the second was checked empirically:

1. The test asserts the warning-view show call was **found** (`index > -1`) with a failure message telling the next maintainer the alert path moved, so a rename fails loudly rather than skipping quietly.
2. The toast was temporarily re-introduced into `maybeShowAlert` and the suite re-run. It failed on exactly the intended assertion; the toast was then reverted and the suite re-run green.

Exemptions are a named empty constant (`DOCUMENTED_EXEMPTIONS`) rather than a loosened pattern, so a future divergence has to be written down to be allowed.

## 6. Verification

| Gate | Result |
|---|---|
| `npm run compile` | Pass |
| `npm test` | 439 tests, 28 files, all pass |
| `npm run test:coverage` | Statements 82.33%, branches 78.52%, lines 85.29% - above the 80% line threshold |
| Parity test, defect re-introduced | Fails on the intended assertion |
| Parity test, defect removed | Passes |
| `.github/workflows/github-usage-monitor.yml` | **No-op, recorded deliberately.** The runner is `vitest run`, which discovers `test/*.test.ts` without enumeration, and the path filter `extensions/github-usage-monitor/**` already covers both new files. No new command is needed. |

## 7. Deferred to Later Phases

- The drawdown model itself (defect two) is Phase 2 and untouched here, deliberately, so a failed drawdown change cannot be confused with a warning-surface change.
- The version bump to 0.4.0 and the CHANGELOG entry belong to Phase 6.2, which announces all three defects as one.

## 8. Next Step

Phase 2: thread `pricePerUnit` through the pipeline and derive the drawdown weight from it, retiring `OS_DRAWDOWN_WEIGHTS` as a behavioral input.
