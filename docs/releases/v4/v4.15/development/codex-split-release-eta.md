# Codex Split and Release ETA

Summary: maintenance requested on 2026-11-16 to open the Codex editor-title action beside the current editor and show separate next-release and whole-scope forecasts in compact/full status. Release maintainers use this record for v4.15.2 integration, artifact provenance and installed-client follow-up.

## Scope

Work is isolated in `fix/codex-split-and-release-eta`, based on `origin/develop` at `9112587a6`. The previous portable status change is already integrated through PR #673. This change extends that shared owner and preserves unrelated primary-checkout edits and active release work. It does not publish, install into the live user profile or complete another agent's release-plan tasks.

## Codex Navigation

The installed provider's native new-panel command opens `openai-codex://route/extension/panel/new` with `vscode.openWith`, custom-editor type `chatgpt.conversationEditor`, and the active editor column. It does not accept a placement override. Nexus Hub now opens that same native route using the public VS Code `ViewColumn.Beside` option. This retains the current tab and opens Codex beside it without pre-splitting an empty group or changing the vendor's code. The existing `codexTabs` preference and agent-accessible command remain compatible; switching it off retains sidebar behavior. The UI label and help text describe the split behavior.

The shared production routing function is exported for the native qualification entry point in `extensions/nexus-hub-settings/scripts/codex-split-live.js`. The probe runs in a private VS Code profile with a local copy of the real Codex provider and a private Codex home. It exercises the native custom editor from both a text editor and an existing VS Code webview. It does not activate Settings background synchronization or replace the user's installed extension. Toolbar registration, preference handling, untrusted-workspace refusal and availability before slow adapter setup are covered by extension tests.

## Release Forecasts

Both status formats now put bold Last released and Next release versions on separate lines near the top. Next release carries its own Release ETA, blocking condition, confidence and estimate basis. Whole <scope> completion explicitly labels the time for the entire reported scope; for a minor run this includes the remaining releases and minor closure. The progress line no longer contains an ambiguous `time left` field.

The snapshot's additive `next_release` object contains `version`, `remaining`, `condition`, `confidence` and `basis`. Malformed forecasts are rejected. Legacy snapshots remain readable but explicitly show that the next-release estimate was not supplied. The producer resolves the next eligible release from the authoritative inventory and includes remaining validation, integration, packaging and publication work. It must not infer a release deadline by incrementing a version or reusing the whole-minor estimate. Unknown external waits stay unknown or make an estimate conditional.

For illustration only, a report could say `Next release: v4.15.2 | Release ETA: ~1-2 h after the checker PR merges`, while separately saying `Whole v4.15 completion: ~2-4 d`. These are explanatory examples, not forecasts for the current release. The release coordinator owns the live observations needed to produce those estimates.

## Qualification

- The new routing and forecast regressions failed against the original behavior before implementation.
- The final Settings compile passed; all 30 test files passed with 493 tests and three existing skips.
- The reporting, command-contract and platform-delivery selection passed all 70 tests.
- The real VS Code extension-host probe exited 0 with Codex 26.1111.21308. It observed one initial group, two groups after opening Codex, original column 1 retained, and Codex in column 2. The webview-origin check likewise retained the visible original panel in column 1 with Codex in column 2.
- VSIX packaging and package-content verification passed. The actual archive's compiled extension and panel script match the qualified working-tree bytes.
- [Proof](codex-split-release-eta-proof.json) records the native observations, test counts and VSIX hash. The shared [compact](portable-status-compact-example.md) and [full](portable-status-full-example.md) examples were regenerated from the updated renderer.

## Integration

This is one local maintenance phase with one local commit. No pipeline changes or remote CI were started. The existing suites collect the new regression cases. Integrate through the normal develop/release path under existing authority, reconcile shared tracker and reporting files with current work, and include both requests in v4.15.2's release notes. Keep the release agent's extension-version ownership; the candidate VSIX retains the source version 0.8.8 and is not a published replacement.

After authorized installation, verify the actual toolbar click on initial activation and after reload, both preference positions, and status output using fresh release observations. The native probe establishes the production routing function's actual placement against the real provider; it does not establish every installed client's startup state or a live ETA for the current release.

construction-debt: reuse the native custom-editor route and existing preference; add only the release forecast fields, corresponding contract text, regression coverage and a native probe. No provider patch, new setting, dependency, scheduler or separate reporting engine.
