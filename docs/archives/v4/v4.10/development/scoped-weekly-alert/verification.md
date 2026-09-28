# v4.10 WN-4 - scoped weekly alert verification

This frozen record qualifies an opt-in model-scoped weekly threshold on the Claude Usage Monitor. It covers synthetic provider data in an isolated VS Code host, not a live account fetch or a paid provider call.

## Boundary

- Date: 2026-09-24. Base revision: `6a70269e` (`origin/develop` before this follow-up).
- Artifact: `claude-usage-monitor-0.10.0.vsix`, SHA-256 `46ea54b55078e1edb735fa58e1b2631609885770a0eddd40b843c24ee7738dc6`. The VSIX excludes `test/` and includes the compiled extension.
- Host: installed Windows VS Code 1.139.0 with disposable user-data and extensions directories. The test used the unpacked, installed VSIX as its extension-development path and loaded the modules from VS Code's active extension entry. `claudeUsage.autoFetch` was disabled; the provider's `fetchUsage` method returned a synthetic fixture, so no account credential or provider request was used.
- Fixture: session 12%, all-models weekly 34%, scoped weekly Fable 86%, then a second response with session 98% and no scoped limit.

## Observed result

- `npm run compile --silent` passed. Seven Vitest files passed all 24 tests, including selection, default preservation, missing-data no-fallback, settings markup, and dashboard suggestion controls.
- The repository's Windows fast profile passed 17/17; `validate_decision_records.py` accepted all 52 records before this evidence file was added.
- The packaged-host test drove `Claude Usage: Refresh`. With `weeklyScoped` selected, it observed one high-urgency warning, resolved the actual warning sidebar, found `Weekly (Fable)` in its HTML, and saw a status-bar highlight while the status text stayed `12% (current) 34% (week)`.
- With the scoped metric absent and session at 98%, it observed no second threshold warning and no status-bar highlight. Selecting the default `highest` with the 86% scoped bar likewise raised no warning. Switching back to `weeklyScoped` raised a second warning, proving the in-memory notified bucket reset on metric change.
- The final packaged-host renderer log recorded `HOST_SCOPED_THRESHOLD_PASS warnings=2 missing=quiet highest=unchanged switch=reset`. The test process exited successfully, and the extension-host log recorded a clean exit. A nonfatal `Error mutex already exists` line appeared in the main-process log alongside this successful run; no test assertion depended on it.

## Failed attempt retained

The first strict presentation run asserted that the sidebar view was resolved immediately after `show()` returned and failed. A fresh-profile retry waited for the asynchronous view to resolve and passed. The first packaged attempt then patched a duplicate Node module cache entry caused by drive-letter casing (`C:` versus `c:`), so the refresh command used an unpatched provider and the test failed before reaching alert logic. The final test binds to the active extension entry in VS Code's module cache and passed against the same packaged code. These failed-run logs remain in their disposable profiles; the passing result does not rewrite them.

The host run observes code paths and rendered warning HTML, not a visual screenshot of the notification or a live Anthropic account response. The prior v4.10 MT-2 record separately proves the bars painted in VS Code with synthetic stored data.
