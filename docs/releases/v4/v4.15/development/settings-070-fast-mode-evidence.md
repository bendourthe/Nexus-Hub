# Nexus Hub 0.7.0 Verification

This record covers the shared Fast mode switch, the persistent Codex tab preference, installed payload checks, and the remaining Claude Fast verification gap. It is local implementation and installation evidence, not a remote release qualification.

## Changes

- Added Fast mode inside Global effort level. Speed and effort have separate revisions, so changing one preserves a manual override of the other. Apply to all reapplies both configured defaults.
- Added Editor > Open Codex in tabs. The existing Codex toolbar icon opens independent editor tabs when enabled and the native activity pane when disabled. The editor toolbar retains Codex History. The vendor menu falls back to its native sidebar command when Nexus is disabled.
- Stored speed and navigation preferences in `~/.nexus-hub/session-defaults.json`, outside the extension package. An unset Fast preference preserves native speeds. Existing installer delivery includes the extension and its exact-build adapter installation at activation.
- Started live adapters when workspace trust is granted after an initially untrusted activation. Added a regression test for this startup path.

## Automated Evidence

- Final extension suite: 391 passed, one skipped, zero failed. TypeScript compilation and package-content verification passed.
- Disposable Cursor 3.29.9 adapter checks passed syntax, repeat installation, preservation of independent edits, exact restoration, unknown-build rejection, and retention of all six integrity entries.
- Disposable Claude Code 2.1.318 and Codex 26.1021.22027 adapter checks passed parsing, repeat installation, preservation of independent edits, exact restoration, and rejection of redirected receipts.
- All 30 package files matched the registered 0.7.0 installations in VS Code, Cursor, and Antigravity. The installer-added `package.json` metadata was excluded from the semantic manifest comparison.
- The actual installed native files matched their receipt hashes. Cursor's workbench checksum matched its product manifest, which retained all six entries.

## Native Observations

- In a disposable trusted VS Code window, changing Nexus Fast off/on removed/restored Codex's native lightning indicator while effort remained Medium. Selecting Standard manually in Codex persisted through polling while Nexus stayed Fast. Apply to all restored the native Fast indicator. A new Codex tab also received Fast.
- In the installed Cursor test window, the built-in Grok 4.7 Agent changed live between Medium and Medium Fast. The existing effort value remained Medium.
- Turning Open Codex in tabs off made the existing editor toolbar icon open the activity pane. Turning it on made the same icon open an additional Codex editor tab. Codex History opened a local-session picker, which was dismissed without opening a conversation.
- Both the normal-width and narrow sidebar controls were observed. Narrow effort labels use the existing vertical fallback instead of overlapping.
- No model prompts were submitted during Fast verification.

## Open Verification

Claude's installed native Opus 5.5 model menu did not expose a Fast control during the blank-session test. The adapter preserves the native supported-model check and uses the native `/fast on` and `/fast off` actions when available. Its action wiring passed focused tests, but live Claude Fast application was not confirmed. Do not describe Claude Fast as verified. Native restrictions and any usage-credit requirements were not bypassed.

Cursor Fast manual overrides and Apply to all passed adapter tests; they were not separately exercised in the native Cursor UI. Fast changes affect subsequent requests, not a response already running. Existing native effort behavior was preserved; this run did not repeat every earlier effort scenario.

## Restoration and Delivery

The original Nexus preference was Medium and is again exactly `{"default_effort":"medium"}`. The test-only shared session-defaults file was removed after restoring all three Cursor drafts to their original Medium Fast state. Cursor was reloaded to clear the temporary default projection. Claude's native user settings still have no `fastMode` key. The disposable VS Code test window was closed; the user's working VS Code windows were not reloaded or closed. Codex tabs use the original default of on.

The final VSIX SHA-256 is `20af091774c066b7bd331903b7519f8affb44ababe15afbd292269f3b843a97a`. Local reports and the package are under `C:/Users/you/Documents/nx-settings070-qualification/`: `final-tests.json`, `final-delivery.json`, `final-payloads.json`, `final-native-receipts.json`, and the `final-checks` reports. The primary checkout retained its 34 unrelated changed files.

Two documentation writes were not recorded within the edit guard's two-minute window after a command ran from the wrong directory. Their record attempts were refused. Their current contents were preserved, with no further edits or baseline acceptance. No edit-guard accept operation was used in this run. The progress tracker keeps the 0.7.0 item open because live Claude Fast verification is outstanding.
